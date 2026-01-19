#!/usr/bin/env python3
import json
import os
import sqlite3
import time
import ssl

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

from predictor import PREDICTORS


COLLECTOR_INTERVAL = 60  # seconds
COLLECTOR_DB_PATH = f"collect/"


db = sqlite3.connect(os.getenv('DB_PATH', 'vitens.db'))

client = mqtt.Client(
    CallbackAPIVersion.VERSION2,
    transport='websockets',
    client_id="inserter",
)

device_valves: dict[str, dict[str, int]] = {}


@client.connect_callback()
def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties):
    print("subscriber connected:", reason_code)
    client.subscribe("vitens/pi/+/telemetry")


@client.topic_callback("vitens/pi/+/telemetry")
def on_telemetry(client, userdata, msg):
    ts = time.time()
    payload = json.loads(msg.payload)
    device: str = payload['device']
    measurements: dict[str, tuple[float, str]] = payload['measurements']
    valves: dict[str, dict] = payload['valves']

    data = {sensor_name: pair[0] for sensor_name, pair in measurements.items()}
    units = {sensor_name: pair[1]
             for sensor_name, pair in measurements.items()}

    if device not in device_valves:
        device_valves[device] = {
            valve_name: opt['group'] for valve_name, opt in valves.items()
        }

    cur = db.cursor()
    cur.execute('INSERT INTO sample (timestamp, device) VALUES (?, ?);',
                (ts, device))
    db.commit()

    sample_id = cur.lastrowid

    for key, valve in valves.items():
        cur = db.cursor()
        cur.execute('INSERT INTO valve (sample, name, state, wants) VALUES (?, ?, ?, ?)',
                    (sample_id, key, valve['state'], valve['wants']))

    for algo_name, algo in PREDICTORS.items():
        new_data = algo.predict(data)
        for key, value in new_data.items():
            cur = db.cursor()
            cur.execute('INSERT INTO measurement (sample, algorithm, unit, name, value) VALUES (?, ?, ?, ?, ?)',
                        (sample_id, algo_name, units[key], key, value))

    db.commit()

    calctime = (time.time() - ts) * 1000
    print(
        f'added {len(data)} values at id={sample_id} from `{device}` in {calctime:.1f}ms')


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
