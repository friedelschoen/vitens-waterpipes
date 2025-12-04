import os
from typing import Any


def unflatten_dict(d: dict[str, float]) -> dict[str, Any]:
    s = {}
    for key, val in d.items():
        cur = s
        *attrs, last = key.split('.')
        for attr in attrs:
            cur = cur.setdefault(attr, {})
        cur[last] = val
    return s


def flatten_dict(d: dict[str, Any], prefix: str = "") -> dict[str, float]:
    flat = {}
    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_dict(value, full_key))
        else:
            flat[full_key] = value
    return flat


class CSVDatabase:
    def __init__(self, filename: str, read=True):
        self.filename = filename
        self.columns: list[str] = []
        self.readings: list[list[float]] = []

        if read and os.path.exists(self.filename):
            self.read_csv()

    def read_csv(self):
        with open(self.filename) as csv:
            for line in csv:
                line = line.strip()
                if len(self.columns) == 0:
                    self.columns = line.split(',')
                    continue

                self.readings.append([float(v) for v in line.split(',')])

    def insert(self, sensor_values: dict[str, float]):
        with open(self.filename, "a") as output:
            if 'id' in sensor_values and sensor_values['id'] == -1:
                sensor_values['id'] = len(self.readings)

            if len(self.columns) == 0:
                self.columns = list(sensor_values.keys())
                output.write(",".join(self.columns) + "\n")

            values = [sensor_values.get(key, 0) for key in self.columns]
            self.readings.append(values)
            output.write(",".join(str(v) for v in values) + "\n")

            notwrite = [c for c in sensor_values.keys()
                        if c not in self.columns]
            if len(notwrite):
                print("[warn] not writing values: " + ", ".join(notwrite))

    def get_rows(self, limit=0) -> list[dict[str, float]]:
        return [dict(zip(self.columns, row)) for row in self.readings[-limit:]]
