package io.github.kkhos.marvellcg;

import android.app.Activity;
import android.os.Bundle;
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
    private String loadedUrl = "";

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        status = new TextView(this);
        status.setTextIsSelectable(true);
        layout.addView(status);
        start = new Button(this);
        start.setText("Start game engine");
        start.setEnabled(false);
        layout.addView(start);
        web = new WebView(this);
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
        layout.addView(web, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(layout);
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

    // Fresh-install PoC only: keep saves/artwork in the extracted game folder.
    // Never overwrite existing user files. Upgrade/migration is a separate milestone.
    private File unpack() throws IOException {
        File root = new File(getFilesDir(), "game");
        File marker = new File(root, ".installed");
        if (marker.isFile()) return root;
        if (!root.isDirectory() && !root.mkdirs()) throw new IOException("Cannot create game folder");
        String prefix = root.getCanonicalPath() + File.separator;
        try (ZipInputStream zip = new ZipInputStream(getAssets().open("game.zip"))) {
            ZipEntry entry;
            byte[] buf = new byte[65536];
            while ((entry = zip.getNextEntry()) != null) {
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
        if (!marker.createNewFile()) throw new IOException("Cannot mark installed bundle");
        return root;
    }

    @Override protected void onDestroy() {
        handler.removeCallbacks(poll);
        web.destroy();
        super.onDestroy();
    }
}
