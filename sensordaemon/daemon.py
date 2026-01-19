#!/usr/bin/env python3

import json
import os
import socket
import time
import ssl

from common import RandomizedSensor, Sensor,  ManualValve, TestValve, Valve
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

# NOTE: return to 0.2s
LOOP_DELAY = 1  # seconds

device_name = socket.gethostname()

client = mqtt.Client(
    CallbackAPIVersion.VERSION2,
    transport='websockets',
    client_id=device_name,
)

valves: dict[str, Valve] = {
    'bigvalve0': ManualValve(),
    'bigvalve1': ManualValve(),
    'valve0': TestValve(),
    'valve1': TestValve(),
    'valve2': TestValve(),
    'valve3': TestValve(),
    'valve4': TestValve(),
}

# valves belonging to the same group (identified by a unique integer) can't be closed simultaneously.
# this is done do prevent both manual valves being closed together and causing too much pressure on the system.
valve_groups: dict[str, int] = {
    'bigvalve0': 0,
    'bigvalve1': 0,
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


def push_sensor_data(client: mqtt.Client):
    prev_valve_time = time.time()
    prev_valve_state = [v.state for v in valves.values()]
    try:
        while True:
            start_time = time.time()
            delay = LOOP_DELAY

            row: dict = {}
            row["device"] = device_name
            data = {}

            for sensor_name, sensor in sensors.items():
                data[f'sensor.{sensor_name}'] = (sensor.read(), sensor.unit)

            for valve_name, valve in valves.items():
                data[f'valve.{valve_name}'] = (valve.state, None)

            new_valve_state = [v.state for v in valves.values()]
            curtime = time.time()
            if new_valve_state != prev_valve_state:
                prev_valve_state = new_valve_state
                prev_valve_time = curtime

            data["last_valve_change"] = (curtime - prev_valve_time, None)

            row['measurements'] = data

            row['valves'] = {
                valve_name: {
                    'group': valve_groups.get(valve_name, -1),
                    'wants': valve.wants,
                    'state': valve.state
                }
                for valve_name, valve in valves.items()
            }

            client.publish(
                f"vitens/pi/{device_name}/telemetry", json.dumps(row))

            d = delay - time.time() + start_time
            if d > 0:
                time.sleep(d)
    except KeyboardInterrupt:
        print("!! received, exiting...")


@client.connect_callback()
def on_connect(client: mqtt.Client, userdata: None, flags, reason_code, properties):
    print("publisher connected:", reason_code)
    client.subscribe("vitens/pi/+/set_valves")


@client.topic_callback(
    f"vitens/pi/{device_name}/set_valves")
def on_set_valves(client: mqtt.Client, _: None, msg: mqtt.MQTTMessage):
    payload = json.loads(msg.payload)
    for valve_name, opt in payload.items():
        if 'wants' in opt:
            valves[valve_name].set_wants(opt['wants'])
        if 'state' in opt:
            valves[valve_name].set_state(opt['state'])
        print(f"!! setting valve: {valve_name} -> {opt!r}")

    print("received:", payload)


def main():
    try:
        import rpi
        rpi.init_peripherals(sensors, valves)
    except Exception as e:
        print(f"unable to initialize RPi peripherals: {e}")

    print(f"starting MQTT-client as '{device_name}'")

    if os.getenv('MQTT_USER'):
        client.username_pw_set(os.getenv('MQTT_USER'),
                               os.getenv('MQTT_PASSWD'))
    if os.getenv('MQTT_WSPATH'):
        client.ws_set_options(path=os.getenv('MQTT_WSPATH', '/mqtt/'))
    if os.getenv('MQTT_TLS') == '1':
        client.tls_set(
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS)
    client.connect(os.getenv('MQTT_HOST', 'localhost'),
                   int(os.getenv('MQTT_PORT', '1883')))
    client.loop_start()

    push_sensor_data(client)

    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
