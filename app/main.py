from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import numpy as np
import cv2
import time
import logging
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SmartGlasses - Obstacle Detection Service",
    version="5.0.0"
)

# ── Chargement du modèle ──────────────────────────────────────────────────────
logger.info("Chargement du modèle...")
model = YOLO("yolov8n.pt")
logger.info("Modèle chargé ✅")

# ── Classes de best_v3.pt (20 classes) ───────────────────────────────────────
MODEL_CLASSES = {
    0: "personne",
    1: "vélo",
    2: "voiture",
    3: "moto",
    5: "bus",
    7: "camion",
    9: "feu de circulation",
    11: "panneau stop",
    13: "banc",
    15: "chat",
    16: "chien",
    24: "sac à dos",
    25: "parapluie",
    28: "valise",
    56: "chaise",
    57: "canapé",
    58: "plante",
    59: "lit",
    60: "table",
    67: "téléphone",
}

def estimate_distance(bbox_height: float, image_height: float) -> str:
    ratio = bbox_height / image_height
    if ratio > 0.6:
        return "très proche (<0.5m)"
    elif ratio > 0.35:
        return "proche (~1m)"
    elif ratio > 0.15:
        return "moyen (~2-3m)"
    else:
        return "loin (>3m)"

def get_position(bbox_x: float, bbox_width: float, image_width: float) -> str:
    center_x = bbox_x + bbox_width / 2
    ratio = center_x / image_width
    if ratio < 0.33:
        return "gauche"
    elif ratio < 0.66:
        return "centre"
    else:
        return "droite"

@app.get("/")
def root():
    return {
        "service": "obstacle-service",
        "status": "running",
        "model": "yolov8n.pt",
        "classes_detectables": list(MODEL_CLASSES.values())
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": time.time()}

@app.post("/detect")
async def detect_obstacles(image: UploadFile = File(...)):
    if image.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/jfif"]:
        raise HTTPException(status_code=400, detail="Utilisez JPEG ou PNG.")
    try:
        image_bytes = await image.read()
        start_time = time.time()

        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Image invalide ou corrompue")

        height, width = img.shape[:2]

        # ── Détection YOLO ────────────────────────────────────────────────────
        results = model(img, conf=0.3)

        detections = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])

                if class_id not in MODEL_CLASSES:
                    continue

                confidence = float(box.conf[0])
                x, y, w, h = box.xywh[0].tolist()

                detections.append({
                    "label": MODEL_CLASSES[class_id],
                    "confidence": round(confidence, 2),
                    "distance_estimate": estimate_distance(h, height),
                    "position": get_position(x - w/2, w, width),
                    "bbox": {
                        "x": round(x), "y": round(y),
                        "width": round(w), "height": round(h)
                    }
                })

        # Tri par distance
        distance_order = {
            "très proche (<0.5m)": 0,
            "proche (~1m)": 1,
            "moyen (~2-3m)": 2,
            "loin (>3m)": 3
        }
        detections.sort(key=lambda d: distance_order.get(d["distance_estimate"], 99))

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        # ── Message vocal ─────────────────────────────────────────────────────
        if not detections:
            vocal_message = "Aucun obstacle détecté. Voie libre."
        else:
            parts = [f"{d['label']} {d['distance_estimate']} à {d['position']}" for d in detections]
            vocal_message = "Attention ! " + ", ".join(parts) + "."

        return JSONResponse(content={
            "status": "success",
            "vocal_message": vocal_message,
            "detections": detections,
            "processing_time_ms": processing_time_ms,
            "meta": {
                "image_size": {"width": width, "height": height},
                "model": "best_v3.pt"
            }
        })

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)