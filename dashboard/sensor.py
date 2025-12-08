from abc import ABC, abstractmethod
import random
import time

from adafruit_ads1x15.ads1x15 import ADS1x15
from adafruit_ads1x15.analog_in import AnalogIn

from .error import NotSupportedError
try:
    import RPi.GPIO as GPIO
except:
    GPIO = None


class Sensor(ABC):
    unit: str

    @abstractmethod
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


class PressureSensor(AnalogIn, Sensor):
    unit = "bar"

    def __init__(self, ads: ADS1x15, positive_pin: int, negative_pin: int | None = None, factor=1.0):
        super().__init__(ads, positive_pin, negative_pin)
        self.factor = factor

    def read(self) -> float:
        return self.voltage * self.factor


FLOW_MEDIAN_TIME = 2


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
        if current_time-self.previous_time > FLOW_MEDIAN_TIME:
            self.previous_value = self.flow_count / \
                (current_time - self.previous_time)
            self.previous_time = current_time
            self.flow_count = 0

        return self.previous_value / 4.8
