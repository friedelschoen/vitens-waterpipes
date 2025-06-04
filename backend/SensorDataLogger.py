import random
import time

class SensorDataLogger:
    def __init__(self):
        print("Initialized mock sensor logger.")

    def read_sensors(self):
        # Simulate sensor readings
        return {
            "timestamp": time.time(),
            "pressure": round(random.uniform(1.0, 2.5), 2),  # bar
            "flow": round(random.uniform(0.1, 1.0), 2),      # liters/sec
            "valve_open": random.choice([True, False])
        }
