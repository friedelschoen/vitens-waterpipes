
from adafruit_ads1x15.analog_in import AnalogIn
from .sensor_data import Sensor, SensorFailure


class PressureSensor(AnalogIn, Sensor):
    def read_data(self) -> tuple[float, SensorFailure]:
        return self.voltage, SensorFailure.NONE
