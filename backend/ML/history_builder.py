import os, cv2, json
from datetime import datetime
from .gemini_analyzer import analyze_frame

def extract_frames(video_path: str, output_dir: str, step: int = 60):
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    frame_idx, saved = 0, 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % step == 0:
            out = os.path.join(output_dir, f"frame_{saved:05d}.jpg")
            cv2.imwrite(out, frame)
            saved += 1
        frame_idx += 1
    cap.release()
    return saved

def frames_to_history(frames_dir: str, out_json: str, area_label: str = "general"):
    records = []
    for name in sorted(os.listdir(frames_dir)):
        if not name.lower().endswith(".jpg"):
            continue
        path = os.path.join(frames_dir, name)
        result = analyze_frame(path)
        result["area"] = area_label
        records.append(result)
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(records, f, indent=2)
    return len(records)
