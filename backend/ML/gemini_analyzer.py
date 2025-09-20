import os, json
from datetime import datetime
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_model = genai.GenerativeModel("gemini-1.5-flash")

PROMPT = """
You are analyzing an aerial view of a general parking area.
Count how many parking spaces appear TAKEN (cars present) and how many appear OPEN.
Return ONLY compact JSON (no prose) like:
{"open_spots": X, "occupied": Y}
"""

def analyze_frame(image_path: str):
    img = Image.open(image_path)
    resp = _model.generate_content([PROMPT, img])
    parsed = json.loads(resp.text.strip())

    # convert to taken / estimated total + confidence
    occupied = int(parsed.get("occupied", 0))
    open_spots = int(parsed.get("open_spots", 0))
    estimated_total = max(occupied + open_spots, 1)
    taken_spots = occupied
    # simple static confidence (you can improve later using prompt reasoning/metadata)
    confidence = 0.75

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "taken_spots": taken_spots,
        "estimated_total": estimated_total,
        "confidence": confidence,
        "source": "Gemini vision analysis"
    }
