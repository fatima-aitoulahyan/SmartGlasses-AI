package com.example.android_app.wifi;

public class WifiSession {

    private static String ssid = "";
    private static String password = "";

    public static void setSsid(String value) {
        ssid = value;
    }

    public static String getSsid() {
        return ssid;
    }

    public static void setPassword(String value) {
        password = value;
    }

    public static String getPassword() {
        return password;
    }
    public static String debug() {
        return "SSID: " + ssid + " | Password: " + password;
    }
}