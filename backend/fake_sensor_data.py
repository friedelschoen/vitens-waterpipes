import time
import random
import database_api


class MockSensorLogger:
    def __init__(self, interval=1):
        self.interval = interval  # seconds between readings
        self.start_time = time.time()

    def read_mock_data(self):
        # Generate random flow rates and pressures
        flows = [round(random.uniform(0, 10), 2) for _ in range(5)]
        pressures = [round(random.uniform(0.0, 5.0), 3) for _ in range(6)]
        return flows, pressures

    def run(self):
        print("Running Mock Sensor Logger — type Ctrl+C to stop.")
        try:
            while True:
                flow_rates, pressures = self.read_mock_data()
                timestamp = round(time.time() - self.start_time, 2)

                sensor_values = {}

                for i, flow in enumerate(flow_rates, 1):
                    sensor_values[f"flow_{i}"] = flow

                # Add pressures
                for i, pressure in enumerate(pressures, 1):
                    sensor_values[f"pressure_{i}"] = pressure

                # Insert all at once
                database_api.insert_real_sensor_row(sensor_values)

                print(f"[{timestamp:.2f}s] Flows: {flow_rates} | Pressures: {pressures}")
                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("Mock logger stopped.")
