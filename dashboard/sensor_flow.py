
import time
from typing import Dict
try:
    import RPi.GPIO as GPIO
except:
    import Mock.GPIO as GPIO
from . import sensor_data


class FlowSensor(sensor_data.Sensor):
    def __init__(self, flow_sensor_pins, interval=1):
        self.flow_sensor_pins = flow_sensor_pins
        self.interval = interval
        self.flow_counts = [0] * len(self.flow_sensor_pins)
        self.previous_time = time.time()

        # Initialize GPIO and flow sensor interrupts
        for pin in self.flow_sensor_pins:
            GPIO.setup(pin, GPIO.IN, GPIO.PUD_UP)
            GPIO.add_event_detect(
                pin, GPIO.FALLING, self.flow_sensor_interrupt)

    def flow_sensor_interrupt(self, gpio):
        index = self.flow_sensor_pins.index(gpio)
        if index != -1:
            self.flow_counts[index] += 1

    def read_data(self, dest: Dict[str, float]):
        current_time = time.time()
        delta_t = current_time - self.previous_time

        for i, count in enumerate(self.flow_counts):
            dest[f'flow_{i+1}'] = count / delta_t

        if delta_t >= self.interval:
            self.previous_time = current_time
            for i in range(len(self.flow_counts)):
                self.flow_counts[i] = 0
