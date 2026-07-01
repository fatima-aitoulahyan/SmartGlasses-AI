"""
tts_service.py — v6.0
======================
Languages:
  - French  (fr) → gTTS
  - Spanish (es) → gTTS
  - Arabic  (ar) → Meta MMS (facebook/mms-tts-ara) + gTTS fallback
"""

import hashlib, logging, os
from pathlib import Path

logger   = logging.getLogger(__name__)
AUDIO_DIR = Path(os.getenv("AUDIO_DIR", "./audio_output"))
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

_MMS_MODELS:     dict = {}
_MMS_TOKENIZERS: dict = {}


def _synthesize_amazigh_space(text: str, output_path: str) -> str:
    """
    Use HuggingFace Space ayymen/Amazigh-tts.
    Accepts Tifinagh Unicode directly — no Latin conversion needed.
    """
    from gradio_client import Client
    import shutil, tempfile, os

    client = Client("ayymen/Amazigh-tts")
    # "Tamajaq, Tawallammat (Tifinagh script)" accepts Tifinagh Unicode directly
    # "Tachelhit" needs Latin script input
    if _has_tifinagh(text):
        variant = "Tamajaq, Tawallammat (Tifinagh script)"
    else:
        variant = "Tachelhit"
    result = client.predict(text, variant, api_name="/predict")
    logger.info(f"[TTS] Amazigh space using variant: {variant}")

    # result is a file path returned by Gradio
    if isinstance(result, str) and os.path.exists(result):
        shutil.copy(result, output_path)
        return output_path
    # Sometimes result is a tuple (path, sample_rate) or dict
    if isinstance(result, (list, tuple)):
        src = result[0] if isinstance(result[0], str) else result
        if os.path.exists(str(src)):
            shutil.copy(str(src), output_path)
            return output_path
    raise ValueError(f"Unexpected result format from Amazigh TTS space: {result}")



def _get_mms_model(model_name: str):
    if model_name not in _MMS_MODELS:
        from transformers import VitsModel, AutoTokenizer
        import torch
        print(f"[MMS-TTS] Loading {model_name}...")
        _MMS_TOKENIZERS[model_name] = AutoTokenizer.from_pretrained(model_name)
        _MMS_MODELS[model_name]     = VitsModel.from_pretrained(model_name)
        if torch.cuda.is_available():
            _MMS_MODELS[model_name] = _MMS_MODELS[model_name].cuda()
        print(f"[MMS-TTS] {model_name} loaded.")
    return _MMS_MODELS[model_name], _MMS_TOKENIZERS[model_name]


def _synthesize_mms(text: str, model_name: str, output_path: str) -> str:
    import torch, scipy.io.wavfile as wav
    model, tokenizer = _get_mms_model(model_name)
    device = next(model.parameters()).device
    inputs = tokenizer(text, return_tensors="pt").to(device)
    with torch.no_grad():
        audio = model(**inputs).waveform.squeeze().cpu().numpy()
    wav_path = output_path.replace(".mp3", ".wav")
    wav.write(wav_path, rate=model.config.sampling_rate, data=audio)
    try:
        from pydub import AudioSegment
        AudioSegment.from_wav(wav_path).export(output_path, format="mp3")
        os.remove(wav_path)
        return output_path
    except Exception:
        return wav_path


def _gtts(text: str, lang: str, output_path: str) -> bool:
    from gtts import gTTS
    gTTS(text=text, lang=lang, slow=False).save(output_path)
    return True


def _has_tifinagh(text: str) -> bool:
    """Return True if text contains Tifinagh Unicode characters."""
    return any("\u2D30" <= c <= "\u2D7F" for c in text)


def _clean_text(text: str) -> str:
    """Remove JSON artifacts and control characters before TTS."""
    import re, json
    # If text looks like JSON, extract meaningful content
    if text.strip().startswith("{"):
        try:
            d = json.loads(text)
            summary = (d.get("summary") or "").strip()
            raw_text = (d.get("text") or "").strip()
            # Use summary if it has Latin content, else use text field
            if summary and not _has_tifinagh(summary):
                text = summary
            elif raw_text and not _has_tifinagh(raw_text):
                text = raw_text
            else:
                # Both fields have Tifinagh — MMS cannot speak them
                logger.warning("[TTS] Text contains only Tifinagh chars — MMS needs Latin")
                return ""
        except Exception:
            text = re.sub(r'[{}"\\":]', " ", text)
    # Reject if still Tifinagh (can't be synthesized by MMS)
    if _has_tifinagh(text):
        logger.warning("[TTS] Tifinagh chars in text — rejecting for MMS")
        return ""
    # Remove escape sequences and collapse spaces
    text = text.replace("\\n", " ").replace("\n", " ")
    text = re.sub(r" +", " ", text).strip()
    return text


