# sensor_logger_runner.py

from SensorDataLogger import FlowSensorLogger
import database_api
import time

# Ensure tables exist
database_api.create_tables()

# Use GPIO pins that match Pi's setup
flow_pins = [17, 27, 22]  # Example GPIOs

logger = FlowSensorLogger(flow_sensor_pins=flow_pins)

try:
    while True:
        flow_rates = logger.monitor_flow_sensors()
        if flow_rates:
            pressures = logger.read_adc_data()
            
            for i, fr in enumerate(flow_rates):
                database_api.insert_real_sensor_data(f"flow_{i+1}", fr)
            for i, p in enumerate(pressures):
                database_api.insert_real_sensor_data(f"pressure_{i+1}", p)

        time.sleep(1)

except KeyboardInterrupt:
    logger.stop()
