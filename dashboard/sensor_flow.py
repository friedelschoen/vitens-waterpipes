
import time
try:
    import RPi.GPIO as GPIO
except:
    pass
from .sensor_data import Sensor, SensorFailure


class FlowSensor(Sensor):
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

    def read_data(self) -> tuple[float, SensorFailure]:
        current_time = time.time()
        delta_t = current_time - self.previous_time

        if delta_t >= self.interval:
            self.previous_time = current_time
            self.previous_value = self.flow_count / delta_t
            self.flow_count = 0

        return self.previous_value, SensorFailure.NONE
