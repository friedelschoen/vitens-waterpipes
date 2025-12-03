from enum import Enum
import time
try:
    import RPi.GPIO as GPIO
except:
    pass


class ValveState(Enum):
    CLOSED = 0
    OPEN = 1


class Valve:
    def __init__(self):
        self.state = ValveState.OPEN

    def set_state(self, state: ValveState):
        self.state = state
        time.sleep(0.5)
        print("valve is now " + state.name)


class GPIOValve(Valve):
    def __init__(self, pin):
        self.pin = pin

        GPIO.setup(pin, GPIO.OUT)
        self.set_state(ValveState.OPEN)

    def set_state(self, state: ValveState):
        self.state = state
        GPIO.output(self.pin, state.value)
