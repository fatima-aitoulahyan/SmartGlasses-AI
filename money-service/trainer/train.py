import os
import shutil
from ultralytics import YOLO

DATA_YAML = "/app/data/moroccan_money_detection.yolov8/data.yaml"
MODEL_OUT_DIR = "/app/models"
MODEL_OUT_FILE = os.path.join(MODEL_OUT_DIR, "best.pt")

EPOCHS = int(os.getenv("EPOCHS", "20"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "16"))

def train():
    if not os.path.exists(DATA_YAML):
        print(f"ERROR: Dataset YAML not found at {DATA_YAML}")
        exit(1)

    print(f"Loading YOLOv8n model...")
    model = YOLO('yolov8n.pt') # Load pretrained YOLOv8n

    print(f"Starting training for {EPOCHS} epochs...")
    
    results = model.train(
        data=DATA_YAML,
        epochs=EPOCHS,
        batch=BATCH_SIZE,
        imgsz=640,
        project="/app/runs",
        name="money_training",
        exist_ok=True
    )
    
    best_model_path = "/app/runs/money_training/weights/best.pt"
    
    if os.path.exists(best_model_path):
        os.makedirs(MODEL_OUT_DIR, exist_ok=True)
        print(f"Copying best model to {MODEL_OUT_FILE}...")
        shutil.copy(best_model_path, MODEL_OUT_FILE)
        print("Training complete! Model saved.")
    else:
        print("ERROR: Training completed but best.pt was not found.")

if __name__ == "__main__":
    train()
