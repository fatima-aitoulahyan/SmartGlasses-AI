import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from classifier import money_classifier

app = FastAPI(
    title="Money Recognition Service",
    description="Moroccan banknote recognition — Mode Argent",
    version="1.0.0"
)


@app.get("/health")
async def health():
    try:
        return {
            "status": "ok",
            "model_ready": money_classifier.ready
        }
    except Exception as e:
        return {"error": str(e)}



    @app.get("/health")
    async def health():
        return {"status": "ok"}


@app.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return JSONResponse(
                {"error": "Could not decode image"}, status_code=400
            )

        result =money_classifier.classify(image)

        return result

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)