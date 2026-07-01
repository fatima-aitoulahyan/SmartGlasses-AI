from ultralytics import YOLO
import os
import shutil
from sklearn.model_selection import train_test_split
from pathlib import Path

# ── Chemins ───────────────────────────────────────────────────────────────────
DATASET_PATH = "dataset/Obstacle detection.yolov8"
TRAIN_IMAGES = f"{DATASET_PATH}/train/images"
TRAIN_LABELS = f"{DATASET_PATH}/train/labels"

# ── Diviser train → train (80%) + valid (20%) ─────────────────────────────────
print("📂 Préparation du dataset...")

# Cherche toutes les extensions possibles
images = list(Path(TRAIN_IMAGES).glob("*.jpg")) + \
         list(Path(TRAIN_IMAGES).glob("*.jpeg")) + \
         list(Path(TRAIN_IMAGES).glob("*.png"))

print(f"📸 {len(images)} images trouvées")

train_imgs, valid_imgs = train_test_split(images, test_size=0.2, random_state=42)

# Créer dossiers valid/
os.makedirs(f"{DATASET_PATH}/valid/images", exist_ok=True)
os.makedirs(f"{DATASET_PATH}/valid/labels", exist_ok=True)

# Déplacer les images valid
for img in valid_imgs:
    label = Path(TRAIN_LABELS) / (img.stem + ".txt")
    if img.exists():
        shutil.copy(str(img), f"{DATASET_PATH}/valid/images/")
    if label.exists():
        shutil.copy(str(label), f"{DATASET_PATH}/valid/labels/")

print(f"✅ Train : {len(train_imgs)} images")
print(f"✅ Valid : {len(valid_imgs)} images")

# ── Corriger data.yaml ────────────────────────────────────────────────────────
import os

BASE = os.path.abspath(DATASET_PATH)

yaml_content = f"""train: {BASE}/train/images
val: {BASE}/valid/images

nc: 10
names: ['Bicycle', 'Bus', 'Car', 'Dog', 'Electric pole', 'Motorcycle', 'Person', 'Traffic signs', 'Tree', 'Uncovered manhole']
"""

with open(f"{DATASET_PATH}/data.yaml", "w") as f:
    f.write(yaml_content)

print("✅ data.yaml corrigé")
print(f"📁 Chemin absolu : {BASE}")

# ── Entraînement ──────────────────────────────────────────────────────────────
print("🚀 Démarrage de l'entraînement YOLO...")

model = YOLO("yolov8n.pt")  # part du modèle de base

model.train(
    data=f"{DATASET_PATH}/data.yaml",
    epochs=10,
    imgsz=416,
    batch=4,
    name="obstacle_model",
    project="runs",
    patience=5,
    device="cpu"
)

print("🎉 Entraînement terminé !")
print("📁 Modèle sauvegardé dans : runs/obstacle_model/weights/best.pt")