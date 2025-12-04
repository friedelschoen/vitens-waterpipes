from gc import collect
from itertools import product
import threading
import time
from traceback import print_exc
from typing import Any

import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.ads1x15 import Pin
import board
import busio
from flask import Flask, jsonify, redirect, request

from .collector import Collector
from .csv_database import CSVDatabase
from .sensor import FlowSensor, PressureSensor, RandomizedSensor, Sensor
from .valve import GPIOValve, Valve, ValveState

COLLECTOR_INTERVAL = 2  # seconds
DB_PATH = "readings.csv"
COLLECTOR_DB_PATH = f"collect-%.csv"

valves: dict[str, Valve] = {
    'valve0': Valve(),
    'valve1': Valve(),
    'valve2': Valve(),
    'valve3': Valve(),
    'valve4': Valve(),
}

sensors: dict[str, Sensor] = {
    'flow0': RandomizedSensor("L/min", 0, 5),
    'flow1': RandomizedSensor("L/min", 0, 5),
    'flow2': RandomizedSensor("L/min", 0, 5),
    'flow3': RandomizedSensor("L/min", 0, 5),
    'flow4': RandomizedSensor("L/min", 0, 5),
    'pressure0': RandomizedSensor("bar", 0, 5),
    'pressure1': RandomizedSensor("bar", 0, 5),
    'pressure2': RandomizedSensor("bar", 0, 5),
    'pressure3': RandomizedSensor("bar", 0, 5),
    'pressure4': RandomizedSensor("bar", 0, 5),
    'pressure5': RandomizedSensor("bar", 0, 5),
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
db = CSVDatabase(DB_PATH)
collector = Collector(COLLECTOR_INTERVAL, COLLECTOR_DB_PATH)


def push_sensor_data():
    prev_valve_time = time.time()
    prev_valve_state = [v.state for v in valves.values()]
    while True:
        row: dict[str, float] = {}
        row['id'] = -1
        row['timestamp'] = time.time()
        for name, sensor in sensors.items():
            value = sensor.read()
            row[f"sensors.{name}.value"] = value

        for name, valve in valves.items():
            row[f"valves.{name}.value"] = valve.state.value

        new_valve_state = [v.state for v in valves.values()]
        curtime = time.time()
        if new_valve_state != prev_valve_state:
            prev_valve_state = new_valve_state
            prev_valve_time = curtime

        row["valves.change_time"] = curtime - prev_valve_time

        if collector.active:
            todo = collector.pop()
            for name, state in todo.items():
                valves[name].set_state(state)

            if collector.db is not None:
                collector.db.insert(row)

        db.insert(row)

        time.sleep(0.25)


@app.route("/")
def index():
    return redirect("index.html")


@app.route('/api/sensors')
def get_sensors():
    result = [dict(name=name, unit=sensor.unit)
              for name, sensor in sensors.items()]
    return jsonify(result)


@app.route('/api/sensor_data')
def get_real_sensor_data():
    limit = request.args.get('limit', default=100, type=int)
    sensors = []
    for row in db.get_rows(limit):
        s = {}
        for key, val in row.items():
            cur = s
            *attrs, last = key.split('.')
            for attr in attrs:
                cur = cur.setdefault(attr, {})
            cur[last] = val
        sensors.append(s)
    return jsonify(sensors)


@app.route('/api/set_valves', methods=['POST'])
def set_valve_state():
    if collector.active:
        return jsonify({"error": "collector active"})
    data: dict[str, int] | None = request.json
    if type(data) is not dict:
        return jsonify({"error": "invalid requirest"})
    if 'valve' not in data or 'state' not in data:
        return jsonify({"error": "missing parameters"})

    if data['valve'] not in valves:
        return jsonify({"error": "unknown valve"})

    if data['state'] not in ['open', 'close']:
        return jsonify({"error": "unknown state"})

    state = ValveState.OPEN if data['state'] == 'open' else ValveState.CLOSED
    valves[data['valve']].set_state(state)

    return jsonify(error=None)


@app.route('/api/get_valves', methods=['GET'])
def get_valve_states():
    valve_states = {name: v.state.name.lower() for name, v in valves.items()}
    return jsonify(valve_states)


@app.route('/api/start_collector', methods=['POST'])
def start_collector():
    if collector.active:
        return jsonify({"error": "collector active"})
    collector.start(list(valves.keys()))
    dbname = "???"
    if collector.db is not None:
        dbname = collector.db.filename
    return jsonify(active=True, dbname=dbname)


@app.route('/api/cancel_collector', methods=['POST'])
def cancel_collector():
    if not collector.active:
        return jsonify({"error": "collector inactive"})
    collector.cancel()
    return jsonify()


@app.route('/api/get_collector', methods=['GET'])
def get_collector_state():
    dbname = "???"
    if collector.db is not None:
        dbname = collector.db.filename
    return jsonify(active=collector.active, dbname=dbname, progress=collector.progress, time=collector.timeleft)


def main():
    sensor_init()
    valves_init()

    threading.Thread(target=push_sensor_data).start()

    app.run(host='0.0.0.0', port=5000)
