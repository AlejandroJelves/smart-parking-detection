# 🚗 Smart Parking Detection

Smart Parking Detection is a hackathon project that uses **FastAPI**, **Google Gemini AI**, **Streamlit**, and **OpenCV** to analyze live drone/stream video feeds and predict parking occupancy trends in real time.

The system captures frames from a livestream or fallback video, ingests them through Gemini AI for parking spot detection, stores results in a JSON history, and then forecasts future parking demand using a Random Forest model. A Streamlit dashboard visualizes live occupancy, historical trends, and AI-powered forecasts.

---

## 🛠️ Tech Stack
- **Backend:** FastAPI, Python, Uvicorn, Requests, OpenCV, Pillow  
- **AI/ML:** Google Gemini API, scikit-learn (RandomForest), Pandas, NumPy  
- **Frontend:** Streamlit, Plotly, Requests  
- **Data Handling:** JSON history logs, .env config with dotenv

---

## ⚡ Setup

### 1. Clone the repo
```bash
git clone https://github.com/<your-org>/smart-parking-detection.git
cd smart-parking-detection

2. Backend Setup
cd backend
python -m venv venv

# Activate environment
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt


Run the FastAPI server:

uvicorn main:app --reload --host 127.0.0.1 --port 8000

3. Dashboard Setup
cd dashboard
python -m venv venv

# Activate environment
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt


Run the Streamlit dashboard:

streamlit run app.py

4. Environment Variables (.env)

Create a .env file in the backend/ directory with these keys:

MODE=live
GEMINI_API_KEY=xxxx
API_URL=http://127.0.0.1:8000
STREAM_URL=https://customer-xxxx.cloudflarestream.com/.../manifest/video.m3u8
FALLBACK_URL=data/videos/sample.mp4

📊 Workflow

Livestream → Frames (captured every 30s via OpenCV)

Frames → JSON (Gemini AI counts open/occupied spots)

JSON → History (appends to parking_history.json)

ML Forecasting (Random Forest or fallback moving average)

Dashboard Visualization (real-time status + predictions)

▶️ Instructions for Use

Start the Backend (FastAPI)

cd backend
# Activate venv
venv\Scripts\activate   # Windows
# or
source venv/bin/activate   # macOS / Linux

uvicorn main:app --reload --host 127.0.0.1 --port 8000


Start the Snapshot Worker (grabs frames every INTERVAL_SECONDS and sends them to FastAPI)

cd backend
# Activate venv
venv\Scripts\activate
python streaming/snapshot_worker.py


Run the Dashboard (Streamlit)

cd dashboard
# Activate venv
venv\Scripts\activate
streamlit run app.py


Open the Dashboard

Visit: http://localhost:8501

Live Mode vs Fallback Mode

If STREAM_URL responds, the worker ingests the live drone/cloud HLS stream.

If the stream is offline or unreachable, the worker falls back to FALLBACK_URL (local MP4) automatically.

✅ Fallbacks & Robustness

Stream fallback: snapshot worker attempts STREAM_URL then FALLBACK_URL.

Vision fallback: if Gemini fails or is unavailable, the backend uses safe default counts to keep the pipeline moving.

Prediction fallback: if history is too small to train the RF model, the predictor uses a moving average or a dummy trend.

🚀 Inspiration

Parking inefficiency costs cities, businesses, and drivers time and money. Real-time parking visibility transforms video into actionable intelligence: optimize lot layouts and staffing, improve customer flows, reduce congestion and emissions, and enable predictive urban mobility solutions. The same pipeline can scale to fleet yards, event management, and broader smart-city analytics.
