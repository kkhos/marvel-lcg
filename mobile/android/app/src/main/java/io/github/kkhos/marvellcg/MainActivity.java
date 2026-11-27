package io.github.kkhos.marvellcg;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.os.Build;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.view.WindowManager;
import android.graphics.Insets;
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
    private static final String UI_REVISION = "24";
    private String loadedUrl = "";

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        status = new TextView(this);
        status.setText("Marvel Champions\n게임 로딩 중…");
        status.setGravity(android.view.Gravity.CENTER);
        status.setTextSize(20);
        layout.addView(status);
        start = new Button(this);
        start.setText("앱 종료 후 다시 실행");
        start.setVisibility(View.GONE);
        start.setEnabled(false);
        layout.addView(start);
        web = new WebView(this);
        web.getSettings().setUseWideViewPort(true);
        // Use the existing wizard's native-app marker to suppress its Back button.
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
        // Android 15+ enforces edge-to-edge for targetSdk 35. Keep the
        // WebView outside system bars/cutouts until fullscreen is applied.
        if (Build.VERSION.SDK_INT >= 30) {
            getWindow().setDecorFitsSystemWindows(false);
            layout.setOnApplyWindowInsetsListener((v, insets) -> {
                // Fullscreen step 2: transient system bars must not resize the
                // game viewport. Preserve physical display cutout protection.
                Insets safe = insets.getInsets(WindowInsets.Type.displayCutout());
                v.setPadding(safe.left, safe.top, safe.right, safe.bottom);
                return insets;
            });
            layout.requestApplyInsets();
        }
        // Fullscreen isolation step 3: extend into the display cutout
        // only after the content is attached. If the window policy fails,
        // keep the tested step-2 inset listener and safe padding.
        layout.post(() -> {
            if (isDestroyed() || isFinishing() || Build.VERSION.SDK_INT < 30) return;
            try {
                WindowManager.LayoutParams attrs = getWindow().getAttributes();
                attrs.layoutInDisplayCutoutMode =
                        WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_ALWAYS;
                getWindow().setAttributes(attrs);
                layout.setOnApplyWindowInsetsListener((v, insets) -> {
                    v.setPadding(0, 0, 0, 0);
                    return insets;
                });
                layout.setPadding(0, 0, 0, 0);
                layout.requestApplyInsets();
            } catch (RuntimeException e) {
                android.util.Log.w("MarvelChampions", "Cutout extension unavailable; keeping safe insets", e);
            }
        });
        // Fullscreen isolation step 1: hide system bars after content attachment.
        // Legacy onBackPressed remains unchanged.
        layout.post(() -> {
            if (isDestroyed() || isFinishing()) return;
            try {
                if (Build.VERSION.SDK_INT >= 30) {
                    WindowInsetsController controller = getWindow().getInsetsController();
                    if (controller != null) {
                        controller.setSystemBarsBehavior(
                                WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
                        controller.hide(WindowInsets.Type.systemBars());
                    }
                } else {
                    getWindow().getDecorView().setSystemUiVisibility(
                            View.SYSTEM_UI_FLAG_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
                }
            } catch (RuntimeException e) {
                android.util.Log.w("MarvelChampions", "Fullscreen bars unavailable; keeping normal window", e);
            }
        });
        start.setOnClickListener(v -> finishAndRemoveTask());
        if (!preparing) {
            preparing = true;
            launching = true;
            worker.execute(() -> {
                try {
                    if (!Python.isStarted()) Python.start(new AndroidPlatform(getApplicationContext()));
                    PyObject module = Python.getInstance().getModule("mobile_entry");
                    runtime = module;
                    File root = unpack();
                    module.callAttr("start", root.getAbsolutePath());
                } catch (Throwable e) {
                    diagnostic = android.util.Log.getStackTraceString(e);
                    launching = false;
                }
            });
        }
        handler.post(poll);
    }

    private final Runnable poll = new Runnable() {
        public void run() {
            if (isFinishing() || isDestroyed()) return;
            String message = "Marvel Champions\n게임 로딩 중…";
            boolean failed = !launching;
            if (runtime != null) {
                
                try {
                    String state = runtime.callAttr("status").toString();
                    String url = runtime.callAttr("url").toString();
                    if (state.startsWith("Traceback") || state.startsWith("Engine stopped")) { failed = true; message = state; }
                    else if (launching) message += "\n" + state;
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
                    failed = true;
                    message = android.util.Log.getStackTraceString(e);
                }
            }
            if (failed) {
                web.setVisibility(View.GONE);
                status.setVisibility(View.VISIBLE);
                start.setVisibility(View.VISIBLE);
                start.setEnabled(true);
                if (!launching) message = diagnostic;
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

    @Override public void onBackPressed() {
        handleBack();
    }

    private void handleBack() {
        if (web.getVisibility() != View.VISIBLE) {
            new AlertDialog.Builder(this).setTitle("게임을 종료할까요?")
                    .setNegativeButton("취소", null)
                    .setPositiveButton("종료", (d, w) -> finishAndRemoveTask()).show();
            return;
        }
        web.evaluateJavascript("!!((window.MarvelDeckTouch && window.MarvelDeckTouch.back && window.MarvelDeckTouch.back()) || (window.MarvelSetup && window.MarvelSetup.back()) || (window.MarvelTouch && window.MarvelTouch.back()))", result -> {
            if (isDestroyed() || "true".equals(result)) return;
            String current = web.getUrl();
            Uri uri = current == null ? Uri.EMPTY : Uri.parse(current);
            String path = uri.getPath();
            boolean gamePage = "/marvel".equals(path) || "/watch".equals(path)
                    || "/public/marvel.html".equals(path)
                    || ("/".equals(path) && uri.getQuery() != null);
            if (gamePage) {
                new AlertDialog.Builder(this).setTitle("게임 화면에서 나갈까요?")
                        .setMessage("차례 종료나 되돌리기는 실행되지 않습니다. 필요하면 먼저 게임을 저장하세요.")
                        .setNegativeButton("계속 플레이", null)
                        .setPositiveButton("나가기", (d, w) -> web.loadUrl(loadedUrl)).show();
            } else if (web.canGoBack()) {
                web.goBack();
            } else {
                new AlertDialog.Builder(this).setTitle("게임을 종료할까요?")
                    .setNegativeButton("취소", null)
                    .setPositiveButton("종료", (d, w) -> finishAndRemoveTask()).show();
            }
        });
    }

    @Override protected void onDestroy() {
        handler.removeCallbacks(poll);
        web.stopLoading();
        if (web.getParent() instanceof android.view.ViewGroup) ((android.view.ViewGroup) web.getParent()).removeView(web);
        web.destroy();
        super.onDestroy();
        // The upstream GameRun loop has no cooperative process-stop API.
        // Only an explicit Activity finish ends the process; backgrounding or
        // configuration recreation must preserve the running game.
        if (isFinishing()) {
            worker.shutdownNow();
            android.os.Process.killProcess(android.os.Process.myPid());
        }
    }
}
