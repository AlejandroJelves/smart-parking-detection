# backend/streaming/snapshot_worker.py
import os, time, requests, cv2
from dotenv import load_dotenv

load_dotenv()

API = os.getenv("API_URL", "http://127.0.0.1:8000")
STREAM_URL = os.getenv("STREAM_URL", "")
FALLBACK_URL = os.getenv("FALLBACK_URL", "")

# Save where FastAPI serves/reads: backend/data/images/latest.jpg
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMAGES_DIR = os.path.join(BACKEND_DIR, "data", "images")
LATEST = os.path.join(IMAGES_DIR, "latest.jpg")

INTERVAL_SECONDS = 30
TIMEOUT_SEC = 10

def _resolve(url_or_path: str) -> str:
    # URLs pass through; local paths resolved relative to backend/
    if url_or_path.startswith(("http://","https://","rtsp://")):
        return url_or_path
    return os.path.abspath(os.path.join(BACKEND_DIR, url_or_path))

def _open_capture(src: str):
    cap = cv2.VideoCapture(src, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        try: cap.release()
        except Exception: pass
        return None
    return cap

def grab_one_frame():
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # try live first
    live_src = _resolve(STREAM_URL) if STREAM_URL else None
    cap = _open_capture(live_src) if live_src else None
    source = "STREAM_URL"

    # fallback to local MP4 if live fails
    if cap is None and FALLBACK_URL:
        fb_src = _resolve(FALLBACK_URL)
        cap = _open_capture(fb_src)
        source = "FALLBACK_URL"

    if cap is None:
        raise RuntimeError("Cannot open any source (STREAM_URL and FALLBACK_URL).")

    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError(f"Failed to read frame from {source}")

    cv2.imwrite(LATEST, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return LATEST, source

def post_ingest(frame_path):
    # FastAPI expects {"path": "..."} at /ingest/frame
    payload = {"path": frame_path}
    r = requests.post(f"{API}/ingest/frame", json=payload, timeout=TIMEOUT_SEC)
    r.raise_for_status()
    return r.json()

if __name__ == "__main__":
    print(f"[worker] STREAM_URL set? {bool(STREAM_URL)} | FALLBACK_URL set? {bool(FALLBACK_URL)}")
    while True:
        try:
            path, src = grab_one_frame()
            resp = post_ingest(path)
            print(f"✅ frame ({src}) -> /ingest/frame | spots logged -> history count may grow")
        except Exception as e:
            print("⚠️ worker error:", e)
        time.sleep(INTERVAL_SECONDS)