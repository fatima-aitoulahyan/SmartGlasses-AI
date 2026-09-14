#  SmartGlasses AI

Système de lunettes intelligentes pour personnes malvoyantes, basé sur une architecture de microservices IA. Une caméra ESP32-CAM capture les images du terrain, qui sont analysées en temps réel par des services d'IA spécialisés (détection d'obstacles, lecture de texte, reconnaissance de billets marocains), puis les résultats sont renvoyés à une application Android via WebSocket.

##  Architecture

```
ESP32-CAM ──HTTP──> API Gateway (FastAPI) ──┬──> Obstacle Service (YOLOv8)
                          │                  ├──> OCR Service (Tesseract/EasyOCR)
                          │                  └──> Money Service (YOLOv8)
                          │
                          └──WebSocket──> Application Android
```

Chaque service IA est un conteneur Docker indépendant, exposé via une API REST interne. L'API Gateway route les requêtes selon le mode demandé (`obstacle`, `ocr`, `money`) et diffuse les résultats en temps réel aux clients connectés via WebSocket.

##  Services

| Service | Port | Rôle | Modèle |
|---|---|---|---|
| **api-gateway** | 8000 | Point d'entrée unique, routage, WebSocket | FastAPI |
| **obstacle-service** | 8001 | Détection d'obstacles et distances | YOLOv8 |
| **ocr-service** | 8002 | Lecture de texte (FR/AR/ES/Tifinagh) | Tesseract + EasyOCR + fallback Groq/Gemini |
| **money-service** | 8003 | Reconnaissance de billets/pièces marocains | YOLOv8 |

Un service **Portainer** est inclus pour la supervision des conteneurs.

##  Fonctionnalités clés

- **Routage dynamique** des images selon le mode d'analyse (`/analyze?mode=obstacle|ocr|money`)
- **Diffusion temps réel** des résultats vers l'application Android via WebSocket (`/ws/resultats`)
- **OCR multilingue** avec détection automatique de la langue (français, arabe, espagnol) et lecture à voix haute adaptée pour utilisateurs malvoyants
- **Support du Tifinagh/Amazigh** avec fallback sur un modèle vision (Gemini) lorsque le script n'est pas reconnu par le modèle principal
- **Limitation de débit et mémoire de contexte** pour l'OCR, afin d'améliorer la cohérence des lectures successives
- **Statut de connexion ESP32** exposé via `/glasses/status`
- **Entraînement des modèles** intégré via des conteneurs dédiés (`obstacle-trainer`, `ocr-trainer`, `money-trainer`)

##  Démarrage rapide

### Prérequis

- Docker & Docker Compose
- Un fichier `.env` à la racine (voir [Configuration](#-configuration))

### Lancer en développement

```bash
docker compose --profile dev up --build
```

### Lancer en production

```bash
docker compose --profile production up --build -d
```

### Lancer un entraînement (ex: obstacle)

```bash
docker compose --profile training run obstacle-trainer
```

##  Configuration

Créer un fichier `.env` à la racine du projet (**ne jamais le committer**) :

```env
OBSTACLE_URL=http://obstacle-service:8001
OCR_URL=http://ocr-service:8002
MONEY_URL=http://money-service:8003

GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key

EPOCHS=50
BATCH_SIZE=16
IMG_SIZE=640
```

>  **Sécurité** : le fichier `.env` doit impérativement être ajouté au `.gitignore`. En cas de fuite de clés API, les régénérer immédiatement depuis les consoles Groq/Google AI Studio.

## 📡 Endpoints principaux (API Gateway)

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/` | Informations générales sur l'API |
| `GET` | `/health` | Vérifie l'état des services connectés |
| `GET` | `/glasses/status` | Statut de connexion de l'ESP32-CAM |
| `POST` | `/analyze?mode=obstacle\|ocr\|money` | Envoie une image pour analyse |
| `WS` | `/ws/resultats` | Flux temps réel des résultats vers l'app Android |

##  Tests

```bash
cd obstacle-service
pytest tests/
```

##  Stack technique

- **Backend** : FastAPI, httpx, Uvicorn
- **Vision** : YOLOv8 (Ultralytics), OpenCV
- **OCR** : Tesseract (fra/ara/eng + modèle Tifinagh personnalisé), EasyOCR, Groq (Llama 4 Scout) + Gemini en fallback
- **Infra** : Docker Compose (profils `dev`, `production`, `training`), Portainer
- **Hardware** : ESP32-CAM
- **Client** : Application Android (Kotlin, Gradle) connectée en WebSocket

##  Structure du projet

```
Projet_PI/
├── android-app/                 # Application Android (client WebSocket)
├── api-gateway/
│   ├── tests/
│   ├── Dockerfile
│   ├── main.py
│   ├── router.py
│   ├── schemas.py
│   └── requirements.txt
├── obstacle-service/
│   ├── app/
│   │   ├── build/
│   │   └── src/
│   ├── build/
│   ├── datasets/
│   ├── models/
│   └── main.py
├── money-service/
│   ├── models/
│   ├── tests/
│   ├── trainer/
│   │   ├── classifier.py
│   │   └── Dockerfile
│   └── main.py
├── ocr-service/
│   ├── groq_service.py
│   ├── trainer/
│   │   └── train_tesseract.py
│   └── tessdata/
├── docker-compose.yml
└── .env (non versionné)
```
