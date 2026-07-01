package com.example.android_app.Login;

import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import androidx.appcompat.app.AppCompatActivity;

import com.example.android_app.MainActivity;
import com.example.android_app.R;

public class LoginActivity extends AppCompatActivity {

    private EditText editUsername;
    private Button btnStart;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);

        SharedPreferences prefs = getSharedPreferences("user_data", MODE_PRIVATE);
        boolean isFirstTime = prefs.getBoolean("isFirstTime", true);

        if (!isFirstTime) {
            startActivity(new Intent(this, MainActivity.class));
            finish();
            return;
        }

        editUsername = findViewById(R.id.editUsername);
        btnStart = findViewById(R.id.btnStart);

        btnStart.setOnClickListener(v -> {
            String name = editUsername.getText().toString().trim();

            if (name.isEmpty()) {
                editUsername.setError(getString(R.string.enter_name));
                return;
            }
            prefs.edit()
                    .putString("user_name", name)
                    .putBoolean("isFirstTime", false)
                    .apply();

            startActivity(new Intent(this, MainActivity.class));
            finish();
        });
    }
}