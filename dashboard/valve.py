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
    wants: ValveState

    def set_wants(self, state: ValveState):
        self.set_state(state)

    @abstractmethod
    def set_state(self, state: ValveState):
        ...


class ManualValve(Valve):
    def __init__(self):
        self.state = ValveState.OPEN
        self.wants = ValveState.OPEN

    def set_wants(self, newstate: ValveState):
        if self.wants == newstate:
            return  # nothing changes

        self.wants = newstate
        print(f"valve wants {self.wants.name}, currently {self.state}")

    def set_state(self, newstate: ValveState):
        if newstate != self.wants:
            print(
                f"setting state {newstate.name} which valves does not want {self.wants.name}")

        self.wants = newstate
        self.state = newstate
        print(f"valve wants {self.wants.name}, currently {self.state}")


class TestValve(Valve):
    def __init__(self):
        self.state = ValveState.OPEN
        self.wants = ValveState.OPEN

    def set_state(self, state: ValveState):
        if self.state == state:
            return  # nothing changes

        self.state = state
        self.wants = state
        print("valve is now " + state.name)


class GPIOValve(Valve):
    def __init__(self, pin):
        if GPIO is None:
            raise NotSupportedError("flow sensors are not supported")

        self.pin = pin

        GPIO.setup(pin, GPIO.OUT)
        self.state = ValveState.OPEN
        self.wants = ValveState.OPEN
        GPIO.output(self.pin, self.state.value)

    def set_state(self, state: ValveState):
        if GPIO is None:
            raise NotSupportedError("flow sensors are not supported")
        if self.state == state:
            return  # nothing changes

        self.state = state
        self.wants = state
        GPIO.output(self.pin, state.value)
