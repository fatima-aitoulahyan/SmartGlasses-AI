package com.example.android_app.wifi;

import android.content.Context;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.Bundle;
import android.util.Log;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.example.android_app.BaseActivity;
import com.example.android_app.R;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.textfield.TextInputLayout;

public class WifiInfoManagerActivity extends BaseActivity {

    TextView ssidText;
    MaterialButton buttonConnect;
    TextInputLayout input;

    private final String[] REQUIRED_PERMISSIONS = {
            android.Manifest.permission.ACCESS_FINE_LOCATION,
            android.Manifest.permission.ACCESS_COARSE_LOCATION
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.wifi_info_manager);

        ssidText = findViewById(R.id.textWifiValue);
        buttonConnect = findViewById(R.id.buttonConnect);
        input = findViewById(R.id.inputLayoutPassword);

        if (checkSelfPermission(android.Manifest.permission.ACCESS_FINE_LOCATION)
                == android.content.pm.PackageManager.PERMISSION_GRANTED) {
            afficherWifi();
        } else {
            requestPermissions(REQUIRED_PERMISSIONS, 1);
        }

        buttonConnect.setOnClickListener(v -> {

            String ssid = getWifiSSID();

            String password = "";
            if (input.getEditText() != null) {
                password = input.getEditText().getText().toString();
            }

            if (password.isEmpty()) {
                input.setError("Veuillez entrer un mot de passe");
                return;
            }

            input.setError(null);

            WifiSession.setSsid(ssid);
            WifiSession.setPassword(password);

            Log.d("WiFi", WifiSession.debug());
            if (input.getEditText() != null) {
                input.getEditText().setText("");
            }
        });
    }

    private void afficherWifi() {
        String ssid = getWifiSSID();
        ssidText.setText(ssid);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == 1 && grantResults.length > 0
                && grantResults[0] == android.content.pm.PackageManager.PERMISSION_GRANTED) {
            afficherWifi();
        } else {
            ssidText.setText("Permission refusée");
        }
    }

    private String getWifiSSID() {
        WifiManager wifiManager = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
        if (wifiManager != null) {
            WifiInfo info = wifiManager.getConnectionInfo();
            String ssid = info.getSSID();
            if (ssid != null && !ssid.equals("<unknown ssid>")) {
                return ssid.replace("\"", "");
            }
        }
        return "Non connecté";
    }
}