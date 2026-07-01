FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi==0.111.0 \
    uvicorn==0.30.1 \
    python-multipart==0.0.9 \
    torch==2.3.0 \
    torchvision==0.18.0 \
    opencv-python-headless==4.9.0.80 \
    numpy==1.26.4 \
    Pillow==10.3.0 \
    ultralytics==8.2.15 \
    easyocr==1.7.1

COPY . .


CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]