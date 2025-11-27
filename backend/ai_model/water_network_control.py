import time
import database_api
import os
if os.name == "posix" and os.uname().sysname == "Linux":
    import RPi.GPIO as GPIO
else:
    import Mock.GPIO as GPIO
from sensor_data import SensorLogger
from ai_model.ai_prediction import AiPrediction

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
        ai_prediction = AiPrediction(
            model_path='ai_model/models/trained_model_0.0263541944206078.pth',
            dataset_file='ai_model/dataset/real_dataset.csv'
        )
        # valves_init()
        while True:
            # valves_sync()
            # Read sensor data
            values = sensorlogger.single_read(mock=False)
            
            selected_keys = [f'flow_{i}' for i in range(1, 5)] + [f'pressure_{i}' for i in range(1, 6)]
            flat_values = [values[k] for k in selected_keys]

            # Make prediction
            prediction = ai_prediction.predict(flat_values)
            print("AI Prediction:", prediction)

            # Simulate some delay for the loop
            time.sleep(1)
    except Exception as e:
        print("Error:", e)
    

