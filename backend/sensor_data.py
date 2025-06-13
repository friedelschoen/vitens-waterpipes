
import time
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import pigpio
import database_api


class SensorLogger:
    def __init__(self, flow_sensor_pins, interval=1):
        self.flow_sensor_pins = flow_sensor_pins
        self.interval = interval
        self.flow_counts = [0] * len(self.flow_sensor_pins)
        self.previous_time = time.time()
        self.start_time = time.time()

        # Initialize GPIO and flow sensor interrupts
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise ConnectionError("Failed to connect to PiGPIO daemon.")

        for pin in self.flow_sensor_pins:
            self.pi.set_mode(pin, pigpio.INPUT)
            self.pi.set_pull_up_down(pin, pigpio.PUD_UP)
            self.pi.callback(pin, pigpio.FALLING_EDGE, self.flow_sensor_interrupt)

        # Initialize I2C and ADCs
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            while not self.i2c.try_lock():
                pass
            devices = self.i2c.scan()
            self.i2c.unlock()

            self.ads1 = ADS.ADS1015(self.i2c, address=0x48) if 0x48 in devices else None
            self.ads2 = ADS.ADS1015(self.i2c, address=0x49) if 0x49 in devices else None

            self.channels1 = [AnalogIn(self.ads1, getattr(ADS, f"P{i}")) for i in range(4)] if self.ads1 else []
            self.channels2 = [AnalogIn(self.ads2, getattr(ADS, f"P{i}")) for i in range(4)] if self.ads2 else []

        except Exception as e:
            print(f"Error initializing I2C/ADC: {e}")
            self.ads1 = self.ads2 = self.channels1 = self.channels2 = []

    def flow_sensor_interrupt(self, gpio, level, tick):
        try:
            index = self.flow_sensor_pins.index(gpio)
            self.flow_counts[index] += 1
        except ValueError:
            pass  # GPIO not recognized

    def read_flow_data(self):
        current_time = time.time()
        if current_time - self.previous_time >= self.interval:
            self.previous_time = current_time
            flow_rates = [round(count / self.interval, 2) for count in self.flow_counts]
            self.flow_counts = [0] * len(self.flow_counts)
            return flow_rates
        return None

    def read_pressure_data(self):
        zero_voltage = 0.460
        pressures = []
        if self.channels1:
            pressures += [round((ch.voltage - zero_voltage) * 0.5, 3) for ch in self.channels1]
        if self.channels2:
            pressures += [round((ch.voltage - zero_voltage) * 0.5, 3) for ch in self.channels2[:2]]
        return pressures

    def run(self):
        print("Running Real Sensor Logger — Ctrl+C to stop.")
        try:
            while True:
                flow_rates, pressures = self.read_mock_data()
                timestamp = round(time.time() - self.start_time, 2)

                sensor_values = {}

                for i, flow in enumerate(flow_rates, 1):
                    sensor_values[f"flow_{i}"] = flow

                # Add pressures
                for i, pressure in enumerate(pressures, 1):
                    sensor_values[f"pressure_{i}"] = pressure

                # Insert all at once
                database_api.insert_real_sensor_row(sensor_values)

                print(f"[{timestamp:.2f}s] Flows: {flow_rates} | Pressures: {pressures}")
                time.sleep(0.01)

        except KeyboardInterrupt:
            print("Sensor logger stopped.")
            self.stop()

    def stop(self):
        self.pi.stop()
