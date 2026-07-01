from ultralytics import YOLO
import os

def train():
    print("Démarrage de l'entraînement pour le Money Service...")

    model = YOLO('yolov8n.pt')

    results = model.train(
        data='../../datasets/money/moroccan_money_detection.yolov8/data.yaml',
        imgsz=640,
        batch=16,
        name='money_model',
        project='../../models/money',
        device='cpu',
        workers=2,
        verbose=True
    )
    
    print("Entraînement terminé !")
    print(f"Ton modèle est ici: models/money/money_model/weights/best.pt")

if __name__ == "__main__":
    train()