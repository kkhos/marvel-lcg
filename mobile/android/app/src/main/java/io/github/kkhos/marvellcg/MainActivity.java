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
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.content.res.ColorStateList;
import android.view.Gravity;
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
    private FrameLayout splash;
    private LinearLayout failurePanel;
    private ProgressBar loadingBar;
    private boolean splashFading;
    private static final String UI_REVISION = "33";
    private String loadedUrl = "";

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        FrameLayout layout = new FrameLayout(this);
        layout.setBackgroundColor(0xff0a1511);
        web = new WebView(this);
        web.getSettings().setUseWideViewPort(true);
        // Use the existing wizard's native-app marker to suppress its Back button.
        web.getSettings().setUserAgentString(web.getSettings().getUserAgentString() + " MarvelAndroid");
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setAllowFileAccess(false);
        web.getSettings().setAllowContentAccess(false);
        web.setWebViewClient(new WebViewClient() {
            @Override public void onPageCommitVisible(WebView view, String url) {
                super.onPageCommitVisible(view, url);
                if (!loadedUrl.isEmpty() && failurePanel != null &&
                        failurePanel.getVisibility() != View.VISIBLE) hideSplash();
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri u = request.getUrl();
                return !("http".equals(u.getScheme()) && "127.0.0.1".equals(u.getHost()) && u.getPort() == 2345);
            }
        });
        web.setVisibility(View.GONE);
        web.setBackgroundColor(0xff0a1511);
        layout.addView(web, new FrameLayout.LayoutParams(-1, -1));
        createSplash(layout);
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

    private int dp(float n) {
        return Math.round(n * getResources().getDisplayMetrics().density);
    }

    private Bitmap splashBitmap(String name) {
        try (InputStream in = getAssets().open("splash/" + name)) {
            return BitmapFactory.decodeStream(in);
        } catch (IOException e) {
            return null;
        }
    }

    private void createSplash(FrameLayout root) {
        splash = new FrameLayout(this);
        splash.setBackground(new GradientDrawable(GradientDrawable.Orientation.TL_BR,
                new int[]{0xff223f32, 0xff091510, 0xff050a08}));
        splash.setClickable(true);
        root.addView(splash, new FrameLayout.LayoutParams(-1, -1));

        Bitmap background = splashBitmap("doom.webp");
        if (background != null) {
            ImageView image = new ImageView(this);
            image.setScaleType(ImageView.ScaleType.CENTER_CROP);
            image.setImageBitmap(background);
            splash.addView(image, new FrameLayout.LayoutParams(-1, -1));
        }

        View shade = new View(this);
        shade.setBackground(new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,
                new int[]{0x05000000, 0x20000000, 0xc008110d}));
        splash.addView(shade, new FrameLayout.LayoutParams(-1, -1));
        View bottomShade = new View(this);
        bottomShade.setBackground(new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,
                new int[]{0x00000000, 0xc0050a08}));
        splash.addView(bottomShade, new FrameLayout.LayoutParams(-1, dp(76), Gravity.BOTTOM));

        ImageView logo = new ImageView(this);
        logo.setContentDescription("Marvel Champions: The Card Game");
        logo.setScaleType(ImageView.ScaleType.FIT_CENTER);
        logo.setImageBitmap(splashBitmap("champions.png"));
        if (logo.getDrawable() instanceof android.graphics.drawable.BitmapDrawable) {
            ((android.graphics.drawable.BitmapDrawable) logo.getDrawable()).setFilterBitmap(true);
        }
        FrameLayout.LayoutParams logoParams = new FrameLayout.LayoutParams(dp(220), dp(119),
                Gravity.END | Gravity.CENTER_VERTICAL);
        logoParams.rightMargin = dp(24);
        splash.addView(logo, logoParams);
        splash.addOnLayoutChangeListener((v, l, t, r, b, ol, ot, or, ob) -> {
            int width = r - l, height = b - t;
            if (width <= 0 || height <= 0 || (width == or - ol && height == ob - ot)) return;
            int logoWidth = Math.round(Math.min(width * .32f, height * .72f));
            FrameLayout.LayoutParams lp = (FrameLayout.LayoutParams) logo.getLayoutParams();
            lp.width = logoWidth;
            lp.height = Math.round(logoWidth * 435f / 804f);
            lp.rightMargin = Math.round(width * .06f);
            logo.setLayoutParams(lp);
        });

        loadingBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        loadingBar.setIndeterminate(true);
        loadingBar.setIndeterminateTintList(ColorStateList.valueOf(0xff72d7a3));
        loadingBar.setContentDescription("게임 로딩 중");
        FrameLayout.LayoutParams barParams = new FrameLayout.LayoutParams(-1, dp(4), Gravity.BOTTOM);
        barParams.setMargins(dp(24), 0, dp(24), dp(18));
        loadingBar.setPadding(0, 0, 0, 0);
        loadingBar.setBackgroundColor(0x66478b70);
        splash.addView(loadingBar, barParams);

        // Only actual failures show diagnostic text and a restart action.
        failurePanel = new LinearLayout(this);
        failurePanel.setOrientation(LinearLayout.VERTICAL);
        failurePanel.setGravity(Gravity.CENTER);
        failurePanel.setPadding(dp(16), dp(12), dp(16), dp(12));
        failurePanel.setBackgroundColor(0xe6111b19);
        failurePanel.setVisibility(View.GONE);
        FrameLayout.LayoutParams errorParams = new FrameLayout.LayoutParams(-1, -2, Gravity.CENTER);
        errorParams.setMargins(dp(24), dp(12), dp(24), dp(12));
        splash.addView(failurePanel, errorParams);
        status = new TextView(this);
        status.setTextColor(Color.WHITE);
        status.setTextSize(12);
        status.setMaxLines(7);
        status.setMovementMethod(new android.text.method.ScrollingMovementMethod());
        failurePanel.addView(status, new LinearLayout.LayoutParams(-1, -2));
        start = new Button(this);
        start.setText("앱 종료 후 다시 실행");
        failurePanel.addView(start);
    }

    private void showSplash() {
        splash.animate().cancel();
        splashFading = false;
        splash.setAlpha(1f);
        splash.setVisibility(View.VISIBLE);
        loadingBar.setVisibility(View.VISIBLE);
        failurePanel.setVisibility(View.GONE);
    }

    private void hideSplash() {
        if (splash.getVisibility() != View.VISIBLE || splashFading) return;
        splashFading = true;
        splash.animate().alpha(0f).setDuration(220).withEndAction(() -> {
            splash.setVisibility(View.GONE);
            loadingBar.setVisibility(View.GONE);
            splashFading = false;
        }).start();
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
                                    showSplash();
                                    web.setVisibility(View.VISIBLE);
                                    web.loadUrl(url);
                                });
                            } catch (IOException ignored) {}
                        });
                    }
                    if (launching && url.isEmpty() && !loadedUrl.isEmpty()) {
                        web.setVisibility(View.GONE);
                        showSplash();
                        loadedUrl = "";
                    }
                } catch (Throwable e) {
                    failed = true;
                    message = android.util.Log.getStackTraceString(e);
                }
            }
            if (failed) {
                web.setVisibility(View.GONE);
                showSplash();
                loadingBar.setVisibility(View.GONE);
                failurePanel.setVisibility(View.VISIBLE);
                if (!launching) message = diagnostic;
                status.setText(message);
            }
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
                if (uiOnly && !entry.getName().startsWith("public/")
                        && !entry.getName().equals("engine/device/web/server/server_new_game.py")
                        && !entry.getName().equals("engine/device/web/server/server_files.py")) {
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
        if (web.getVisibility() != View.VISIBLE || splash.getVisibility() == View.VISIBLE) {
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
        splash.animate().cancel();
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
