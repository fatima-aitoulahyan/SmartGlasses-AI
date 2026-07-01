package com.example.android_app;

import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.os.Bundle;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.Toast;
import java.util.Locale;

public class SettingsLanguge extends BaseActivity {

    private static final String PREFS_NAME = "app_settings";
    private static final String KEY_LANG   = "language";

    private RadioGroup radioGroup;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings_language);

        radioGroup = findViewById(R.id.radioGroupLanguage);
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        String savedLang = prefs.getString(KEY_LANG, "fr");
        checkCurrentLanguage(savedLang);
        radioGroup.setOnCheckedChangeListener((group, checkedId) -> {
            String langCode;
            if      (checkedId == R.id.radioFr) langCode = "fr";
            else if (checkedId == R.id.radioEn) langCode = "en";
            else if (checkedId == R.id.radioAr) langCode = "ar";
            else return;

            applyLanguage(langCode);
        });
    }

    private void checkCurrentLanguage(String langCode) {
        switch (langCode) {
            case "en": radioGroup.check(R.id.radioEn); break;
            case "ar": radioGroup.check(R.id.radioAr); break;
            default:   radioGroup.check(R.id.radioFr); break;
        }
    }

    private void applyLanguage(String langCode) {
        getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                .edit()
                .putString(KEY_LANG, langCode)
                .apply();
        Locale locale = new Locale(langCode);
        Locale.setDefault(locale);
        Configuration config = new Configuration();
        config.setLocale(locale);
        getResources().updateConfiguration(config,
                getResources().getDisplayMetrics());
        Toast.makeText(this, getLocalizedMessage(langCode), Toast.LENGTH_SHORT).show();
        new android.os.Handler().postDelayed(() -> {
            android.content.Intent intent = new android.content.Intent(
                    this,
                    getClassForName("com.example.android_app.MainActivity")
            );
            intent.addFlags(android.content.Intent.FLAG_ACTIVITY_CLEAR_TOP
                    | android.content.Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
            finish();
        }, 700);
    }

    private String getLocalizedMessage(String langCode) {
        switch (langCode) {
            case "en": return "Language changed to English";
            case "ar": return "تم تغيير اللغة إلى العربية";
            default:   return "Langue changée en Français";
        }
    }

    private Class<?> getClassForName(String className) {
        try {
            return Class.forName(className);
        } catch (ClassNotFoundException e) {
            throw new RuntimeException("Classe introuvable : " + className, e);
        }
    }
}