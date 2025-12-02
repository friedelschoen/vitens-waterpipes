import random


class Sensor:
    unit: str

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
