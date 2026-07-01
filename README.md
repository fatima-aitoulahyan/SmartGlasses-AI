# SmartGlasses AI

AI-powered smart glasses for visually impaired people.  
Detects obstacles, reads text (OCR), and recognizes banknotes using voice feedback.

---

## Team

| Member | Role | Service | Branch |
|--------|------|---------|--------|
| M1 | Project Lead + API Gateway | `api-gateway/` | `main` + `dev` |
| M2 | Obstacle Detection | `obstacle-service/` | `feature/M2-obstacle` |
| M3 | OCR Multilingual | `ocr-service/` | `feature/M3-ocr` |
| M4 | Money Recognition | `money-service/` | `feature/M4-money` |
| M5 | Android App | `android-app/` | `feature/M5-android` |

---

## Architecture

```
[SmartGlasses Hardware]
        ↓ Bluetooth
[Android App — M5]
        ↓ WiFi → POST /analyze?mode=obstacle|ocr|money
[API Gateway :8000 — M1]
        ├── obstacle → [Obstacle Service :8001 — M2]  YOLO
        ├── ocr      → [OCR Service     :8002 — M3]  Tesseract + ML Kit
        └── money    → [Money Service   :8003 — M4]  MobileNet CNN
```

---

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2+
- Android Studio (M5 only)
- Git

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-org/smartglasses-ai.git
cd smartglasses-ai
```

### 2. Setup environment variables

```bash
cp .env .env
# Edit .env and set your machine's local IP in API_BASE_URL
```

### 3. Run in development mode

```bash
docker compose --profile dev up --build
```

Services will be available at:
- API Gateway  → http://localhost:8000
- Obstacle     → http://localhost:8001
- OCR          → http://localhost:8002
- Money        → http://localhost:8003
- Portainer    → http://localhost:9000

### 4. Run your service only (recommended during development)

```bash
# M2 — only run obstacle service
docker compose up obstacle-service --build

# M3 — only run OCR service
docker compose up ocr-service --build

# M4 — only run money service
docker compose up money-service --build
```

### 5. Run training

```bash
# Train all models
docker compose --profile training up

# Train one model only
docker compose run obstacle-trainer
docker compose run ocr-trainer
docker compose run money-trainer
```

### 6. Run in production

```bash
docker compose --profile production up -d
```

---

## API Reference

### POST /analyze

Send an image with a mode to get AI analysis.

**Request:**
```
POST http://localhost:8000/analyze?mode=obstacle
Content-Type: multipart/form-data
Body: file=<image.jpg>
```

**Modes:**
- `obstacle` → returns detected obstacles with positions
- `ocr`      → returns extracted text with detected language
- `money`    → returns banknote value and confidence

**Response (obstacle):**
```json
{
  "mode": "obstacle",
  "success": true,
  "processing_time_ms": 245.3,
  "result": {
    "objects": ["personne", "voiture"],
    "distances": ["devant vous", "à droite"],
    "alert_message": "Attention, personne devant vous, voiture à droite"
  }
}
```

**Response (ocr):**
```json
{
  "mode": "ocr",
  "success": true,
  "processing_time_ms": 890.1,
  "result": {
    "text": "Pharmacie centrale",
    "language": "fr",
    "script": "latin",
    "confidence": 0.94
  }
}
```

**Response (money):**
```json
{
  "mode": "money",
  "success": true,
  "processing_time_ms": 120.7,
  "result": {
    "value": "200 dirhams",
    "currency": "MAD",
    "confidence": 0.97
  }
}
```

---

## Git Workflow

```bash
# Each member works on their own branch
git checkout -b feature/M3-ocr

# Only commit your own folder
git add ocr-service/
git commit -m "feat: add Tifinagh script detection"
git push origin feature/M3-ocr

# M1 merges into dev when ready
git checkout dev
git merge feature/M3-ocr
```

**Rule: never modify another member's folder.**

---

## Datasets

Datasets are NOT stored in GitHub (too large).  
Place your data in the `datasets/` folder locally:

```
datasets/
├── obstacle/    → COCO format images + labels
├── ocr/         → Tifinagh images + transcriptions (IRCAM dataset)
└── money/       → Photos of MAD banknotes (200+ per class)
```

## Models

Trained models are NOT stored in GitHub.  
After training, models are saved to `models/` locally.  
Share models via USB or cloud storage (Google Drive, etc.).

---

## Useful Commands

```bash
# See all running containers
docker ps

# See logs of a service
docker compose logs -f ocr-service

# Rebuild one service after code change
docker compose up ocr-service --build

# Stop everything
docker compose down

# Stop and remove all data
docker compose down -v
```
