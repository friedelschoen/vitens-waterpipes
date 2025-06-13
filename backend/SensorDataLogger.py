import time
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import csv
import pigpio
import os


class FlowSensorLogger:
    def __init__(self, flow_sensor_pins, interval=1, csv_folder="logs", csv_file_name="data_log.csv"):
        """
        Initializes the FlowSensorLogger instance.

        Args:
            flow_sensor_pins (list): List of GPIO pins connected to flow sensors.
            interval (int): Time interval (in seconds) for calculating flow rates.
            csv_folder (str): Folder path to store log files.
            csv_file_name (str): Name of the CSV file for logging data.
        """
        # Initialize PiGPIO for GPIO control
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise ConnectionError("Failed to connect to PiGPIO")

        try:
            # Initialize the I2C bus
            self.i2c = busio.I2C(board.SCL, board.SDA)

            # Check if I2C is locked and wait if necessary
            while not self.i2c.try_lock():
                pass

            # Scan for I2C devices
            devices = self.i2c.scan()
            self.i2c.unlock()

            if 0x48 in devices:
                self.ads1 = ADS.ADS1015(self.i2c, address=0x48)
                self.channels1 = [AnalogIn(self.ads1, getattr(ADS, f"P{i}")) for i in range(4)]
            else:
                self.ads1 = None
                self.channels1 = []

            if 0x49 in devices:
                self.ads2 = ADS.ADS1015(self.i2c, address=0x49)
                self.channels2 = [AnalogIn(self.ads2, getattr(ADS, f"P{i}")) for i in range(4)]
            else:
                self.ads2 = None
                self.channels2 = []

        except Exception as e:
            print(f"Error initializing I2C or ADS devices: {e}")
            self.i2c = None
            self.ads1 = None
            self.ads2 = None
            self.channels1 = []
            self.channels2 = []

        # Setup flow sensor attributes
        self.flow_sensor_pins = flow_sensor_pins
        self.flow_counts = [0] * len(self.flow_sensor_pins)
        self.interval = interval
        self.previous_time = time.time()

        # Configure GPIO pins for flow sensors with interrupts
        for pin in self.flow_sensor_pins:
            self.pi.set_mode(pin, pigpio.INPUT)
            self.pi.set_pull_up_down(pin, pigpio.PUD_UP)
            self.pi.callback(pin, pigpio.FALLING_EDGE, self.flow_sensor_interrupt)

        # Configure CSV logging settings
        self.csv_folder = csv_folder
        self.csv_file_name = csv_file_name
        self.start_time = time.time()

    def flow_sensor_interrupt(self, gpio, level, tick):
        """
        Increment pulse count for the flow sensor triggered by an interrupt.

        Args:
            gpio (int): GPIO pin number.
            level (int): Signal level.
            tick (int): Timestamp of the interrupt event.
        """
        index = self.flow_sensor_pins.index(gpio)
        self.flow_counts[index] += 1

    def monitor_flow_sensors(self):
        """
        Calculate and return flow rates for all sensors.

        Returns:
            list: List of flow rates (pulses per second) for each sensor.
        """
        current_time = time.time()
        flow_rates = []

        if current_time - self.previous_time >= self.interval:
            self.previous_time = current_time

            for count in self.flow_counts:
                flow_rate = count / self.interval  # Flow rate in pulses per second
                flow_rates.append(round(flow_rate, 2))

            # Reset flow counts after calculation
            self.flow_counts = [0] * len(self.flow_counts)

        return flow_rates

    def read_adc_data(self):
        """
        Read analog voltage data from available ADC channels and calculate pressure.

        Returns:
            list: List of pressures (in bars) calculated from each ADC channel.
                  Includes 4 channels from address 0x48 and the first 2 channels from address 0x49 (if available).
        """
        # Constants
        zero_pressure_voltage = 0.460  # Voltage at 1 bar

        # Read voltages and calculate pressures
        pressures = []
        if self.ads1:
            pressures += [round((channel.voltage - zero_pressure_voltage) * 0.5, 3) for channel in self.channels1]
        if self.ads2:
            pressures += [round((self.channels2[i].voltage - zero_pressure_voltage) * 0.5, 3) for i in range(2)]
        
        return pressures

    def log_data(self):
        """
        Log flow sensor and ADC data to a CSV file at regular intervals.
        """
        # Ensure the directory for logs exists
        os.makedirs(self.csv_folder, exist_ok=True)
        csv_path = os.path.join(self.csv_folder, self.csv_file_name)

        with open(csv_path, mode='w', newline='') as file:
            # Define CSV header
            fieldnames = ["Timestamp", "F1", "F2", "F3", "F4", "F5", "P1", "P2", "P3", "P4", "P5", "P6"]
            writer = csv.writer(file)
            writer.writerow(fieldnames)

            while True:
                # Calculate flow rates and read ADC data
                flow_rates = self.monitor_flow_sensors()
                if flow_rates:  # Log only when data is available
                    adc_data = self.read_adc_data()
                    runtime = round(time.time() - self.start_time, 0)  # Runtime since the logger started
                    row = [runtime] + flow_rates + adc_data
                    writer.writerow(row)
                    print(f"Logged Data: {row}")

                file.flush()
                time.sleep(0.01)

    def stop(self):
        """
        Stop the PiGPIO instance and clean up resources.
        """
        self.pi.stop()

import random
import time
import os
import csv
from datetime import datetime

class DummyFlowSensorLogger:
    def __init__(self, num_flow_sensors=5, num_pressure_sensors=6, num_valves=5, interval=1, csv_folder="logs", csv_file_name="dummy_data_log.csv"):
        self.num_flow_sensors = num_flow_sensors
        self.num_pressure_sensors = num_pressure_sensors
        self.num_valves = num_valves
        self.interval = interval
        self.start_time = time.time()
        self.csv_folder = csv_folder
        self.csv_file_name = csv_file_name

    def monitor_flow_sensors(self):
        return [round(random.uniform(0.0, 10.0), 2) for _ in range(self.num_flow_sensors)]

    def read_adc_data(self):
        return [round(random.uniform(0.5, 5.0), 3) for _ in range(self.num_pressure_sensors)]

    def read_valve_states(self):
        return [random.choice(["ON", "OFF"]) for _ in range(self.num_valves)]

    def log_data(self):
        os.makedirs(self.csv_folder, exist_ok=True)
        csv_path = os.path.join(self.csv_folder, self.csv_file_name)

        with open(csv_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["json_row"])  # CSV header with single column

            while True:
                timestamp = datetime.now().isoformat()
                runtime = round(time.time() - self.start_time, 0)

                flow_rates = self.monitor_flow_sensors()
                pressures = self.read_adc_data()
                valve_states = self.read_valve_states()

                # Build dictionary-like row
                row_data = {
                    "timestamp": timestamp,
                    "runtime": runtime,
                }
                row_data.update({f"F{i+1}": flow_rates[i] for i in range(self.num_flow_sensors)})
                row_data.update({f"P{i+1}": pressures[i] for i in range(self.num_pressure_sensors)})
                row_data.update({f"V{i+1}": valve_states[i] for i in range(self.num_valves)})

                # Convert dict to JSON-style string and write it
                json_row = str(row_data).replace("'", '"')  # Replace single quotes with double quotes for JSON look
                writer.writerow([json_row])
                print(json_row)
                file.flush()
                time.sleep(self.interval)
