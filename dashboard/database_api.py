import os

DB_PATH = "sensor_data.db"


class Database:
    def __init__(self, filename: str):
        self.filename = filename
        self.columns: list[str] = []
        self.readings: list[list[float]] = []

        if os.path.exists(self.filename):
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

    def get_rows(self, limit=0) -> list[dict[str, float]]:
        return [dict(zip(self.columns, row)) for row in self.readings[-limit:]]


db = Database("readings.csv")
