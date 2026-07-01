from ultralytics import YOLO
import os

EPOCHS     = int(os.getenv("EPOCHS",     "50"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "16"))
IMG_SIZE   = int(os.getenv("IMG_SIZE",   "640"))
DATA_PATH  = "/app/data/dataset.yaml"
MODEL_OUT  = "/app/models"


def train():
    print(f"Starting training: {EPOCHS} epochs, batch={BATCH_SIZE}")
    model = YOLO("yolov8n.pt")

    model.train(
        data=DATA_PATH,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        project=MODEL_OUT,
        name="obstacle_detector",
        patience=10,
        save=True,
        plots=True
    )

    best = f"{MODEL_OUT}/obstacle_detector/weights/best.pt"
    dest = f"{MODEL_OUT}/yolo_trained.pt"
    if os.path.exists(best):
        import shutil
        shutil.copy(best, dest)
        print(f"Model saved to {dest}")
    else:
        print("Training complete. Check logs for best model path.")


if __name__ == "__main__":
    train()
