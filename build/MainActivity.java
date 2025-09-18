package com.example.collector;

import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;
import java.io.*;

public class MainActivity extends AppCompatActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        new Thread(() -> {
            try {
                File outFile = new File(getFilesDir(), "b_collector_monitor");
                copyAsset("b_collector_monitor", outFile);
                outFile.setExecutable(true);

                Process proc = new ProcessBuilder(outFile.getAbsolutePath(), "192.168.1.50")
                        .redirectErrorStream(true)
                        .start();

                BufferedReader reader = new BufferedReader(new InputStreamReader(proc.getInputStream()));
                String line;
                while ((line = reader.readLine()) != null) {
                    System.out.println("[B_MONITOR] " + line);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();
    }

    private void copyAsset(String name, File outFile) throws IOException {
        try (InputStream in = getAssets().open(name);
             OutputStream out = new FileOutputStream(outFile)) {
            byte[] buffer = new byte[4096];
            int read;
            while ((read = in.read(buffer)) != -1) {
                out.write(buffer, 0, read);
            }
        }
    }
}
