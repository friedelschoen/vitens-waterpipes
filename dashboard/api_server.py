#!/usr/bin/env python3

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
from .csv_database import CSVDatabase, Cursor
from .predictor import (
    KerasPredictor,
    PassthroughPredictor,
    Predictor,
    RandomForestPredictor,
)
from .sensor import FlowSensor, PressureSensor, RandomizedSensor, Sensor
from .valve import GPIOValve, ManualValve, Valve, ValveState

MAX_REPLAY_DELAY = 3  # seconds
COLLECTOR_INTERVAL = 2  # seconds
COLLECTOR_DB_PATH = f"collect-%.csv"
PREDICTOR_DB_PATH = f"predict-%.csv"
REPLAY_PATH = "replay/replay.csv"

valves: dict[str, Valve] = {
    'bigvalve0': ManualValve(),
    'bigvalve1': ManualValve(),
    'valve0': ManualValve(),
    'valve1': ManualValve(),
    'valve2': ManualValve(),
    'valve3': ManualValve(),
    'valve4': ManualValve(),
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

predictors: dict[str, Predictor] = {
    "none": PassthroughPredictor(),
    "dense": KerasPredictor("dashboard/model/dense", ["timestamp"]),
    "rf": RandomForestPredictor("dashboard/model/rf", ["timestamp"]),
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
predict_db = {
    name: CSVDatabase(PREDICTOR_DB_PATH.replace("%", name)) for name in predictors.keys()
}
collector = Collector(COLLECTOR_INTERVAL, COLLECTOR_DB_PATH)

replay_cursor: Cursor | None = None
replay_timestamp = 0.0


def push_sensor_data():
    global replay_cursor, replay_timestamp

    prev_valve_time = time.time()
    prev_valve_state = [v.state for v in valves.values()]
    while True:
        row: dict[str, Any] | None = None
        if replay_cursor is not None:
            row = replay_cursor.read()
            if row is None:
                replay_cursor.close()
                replay_cursor = None
            else:
                delay = row["timestamp"] - replay_timestamp
                time.sleep(min(delay, MAX_REPLAY_DELAY))
                replay_timestamp = row["timestamp"]
                for name, state in row["valves"].items():
                    if name == "change_time":
                        continue
                    valves[name].set_state(ValveState(state["value"]))

        if row is None:
            time.sleep(0.25)
            row = {}
            row["sensors"] = {
                name: dict(value=sensor.read()) for name, sensor in sensors.items()
            }
            row["valves"] = {
                name: dict(value=valve.state.value) for name, valve in valves.items()
            }

            new_valve_state = [v.state for v in valves.values()]
            curtime = time.time()
            if new_valve_state != prev_valve_state:
                prev_valve_state = new_valve_state
                prev_valve_time = curtime

            row["valves.change_time"] = curtime - prev_valve_time

        for name, model in predictors.items():
            prow = model.predict(row)
            predict_db[name].insert(prow)

        if collector.active:
            todo = collector.pop()
            for name, state in todo.items():
                valves[name].set_state(state)

            if collector.db is not None:
                collector.db.insert(row)


@app.route("/")
def index():
    return redirect("index.html")


@app.route('/api/sensors')
def get_sensors():
    result = [dict(name=name, unit=sensor.unit)
              for name, sensor in sensors.items()]
    return jsonify(sensors=result, predictors=list(predictors.keys()))


@app.route('/api/sensor_data')
def get_real_sensor_data():
    since = request.args.get('since', default=0, type=float)
    preds = {}
    for name, preddb in predict_db.items():
        with preddb.cursor_since(since) as cur:
            preds[name] = list(cur)
    replay_data = None
    if replay_cursor is not None:
        replay_data = dict(timestamp=replay_timestamp,
                           progress=replay_cursor.offset/(replay_cursor.offset+replay_cursor.size))
    return jsonify(values=preds, replay=replay_data)


@app.route('/api/set_valves', methods=['POST'])
def set_valve_state():
    if collector.active:
        return jsonify({"error": "collector active"})
    if replay_cursor is not None:
        return jsonify({"error": "replay active"})
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


@app.route('/api/replay', methods=['POST'])
def do_replay():
    global replay_cursor
    if replay_cursor is not None:
        return jsonify({"error": "replay active"})
    since = request.args.get('since', default=0, type=float)
    replay_cursor = predict_db["none"].cursor_since(since)
    return jsonify()


@app.route('/api/cancel_replay', methods=['POST'])
def cancel_replay():
    global replay_cursor
    if replay_cursor is None:
        return jsonify({"error": "replay inactive"})
    replay_cursor = None
    return jsonify()


def main():
    sensor_init()
    valves_init()

    threading.Thread(target=push_sensor_data).start()

    app.run(host='0.0.0.0', port=5000)
