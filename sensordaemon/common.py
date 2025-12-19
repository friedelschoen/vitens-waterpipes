from abc import ABC, abstractmethod
import random


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
