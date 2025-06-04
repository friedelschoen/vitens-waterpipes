# sensor_logger_runner.py

import time
from SensorDataLogger import SensorDataLogger

logger = SensorDataLogger()

# Demo loop — prints mock data every 2 seconds
if __name__ == "__main__":
    try:
        while True:
            data = logger.read_sensors()
            print(data)
            time.sleep(2)
    except KeyboardInterrupt:
        print("Stopped mock sensor logger.")

