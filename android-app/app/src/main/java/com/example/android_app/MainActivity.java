package com.example.android_app;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.tts.TextToSpeech;
import android.util.Log;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.TextView;
import androidx.cardview.widget.CardView;
import androidx.core.content.ContextCompat;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Locale;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;

public class MainActivity extends BaseActivity {

    private static final int REFRESH_INTERVAL_MS = 5000;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private Runnable refreshRunnable;

    private TextView tvStatusLabel, tvSsid, tvRssi, tvCameraStatus, tvBatteryValue;
    private ImageView ivStatusIcon;
    private CardView cardStatus, cardWifi, cardBattery, cardCamera;
    private ProgressBar pbBattery;

    private TextToSpeech tts;
    private WebSocket webSocket;
    private OkHttpClient client;
    private String langCode;

    private boolean lastConnectedState = false;
    private boolean lastCameraState = false;
    private int lastBatteryValue = -1;
    private boolean isFirstLoad = true;
    private boolean isTtsInitialized = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_dashboard);

        SharedPreferences settingsPrefs = getSharedPreferences("app_settings", MODE_PRIVATE);
        langCode = settingsPrefs.getString("language", "fr");

        bindViews();
        setupAccessibilityClicks();

        Intent checkIntent = new Intent();
        checkIntent.setAction(TextToSpeech.Engine.ACTION_CHECK_TTS_DATA);
        startActivityForResult(checkIntent, 1);
    }

    private void bindViews() {
        tvStatusLabel  = findViewById(R.id.tvStatusLabel);
        ivStatusIcon   = findViewById(R.id.ivStatusIcon);
        cardStatus     = findViewById(R.id.cardStatus);
        tvSsid         = findViewById(R.id.tvSsid);
        tvRssi         = findViewById(R.id.tvRssi);
        tvCameraStatus = findViewById(R.id.tvCameraStatus);
        tvBatteryValue = findViewById(R.id.tvBatteryValue);
        pbBattery      = findViewById(R.id.pbBattery);
        cardWifi       = findViewById(R.id.cardWifi);
        cardBattery    = findViewById(R.id.cardBattery);
        cardCamera     = findViewById(R.id.cardCamera);
    }

    private void setupAccessibilityClicks() {
        cardStatus.setOnClickListener(v -> lireStatutGlobal());

        if (cardBattery != null) {
            cardBattery.setOnClickListener(v -> {
                String annonceBat = getString(R.string.tts_battery_level, tvBatteryValue.getText().toString());
                vocaliserTexte(annonceBat);
            });
        }

        if (cardWifi != null) {
            cardWifi.setOnClickListener(v -> {
                String annonceWifi = getString(R.string.tts_wifi_prefix) + tvSsid.getText().toString();
                vocaliserTexte(annonceWifi);
            });
        }
        if (cardCamera != null) {
            cardCamera.setOnClickListener(v -> {
                String etatCam = lastCameraState ? getString(R.string.status_ready) : getString(R.string.status_inactive);
                String annonceCam = getString(R.string.label_embedded_camera) + " : " + etatCam;
                vocaliserTexte(annonceCam);
            });
        }
    }

    private void startWebSocketConnection() {
        if (webSocket != null) return;

        client = new OkHttpClient();
        String wsUrl = BuildConfig.GATEWAY_WS_URL;
        Log.d("WS_ANDROID", "Connexion au WebSocket : " + wsUrl);

        Request request = new Request.Builder().url(wsUrl).build();
        WebSocketListener listener = new WebSocketListener() {
            @Override
            public void onOpen(WebSocket webSocket, Response response) {
                Log.d("WS_ANDROID", "Connecté au flux Live.");
            }

            @Override
            public void onMessage(WebSocket webSocket, String text) {
                Log.d("WS_MESSAGE", text);
                parseAndSpeakWebSocketResult(text);
            }

            @Override
            public void onFailure(WebSocket webSocket, Throwable t, Response response) {
                Log.e("WS_ANDROID", "Erreur WebSocket: " + t.getMessage());

            }
        };
        webSocket = client.newWebSocket(request, listener);
    }

    private void parseAndSpeakWebSocketResult(String jsonString) {
        if (tts == null || !isTtsInitialized) return;
        try {
            JSONObject json = new JSONObject(jsonString);
            if (json.optBoolean("success", false)) {
                String mode = json.getString("mode");
                JSONObject resultObj = json.getJSONObject("result");

                if ("money".equals(mode)) {
                    double total = resultObj.getDouble("total");
                    vocaliserTexte(getString(R.string.money_detected, total));
                }
                else if ("ocr".equals(mode)) {
                    String text = resultObj.optString("text", "");
                    String summary = resultObj.optString("summary", "");
                    String textLanguage = resultObj.optString("language", "fr");

                    Locale ocrLocale = "ar".equals(textLanguage) ? new Locale("ar", "MA") :
                            "en".equals(textLanguage) ? Locale.ENGLISH : Locale.FRENCH;

                    String texteALire = summary.isEmpty() ? text : summary;
                    String annoncePrefix = getString(R.string.ocr_text_prefix);

                    if ("ar".equals(textLanguage)) {
                        annoncePrefix = "النص: ";
                    } else if ("en".equals(textLanguage)) {
                        annoncePrefix = "Text: ";
                    } else if ("fr".equals(textLanguage)) {
                        annoncePrefix = "Texte : ";
                    }

                    tts.setLanguage(ocrLocale);
                    tts.speak(annoncePrefix + texteALire, TextToSpeech.QUEUE_FLUSH, null, "tts_ocr");
                }
                else if ("obstacle".equals(mode)) {
                    String annonceVocale = "";
                    if (resultObj.has("result")) {
                        JSONObject sousResultObj = resultObj.getJSONObject("result");
                        Object vocalField = sousResultObj.opt("vocal_message");
                        if (vocalField instanceof JSONObject) {
                            JSONObject vObj = (JSONObject) vocalField;
                            annonceVocale = vObj.optString(langCode, vObj.optString("fr"));
                        } else if (vocalField instanceof String) {
                            annonceVocale = (String) vocalField;
                        }
                    }
                    if (!annonceVocale.isEmpty()) vocaliserTexte(annonceVocale);
                }
            }
        } catch (Exception e) {
            Log.e("WS_PARSE", "Erreur Parsing WebSocket", e);
        }
    }

    private static final String STATIC_STATUS_JSON = "{\n" +
            "  \"success\": true,\n" +
            "  \"esp32\": {\n" +
            "    \"ip\": \"192.168.100.110\",\n" +
            "    \"wifi_ssid\": \"dlink-DBAC\",\n" +
            "    \"wifi_rssi\": -59,\n" +
            "    \"camera_status\": \"OK\",\n" +
            "    \"mode\": \"none\",\n" +
            "    \"mode_id\": 0,\n" +
            "    \"mode_time_ms\": 0,\n" +
            "    \"battery_voltage\": 4.19,\n" +
            "    \"battery_percent\": 99,\n" +
            "    \"api_upload_enabled\": true,\n" +
            "    \"api_host\": \"192.168.100.109\",\n" +
            "    \"api_port\": 8000,\n" +
            "    \"api_path\": \"/analyze\",\n" +
            "    \"last_api_url\": \"\",\n" +
            "    \"last_api_http_code\": 0,\n" +
            "    \"last_api_time_ms\": 0,\n" +
            "    \"last_api_error\": \"\",\n" +
            "    \"best_image_mode\": \"none\",\n" +
            "    \"best_image_bytes\": 0,\n" +
            "    \"stream_url\": \"http://192.168.100.110:81/stream\",\n" +
            "    \"capture_url\": \"http://192.168.100.110/best.jpg\"\n" +
            "  }\n" +
            "}";

    private void startAutoRefresh() {
        if (refreshRunnable != null) handler.removeCallbacks(refreshRunnable);

        refreshRunnable = new Runnable() {
            @Override
            public void run() {
                try {
                    JSONObject json = new JSONObject(STATIC_STATUS_JSON);
                    boolean connected = json.optBoolean("success", false);
                    JSONObject esp32 = json.optJSONObject("esp32");

                    if (connected && esp32 != null) {
                        String ssid = esp32.optString("wifi_ssid", "—");
                        int rssi = esp32.optInt("wifi_rssi", 0);
                        int battery = esp32.optInt("battery_percent", 0);
                        boolean camera = "OK".equalsIgnoreCase(esp32.optString("camera_status", ""));

                        updateUI(true, ssid, rssi, camera, battery);
                    } else {
                        updateUI(false, "—", 0, false, 0);
                    }
                } catch (Exception e) {
                    Log.e("STATIC_STATUS", "Erreur parsing", e);
                    updateUI(false, "—", 0, false, 0);
                }
                handler.postDelayed(this, REFRESH_INTERVAL_MS);
            }
        };
        handler.post(refreshRunnable);
    }

    private void fetchHttpStatus() {
        new Thread(() -> {
            try {
                String baseIp = BuildConfig.GATEWAY_WS_URL
                        .replace("ws://", "http://")
                        .replace("/ws/resultats", "/glasses/status");

                URL url = new URL(baseIp);
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("GET");
                conn.setConnectTimeout(3000);

                if (conn.getResponseCode() == 200) {
                    BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                    StringBuilder sb = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) sb.append(line);
                    reader.close();

                    JSONObject json = new JSONObject(sb.toString());
                    boolean connected = json.optBoolean("success", false);
                    JSONObject esp32 = json.optJSONObject("esp32");

                    if (connected && esp32 != null) {
                        String ssid = esp32.optString("wifi_ssid", "—");
                        int rssi = esp32.optInt("wifi_rssi", 0);
                        int battery = esp32.optInt("battery_percent", 0);

                        boolean camera = "OK".equalsIgnoreCase(esp32.optString("camera_status", ""));

                        runOnUiThread(() -> updateUI(true, ssid, rssi, camera, battery));
                    } else {
                        runOnUiThread(() -> updateUI(false, "—", 0, false, 0));
                    }
                } else {
                    runOnUiThread(() -> updateUI(false, "—", 0, false, 0));
                }
            } catch (Exception e) {
                Log.e("HTTP_STATUS", "Erreur lors de la récupération du statut", e);
                runOnUiThread(() -> updateUI(false, "—", 0, false, 0));
            }
        }).start();
    }

    private void updateUI(boolean connected, String ssid, int rssi, boolean cameraOn, int battery) {
        android.view.View viewStatusDot = findViewById(R.id.viewStatusDot);

        if (connected) {
            cardStatus.setCardBackgroundColor(ContextCompat.getColor(this, android.R.color.white));
            tvStatusLabel.setText(getString(R.string.status_connected));

            if (ivStatusIcon != null) {
                ivStatusIcon.setImageResource(R.drawable.ic_camera);
                ivStatusIcon.setImageTintList(android.content.res.ColorStateList.valueOf(ContextCompat.getColor(this, R.color.teal_700)));
            }
            if (viewStatusDot != null) {
                viewStatusDot.setBackground(ContextCompat.getDrawable(this, R.drawable.shape_dot_online));
            }
        } else {
            cardStatus.setCardBackgroundColor(ContextCompat.getColor(this, android.R.color.darker_gray));
            tvStatusLabel.setText(getString(R.string.status_disconnected));
            if (ivStatusIcon != null) {
                ivStatusIcon.setImageResource(R.drawable.ic_glasses_off);
                ivStatusIcon.setImageTintList(android.content.res.ColorStateList.valueOf(ContextCompat.getColor(this, android.R.color.darker_gray)));
            }
            if (viewStatusDot != null) {
                viewStatusDot.setBackgroundColor(ContextCompat.getColor(this, android.R.color.holo_red_dark));
            }
        }

        tvSsid.setText(ssid);
        tvRssi.setText(connected ? rssi + " dBm" : "—");
        tvBatteryValue.setText(battery + "%");
        pbBattery.setProgress(battery);

        tvCameraStatus.setText(cameraOn ? getString(R.string.status_ready) : getString(R.string.status_inactive));

        if (tts != null && isTtsInitialized && !isFirstLoad) {
            if (connected != lastConnectedState) {
                vocaliserTexte(getString(R.string.alert_connection_changed));
            }
            if (connected && battery <= 20 && battery < lastBatteryValue) {
                vocaliserTexte(getString(R.string.alert_battery_low_msg, battery));
            }
        }

        lastConnectedState = connected;
        lastCameraState = cameraOn;
        lastBatteryValue = battery;
        isFirstLoad = false;
    }

    private void vocaliserTexte(String texte) {
        if (tts == null || !isTtsInitialized) return;
        Locale appLocale = "ar".equals(langCode) ? new Locale("ar", "MA") :
                "en".equals(langCode) ? Locale.ENGLISH : Locale.FRENCH;
        tts.setLanguage(appLocale);
        tts.speak(texte, TextToSpeech.QUEUE_FLUSH, null, "main_tts");
    }

    private void lireStatutGlobal() {
        String message;
        if (lastConnectedState) {
            String etatCam = lastCameraState ? getString(R.string.status_ready) : getString(R.string.status_inactive);
            message = getString(R.string.status_global_connected, lastBatteryValue, etatCam);
        } else {
            message = getString(R.string.status_global_disconnected);
        }
        vocaliserTexte(message);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (isTtsInitialized) {
            startAutoRefresh();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (refreshRunnable != null) handler.removeCallbacks(refreshRunnable);
    }

    @Override
    protected void onDestroy() {
        if (webSocket != null) webSocket.close(1000, "App détruite");
        if (tts != null) { tts.stop(); tts.shutdown(); }
        super.onDestroy();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == 1) {
            if (resultCode == TextToSpeech.Engine.CHECK_VOICE_DATA_PASS) {
                tts = new TextToSpeech(this, status -> {
                    if (status == TextToSpeech.SUCCESS) {
                        isTtsInitialized = true;
                        Locale locale;
                        switch (langCode) {
                            case "ar":
                                locale = new Locale("ar", "MA");
                                break;
                            case "en":
                                locale = Locale.ENGLISH;
                                break;
                            default:
                                locale = Locale.FRENCH;
                                break;
                        }
                        tts.setLanguage(locale);

                        SharedPreferences userPrefs = getSharedPreferences("user_data", MODE_PRIVATE);
                        String name = userPrefs.getString("user_name", "Utilisateur");
                        String greeting = getString(R.string.greeting, name);

                        tts.speak(greeting, TextToSpeech.QUEUE_FLUSH, null, "tts_greeting");

                        runOnUiThread(() -> {
                            startWebSocketConnection();
                            startAutoRefresh();
                        });
                    } else {
                        initWithoutTts();
                    }
                });
            } else {
                Intent installIntent = new Intent();
                installIntent.setAction(TextToSpeech.Engine.ACTION_INSTALL_TTS_DATA);
                startActivity(installIntent);
                initWithoutTts();
            }
        }
    }

    private void initWithoutTts() {
        isTtsInitialized = false;
        runOnUiThread(() -> {
            startWebSocketConnection();
            startAutoRefresh();
        });
    }
}