class TtsService:

    def synthesize(self, text: str, language: str) -> dict:
        import json as _json, re as _re

        if language in ("ber", "tzm", "shi"):
            if text.strip().startswith("{"):
                try:
                    d = _json.loads(text)
                    summary = (d.get("summary") or "").strip()
                    raw     = (d.get("text")    or "").strip()
                    text = summary if summary else raw
                except Exception:
                    text = _re.sub(r'[{}":]', " ", text).strip()
            text = text.replace("\\n", " ").replace("\n", " ").strip()
        else:
            text = _clean_text(text)
        if not text or not text.strip():
            return {"audio_path": None, "language": language, "error": "Empty text"}

        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        filename  = str(AUDIO_DIR / f"{language}_{text_hash}.mp3")

        if Path(filename).exists():
            return {"audio_path": filename, "language": language, "cached": True, "engine": "cache"}

        # Berber / Tamazight / Tachelhit
        if language in ("ber", "tzm", "shi"):
            # 1st choice: ayymen/Amazigh-tts space (accepts Tifinagh directly)
            try:
                actual_path = _synthesize_amazigh_space(text, filename)
                logger.info("[TTS] Berber TTS OK with ayymen/Amazigh-tts space")
                return {"audio_path": actual_path, "language": language, "cached": False, "engine": "amazigh-tts-space"}
            except Exception as e:
                logger.warning(f"[TTS] Amazigh space failed: {e} -> MMS fallback")
            # 2nd choice: MMS local models
            for mms_model in ("facebook/mms-tts-shi", "facebook/mms-tts-tzm", "facebook/mms-tts-kab"):
                try:
                    actual_path = _synthesize_mms(text, mms_model, filename)
                    logger.info(f"[TTS] Berber TTS OK with {mms_model}")
                    return {"audio_path": actual_path, "language": language, "cached": False, "engine": mms_model}
                except Exception as e:
                    logger.warning(f"[TTS] {mms_model} failed: {e}")
                    continue
            # Last resort: Arabic gTTS
            logger.warning("[TTS] All Berber engines failed -> Arabic gTTS")
            try:
                _gtts(text, "ar", filename)
                return {"audio_path": filename, "language": language, "cached": False, "engine": "gtts-ar-fallback"}
            except Exception as e:
                return {"audio_path": None, "language": language, "error": str(e)}

        # Arabic → MMS primary, gTTS fallback
        elif language == "ar":
            try:
                actual_path = _synthesize_mms(text, "facebook/mms-tts-ara", filename)
                return {"audio_path": actual_path, "language": language, "cached": False, "engine": "mms-tts-ara"}
            except Exception as e:
                logger.warning(f"[TTS] MMS Arabic failed: {e} → gTTS fallback")
                try:
                    _gtts(text, "ar", filename)
                    return {"audio_path": filename, "language": language, "cached": False, "engine": "gtts-ar-fallback"}
                except Exception as e2:
                    return {"audio_path": None, "language": language, "error": str(e2)}

        # French or Spanish → gTTS
        elif language in ("fr", "es"):
            try:
                _gtts(text, language, filename)
                return {"audio_path": filename, "language": language, "cached": False, "engine": f"gtts-{language}"}
            except Exception as e:
                return {"audio_path": None, "language": language, "error": str(e)}

        # Unknown → French fallback
        else:
            try:
                _gtts(text, "fr", filename)
                return {"audio_path": filename, "language": language, "cached": False, "engine": "gtts-fr-fallback"}
            except Exception as e:
                return {"audio_path": None, "language": language, "error": str(e)}

    def list_audio_files(self) -> list:
        return [
            {"filename": f.name, "path": str(f), "size_kb": round(f.stat().st_size / 1024, 1)}
            for f in sorted(AUDIO_DIR.glob("*.mp3"))
        ]


tts_service = TtsService()