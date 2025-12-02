import threading
import time
from traceback import print_exc
from typing import Any

import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.ads1x15 import Pin
import board
import busio
from flask import Flask, jsonify, redirect, request
from flask_cors import CORS

from .valve import GPIOValve, Valve, ValveState
from .database_api import db
from .sensor_data import RandomizedSensor, SensorFailure
from .sensor_data import RandomizedSensor, Sensor
from .sensor_flow import FlowSensor
from .sensor_pressure import PressureSensor

valves: dict[str, Valve] = {
    'valve0': Valve(),
    'valve1': Valve(),
    'valve2': Valve(),
    'valve3': Valve(),
    'valve4': Valve(),
}

sensors: dict[str, Sensor] = {
    'flow0': RandomizedSensor(0, 5),
    'flow1': RandomizedSensor(0, 5),
    'flow2': RandomizedSensor(0, 5),
    'flow3': RandomizedSensor(0, 5),
    'flow4': RandomizedSensor(0, 5),
    'pressure0': RandomizedSensor(0, 5),
    'pressure1': RandomizedSensor(0, 5),
    'pressure2': RandomizedSensor(0, 5),
    'pressure3': RandomizedSensor(0, 5),
    'pressure4': RandomizedSensor(0, 5),
    'pressure5': RandomizedSensor(0, 5),
}


def sensor_init():
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        while not i2c.try_lock():
            pass
        devices = i2c.scan()
        i2c.unlock()

        if 0x48 in devices:
            ads = ADS.ADS1015(i2c, address=0x48)
            sensors['pressure0'] = PressureSensor(ads, Pin.A0)
            sensors['pressure1'] = PressureSensor(ads, Pin.A1)
            sensors['pressure2'] = PressureSensor(ads, Pin.A2)
            sensors['pressure3'] = PressureSensor(ads, Pin.A3)

        if 0x49 in devices:
            ads = ADS.ADS1015(i2c, address=0x49)
            sensors['pressure4'] = PressureSensor(ads, Pin.A0)
            sensors['pressure5'] = PressureSensor(ads, Pin.A1)
    except:
        print("unable to get adc's")
        print_exc()

    try:
        sensors['flow0'] = FlowSensor(17)
        sensors['flow1'] = FlowSensor(27)
        sensors['flow2'] = FlowSensor(22)
        sensors['flow3'] = FlowSensor(10)
        sensors['flow4'] = FlowSensor(9)
    except:
        print("unable to get flow-sensors")
        print_exc()


def valves_init():
    try:
        valves['valve0'] = GPIOValve(25)
        valves['valve1'] = GPIOValve(8)
        valves['valve2'] = GPIOValve(7)
        valves['valve3'] = GPIOValve(12)
        valves['valve4'] = GPIOValve(16)
    except:
        print("unable to get valves")
        print_exc()


app = Flask(__name__, static_url_path='', static_folder='./static')
CORS(app)


def push_sensor_data():
    row: dict[str, float] = {}
    row['id'] = -1
    row['timestamp'] = time.time()
    for name, sensor in sensors.items():
        value, fail = sensor.read_data()
        row[name+":value"] = value
        for elem in SensorFailure:
            row[name+":fail_" + elem.name.lower()] = 1 if fail == elem else 0

    db.insert(row)

    threading.Timer(0.25, push_sensor_data).start()


@app.route("/")
def index():
    return redirect("index.html")


@app.route('/api/sensor_data')
def get_real_sensor_data():
    limit = request.args.get('limit', default=100, type=int)
    sensors = []
    for row in db.get_rows(limit):
        s: dict[str, Any] = {"sensors": {}}
        for key, value in row.items():
            if ':' in key:
                sensor, attr = key.split(':', 2)
                if sensor not in s['sensors']:
                    s['sensors'][sensor] = {}
                s['sensors'][sensor][attr] = value
            else:
                s[key] = value
        sensors.append(s)

    return jsonify(sensors)


@app.route('/api/set_valve', methods=['POST'])
def set_valve_state():
    data: dict[str, int] | None = request.json
    if type(data) is not dict:
        return jsonify({"error": "invalid requirest"}, success=False)
    if 'valve' not in data or 'state' not in data:
        return jsonify({"error": "missing parameters"}, success=False)

    if data['valve'] not in valves:
        return jsonify({"error": "unknown valve"}, success=False)

    if data['state'] not in ['open', 'close']:
        return jsonify({"error": "unknown state"}, success=False)

    state = ValveState.OPEN if data['state'] == 'open' else ValveState.CLOSED
    valves[data['valve']].set_state(state)

    return jsonify(success=True)


@app.route('/api/get_valves', methods=['GET'])
def get_valve_states():
    valve_states = {name: v.state.name.lower() for name, v in valves.items()}
    return jsonify(valve_states)


def main():
    sensor_init()
    valves_init()

    threading.Timer(0.25, push_sensor_data).start()

    app.run(host='0.0.0.0', port=5000)
