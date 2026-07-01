import os
import time
import argparse
import logging
import subprocess
import platform
import threading
from pathlib import Path
import mimetypes
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SIM] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("simulator")

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}

def download_audio(audio_url: str) -> str | None:
    import tempfile
    try:
        filename = audio_url.split("/")[-1]
        tmp_path = str(Path(tempfile.gettempdir()) / filename)
        if Path(tmp_path).exists():
            return tmp_path
        r = requests.get(audio_url, timeout=15)
        r.raise_for_status()
        with open(tmp_path, "wb") as f:
            f.write(r.content)
        return tmp_path
    except Exception as e:
        logger.warning(f"  Échec téléchargement audio : {e}")
        return None


def play_audio(audio_url: str):
    if not audio_url:
        return
    local_path = download_audio(audio_url)
    if not local_path:
        return
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(local_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        logger.info(f"  Audio joué : {Path(local_path).name}")
        return
    except Exception:
        pass

    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(local_path)
        elif system == "Darwin":
            subprocess.Popen(["afplay", local_path])
        else:
            for player in ["mpg123", "mpg321", "ffplay"]:
                try:
                    subprocess.Popen(
                        [player, "-q", local_path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return
                except FileNotFoundError:
                    continue
    except Exception as e:
        logger.warning(f"  Impossible de jouer l'audio : {e}")

def send_image(path: Path, api_url: str, timeout: int = 60) -> dict:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"

    for attempt in range(1, 4):
        try:
            with open(path, "rb") as f:
                response = requests.post(
                    f"{api_url}/read",
                    files={"file": (path.name, f, mime)},
                    timeout=timeout,
                )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"  Tentative {attempt}/3 échouée : {e}")
            if attempt < 3:
                time.sleep(2)

    return {"error": "Connexion impossible après 3 tentatives"}


def process_result(result: dict, img_name: str):
    if "error" in result:
        logger.error(f"[X]  Erreur : {result['error']}")
        return

    if not result.get("success"):
        logger.info(f"[ ]  Pas de texte détecté dans : {img_name}")
        return

    lang      = result.get("language", "?")
    engine    = result.get("tts_engine", "?")
    summary   = result.get("summary", "")
    audio_url = result.get("audio_url")

    preview = summary[:80] + ("..." if len(summary) > 80 else "")
    logger.info(f"[OK] [{lang}] engine={engine}")
    logger.info(f"     Résumé : \"{preview}\"")

    if audio_url:
        play_audio(audio_url)
    else:
        logger.warning("  audio_url absent — vérifier SERVER_BASE_URL dans .env")


# ── Get images from folder ─────────────────────────────────────────────────────

def get_images(directory: Path) -> list[Path]:
    """Return sorted list of images in directory."""
    images = sorted([
        f for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ])
    return images


# ── Main loop ──────────────────────────────────────────────────────────────────

def run(directory: str, api_url: str, timeout: int):
    watch_dir = Path(directory)
    watch_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 55)
    logger.info("  Simulateur ESP32 v5.0 — Mode bouton")
    logger.info(f"  Dossier : {watch_dir.resolve()}")
    logger.info(f"  API     : {api_url}")
    logger.info("=" * 55)
    logger.info("")
    logger.info("  → Appuyez sur ENTRÉE pour simuler un clic sur le bouton")
    logger.info("  → Chaque appui = 1 photo envoyée = 1 audio lu")
    logger.info("  → Ctrl+C pour quitter")
    logger.info("")

    # Check server health
    try:
        r = requests.get(f"{api_url}/health", timeout=5)
        r.raise_for_status()
        logger.info(f"Serveur OK : {r.json().get('version', '?')}")
    except Exception as e:
        logger.error(f"Serveur inaccessible : {e}")
        logger.error(f"Lance le serveur avec : uvicorn main:app --host 0.0.0.0 --port 8002 --workers 4")
        return

    index = 0

    try:
        while True:
            input("\n  [ Appuyez sur ENTRÉE pour lire ] ")

            # Refresh image list at each press (supports adding new images)
            images = get_images(watch_dir)

            if not images:
                logger.warning(f"  Aucune image dans {watch_dir} — ajoute des images JPEG")
                continue

            # Cycle through images
            img_path = images[index % len(images)]
            index += 1

            logger.info(f"->  Envoi : {img_path.name}")

            start = time.time()
            result = send_image(img_path, api_url, timeout)
            elapsed = round(time.time() - start, 1)

            logger.info(f"    Réponse reçue en {elapsed}s")
            process_result(result, img_path.name)

    except KeyboardInterrupt:
        logger.info("\nSimulation arrêtée.")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ESP32-CAM Simulator v5.0 — One click one photo"
    )
    parser.add_argument("--dir",     default="./images_input",       help="Dossier contenant les images")
    parser.add_argument("--url",     default="http://localhost:8002", help="URL du serveur")
    parser.add_argument("--timeout", type=int, default=60,           help="Timeout requête (s)")
    parser.add_argument("--verbose", action="store_true",            help="Logs DEBUG")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    run(args.dir, args.url, args.timeout)