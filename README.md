# 🚀 Smart Parking Detection

Hackathon project using FastAPI + Gemini + Streamlit.

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Dashboard
```bash
cd dashboard
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Env Vars (.env)
```
GEMINI_API_KEY=xxxx
MONGO_URI=xxxx
```
