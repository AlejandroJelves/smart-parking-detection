import os, json
from fastapi import FastAPI, Body
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from ML.history_builder import extract_frames, frames_to_history
from ML.live_updater import update_live_from_frame
from ML.predictor import forecast_from_history

load_dotenv()

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
FRAMES_DIR = os.path.join(DATA_DIR, "frames")
HISTORY_JSON = os.path.join(DATA_DIR, "parking_history.json")
LIVE_JSON = os.path.join(DATA_DIR, "live_parking.json")
LATEST_SNAPSHOT = os.path.join(IMAGES_DIR, "latest.jpg")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)

app = FastAPI(title="Smart Parking Backend")

# serve images so Streamlit can show latest snapshot
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# ---------- Models ----------
class IngestVideoReq(BaseModel):
    video_path: str
    step: int = 60             # every N frames (≈2s at 30fps)
    frames_dir: str | None = None
    area: str = "general"

class IngestLiveReq(BaseModel):
    frame_path: str = LATEST_SNAPSHOT
    area: str = "general"

# ---------- Helpers ----------
def _read_json(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)

# ---------- Endpoints ----------

@app.get("/status")
def status():
    return {"ok": True}

@app.get("/snapshot")
def snapshot():
    # expects hexair_stream.py (or similar) to keep saving images/latest.jpg
    return {"url": "http://127.0.0.1:8000/images/latest.jpg"}

@app.get("/spots")
def spots():
    """
    Current estimate for the entire area in format:
    { taken_spots, estimated_total, confidence, timestamp, source }
    """
    live = _read_json(LIVE_JSON)
    if live:
        return live
    # fallback demo
    return {
        "timestamp": "2025-09-20T12:00:00Z",
        "taken_spots": 130,
        "estimated_total": 200,
        "confidence": 0.70,
        "source": "demo"
    }

@app.get("/predict")
def predict():
    """
    Forecast over time:
    { "forecast": [ {time, taken_spots, estimated_total}, ... ] }
    """
    hist = _read_json(HISTORY_JSON) or []
    horizon = forecast_from_history(hist, horizon_hours=12, step_minutes=60)
    return {"forecast": horizon}

# ---------- Ingestion / Build ----------

@app.post("/ingest/video")
def ingest_video(req: IngestVideoReq):
    """
    1) Extract frames from a recorded video
    2) Run Gemini on frames -> build/overwrite parking_history.json
    """
    frames_dir = req.frames_dir or FRAMES_DIR
    saved = extract_frames(req.video_path, frames_dir, step=req.step)
    count = frames_to_history(frames_dir, HISTORY_JSON, area_label=req.area)
    return {"frames_saved": saved, "records_built": count, "history_path": HISTORY_JSON}

@app.post("/ingest/live")
def ingest_live(req: IngestLiveReq):
    """
    Take a single frame (e.g., images/latest.jpg from live stream) and
    compute the current area estimate -> live_parking.json
    """
    result = update_live_from_frame(req.frame_path, LIVE_JSON, area_label=req.area)
    return result
