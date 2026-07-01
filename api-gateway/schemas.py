from pydantic import BaseModel
from typing import Optional, List, Any


class ObstacleResult(BaseModel):
    objects: List[str]
    distances: List[str]
    alert_message: str


class OcrResult(BaseModel):
    text: str
    language: str
    script: str
    confidence: float


class MoneyResult(BaseModel):
    value: str
    currency: str
    confidence: float


class AnalyzeResponse(BaseModel):
    mode: str
    result: dict
    processing_time_ms: float
    success: bool
    error: Optional[str] = None
