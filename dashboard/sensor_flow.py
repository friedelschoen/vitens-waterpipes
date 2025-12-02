
import time
try:
    import RPi.GPIO as GPIO
except:
    pass
from .sensor_data import Sensor


class FlowSensor(Sensor):
    unit = "L/min"

    def __init__(self, pin: int, interval=1):
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
