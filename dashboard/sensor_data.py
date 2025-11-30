from typing import Dict


class Sensor:
    def read_data(self, dest: Dict[str, float]):
        ...
