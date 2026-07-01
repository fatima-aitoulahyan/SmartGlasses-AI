import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from detector import detector

app = FastAPI(
    title="Obstacle Detection Service",
    description="YOLO-based obstacle detection for Mode Marche",
    version="1.0.0"
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "obstacle-detection"}


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr    = np.frombuffer(contents, np.uint8)
        image    = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return JSONResponse(
                {"error": "Could not decode image"}, status_code=400
            )

        result = detector.detect(image)
        return result

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
