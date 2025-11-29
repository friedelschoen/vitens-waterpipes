
import time
from typing import Dict
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
try:
    import RPi.GPIO as GPIO
except:
    import Mock.GPIO as GPIO
from . import database_api, fake_sensor_data

class SensorLogger:
    def __init__(self, flow_sensor_pins, interval=1):
        self.flow_sensor_pins = flow_sensor_pins
        self.interval = interval
        self.flow_counts = [0] * len(self.flow_sensor_pins)
        self.previous_time = time.time()
        self.start_time = time.time()

        # Initialize GPIO and flow sensor interrupts
        for pin in self.flow_sensor_pins:
            GPIO.setup(pin, GPIO.IN, GPIO.PUD_UP)
            GPIO.add_event_detect(pin, GPIO.FALLING, self.flow_sensor_interrupt)

        # Initialize I2C and ADCs
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            while not self.i2c.try_lock():
                pass
            devices = self.i2c.scan()
            self.i2c.unlock()

            self.ads1 = ADS.ADS1015(self.i2c, address=0x48) if 0x48 in devices else None
            self.ads2 = ADS.ADS1015(self.i2c, address=0x49) if 0x49 in devices else None

            self.channels1 = [AnalogIn(self.ads1, getattr(ADS, f"P{i}")) for i in range(4)] if self.ads1 else []
            self.channels2 = [AnalogIn(self.ads2, getattr(ADS, f"P{i}")) for i in range(4)] if self.ads2 else []

        except Exception as e:
            print(f"Error initializing I2C/ADC: {e}")
            self.ads1 = self.ads2 = self.channels1 = self.channels2 = []

    def flow_sensor_interrupt(self, gpio):
        try:
            index = self.flow_sensor_pins.index(gpio)
            self.flow_counts[index] += 1
        except ValueError:
            pass

    def read_flow_data(self):
        current_time = time.time()
        flow_rates = [count / self.interval for count in self.flow_counts]

        if current_time - self.previous_time >= self.interval:
            self.previous_time = current_time
            self.flow_counts = [0] * len(self.flow_counts)

        return flow_rates

    def read_pressure_data(self):
        pressures = []
        if self.channels1:
            pressures += [ch.voltage for ch in self.channels1]
        if self.channels2:
            pressures += [ch.voltage for ch in self.channels2[:2]]
        return pressures

    def read_mock_data(self):
        # Use the MockSensorLogger to generate fake data
        mock_logger = fake_sensor_data.MockSensorLogger(interval=self.interval)
        return mock_logger.read_mock_data()

    def single_read(self) -> Dict[str, float]:
        # mock = os.getenv("VITENS_MOCK") is not None
        # if mock:
        #     flow_rates, pressures = self.read_mock_data()
        # else:
            # Read real sensor data
        flow_rates = self.read_flow_data()
        pressures= self.read_pressure_data()

        if flow_rates is None or pressures is None:
            print("none found")
            return {}

        sensor_values = {}

        for i in range(4):
            if i < len(flow_rates):
                sensor_values[f"flow_{i+1}"] = flow_rates[i]
            else:
                sensor_values[f"flow_{i+1}"] = 0

        # Add pressures
        for i in range(5):
            if i < len(pressures):
                sensor_values[f"pressure_{i+1}"] = pressures[i]
            else:
                sensor_values[f"pressure_{i+1}"] = 0

        database_api.insert_real_sensor_row(sensor_values)
        return sensor_values
