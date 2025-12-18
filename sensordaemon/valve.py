from abc import ABC, abstractmethod
from enum import Enum
import time

try:
    import RPi.GPIO as GPIO
except:
    GPIO = None


# class int(Enum):
#    CLOSED = 0
#    OPEN = 1


class Valve(ABC):
    state: int
    wants: int

    def set_wants(self, state: int):
        self.set_state(state)

    @abstractmethod
    def set_state(self, state: int):
        ...


class ManualValve(Valve):
    def __init__(self):
        self.state = 1
        self.wants = 1

    def set_wants(self, newstate: int):
        if self.wants == newstate:
            return  # nothing changes

        self.wants = newstate
        print(f"valve wants {self.wants}, currently {self.state}")

    def set_state(self, newstate: int):
        if newstate != self.wants:
            print(
                f"setting state {newstate} which valves does not want {self.wants}")

        self.wants = newstate
        self.state = newstate
        print(f"valve wants {self.wants}, currently {self.state}")


class TestValve(Valve):
    def __init__(self):
        self.state = 1
        self.wants = 1

    def set_state(self, state: int):
        if self.state == state:
            return  # nothing changes

        self.state = state
        self.wants = state
        print(f"valve is now {state}")


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
