"""
test_gemini.py — Lance avec : python test_gemini.py
Teste ta clé Gemini directement depuis le .env
"""
import os
from dotenv import load_dotenv
load_dotenv(".env")

key = os.getenv("GEMINI_API_KEY", "").strip()
print(f"Clé dans .env : '{key[:12]}...' ({len(key)} chars)")

if not key:
    print("❌ GEMINI_API_KEY manquante dans .env !")
    exit(1)

import httpx

models_to_test = [
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-pro",
]

payload = {
    "contents": [{"parts": [{"text": "Say hello in one word."}]}],
    "generationConfig": {"maxOutputTokens": 20},
}

base = "https://generativelanguage.googleapis.com/v1beta/models"

print("\nTest des modèles avec X-goog-api-key header :")
for model in models_to_test:
    url = f"{base}/{model}:generateContent"
    try:
        r = httpx.post(url, json=payload,
                       headers={"Content-Type": "application/json",
                                "X-goog-api-key": key},
                       timeout=10)
        if r.status_code == 200:
            print(f"  ✅ {model} → OK")
        else:
            print(f"  ❌ {model} → {r.status_code}")
    except Exception as e:
        print(f"  ❌ {model} → {e}")

print("\nTest avec ?key= param :")
for model in models_to_test[:2]:
    url = f"{base}/{model}:generateContent?key={key}"
    try:
        r = httpx.post(url, json=payload,
                       headers={"Content-Type": "application/json"},
                       timeout=10)
        if r.status_code == 200:
            print(f"  ✅ {model} → OK")
        else:
            print(f"  ❌ {model} → {r.status_code}")
    except Exception as e:
        print(f"  ❌ {model} → {e}")