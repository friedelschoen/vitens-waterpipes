import time

import RPi.GPIO as GPIO
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.ads1x15 import ADS1x15, Pin
from adafruit_ads1x15.analog_in import AnalogIn
import board
import busio

from common import Sensor, Valve


FLOW_MEDIAN_TIME = 2  # seconds


class FlowSensor(Sensor):
    unit = "L/min"

    def __init__(self, pin: int, interval=1):
        if GPIO is None:
            raise RuntimeError("flow sensors are not supported")

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


class PressureSensor(AnalogIn, Sensor):
    unit = "bar"

    def __init__(self, ads: ADS1x15, positive_pin: int, negative_pin: int | None = None, factor=1.0):
        super().__init__(ads, positive_pin, negative_pin)
        self.factor = factor

    def read(self) -> float:
        return self.voltage * self.factor


class GPIOValve(Valve):
    def __init__(self, pin):
        if GPIO is None:
            raise RuntimeError("flow sensors are not supported")

        self.pin = pin

        GPIO.setup(pin, GPIO.OUT)
        self.state = 1
        self.wants = 1
        GPIO.output(self.pin, self.state)

    def set_state(self, state: int):
        if GPIO is None:
            raise RuntimeError("flow sensors are not supported")
        if self.state == state:
            return  # nothing changes

        self.state = state
        self.wants = state
        if state == 0 or state == 1:
            GPIO.output(self.pin, state)


def init_peripherals(sensors: dict[str, Sensor], valves: dict[str, Valve]):
    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        while not i2c.try_lock():
            pass
        devices = i2c.scan()
        i2c.unlock()

        if 0x48 in devices:
            ads = ADS.ADS1015(i2c, address=0x48)
            sensors['pressure0'] = PressureSensor(ads, Pin.A0, factor=2.22)
            sensors['pressure1'] = PressureSensor(ads, Pin.A1, factor=2.22)
            sensors['pressure2'] = PressureSensor(ads, Pin.A2, factor=1.88)
            sensors['pressure3'] = PressureSensor(ads, Pin.A3, factor=2.22)

        if 0x49 in devices:
            ads = ADS.ADS1015(i2c, address=0x49)
            sensors['pressure4'] = PressureSensor(ads, Pin.A0, factor=2.22)
            sensors['pressure5'] = PressureSensor(ads, Pin.A1, factor=2.15)
    except Exception as e:
        print(f"unable to get adc's: {e}")
        print(f"continuing with random values")

    try:
        sensors['flow0'] = FlowSensor(17)
        sensors['flow1'] = FlowSensor(27)
        sensors['flow2'] = FlowSensor(22)
        sensors['flow3'] = FlowSensor(10)
        sensors['flow4'] = FlowSensor(9)
    except Exception as e:
        print(f"unable to get flow-sensors: {e}")
        print(f"continuing with random values")

    try:
        valves['valve0'] = GPIOValve(25)
        valves['valve1'] = GPIOValve(8)
        valves['valve2'] = GPIOValve(7)
        valves['valve3'] = GPIOValve(12)
        valves['valve4'] = GPIOValve(16)
    except Exception as e:
        print(f"unable to get valves: {e}")
        print(f"continuing with NOP-valves")
