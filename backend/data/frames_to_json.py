import google.generativeai as genai
import os, json
from datetime import datetime
from PIL import Image

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

results = []

frames_dir = "frames/"
for filename in os.listdir(frames_dir):
    if filename.endswith(".jpg"):
        frame_path = os.path.join(frames_dir, filename)
        img = Image.open(frame_path)

        prompt = """
        You are analyzing a parking lot from a drone.
        Count how many parking spaces are visible.
        Tell me:
        - How many are occupied by cars
        - How many are open
        Return ONLY JSON in the format:
        {"open_spots": X, "occupied": Y}
        """

        response = model.generate_content([prompt, img])
        parsed = json.loads(response.text)  # parse Gemini’s JSON response

        results.append({
            "timestamp": datetime.now().isoformat(),  # later: sync with frame time
            "lot": "A",
            "open_spots": parsed["open_spots"],
            "occupied": parsed["occupied"]
        })

# Save as JSON
with open("parking_history.json", "w") as f:
    json.dump(results, f, indent=2)
