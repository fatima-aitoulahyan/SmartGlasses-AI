import os, re, base64, json, logging, time, threading
from collections import deque

import cv2, httpx, numpy as np
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GROQ_MODEL           = "meta-llama/llama-4-scout-17b-16e-instruct"
GROQ_URL             = "https://api.groq.com/openai/v1/chat/completions"
MAX_REQUESTS_PER_MIN = 28
MIN_INTERVAL_S       = 60.0 / MAX_REQUESTS_PER_MIN
CONTEXT_MAX_ITEMS    = 3

GEMINI_URL       = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
GEMINI_URL_FLASH = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

GEMINI_PROMPT = (
    "You are a precise OCR for Tifinagh/Neo-Tifinagh script.\n"
    "Extract EXACT characters from the image. NO translation. NO interpretation.\n\n"
    "Character guide:\n"
    "  yA=cross, yU=circle, yN=X-shape, yT=bar+vertical\n"
    "  yI=vertical line, yL=vertical+hook, yS=3dots, yZ=zigzag\n\n"
    'JSON only: {"text": "<exact chars>", "summary": "<same exact chars>"}\n'
    "No markdown. The text and summary must be identical."
)


def analyze_with_gemini(image):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {"text": "", "language": "fr", "summary": "", "error": "GEMINI_API_KEY missing"}
    try:
        _, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        b64 = base64.b64encode(buf).decode("utf-8")
        payload = {
            "contents": [{"parts": [
                {"text": GEMINI_PROMPT},
                {"inline_data": {"mime_type": "image/jpeg", "data": b64}},
            ]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048, "responseMimeType": "application/json"},
        }
        hdrs = {"Content-Type": "application/json", "X-goog-api-key": api_key}
        with httpx.Client(timeout=30.0) as c:
            r = None
            for url in [GEMINI_URL, GEMINI_URL_FLASH]:
                model = url.split("/models/")[1].split(":")[0]
                r = c.post(url, json=payload, headers=hdrs)
                if r.status_code not in (429, 403, 404):
                    break
                logger.warning(f"[GEMINI] {model} -> {r.status_code}")
            if r.status_code == 429:
                time.sleep(15)
                r = c.post(url, json=payload, headers=hdrs)
            r.raise_for_status()
        raw = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        logger.info(f"[GEMINI] raw: {raw[:150]}")
        if raw.startswith("```"):
            raw = "\n".join(l for l in raw.split("\n") if not l.strip().startswith("```")).strip()
        d = None
        try:
            d = json.loads(raw)
        except Exception:
            m = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
            if m:
                try: d = json.loads(m.group())
                except Exception: pass
        if d is None:
            return {"text": raw[:500], "language": "ber", "summary": raw[:900], "error": None}
        text = str(d.get("text", ""))[:500].strip()
        summary = str(d.get("summary", "")).strip() or text
        summary = summary[:900]
        logger.info(f"[GEMINI] lu -> '{summary[:80]}'")
        return {"text": text, "language": "ber", "summary": summary, "error": None}
    except Exception as e:
        logger.error(f"[GEMINI] Erreur : {e}")
        return {"text": "", "language": "fr", "summary": "", "error": str(e)}


GROQ_PROMPT = """You are an assistant helping blind people understand text in images.

STEP 1 - IDENTIFY THE LANGUAGE:
- French OR French+Arabic mix  -> language: "fr", summary IN FRENCH
- ONLY Arabic script           -> language: "ar", summary IN ARABIC
- Spanish                      -> language: "es", summary IN SPANISH
- Tifinagh/Berber/Tamazight    -> language: "other", text: "tifinagh", summary: ""
- Other unreadable script      -> language: "other", text: "unknown", summary: ""

STEP 2 - Copy ALL visible text into "text" field (max 500 chars).

STEP 3 - For FR/AR/ES: write COMPLETE DETAILED summary as if reading aloud.
Include: document type, names, dates, numbers, addresses, prices, warnings.

Return ONLY valid JSON: {"text": "...", "language": "...", "summary": "..."}
text max 500 chars, summary max 900 chars, JSON only no markdown"""


def _encode_image(image):
    _, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return base64.b64encode(buf).decode("utf-8")


def _parse_json(raw):
    text = raw.strip()
    if text.startswith("```"):
        text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```")).strip()
    for attempt in [text, None]:
        if attempt is None:
            m = re.search(r'\{[^{}]*\}', text, re.DOTALL)
            if not m: break
            attempt = m.group()
        try:
            d = json.loads(attempt)
            return {
                "text":     str(d.get("text",     ""))[:500].strip(),
                "language": str(d.get("language", "fr")).strip(),
                "summary":  str(d.get("summary",  ""))[:900].strip(),
                "error":    None,
            }
        except Exception:
            pass
    if len(text) > 10 and not text.startswith("{"):
        return {"text": text[:500], "language": "other", "summary": "", "error": None}
    return {"text": "", "language": "fr", "summary": "", "error": "Cannot parse JSON"}


class RateLimiter:
    def __init__(self, min_interval=MIN_INTERVAL_S):
        self._min = min_interval; self._last = 0.0; self._lock = threading.Lock()
    def wait(self):
        with self._lock:
            w = self._min - (time.time() - self._last)
            if w > 0: time.sleep(w)
            self._last = time.time()
    def backoff(self, s=15.0):
        time.sleep(s)
        with self._lock: self._last = time.time()


class ContextMemory:
    def __init__(self, n=CONTEXT_MAX_ITEMS):
        self._q = deque(maxlen=n); self._lock = threading.Lock()
    def add(self, s):
        if s and s.strip():
            with self._lock: self._q.append(s.strip())
    def get(self):
        with self._lock: return list(self._q)
    def reset(self):
        with self._lock: self._q.clear()


class GroqService:
    def __init__(self):
        self.context = ContextMemory()
        self.rate_limiter = RateLimiter()

    def analyze_image(self, image):
        result = self._call_groq(image)
        if result.get("error") and "HTTP" in str(result.get("error", "")):
            return result

        gemini_needed = (
            result.get("language") == "other"
            or (not result.get("summary") and result.get("error"))
        )
        if gemini_needed:
            if os.getenv("GEMINI_API_KEY", "").strip():
                logger.info("[GROQ] Tifinagh/echec -> Gemini fallback")
                gr = analyze_with_gemini(image)
                if gr.get("summary") and not gr.get("error"):
                    result = gr
                    logger.info(f"[GEMINI] lu : '{result['summary'][:60]}'")
                else:
                    logger.warning(f"[GEMINI] Echec : {gr.get('error')}")
                    result["summary"] = ""; result["language"] = "fr"
            else:
                result["summary"] = "Tifinagh detecte. Ajouter GEMINI_API_KEY dans .env"
                result["language"] = "fr"

        if result.get("summary"):
            self.context.add(result["summary"])
        return result

    def _call_groq(self, image):
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            return {"text": "", "language": "fr", "summary": "", "error": "GROQ_API_KEY missing"}
        self.rate_limiter.wait()
        ctx = self.context.get()
        prompt = GROQ_PROMPT
        if ctx:
            prompt += "\n\nCONTEXT:\n" + "\n".join(f"  - {s}" for s in ctx)
        try:
            payload = {
                "model": GROQ_MODEL,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{_encode_image(image)}"}},
                ]}],
                "max_tokens": 1024, "temperature": 0.1,
            }
            with httpx.Client(timeout=25.0) as c:
                r = c.post(GROQ_URL, json=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
                r.raise_for_status()
            raw = r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            result = _parse_json(raw)
            if result["language"] not in ("ar", "fr", "es", "other"):
                result["language"] = "fr"
            logger.info(f"[GROQ] lang={result['language']} | summary='{result.get('summary','')[:40]}'")
            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"[GROQ] HTTP {e.response.status_code}: {e.response.text[:200]}")
            if e.response.status_code == 429:
                self.rate_limiter.backoff(15.0)
            return {"text": "", "language": "fr", "summary": "", "error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            logger.error(f"[GROQ] {e}")
            return {"text": "", "language": "fr", "summary": "", "error": str(e)}

    def reset_context(self):
        self.context.reset()


groq_service = GroqService()