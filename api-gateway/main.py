import os
import time
import requests
from fastapi import FastAPI, UploadFile, File, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import httpx

from router import route_request
from schemas import AnalyzeResponse

from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketState

app = FastAPI(
    title="SmartGlasses AI — API Gateway",
    description="Routes image analysis requests to the correct AI service",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

URLS = {
    "obstacle": os.getenv("OBSTACLE_URL", "http://obstacle-service:8001"),
    "ocr":      os.getenv("OCR_URL",      "http://ocr-service:8002"),
    "money":    os.getenv("MONEY_URL",    "http://money-service:8003"),
}
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def relier_android(self, websocket: WebSocket):
        await websocket.accept()

        self.active_connections.append(websocket)

        print("Android connecté au flux Temps Réel.")

    def deconnecter_android(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        print("Android déconnecté.")

    async def envoyer_resultat_ia(self, message: dict):

        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)

            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.deconnecter_android(conn)


manager = ConnectionManager()
@app.get("/")
async def root():
    return {
        "project": "SmartGlasses AI",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "POST /analyze?mode=obstacle|ocr|money",
            "health":  "GET  /health",
            "ws_results": "WS /ws/resultats"
        }
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "services": {
            "obstacle": URLS["obstacle"],
            "ocr":      URLS["ocr"],
            "money":    URLS["money"],
        }
    }


@app.get("/glasses/status")
async def glasses_status():
    esp32_url = "http://10.34.192.129/status"
    try:
        response = requests.get(esp32_url, timeout=3)
        if response.status_code != 200:
            raise Exception("ESP32 error")
        return {"success": True, "esp32": response.json()}
    except Exception as e:
        return {
            "success": False,
            "esp32": {
                "connected": False,
                "ssid": None,
                "rssi": None,
                "error": str(e)
            }
        }

@app.websocket("/ws/resultats")
async def websocket_endpoint(websocket: WebSocket):
    await manager.relier_android(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.deconnecter_android(websocket)

@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    mode: str = Query(..., description="obstacle | ocr | money"),
    file: UploadFile = File(..., description="JPEG image from ESP32-CAM")
):
    image_bytes = await file.read()

    result = await route_request(
        mode=mode,
        image_bytes=image_bytes,
        filename=file.filename or "frame.jpg",
        content_type=file.content_type or "image/jpeg",
        urls=URLS
    )
    if result.success:
        await manager.envoyer_resultat_ia(result.model_dump())

    status_code = 200 if result.success else 502
    return JSONResponse(content=result.model_dump(), status_code=status_code)