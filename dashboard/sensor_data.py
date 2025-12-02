from enum import Enum, auto as iota
import random


class SensorFailure(Enum):
    NONE = iota()
    DIMMED = iota()
    RANDOMIZED = iota()
    CONSTANT = iota()


class Sensor:
    def read_data(self) -> tuple[float, SensorFailure]:
        ...


class RandomizedSensor(Sensor):
    def __init__(self, min: int, max: int):
        self.min = min
        self.max = max

    def read_data(self) -> tuple[float, SensorFailure]:
        return random.uniform(self.min, self.max), SensorFailure.RANDOMIZED
