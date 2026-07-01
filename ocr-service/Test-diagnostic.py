"""
test_diagnostic.py
Lance avec : python test_diagnostic.py
"""
import os, sys

print("=" * 50)
print("  DIAGNOSTIC BLIND ASSISTANT")
print("=" * 50)

# ── Test 1 : .env ──────────────────────────────────
print("\n[1] Lecture du .env...")
try:
    from dotenv import load_dotenv
    load_dotenv(".env")
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        print("    ❌ GROQ_API_KEY manquante dans .env !")
        print("    → Vérifie que le fichier .env existe dans ce dossier")
        print("    → Il doit contenir : GROQ_API_KEY=gsk_xxxxx")
        sys.exit(1)
    print(f"    ✅ GROQ_API_KEY trouvée : {key[:8]}...")
except Exception as e:
    print(f"    ❌ Erreur : {e}")
    sys.exit(1)

# ── Test 2 : connexion Groq ────────────────────────
print("\n[2] Test connexion Groq API...")
try:
    import httpx
    r = httpx.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {key}"},
        timeout=10
    )
    if r.status_code == 200:
        print(f"    ✅ Groq API accessible (status {r.status_code})")
    elif r.status_code == 401:
        print(f"    ❌ Clé API invalide (401) — renouvelle ta clé sur console.groq.com")
        sys.exit(1)
    elif r.status_code == 429:
        print(f"    ⚠️  Rate limit (429) — attends 1 minute")
        sys.exit(1)
    else:
        print(f"    ❌ Erreur {r.status_code} : {r.text[:100]}")
        sys.exit(1)
except Exception as e:
    print(f"    ❌ Impossible de contacter Groq : {e}")
    sys.exit(1)

# ── Test 3 : image ────────────────────────────────
print("\n[3] Test décodage image...")
import glob
images = glob.glob("images_input/*")
if not images:
    print("    ⚠️  Aucune image dans images_input/")
else:
    img_path = images[0]
    import cv2, numpy as np
    img = cv2.imread(img_path)
    if img is None:
        from PIL import Image as PILImage
        import io
        with open(img_path, "rb") as f:
            contents = f.read()
        pil = PILImage.open(io.BytesIO(contents)).convert("RGB")
        img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        print(f"    ✅ Image décodée via PIL fallback : {img.shape}")
    else:
        print(f"    ✅ Image décodée : {img.shape}")

# ── Test 4 : appel Groq Vision ────────────────────
print("\n[4] Test appel Groq Vision (image réelle)...")
try:
    import base64, json
    img_path = images[0] if images else None
    if img_path:
        import cv2, numpy as np
        img = cv2.imread(img_path)
        if img is None:
            from PIL import Image as PILImage
            import io
            with open(img_path, "rb") as f:
                contents = f.read()
            pil = PILImage.open(io.BytesIO(contents)).convert("RGB")
            img = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

        _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        b64 = base64.b64encode(buf).decode("utf-8")

        payload = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": "What text do you see in this image? Just describe briefly."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ]}],
            "max_tokens": 200,
        }

        r = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            timeout=30
        )

        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            print(f"    ✅ Groq Vision fonctionne !")
            print(f"    → Réponse : '{content[:100]}'")
        else:
            print(f"    ❌ Erreur {r.status_code} : {r.text[:200]}")
    else:
        print("    ⚠️  Pas d'image pour tester")

except Exception as e:
    print(f"    ❌ Erreur : {e}")

print("\n" + "=" * 50)
print("  FIN DIAGNOSTIC")
print("=" * 50)