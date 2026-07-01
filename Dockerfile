# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# ── Métadonnées ───────────────────────────────────────────────────────────────
LABEL maintainer="SmartGlasses AI Team"
LABEL description="Obstacle Detection Service — Mode Marche"
LABEL version="1.0.0"

# ── Variables d'environnement ─────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# ── Dépendances système (OpenCV headless en a besoin) ────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# ── Répertoire de travail ─────────────────────────────────────────────────────
WORKDIR /app

# ── Installation des dépendances Python ──────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=300 -r requirements.txt

# ── Copie du code source ──────────────────────────────────────────────────────
COPY app/ .

# ── Exposition du port ────────────────────────────────────────────────────────
EXPOSE 8000

# ── Healthcheck Docker ────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# ── Commande de démarrage ─────────────────────────────────────────────────────
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
