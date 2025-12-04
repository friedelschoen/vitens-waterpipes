from abc import ABC, abstractmethod
from enum import Enum
import time

from .error import NotSupportedError
try:
    import RPi.GPIO as GPIO
except:
    GPIO = None


class ValveState(Enum):
    CLOSED = 0
    OPEN = 1


class Valve(ABC):
    state: ValveState

    @abstractmethod
    def set_state(self, state: ValveState):
        ...


class ManualValve(Valve):
    def __init__(self):
        self.state = ValveState.OPEN

    def set_state(self, state: ValveState):
        if self.state == state:
            return  # nothing changes

        self.state = state
        print("valve is now " + state.name)


class GPIOValve(Valve):
    def __init__(self, pin):
        if GPIO is None:
            raise NotSupportedError("flow sensors are not supported")

        self.pin = pin

        GPIO.setup(pin, GPIO.OUT)
        self.state = ValveState.OPEN
        GPIO.output(self.pin, self.state.value)

    def set_state(self, state: ValveState):
        if GPIO is None:
            raise NotSupportedError("flow sensors are not supported")
        if self.state == state:
            return  # nothing changes

        self.state = state
        GPIO.output(self.pin, state.value)
