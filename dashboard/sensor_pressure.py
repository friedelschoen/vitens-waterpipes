
from traceback import print_exc
from typing import Dict, List
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from . import sensor_data


class PressureSensor(sensor_data.Sensor):
    @staticmethod
    def get_pi_channels() -> List[AnalogIn]:
        channels = []
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            while not i2c.try_lock():
                pass
            devices = i2c.scan()
            i2c.unlock()

            if 0x48 in devices:
                ads = ADS.ADS1015(i2c, address=0x48)
                channels += [
                    AnalogIn(ads, ADS.P0), AnalogIn(ads, ADS.P1),
                    AnalogIn(ads, ADS.P2), AnalogIn(ads, ADS.P3),
                ]

            if 0x49 in devices:
                ads = ADS.ADS1015(i2c, address=0x49)
                channels += [
                    AnalogIn(ads, ADS.P0), AnalogIn(ads, ADS.P1),
                ]
        except:
            print("unable to get adc's")
            print_exc()

        return channels

    def __init__(self, channels: List[AnalogIn]):
        self.channels = channels

    def read_data(self, dest: Dict[str, float]):
        for i, ch in enumerate(self.channels):
            dest[f'pressure_{i+1}'] = ch.voltage
