package io.github.kkhos.marvellcg;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.os.Build;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.WindowManager;
import android.window.OnBackInvokedCallback;
import android.window.OnBackInvokedDispatcher;
import android.os.Handler;
import android.os.Looper;
import android.net.Uri;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceRequest;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.view.View;
import android.widget.FrameLayout;
import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;
import java.io.*;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.util.concurrent.Executors;
import java.util.concurrent.ExecutorService;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public class MainActivity extends Activity {
    private static final ExecutorService worker = Executors.newSingleThreadExecutor();
    private static volatile PyObject runtime;
    private static volatile String diagnostic = "Starting Python...";
    private static volatile boolean preparing = false;
    private static volatile boolean launching = false;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private WebView web;
    private TextView status;
    private Button start;
    private OnBackInvokedCallback systemBackCallback;
    private boolean backPending;
    private AlertDialog leaveDialog;
    private static final String UI_REVISION = "18";
    private String loadedUrl = "";

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        configureFullscreen();
        if (Build.VERSION.SDK_INT >= 33) {
            systemBackCallback = this::handleBack;
            getOnBackInvokedDispatcher().registerOnBackInvokedCallback(
                    OnBackInvokedDispatcher.PRIORITY_DEFAULT, systemBackCallback);
        }
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        status = new TextView(this);
        status.setTextIsSelectable(true);
        layout.addView(status);
        start = new Button(this);
        start.setText("게임 엔진 시작");
        start.setEnabled(false);
        layout.addView(start);
        web = new WebView(this);
        web.getSettings().setUseWideViewPort(true);
        web.getSettings().setUserAgentString(web.getSettings().getUserAgentString() + " MarvelAndroid");
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(false);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri u = request.getUrl();
                return !("http".equals(u.getScheme()) && "127.0.0.1".equals(u.getHost()) && u.getPort() == 2345);
            }
        });
        web.setVisibility(View.GONE);
        FrameLayout content = new FrameLayout(this);
        content.addView(web, new FrameLayout.LayoutParams(-1, -1));
        layout.addView(content, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(layout);
        hideSystemBars();
        start.setOnClickListener(v -> {
            if (launching) return;
            launching = true;
            start.setEnabled(false);
            worker.execute(() -> {
                try {
                    File root = unpack();
                    runtime.callAttr("start", root.getAbsolutePath());
                } catch (Throwable e) {
                    diagnostic = android.util.Log.getStackTraceString(e);
                    launching = false;
                }
            });
        });
        if (!preparing) {
            preparing = true;
            worker.execute(() -> {
                try {
                    if (!Python.isStarted()) Python.start(new AndroidPlatform(getApplicationContext()));
                    PyObject module = Python.getInstance().getModule("mobile_entry");
                    diagnostic = module.callAttr("probe").toString();
                    runtime = module;
                } catch (Throwable e) {
                    diagnostic = android.util.Log.getStackTraceString(e);
                }
            });
        }
        handler.post(poll);
    }

    private final Runnable poll = new Runnable() {
        public void run() {
            if (isFinishing() || isDestroyed()) return;
            String message = diagnostic;
            if (runtime != null) {
                start.setEnabled(!launching);
                try {
                    String state = runtime.callAttr("status").toString();
                    String url = runtime.callAttr("url").toString();
                    if (launching) message += "\n" + state;
                    if (!url.isEmpty() && !url.equals(loadedUrl)) {
                        // Check readiness off the UI thread; never block rendering.
                        worker.execute(() -> {
                            try (Socket socket = new Socket()) {
                                socket.connect(new InetSocketAddress("127.0.0.1", 2345), 300);
                                runOnUiThread(() -> {
                                    if (isDestroyed() || url.equals(loadedUrl)) return;
                                    loadedUrl = url;
                                    web.setVisibility(View.VISIBLE);
                                    status.setVisibility(View.GONE);
                                    start.setVisibility(View.GONE);
                                    web.loadUrl(url);
                                });
                            } catch (IOException ignored) {}
                        });
                    }
                    if (launching && url.isEmpty() && !loadedUrl.isEmpty()) {
                        web.setVisibility(View.GONE);
                        status.setVisibility(View.VISIBLE);
                        loadedUrl = "";
                    }
                } catch (Throwable e) {
                    message += "\n" + android.util.Log.getStackTraceString(e);
                }
            }
            status.setText(message);
            handler.postDelayed(this, 1000);
        }
    };

    // Update bundled web files only; do not replace user data, engine config or artwork.
    // Full engine/data upgrades need a separate migration design.
    private File unpack() throws IOException {
        File root = new File(getFilesDir(), "game");
        File marker = new File(root, ".installed");
        File uiMarker = new File(root, ".ui-" + UI_REVISION);
        boolean uiOnly = marker.isFile();
        if (uiOnly && uiMarker.isFile()) return root;
        if (!root.isDirectory() && !root.mkdirs()) throw new IOException("Cannot create game folder");
        String prefix = root.getCanonicalPath() + File.separator;
        try (ZipInputStream zip = new ZipInputStream(getAssets().open("game.zip"))) {
            ZipEntry entry;
            byte[] buf = new byte[65536];
            while ((entry = zip.getNextEntry()) != null) {
                if (uiOnly && !entry.getName().startsWith("public/")) {
                    zip.closeEntry();
                    continue;
                }
                File out = new File(root, entry.getName());
                if (!out.getCanonicalPath().startsWith(prefix)) throw new IOException("Unsafe bundle path");
                if (entry.isDirectory()) {
                    if (!out.isDirectory() && !out.mkdirs()) throw new IOException("mkdir " + out);
                } else {
                    File parent = out.getParentFile();
                    if (!parent.isDirectory() && !parent.mkdirs()) throw new IOException("mkdir " + parent);
                    try (OutputStream stream = new FileOutputStream(out)) {
                        int count;
                        while ((count = zip.read(buf)) != -1) stream.write(buf, 0, count);
                    }
                }
                zip.closeEntry();
            }
        }
        if (!marker.isFile() && !marker.createNewFile()) throw new IOException("Cannot mark installed bundle");
        if (!uiMarker.isFile() && !uiMarker.createNewFile()) throw new IOException("Cannot mark UI revision");
        runOnUiThread(() -> { if (!isDestroyed()) web.clearCache(true); });
        return root;
    }

    private void configureFullscreen() {
        // Allow the content background to fill landscape cutout areas as well.
        if (Build.VERSION.SDK_INT >= 28) {
            WindowManager.LayoutParams attrs = getWindow().getAttributes();
            attrs.layoutInDisplayCutoutMode = Build.VERSION.SDK_INT >= 30
                    ? WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_ALWAYS
                    : WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
            getWindow().setAttributes(attrs);
        }
        if (Build.VERSION.SDK_INT >= 30) getWindow().setDecorFitsSystemWindows(false);
        hideSystemBars();
    }

    private void hideSystemBars() {
        if (Build.VERSION.SDK_INT >= 30) {
            WindowInsetsController controller = getWindow().getInsetsController();
            if (controller != null) {
                controller.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
                controller.hide(WindowInsets.Type.systemBars());
            }
        } else {
            getWindow().getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        }
    }

    @Override protected void onResume() {
        super.onResume();
        hideSystemBars();
    }

    @Override public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideSystemBars();
    }

    @Override public void onBackPressed() {
        handleBack();
    }

    private void handleBack() {
        if (backPending || (leaveDialog != null && leaveDialog.isShowing())) return;
        if (web == null || web.getVisibility() != View.VISIBLE) {
            moveTaskToBack(true);
            return;
        }
        backPending = true;
        web.evaluateJavascript("!!((window.MarvelDeckTouch && window.MarvelDeckTouch.back && window.MarvelDeckTouch.back()) || (window.MarvelSetup && window.MarvelSetup.back()) || (window.MarvelTouch && window.MarvelTouch.back()))", result -> {
            backPending = false;
            if (isDestroyed() || isFinishing() || "true".equals(result)) return;
            String current = web.getUrl();
            Uri uri = current == null ? Uri.EMPTY : Uri.parse(current);
            String path = uri.getPath();
            boolean gamePage = "/marvel".equals(path) || "/watch".equals(path)
                    || "/public/marvel.html".equals(path)
                    || ("/".equals(path) && uri.getQuery() != null);
            if ("/main".equals(path) || "/public/main.html".equals(path)) {
                moveTaskToBack(true);
            } else if (gamePage) {
                leaveDialog = new AlertDialog.Builder(this).setTitle("게임 화면에서 나갈까요?")
                        .setMessage("차례 종료나 되돌리기는 실행되지 않습니다. 필요하면 먼저 게임을 저장하세요.")
                        .setNegativeButton("계속 플레이", null)
                        .setPositiveButton("나가기", (d, w) -> web.loadUrl(loadedUrl)).create();
                leaveDialog.setOnDismissListener(d -> { leaveDialog = null; hideSystemBars(); });
                leaveDialog.show();
            } else if ("/scene".equals(path) || "/public/scene.html".equals(path)) {
                web.loadUrl(loadedUrl);
            } else if (web.canGoBack()) {
                web.goBack();
            } else {
                moveTaskToBack(true);
            }
        });
    }

    @Override protected void onDestroy() {
        if (Build.VERSION.SDK_INT >= 33 && systemBackCallback != null) {
            getOnBackInvokedDispatcher().unregisterOnBackInvokedCallback(systemBackCallback);
        }
        handler.removeCallbacks(poll);
        web.destroy();
        super.onDestroy();
    }
}
