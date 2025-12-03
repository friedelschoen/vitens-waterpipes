import random
import time

from adafruit_ads1x15.analog_in import AnalogIn

from .error import NotSupportedError
try:
    import RPi.GPIO as GPIO
except:
    GPIO = None


class Sensor:
    unit: str

    def read(self) -> float:
        ...


class RandomizedSensor(Sensor):
    def __init__(self, unit: str, min: int, max: int):
        self.unit = unit
        self.min = min
        self.max = max
        self.value = min + (max - min)/2

    def read(self) -> float:
        step = max(self.max-self.value, self.value-self.min)/10
        self.value += random.uniform(-step, step)

        if self.value < self.min:
            self.value = self.min
        if self.value > self.max:
            self.value = self.max

        return self.value


PRESSURE_FACTOR = 2


class PressureSensor(AnalogIn, Sensor):
    unit = "bar"

    def read(self) -> float:
        return self.voltage * PRESSURE_FACTOR


class FlowSensor(Sensor):
    unit = "L/min"

    def __init__(self, pin: int, interval=1):
        if GPIO is None:
            raise NotSupportedError("flow sensors are not supported")

        self.pin = pin
        self.interval = interval
        self.previous_time = time.time()
        self.previous_value = 0
        self.flow_count = 0

        # Initialize GPIO and flow sensor interrupts
        GPIO.setup(self.pin, GPIO.IN, GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING,
                              self.flow_sensor_interrupt)

    def flow_sensor_interrupt(self, _):
        self.flow_count += 1

    def read(self) -> float:
        current_time = time.time()
        value = self.flow_count / (current_time - self.previous_time)
        result = (self.previous_value + value) / 2

        self.previous_time = current_time
        self.previous_value = value
        self.flow_count = 0

        return result / 4.8
