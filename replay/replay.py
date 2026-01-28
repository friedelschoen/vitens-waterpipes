import json
import os
import sqlite3
import threading
import time
import ssl
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

DEFAULT_ALGORITHM = "none"
MAX_INTERVAL = 2

db = sqlite3.connect(os.getenv('DB_PATH', 'vitens.db'),
                     check_same_thread=False)

client = mqtt.Client(
    CallbackAPIVersion.VERSION2,
    transport='websockets',
    client_id="replayer",
)


@client.connect_callback()
def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties):
    print("subscriber connected:", reason_code)
    client.subscribe("vitens/replay/#")


def do_replay(device: str, timestamp: int, break_ev: threading.Event):
    cur = db.cursor()
    cur.execute(
        'SELECT id, timestamp FROM sample WHERE device = ? AND timestamp >= ? ORDER BY timestamp', (device, timestamp))

    samples: list[tuple[int, float]] = cur.fetchall()

    last_ts = 0
    for i, (cur_id, cur_ts) in enumerate(samples):
        if break_ev.is_set():
            break

        cur = db.cursor()
        cur.execute(
            'SELECT name, value, unit FROM measurement WHERE sample = ? AND algorithm = ?', (cur_id, DEFAULT_ALGORITHM))
        measures = cur.fetchall()

        cur = db.cursor()
        cur.execute(
            'SELECT name, state, wants FROM valve WHERE sample = ?', (cur_id,))
        valves = cur.fetchall()

        row = {}
        row['device'] = 'replay!' + device
        row['valves'] = {
            valve_name: {'group': -1, 'state': state, 'wants': wants}
            for valve_name, state, wants in valves
        }

        data = {sensor_name: (value, unit)
                for sensor_name, value, unit in measures}
        row['measurements'] = data

        client.publish(
            f"vitens/pi/replay!{device}/telemetry", json.dumps(row))

        status = {
            "device": device,
            "active": True,
            "timestamp": cur_ts,
            "progress": i / len(samples),
        }
        client.publish(
            f"vitens/replay/status", json.dumps(status))

        delta_t = cur_ts - last_ts
        if last_ts > 0 and delta_t > 0:
            time.sleep(min(delta_t, MAX_INTERVAL))
        print(f"sleeping {delta_t}")
        last_ts = cur_ts

    status = {
        "device": device,
        "active": False,
    }
    client.publish(
        f"vitens/replay/status", json.dumps(status))


breakers: dict[str, threading.Event] = {}


@client.topic_callback("vitens/replay/activate")
def on_activate(client, userdata, msg):
    payload = json.loads(msg.payload)
    device = payload['device']
    timestamp = payload['timestamp']
    event = threading.Event()
    breakers[device] = event
    threading.Thread(target=do_replay, args=(device, timestamp, event)).start()


@client.topic_callback("vitens/replay/deactivate")
def on_deactivate(client, userdata, msg):
    payload = json.loads(msg.payload)

    device = payload['device']
    if device not in breakers:
        return

    breakers[device].set()


if os.getenv('MQTT_USER'):
    client.username_pw_set(os.getenv('MQTT_USER'), os.getenv('MQTT_PASSWD'))
if os.getenv('MQTT_WSPATH'):
    client.ws_set_options(path=os.getenv('MQTT_WSPATH', '/mqtt/'))
if os.getenv('MQTT_TLS') == '1':
    client.tls_set(
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLS)
client.connect(os.getenv('MQTT_HOST', 'localhost'),
               int(os.getenv('MQTT_PORT', '1883')))
client.loop_forever()
