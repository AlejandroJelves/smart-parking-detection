import google.generativeai as genai
import os, json, time
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")
results = []

frames_dir = "backend/data/frames/"
output_json = "backend/parking_history.json"

prompt = """
You are analyzing a parking lot from a drone.
Count how many parking spaces are visible.
Tell me:
- How many are occupied by cars
- How many are open
Keep the estimated total as (occupied + open).
Return ONLY JSON in the format:
{"open_spots": X, "occupied": Y}
"""

for filename in sorted(os.listdir(frames_dir)):
    if filename.endswith(".jpg"):
        frame_path = os.path.join(frames_dir, filename)
        img = Image.open(frame_path)

        success = False
        retries = 0

        while not success and retries < 3:  # retry up to 3 times
            try:
                response = model.generate_content([prompt, img])
                raw = response.text.strip()
                print(f"🔎 Gemini raw output for {filename}:\n{raw}\n")

                # Clean Gemini output (strip markdown code fences like ```json ... ```)
                if raw.startswith("```"):
                    raw = raw.strip("`")  
                    raw = raw.replace("json", "", 1).strip()

                # Parse JSON if valid
                if raw.startswith("{") and raw.endswith("}"):
                    parsed = json.loads(raw)

                    occupied = int(parsed.get("occupied", 0))
                    open_spots = int(parsed.get("open_spots", 0))
                    total = occupied + open_spots

                    results.append({
                        "timestamp": datetime.now().isoformat(),
                        "frame": filename,
                        "taken_spots": occupied,
                        "open_spots": open_spots,
                        "estimated_total": total,
                        "confidence": 0.75,
                        "source": "Gemini scan"
                    })

                    print(f"✅ Processed {filename}: {occupied} taken / {open_spots} open")
                    success = True
                else:
                    print(f"⚠️ Skipping {filename} - not valid JSON")
                    success = True  # skip without retry

            except Exception as e:
                err = str(e)
                if "429" in err:  # quota exceeded
                    wait_time = 40
                    print(f"⏳ Quota exceeded, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    retries += 1
                else:
                    print(f"⚠️ Error processing {filename}: {e}")
                    success = True  # don't retry on other errors

# Save all results to JSON
with open(output_json, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n📂 Saved {len(results)} entries to {output_json}")
