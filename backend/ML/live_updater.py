import os, json
from .gemini_analyzer import analyze_frame

def update_live_from_frame(latest_path: str, out_json: str, area_label: str = "general"):
    if not os.path.exists(latest_path):
        raise FileNotFoundError(latest_path)
    result = analyze_frame(latest_path)
    result["area"] = area_label
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(result, f, indent=2)
    return result
