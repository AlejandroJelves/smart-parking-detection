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
<img width="790" height="502" alt="image" src="https://github.com/user-attachments/assets/5f9f4f34-9448-4b36-9c77-308d637ff7d7" />
