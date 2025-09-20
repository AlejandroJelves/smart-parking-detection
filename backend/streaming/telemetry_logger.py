import json
import paho.mqtt.client as mqtt

# Connection settings
MQTT_HOST = "mqtt.hextronics.net"
MQTT_PORT = 1883
MQTT_USER = "hexair-hack"
MQTT_PASS = "305hack"
TOPIC = "hexair/hexair-hack/telemetry"

# Callback when connected
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker")
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to {TOPIC}")
    else:
        print(f"❌ Connection failed with code {rc}")

# Callback when a message arrives
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        # Print telemetry summary
        print("\n--- TELEMETRY UPDATE ---")
        print(f"Streaming: {data.get('isStreaming')}")
        print(f"Flying: {data.get('isFlying')}")
        if data.get("currentPosition"):
            pos = data["currentPosition"]
            print(f"Position: {pos['latitude']}, {pos['longitude']} @ {pos['altitude']}m")
        if data.get("devices") and data["devices"]["aircraft"]:
            bat = data["devices"]["aircraft"]["batteries"][0]
            print(f"Battery: {round(bat['level']*100,1)}%")
        print("------------------------")
    except Exception as e:
        print("⚠️ Error decoding message:", e)

def main():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()
