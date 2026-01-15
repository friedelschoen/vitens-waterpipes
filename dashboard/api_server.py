#!/usr/bin/env python3

from collections import defaultdict
import json
import os
import sqlite3
import time

from flask import Flask, jsonify, redirect, request
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from mqtt_job import MqttJob

SENSOR_FRAME = 5 * 60  # 5 minutes

app = Flask(__name__, static_url_path='', static_folder='./static')
db = sqlite3.connect(os.getenv('DB_PATH', 'vitens.db'),
                     check_same_thread=False)

client = mqtt.Client(
    CallbackAPIVersion.VERSION2,
    transport='websockets',
    client_id="api_server",
)

# register replay and collector
collector_job = MqttJob(app, client, "collector", ("device",))
replay_job = MqttJob(app, client, "replay", ("device", "timestamp"))


@app.route("/")
def index():
    return redirect("index.html")


@app.route('/api/sensors', methods=['GET'])
def get_real_sensor_data():
    since = request.args.get('since', default=0, type=float)
    since = max(since, time.time()-SENSOR_FRAME)

    cur = db.cursor()
    cur.execute('''
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
    cur = db.cursor()
    cur.execute('''
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
    if data['state'] not in [0, 1]:
        return jsonify({"error": "unknown state"})

    device = data['device']
    valve = data['valve']
    state = data['state']

    client.publish(f'vitens/pi/{device}/set_valves',
                   json.dumps({valve: {'state': state}}))

    return jsonify(error=None)


@client.connect_callback()
def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties):
    print("subscriber connected:", reason_code)
    client.subscribe(collector_job.topic_status)
    client.subscribe(replay_job.topic_status)


if __name__ == "__main__":
    if os.getenv('MQTT_USER'):
        client.username_pw_set(os.getenv('MQTT_USER'),
                               os.getenv('MQTT_PASSWD'))
    if os.getenv('MQTT_WSPATH'):
        client.ws_set_options(path=os.getenv('MQTT_WSPATH', '/mqtt/'))
    client.connect(os.getenv('MQTT_HOST', 'localhost'),
                   int(os.getenv('MQTT_PORT', '1883')))
    client.loop_start()

    app.run(host='0.0.0.0', port=5000)

    client.loop_stop()
    client.disconnect()
