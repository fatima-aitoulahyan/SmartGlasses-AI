# test_read.py — à lancer dans le dossier ocr-service
import requests

with open("images_input/image.png", "rb") as f:
    r = requests.post(
        "http://127.0.0.1:8003/read",
        files={"file": ("image.png", f, "image/png")},
        timeout=30
    )
    print(f"Status : {r.status_code}")
    print(f"Réponse : {r.text}")