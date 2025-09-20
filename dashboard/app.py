import os
from dotenv import load_dotenv
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Load env variables
load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Smart Parking Dashboard", layout="wide")
# Sidebar
st.sidebar.title("Smart Parking Detection")
mode = st.sidebar.radio("Mode", ["Live", "Demo"])

# Main Title
st.title("🚗 Smart Parking Dashboard")

# --- Section 1: KPI ---
st.subheader("Best Lot Right Now")
# Placeholder - will pull from backend later
st.success("✅ Lot B (12 open spots)")  


# --- Section 2: Occupancy Table ---
st.subheader("Current Occupancy")
try:
    response = requests.get(f"{API_URL}/spots").json()
    df = pd.DataFrame(response["spots"])
    st.dataframe(df.style.background_gradient(cmap="RdYlGn_r"))
except Exception as e:
    st.warning(f"Could not load live data: {e}")
    df = pd.DataFrame([
        {"lot": "A", "open_spots": 6, "total": 20, "priority": "High"},
        {"lot": "B", "open_spots": 12, "total": 20, "priority": "Low"},
    ])
    st.dataframe(df)

# --- Section 3: Charts ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Occupancy Forecast (Time Series)")
    # Placeholder demo chart
    sample = pd.DataFrame({"time": range(10), "Lot A": [i+5 for i in range(10)], "Lot B": [15-i for i in range(10)]})
    fig = px.line(sample, x="time", y=["Lot A", "Lot B"], labels={"value": "Open Spots"})
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Current Open Spots by Lot")
    fig = px.bar(df, x="lot", y="open_spots", color="priority")
    st.plotly_chart(fig, use_container_width=True)

# --- Section 4: Snapshot Images ---
st.subheader("Snapshot Preview")
st.image("https://placehold.co/600x400?text=Drone+Snapshot", caption="Latest Drone View")

# --- Section 5: Gemini Summary ---
st.subheader("AI Summary")
st.info("Lot A is nearing full capacity. Lot B is recommended for the next 30 minutes.")