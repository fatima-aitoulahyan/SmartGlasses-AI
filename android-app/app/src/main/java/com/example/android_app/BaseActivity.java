package com.example.android_app;

import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.FrameLayout;
import androidx.appcompat.app.ActionBarDrawerToggle;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.drawerlayout.widget.DrawerLayout;
import com.example.android_app.wifi.WifiInfoManagerActivity;
import com.google.android.material.navigation.NavigationView;

public abstract class BaseActivity extends AppCompatActivity {

    protected DrawerLayout drawerLayout;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        super.setContentView(R.layout.activity_base);

        Toolbar toolbar = findViewById(R.id.toolbar);
        drawerLayout = findViewById(R.id.drawerLayout);
        NavigationView navigationView = findViewById(R.id.navigationView);

        setSupportActionBar(toolbar);
        ActionBarDrawerToggle toggle = new ActionBarDrawerToggle(
                this, drawerLayout, toolbar,
                R.string.open, R.string.close
        );
        drawerLayout.addDrawerListener(toggle);
        toggle.syncState();
        navigationView.setNavigationItemSelectedListener(item -> {
            int id = item.getItemId();

            if (id == R.id.menu_dashboard) {
                if (!(this instanceof MainActivity)) {
                    startActivity(new Intent(this, MainActivity.class));
                    finish();
                }
            } else if (id == R.id.menu_wifi) {
                if (!(this instanceof WifiInfoManagerActivity)) {
                    startActivity(new Intent(this, WifiInfoManagerActivity.class));
                    finish();
                }
            }else if (id== R.id.menu_language){
                if(!(this instanceof SettingsLanguge)){
                    startActivity(new Intent(this , SettingsLanguge.class));
                }
            }else if (id == R.id.menu_about){
                if(!(this instanceof AboutActivity)){
                    startActivity(new Intent(this,AboutActivity.class));
                }
            }

            drawerLayout.closeDrawers();
            return true;
        });
    }
    @Override
    public void setContentView(int layoutResID) {
        FrameLayout contentFrame = findViewById(R.id.content_frame);
        if (contentFrame != null) {
            contentFrame.removeAllViews();
            View child = LayoutInflater.from(this)
                    .inflate(layoutResID, contentFrame, false);
            contentFrame.addView(child);
        }
    }

    @Override
    protected void attachBaseContext(android.content.Context newBase) {

        android.content.SharedPreferences prefs =
                newBase.getSharedPreferences("app_settings", MODE_PRIVATE);

        String lang = prefs.getString("language", "fr");

        java.util.Locale locale = new java.util.Locale(lang);
        java.util.Locale.setDefault(locale);

        android.content.res.Configuration config = new android.content.res.Configuration();
        config.setLocale(locale);

        android.content.Context context = newBase.createConfigurationContext(config);
        super.attachBaseContext(context);
    }
}