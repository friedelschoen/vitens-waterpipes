#!/usr/bin/env python3

from collections import defaultdict
import json
import os
import sqlite3
import time

from flask import Flask, jsonify, redirect, request
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

SENSOR_FRAME = 5 * 60  # 5 minutes

app = Flask(__name__, static_url_path='', static_folder='./static')
db = sqlite3.connect(os.getenv('SQLITE3_PATH', 'vitens.db'),
                     check_same_thread=False)

client = mqtt.Client(
    CallbackAPIVersion.VERSION2,
    client_id="api_server",
)

replay_status: dict[str, dict] = {}
collector_status: dict[str, dict] = {}


@app.route("/")
def index():
    return redirect("index.html")


@app.route('/api/sensors', methods=['GET'])
def get_real_sensor_data():
    since = request.args.get('since', default=0, type=float)
    since = max(since, time.time()-SENSOR_FRAME)

    cur = db.execute('''
SELECT timestamp, device, algorithm, unit, name, value FROM sample
JOIN measurement
ON sample.id = measurement.sample
WHERE sample.timestamp >= ?
ORDER BY device, name, algorithm, timestamp
''', (since, ))

    result = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for timestamp, device, algorithm, unit, sensor_name, value in cur:
        result[device][sensor_name][algorithm].append({
            "timestamp": timestamp,
            "value": value,
            "unit": unit,
        })

    return jsonify(result)


@app.route('/api/valves', methods=['GET'])
def get_valve_states():
    cur = db.execute('''
SELECT s.device, s.timestamp, v.name, v.state, v.wants
FROM sample s
JOIN valve v ON v.sample = s.id
WHERE s.id = (
  SELECT MAX(id) FROM sample s2 WHERE s2.device = s.device
);
    ''')
    result = defaultdict(dict)
    for device, timestamp, valve_name, state, wants in cur:
        result[device][valve_name] = {
            "timestamp": timestamp,
            "state": state,
            "wants": wants
        }

    return jsonify(result)


@app.route('/api/valves', methods=['POST'])
def set_valve_state():
    data: dict[str, int] | None = request.json
    if type(data) is not dict:
        return jsonify({"error": "invalid requirest"})
    if 'valve' not in data or 'state' not in data or 'device' not in data:
        return jsonify({"error": "missing parameters"})
    if data['state'] not in ['open', 'close']:
        return jsonify({"error": "unknown state"})

    device = data['device']
    valve = data['valve']
    state = 1 if data['state'] == 'open' else 0

    client.publish(f'vitens/pi/{device}/set_valves',
                   json.dumps({valve: {'state': state}}))

    return jsonify(error=None)


@app.route("/api/collector", methods=['GET'])
def get_collector():
    return jsonify(collector_status)


@app.route("/api/collector", methods=['POST'])
def start_collector():
    data: dict[str, int] | None = request.json
    if type(data) is not dict:
        return jsonify({"error": "invalid requirest"})
    if 'device' not in data:
        return jsonify({"error": "missing parameters"})

    client.publish('vitens/collector/activate', json.dumps(data))
    return jsonify(error=None)


@app.route("/api/collector/stop", methods=['POST'])
def stop_collector():
    data: dict[str, int] | None = request.json
    if type(data) is not dict:
        return jsonify({"error": "invalid requirest"})
    if 'device' not in data:
        return jsonify({"error": "missing parameters"})

    client.publish('vitens/collector/deactivate', json.dumps(data))
    return jsonify(error=None)


@app.route("/api/replay", methods=['GET'])
def get_replay():
    return jsonify(replay_status)


@app.route("/api/replay", methods=['POST'])
def start_replay():
    data: dict[str, int] | None = request.json
    if type(data) is not dict:
        return jsonify({"error": "invalid requirest"})
    if 'device' not in data or 'timestamp' not in data:
        return jsonify({"error": "missing parameters"})

    client.publish('vitens/replay/activate', json.dumps(data))
    return jsonify(error=None)


@app.route("/api/replay/stop", methods=['POST'])
def stop_replay():
    data: dict[str, int] | None = request.json
    if type(data) is not dict:
        return jsonify({"error": "invalid requirest"})
    if 'device' not in data:
        return jsonify({"error": "missing parameters"})

    client.publish('vitens/replay/deactivate', json.dumps(data))
    return jsonify(error=None)


@client.topic_callback("vitens/collector/status")
def on_collector_status(client, userdata, msg):
    payload = json.loads(msg.payload)
    device = payload['device']
    active = payload['active']
    if active:
        collector_status[device] = payload
    else:
        collector_status.pop(device, None)


@client.topic_callback("vitens/replay/status")
def on_replay_status(client, userdata, msg):
    payload = json.loads(msg.payload)
    device = payload['device']
    active = payload['active']
    if active:
        replay_status[device] = payload
    else:
        replay_status.pop(device, None)


@client.connect_callback()
def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties):
    print("subscriber connected:", reason_code)
    client.subscribe("vitens/#")


if __name__ == "__main__":
    client.connect(os.getenv('MQTT_HOST', 'localhost'),
                   int(os.getenv('MQTT_PORT', '1883')))
    client.loop_start()

    app.run(host='0.0.0.0', port=5000)

    client.loop_stop()
    client.disconnect()
