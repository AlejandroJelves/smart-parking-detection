import os
from dotenv import load_dotenv
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json
import paho.mqtt.client as mqtt
import threading

# Load env variables
load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# --- MQTT CONFIG (drone telemetry) ---
MQTT_HOST = "mqtt.hextronics.net"
MQTT_PORT = 1883
MQTT_USER = "hexair-hack"
MQTT_PASS = "305hack"
TOPIC = "hexair/hexair-hack/telemetry"

telemetry_data = {"isStreaming": False, "isFlying": False, "battery": None, "position": None}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(TOPIC)
    else:
        print("MQTT connect fail", rc)

def on_message(client, userdata, msg):
    global telemetry_data
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        telemetry_data["isStreaming"] = data.get("isStreaming", False)
        telemetry_data["isFlying"] = data.get("isFlying", False)
        if data.get("currentPosition"):
            telemetry_data["position"] = (
                data["currentPosition"]["latitude"],
                data["currentPosition"]["longitude"],
                data["currentPosition"]["altitude"]
            )
        if data.get("devices") and data["devices"]["aircraft"]:
            bat = data["devices"]["aircraft"]["batteries"][0]
            telemetry_data["battery"] = round(bat["level"] * 100, 1)
    except:
        pass

def start_mqtt():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()

threading.Thread(target=start_mqtt, daemon=True).start()

# --- STREAMLIT UI ---
st.set_page_config(page_title="Smart Parking Dashboard", layout="wide")
st.sidebar.title("Smart Parking Detection")
mode = st.sidebar.radio("Mode", ["Live", "Demo"])

st.title("🚗 Smart Parking in the General Area")

# Section 1: KPI – Estimated occupancy
st.subheader("Estimated Parking Occupancy (Entire Area)")
try:
    response = requests.get(f"{API_URL}/spots").json()
    taken_spots = response.get("taken_spots", None)
    estimated_total = response.get("estimated_total", None)
    confidence = response.get("confidence", 0.7)

    if taken_spots is not None and estimated_total is not None:
        st.metric("Current Occupancy", f"{taken_spots} / {estimated_total}")
        st.caption(f"Confidence: {int(confidence*100)}% (AI-estimated)")
        st.progress(taken_spots / estimated_total if estimated_total else 0)
    else:
        st.warning("No live estimate available.")
except Exception as e:
    st.warning(f"Could not load live data: {e}")
    taken_spots, estimated_total = 130, 200
    st.metric("Current Occupancy", f"{taken_spots} / {estimated_total}")
    st.caption("Confidence: 70% (Demo Mode)")
    st.progress(taken_spots / estimated_total)

# Section 2: Forecast – Parking occupancy trends
st.subheader("Forecast: Parking Occupancy Over Time")
try:
    forecast_response = requests.get(f"{API_URL}/predict").json()
    df_forecast = pd.DataFrame(forecast_response["forecast"])
    df_forecast["occupancy_rate"] = df_forecast["taken_spots"] / df_forecast["estimated_total"]

    fig = px.line(df_forecast, x="time", y="occupancy_rate",
                  labels={"occupancy_rate": "Occupancy Rate"},
                  title="Predicted Parking Occupancy (%)")
    st.plotly_chart(fig, use_container_width=True)
except:
    sample = pd.DataFrame({
        "time": pd.date_range("2025-09-20", periods=12, freq="H"),
        "taken_spots": [120, 130, 140, 150, 160, 170, 180, 170, 160, 150, 140, 130],
        "estimated_total": [200]*12
    })
    sample["occupancy_rate"] = sample["taken_spots"] / sample["estimated_total"]
    fig = px.line(sample, x="time", y="occupancy_rate",
                  labels={"occupancy_rate": "Occupancy Rate"},
                  title="Predicted Parking Occupancy (Demo)")
    st.plotly_chart(fig, use_container_width=True)

# Section 3: AI Summary
st.subheader("AI Summary")
st.info("Currently estimated at 130 / 200 taken (~65% full). Based on trends, occupancy could rise to ~85% tomorrow afternoon.")

# Section 4: Drone Operations
st.subheader("🚁 Drone Operations")

col3, col4 = st.columns(2)

with col3:
    
    st.write("**Telemetry Data:**")
    if telemetry_data["isFlying"]:
        st.success("Drone is in the air ✈️ — live feed active")
    else:
        st.warning("Drone is on the ground 🛬 — feed may be idle")
    st.metric("Streaming", "✅" if telemetry_data["isStreaming"] else "❌")
    st.metric("Flying", "✅" if telemetry_data["isFlying"] else "❌")
    st.metric("Battery", f"{telemetry_data['battery']}%" if telemetry_data["battery"] else "Unknown")
    if telemetry_data["position"]:
        lat, lon, alt = telemetry_data["position"]
        st.write(f"🌍 Position: {lat}, {lon}, Alt {alt}m")
    st.subheader("Snapshot Preview")
    st.image("https://placehold.co/600x400?text=Drone+Snapshot", caption="Latest Drone View")


with col4:
    st.write("**Live Drone Video Feed:**")
    st.markdown(
        """
        <iframe 
          src="https://customer-de5fgahocfauk9ea.cloudflarestream.com/fc5cd217af19c699ba75808f9f150250/iframe"
          width="640" height="360" 
          frameborder="0" 
          allow="autoplay; fullscreen" 
          allowfullscreen>
        </iframe>
        """,
        unsafe_allow_html=True,
    

    )

