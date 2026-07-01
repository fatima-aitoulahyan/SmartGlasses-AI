from dotenv import load_dotenv
import os
import logging
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from groq_service import groq_service
from tts_service import tts_service

logger = logging.getLogger(__name__)
load_dotenv(".env")

SERVER_BASE_URL = os.getenv("SERVER_BASE_URL", "http://localhost:8002")
AUDIO_DIR       = os.getenv("AUDIO_DIR", "./audio_output")

def make_audio_url(audio_path: str | None) -> str | None:
    if not audio_path:
        return None
    return f"{SERVER_BASE_URL}/audio_output/{Path(audio_path).name}"

app = FastAPI(
    title="Blind Assistant Service",
    description="One click → one photo → one audio. No deduplication.",
    version="5.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(AUDIO_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/audio_output", StaticFiles(directory=AUDIO_DIR), name="audio_output")


def decode_image(contents: bytes) -> np.ndarray | None:

    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is not None:
        return image

    try:
        from PIL import Image as PILImage
        import io
        pil   = PILImage.open(io.BytesIO(contents)).convert("RGB")
        image = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        logger.info("[DECODE] PIL fallback utilisé (PNG transparent ou format spécial)")
        return image
    except Exception as e:
        logger.error(f"[DECODE] Échec PIL fallback : {e}")
        return None


@app.get("/health")
async def health():
    return {
        "status":     "ok",
        "service":    "blind-assistant",
        "version":    "5.0.0",
        "server_url": SERVER_BASE_URL,
    }


@app.post("/read")
async def read(file: UploadFile = File(...)):

    try:
        contents = await file.read()
        image    = decode_image(contents)

        if image is None:
            return JSONResponse(
                {"error": "Cannot decode image — send a valid JPEG"},
                status_code=400
            )

        result   = groq_service.analyze_image(image)
        summary  = result.get("summary",  "").strip()
        text     = result.get("text",     "").strip()
        language = result.get("language", "fr")

        if result.get("error"):
            error_msg = result["error"]
            if "HTTP" in error_msg or "API" in error_msg or "missing" in error_msg:
                return JSONResponse({"error": error_msg}, status_code=503)
            logger.warning(f"[READ] Erreur non-critique : {error_msg}")
        if not summary:
            return JSONResponse({
                "success":  False,
                "message":  "No text detected in image",
                "text":     "",
                "summary":  "",
                "language": language,
            })

        tts_result = tts_service.synthesize(summary, language)

        return {
            "success":    True,
            "text":       text,
            "language":   language,
            "summary":    summary,
            "audio_url":  make_audio_url(tts_result.get("audio_path")),
            "tts_cached": tts_result.get("cached", False),
            "tts_engine": tts_result.get("engine"),
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/reset")
async def reset():
    groq_service.reset_context()
    return {"message": "Context memory reset"}


@app.get("/audio")
async def list_audio():
    return {"files": tts_service.list_audio_files()}