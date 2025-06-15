import time
import database_api
import os
if os.name == "posix" and os.uname().sysname == "Linux":
    import RPi.GPIO as GPIO
else:
    import Mock.GPIO as GPIO
from sensor_data import SensorLogger

valve_pins = [25, 8, 7, 12, 16]
valve_states = {}
# valve_states = []

def valves_init():
    for pin in valve_pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
        # valve_states[pin] = {'state': GPIO.HIGH}

def valves_sync():
    """
    Get the current state of all valves.
    Returns a dictionary with valve numbers as keys and their states as values.
    """
    global valve_states
    new_valve_states = database_api.get_valve_states()
    if not new_valve_states:
        raise ValueError("No valve states found in the database.")
    if valve_states != new_valve_states:
        valve_states = new_valve_states
        for idx, state in valve_states.items():
            if idx < 1 or idx > len(valve_pins):
                return
            set_state = GPIO.LOW if state == 1 else GPIO.HIGH
            GPIO.output(valve_pins[idx - 1], set_state)
            print(f"Valve {idx} set to {'ON' if state == 1 else 'OFF'}")
        

    return

# def on_closing():
#     print("Closing application and cleaning up GPIO...")
#     for pin in valve_pins:
#         GPIO.output(pin, GPIO.HIGH)
#     GPIO.cleanup()  # Reset all GPIO channels

if __name__ == "__main__":
    try:
        sensorlogger = SensorLogger(flow_sensor_pins=[25, 8, 7, 12, 16])
        valves_init()
        while True:
            valves_sync()
            # Read sensor data
            sensorlogger.single_read(mock=True)
            # Simulate some delay for the loop
            time.sleep(1)
    except Exception as e:
        print("Error:", e)
    

