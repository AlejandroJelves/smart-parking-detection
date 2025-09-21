import os, json, time
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Body
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from PIL import Image

# ML forecast import
from backend.predictor import forecast_from_history

# ---------- Optional Gemini ----------
USE_GEMINI = True
try:
    load_dotenv()
    import google.generativeai as genai
    if os.getenv("GEMINI_API_KEY"):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    else:
        USE_GEMINI = False
except Exception:
    USE_GEMINI = False

# ---------- FastAPI App ----------
app = FastAPI()

# --- Paths ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
FRAMES_DIR = os.path.join(DATA_DIR, "frames")
HISTORY_JSON = os.path.join(DATA_DIR, "parking_history.json")
LATEST_SNAPSHOT = os.path.join(IMAGES_DIR, "latest.jpg")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)

# Serve images (preview latest.jpg)
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# ---------- Gemini Prompt ----------
PROMPT = """
You are analyzing a parking lot from a drone.
Count how many parking spaces are visible.
Tell me:
- How many are occupied by cars
- How many are open
Keep the estimated total as (occupied + open).
Return ONLY JSON in the format:
{"open_spots": X, "occupied": Y}
"""

# ---------- Utils ----------
def read_history() -> List[dict]:
    if not os.path.exists(HISTORY_JSON):
        return []
    with open(HISTORY_JSON, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def write_history(records: List[dict]):
    with open(HISTORY_JSON, "w") as f:
        json.dump(records, f, indent=2)

def append_history(record: dict):
    hist = read_history()
    hist.append(record)
    write_history(hist)

# ---------- Schemas ----------
class FramePath(BaseModel):
    path: str

# ---------- Routes ----------
@app.get("/status")
def status():
    return {"ok": True, "using_gemini": USE_GEMINI, "history_count": len(read_history())}

@app.get("/history")
def get_history(limit: Optional[int] = 200):
    hist = read_history()
    return hist[-limit:] if limit else hist

@app.get("/forecast")
def get_forecast(h: int = 24, step: int = 60):
    """
    Return ML forecast based on parking history.
    """
    history = read_history()
    return forecast_from_history(history_records=history, horizon_hours=h, step_minutes=step)

@app.post("/ingest/frame")
def ingest_frame(body: FramePath = Body(...)):
    """
    Ingest a frame (image path) → run Gemini (if enabled) → save JSON record to history
    """
    img_path = body.path
    if not os.path.exists(img_path):
        return {"ok": False, "error": f"file not found: {img_path}"}

    # Default fallback
    occupied, open_spots = 0, 0

    if USE_GEMINI:
        try:
            im = Image.open(img_path)
            resp = gemini_model.generate_content([PROMPT, im])
            raw = (resp.text or "").strip()

            # Clean markdown fences
            if raw.startswith("```"):
                raw = raw.strip("`")
                if raw.lower().startswith("json"):
                    raw = raw[4:].strip()

            if raw.startswith("{") and raw.endswith("}"):
                parsed = json.loads(raw)
                occupied = int(parsed.get("occupied", 0))
                open_spots = int(parsed.get("open_spots", 0))
            else:
                occupied, open_spots = 100, 80  # soft default
        except Exception:
            occupied, open_spots = 100, 80

    total = max(1, occupied + open_spots)
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "frame": os.path.basename(img_path),
        "taken_spots": occupied,
        "open_spots": open_spots,
        "estimated_total": total,
        "confidence": 0.75 if USE_GEMINI else 0.4,
        "source": "Gemini scan" if USE_GEMINI else "fallback"
    }
    append_history(record)
    return {"ok": True, "appended": record}

@app.post("/ingest/upload")
async def upload_and_ingest(file: UploadFile = File(...)):
    """
    Upload a file directly to images/ and run ingestion
    """
    name = f"upload_{int(time.time())}.jpg"
    path = os.path.join(IMAGES_DIR, name)
    with open(path, "wb") as f:
        f.write(await file.read())
    return ingest_frame(FramePath(path=path))
