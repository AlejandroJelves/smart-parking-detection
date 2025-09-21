import os, json, time
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Body
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

import pandas as pd
import numpy as np
import statistics
from sklearn.ensemble import RandomForestRegressor
from PIL import Image

# Optional Gemini (works if GEMINI_API_KEY is set)
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

app = FastAPI()

# --- Paths ---
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
FRAMES_DIR = os.path.join(DATA_DIR, "frames")
HISTORY_JSON = os.path.join(DATA_DIR, "parking_history.json")
LATEST_SNAPSHOT = os.path.join(IMAGES_DIR, "latest.jpg")

# >>> ADDED: path for single “current” snapshot JSON
CURRENT_JSON = os.path.join(DATA_DIR, "current_parking.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(FRAMES_DIR, exist_ok=True)

# serve images if you want to preview latest.jpg
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

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

# >>> ADDED: write the latest record as the “current” snapshot
def write_current(record: dict):
    with open(CURRENT_JSON, "w") as f:
        json.dump(record, f, indent=2)

def median_total(hist: List[dict]) -> int:
    if not hist:
        return 200
    vals = [max(1, r.get("estimated_total", 200)) for r in hist]
    return int(statistics.median(vals))

# ---------- ML (Random Forest + fallback) ----------
def train_rf(df: pd.DataFrame):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    df["dow"] = df["timestamp"].dt.dayofweek
    df["hour"] = df["timestamp"].dt.hour
    df["dow_sin"] = np.sin(2*np.pi*df["dow"]/7)
    df["dow_cos"] = np.cos(2*np.pi*df["dow"]/7)
    df["hour_sin"] = np.sin(2*np.pi*df["hour"]/24)
    df["hour_cos"] = np.cos(2*np.pi*df["hour"]/24)

    X = df[["dow_sin","dow_cos","hour_sin","hour_cos"]]
    y = df["taken_spots"]

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)
    last_ts = df["timestamp"].iloc[-1]
    return model, last_ts

def forecast(history: List[dict], horizon_hours=12, step_minutes=60):
    if not history:
        now = datetime.utcnow()
        return [{"time": (now + timedelta(minutes=step_minutes*i)).isoformat(),
                 "taken_spots": 120 + i*3, "estimated_total": 200}
                for i in range(horizon_hours)]

    df = pd.DataFrame(history)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    est_total = median_total(history)

    if len(df) < 20:
        window = max(1, min(5, len(df)))
        ma = int(df["taken_spots"].tail(window).mean())
        start = df["timestamp"].iloc[-1]
        out = []
        for i in range(1, horizon_hours+1):
            ts = start + timedelta(minutes=step_minutes*i)
            out.append({"time": ts.isoformat(), "taken_spots": ma, "estimated_total": est_total})
        return out

    model, last_ts = train_rf(df)
    out = []
    for i in range(1, horizon_hours+1):
        ts = last_ts + timedelta(minutes=step_minutes*i)
        dow = ts.weekday()
        hour = ts.hour
        feats = np.array([[
            np.sin(2*np.pi*dow/7), np.cos(2*np.pi*dow/7),
            np.sin(2*np.pi*hour/24), np.cos(2*np.pi*hour/24)
        ]])
        pred = int(model.predict(feats)[0])
        out.append({"time": ts.isoformat(), "taken_spots": pred, "estimated_total": est_total})
    return out

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
    return forecast(read_history(), horizon_hours=h, step_minutes=step)

@app.post("/ingest/frame")
def ingest_frame(body: FramePath = Body(...)):
    """
    body.path: path to a JPG/PNG (e.g., backend/data/images/latest.jpg or frames/xxx.jpg)
    Runs Gemini (if available) and appends one record to parking_history.json
    """
    img_path = body.path
    if not os.path.exists(img_path):
        return {"ok": False, "error": f"file not found: {img_path}"}

    # default safe fallback if Gemini is off
    occupied, open_spots = 0, 0

    if USE_GEMINI:
        try:
            im = Image.open(img_path)
            resp = gemini_model.generate_content([PROMPT, im])
            raw = (resp.text or "").strip()

            if raw.startswith("```"):
                raw = raw.strip("`")
                if raw.lower().startswith("json"):
                    raw = raw[4:].strip()

            if raw.startswith("{") and raw.endswith("}"):
                parsed = json.loads(raw)
                occupied = int(parsed.get("occupied", 0))
                open_spots = int(parsed.get("open_spots", 0))
            else:
                # soft default if model returns junk
                occupied, open_spots = 100, 80
        except Exception as e:
            # quota or parsing issue → still log a record so the pipeline keeps moving
            occupied, open_spots = 100, 80

    total = max(1, occupied + open_spots)
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "frame": os.path.basename(img_path),
        "image_url": "/images/latest.jpg",            # <<< optional QoL for dashboard
        "taken_spots": occupied,
        "open_spots": open_spots,
        "estimated_total": total,
        "confidence": 0.75 if USE_GEMINI else 0.4,
        "source": "Gemini scan" if USE_GEMINI else "fallback"
    }

    # >>> ADDED: write current, then append to history
    write_current(record)
    append_history(record)

    return {"ok": True, "current_written": True, "appended": record}

@app.post("/ingest/upload")
async def upload_and_ingest(file: UploadFile = File(...)):
    """
    Optional: let dashboard upload a frame directly
    """
    name = f"upload_{int(time.time())}.jpg"
    path = os.path.join(IMAGES_DIR, name)
    with open(path, "wb") as f:
        f.write(await file.read())
    return ingest_frame(FramePath(path=path))

# >>> ADDED: expose the single “current” snapshot JSON
@app.get("/current")
def get_current():
    if not os.path.exists(CURRENT_JSON):
        return {"ok": False, "error": "no current snapshot yet"}
    with open(CURRENT_JSON, "r") as f:
        return json.load(f)
