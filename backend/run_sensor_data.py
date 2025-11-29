# run_sensor_data.py
import platform
from database_api import create_tables

# Create necessary database tables
create_tables()

if platform.system() == "Windows":
    from fake_sensor_data import MockSensorLogger
    logger = MockSensorLogger()
else:
    from sensor_data import SensorLogger  # Only import on Raspberry
    logger = SensorLogger(flow_sensor_pins=[4, 17, 27, 22, 5])

# logger.run()
