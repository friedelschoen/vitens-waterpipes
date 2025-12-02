
from adafruit_ads1x15.analog_in import AnalogIn
from .sensor_data import Sensor

PRESSURE_FACTOR = 2


class PressureSensor(AnalogIn, Sensor):
    unit = "bar"

    def read(self) -> float:
        return self.voltage * PRESSURE_FACTOR
