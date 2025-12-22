
#!/usr/bin/env python3
import io
from itertools import product
import json
import os.path
import sqlite3
import time

import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion


class Collector:
    interval: int
    todo: list[dict[str, int]]
    next_run: float
    db: io.TextIOBase
    path: str
    done: int
    pause_since: float | None
    header: list[str] | None

    current: dict[str, int] = {}
    dirty = True

    def __init__(self, interval: int, outdir: str, device_name: str, valve_groups: dict[str, int]):
        self.interval = interval

        valves = list(valve_groups.keys())
        self.todo = [
            dict(zip(valves, states))
            for states in product([0, 1], repeat=len(valves))
            if self._check_group_closed(valves, valve_groups, states)
        ]
        self.next_run = time.time()
        timestr = time.strftime('%Y-%m-%d_%H:%M:%S')
        self.path = os.path.join(
            outdir, f'collect-{device_name}-{timestr}.csv')
        if '/' in self.path:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.db = open(self.path, 'w')
        self.done = 0
        self.pause_since = None
        self.header = None

    @property
    def progress(self) -> float:
        curtime = time.time()

        # Als we gepauzeerd zijn: freeze progress
        if self.pause_since is not None:
            curtime = self.pause_since

        # hoe lang nog in huidige interval?
        if self.next_run > 0:
            remain_current = max(0.0, self.next_run - curtime)
            elapsed_current = self.interval - remain_current
        else:
            remain_current = 0.0
            elapsed_current = 0.0

        doing = remain_current + len(self.todo) * self.interval
        timedone = self.done * self.interval + \
            max(0.0, min(self.interval, elapsed_current))

        total = doing + timedone
        if total <= 0:
            return 0.0

        return timedone / total

    @property
    def timeleft(self) -> float:
        curtime = time.time()
        if self.pause_since is not None:
            curtime = self.pause_since

        return (self.next_run - curtime) + len(self.todo) * self.interval

    def pause(self, flag: bool):
        if flag and self.pause_since is None:
            self.pause_since = time.time()
            print("[collect] paused")

        elif not flag and self.pause_since is not None:
            # Einde pauze → verschuif next_run
            paused_for = time.time() - self.pause_since
            self.next_run += paused_for

            self.pause_since = None
            print(f"[collect] resumed after {paused_for:.2f}s pause")

    def _check_group_closed(self, valves: list[str], valve_groups: dict[str, int], states: tuple[int, ...]):
        groups = {}
        for i, valve in enumerate(valves):
            state = states[i]
            group = valve_groups[valve]
            if group not in groups:
                groups[group] = 0
            if state != 0:
                groups[group] += 1
        return not any(n == 0 for n in groups.values())

    # next returns the next state to set, None if done
    def next(self) -> bool:
        if len(self.todo) == 0 and self.next_run == 0:
            return False

        if self.pause_since is not None:
            return True

        curtime = time.time()
        if self.next_run > 0 and curtime > self.next_run:
            if len(self.todo) == 0:
                self.next_run = 0
                return False

            self.done += 1
            self.next_run = curtime + self.interval
            self.current = self.todo.pop(0)
            self.dirty = True
            print(
                f"[collect] doing {self.current}, still to do {len(self.todo)}")
            return True

        return True

    def insert(self, sample: dict[str, float]):
        if self.header == None:
            self.header = list(sample.keys())
            row = list(sample.values())

            # write header
            self.db.write(','.join(self.header) + '\n')
        else:
            row = [
                0 if key not in sample else sample[key]
                for key in self.header
            ]

        self.db.write(','.join(map(str, row)) + '\n')


COLLECTOR_INTERVAL = 3  # seconds
COLLECTOR_DB_PATH = f"/data/collect/"

db = sqlite3.connect(os.getenv('SQLITE3_PATH', 'vitens.db'))

client = mqtt.Client(
    CallbackAPIVersion.VERSION2,
    client_id="collector",
)

collectors: dict[str, Collector] = {}
device_valves: dict[str, dict[str, int]] = {}


@client.connect_callback()
def on_connect(client: mqtt.Client, userdata, flags, reason_code, properties):
    print("subscriber connected:", reason_code)
    client.subscribe("vitens/#")


@client.topic_callback("vitens/pi/+/telemetry")
def on_telemetry(client, userdata, msg):
    ts = time.time()
    payload = json.loads(msg.payload)
    device: str = payload['device']
    measurements: dict[str, tuple[float, str]] = payload['measurements']
    valves: dict[str, dict] = payload['valves']

    data = {
        sensor_name: pair[0] for sensor_name, pair in measurements.items()
    }

    if device not in device_valves:
        device_valves[device] = {
            valve_name: opt['group'] for valve_name, opt in valves.items()
        }

    if device in collectors:
        collector = collectors[device]
        collector.dirty = any(
            name in collector.current and v['state'] != collector.current[name]
            for name, v in valves.items()
        )
        collector.pause(collector.dirty)

        do_continue = collector.next()
        if not do_continue:
            collector.db.close()
            del collectors[device]

    if device in collectors:
        collector = collectors[device]
        if collector.dirty:
            collector.pause(True)
            client.publish(f'vitens/pi/{device}/set_valves', json.dumps({
                valve_name: {'wants': state}
                for valve_name, state in collector.current.items()
            }))

        row: dict[str, float] = {}
        row['timestamp'] = ts
        for key, valve in data.items():
            row['measure.' + key] = valve

        collector.insert(row)
        col_status = {'device': device, 'active': True, 'dbname': collector.path,
                      'progress': collector.progress, 'timeleft': collector.timeleft}
    else:
        col_status = {'device': device, 'active': False}

    client.publish(f'vitens/collector/status', json.dumps(col_status))


@client.topic_callback("vitens/collector/activate")
def on_collect_activate(client, userdata, msg):
    payload = json.loads(msg.payload)
    device = payload['device']
    if device in collectors:
        return  # already active
    if device not in device_valves:
        return  # unknown device

    collectors[device] = Collector(
        COLLECTOR_INTERVAL, COLLECTOR_DB_PATH, device, device_valves[device])


@client.topic_callback("vitens/collector/deactivate")
def on_collect_deactivate(client, userdata, msg):
    payload = json.loads(msg.payload)
    device = payload['device']
    if device not in collectors:
        return  # already active

    collectors[device].db.close()
    del collectors[device]


client.connect(os.getenv('MQTT_HOST', 'localhost'),
               int(os.getenv('MQTT_PORT', '1883')))
client.loop_forever()
