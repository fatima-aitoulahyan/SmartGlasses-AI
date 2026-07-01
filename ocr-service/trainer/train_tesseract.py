import subprocess
import os
import shutil

DATA_DIR    = "/app/data"
TESSDATA    = "/app/tessdata"
MODEL_OUT   = "/app/models"
LANG        = "ber"
ITERATIONS  = 3600

os.makedirs(MODEL_OUT, exist_ok=True)
os.makedirs(TESSDATA,  exist_ok=True)


def check_data():
    images = os.listdir(f"{DATA_DIR}/images") if os.path.exists(f"{DATA_DIR}/images") else []
    if not images:
        print("ERROR: No training images found in /app/data/images/")
        print("Please provide Tifinagh images before training.")
        exit(1)
    print(f"Found {len(images)} training images")


def generate_training_files():
    training_files = []

    images_dir = f"{DATA_DIR}/images"
    gt_dir     = f"{DATA_DIR}/ground-truth"

    for img_file in os.listdir(images_dir):
        if not img_file.endswith(".png"):
            continue

        base  = img_file.replace(".png", "")
        img   = f"{images_dir}/{img_file}"
        gt    = f"{gt_dir}/{base}.gt.txt"
        lstmf = f"{DATA_DIR}/{base}.lstmf"

        if not os.path.exists(gt):
            continue

        subprocess.run([
            "tesseract", img, f"{DATA_DIR}/{base}",
            "--psm", "6",
            "lstm.train"
        ], check=True)

        if os.path.exists(lstmf):
            training_files.append(lstmf)

    list_file = f"{DATA_DIR}/ber.training_files.txt"
    with open(list_file, "w") as f:
        f.write("\n".join(training_files))

    print(f"Generated {len(training_files)} training files")
    return list_file


def train(list_file: str):
    base_traineddata = f"{TESSDATA}/ber.traineddata"

    if not os.path.exists(base_traineddata):
        print("WARNING: No base ber.traineddata found.")
        print("Training from scratch (fine-tuning from Latin is recommended).")
        base_lstm = None
    else:
        base_lstm = f"{MODEL_OUT}/ber_base.lstm"
        subprocess.run([
            "combine_tessdata", "-e",
            base_traineddata, base_lstm
        ], check=True)

    cmd = [
        "lstmtraining",
        f"--model_output={MODEL_OUT}/ber",
        f"--traineddata={base_traineddata}",
        f"--train_listfile={list_file}",
        f"--max_iterations={ITERATIONS}",
    ]

    if base_lstm and os.path.exists(base_lstm):
        cmd.append(f"--continue_from={base_lstm}")

    subprocess.run(cmd, check=True)

    subprocess.run([
        "lstmtraining", "--stop_training",
        f"--continue_from={MODEL_OUT}/ber_checkpoint",
        f"--traineddata={base_traineddata}",
        f"--model_output={TESSDATA}/ber.traineddata"
    ], check=True)

    print(f"Training complete. Model saved to {TESSDATA}/ber.traineddata")


if __name__ == "__main__":
    check_data()
    list_file = generate_training_files()
    train(list_file)
