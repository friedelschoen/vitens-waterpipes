import time
import database_api
import os
if os.name == "posix" and os.uname().sysname == "Linux":
    import RPi.GPIO as GPIO
else:
    import Mock.GPIO as GPIO
from sensor_data import SensorLogger
from itertools import product
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
def generate_valve_states():
    valve_states = []
    for settings in product([0, 1], repeat=5):
        full_settings = list(settings)
        valve_states.append(full_settings)
    return valve_states

def set_valves_state(state):
    """
    Set the state of all valves based on the provided state list.
    The state list should contain 5 elements, each being 0 (OFF) or 1 (ON).
    """
    if len(state) != len(valve_pins):
        raise ValueError("State must have exactly 5 elements.")
    
    for idx, pin in enumerate(valve_pins):
        GPIO.output(pin, GPIO.LOW if state[idx] == 1 else GPIO.HIGH)
        # print(f"Valve {idx + 1} set to {'ON' if state[idx] == 1 else 'OFF'}")


if __name__ == "__main__":
    try:
        sensorlogger = SensorLogger(flow_sensor_pins=[17, 27, 22, 10, 9])
        ai_prediction = AiPrediction(
            model_path='backend/ai_model/models/trained_model_0.03282613163245908.pth',
            dataset_file='backend/ai_model/dataset/dataset_extended_clean.csv'
        )
        database_api.create_tables()
        valves_init()
        valve_state_list = generate_valve_states()        
        state_index = 0

        previous_update_valve_time = time.time()
        previous_read_sensor_time = time.time()
        update_valve_interval = 20 # seconds
        read_sensor_interval = 1 # seconds
        time.sleep(2)
        while True:
            valves_sync()
            current_time = time.time()

            # if current_time - previous_update_valve_time >= update_valve_interval:  
                # isSettingValid = False
                # while isSettingValid == False:
                    # if state_index >= len(valve_state_list):
                        # break
                    # new_state = valve_state_list[state_index]
                    # state_index +=1
                    # if new_state[0] == 1 or new_state[1] == 1:
                        # isSettingValid = True
                    
                # set_valves_state(new_state)            
                # previous_update_valve_time = current_time
                # print(f"[{state_index}] Set valves to state: {new_state}")
            
            if current_time - previous_read_sensor_time >= read_sensor_interval:
                previous_read_sensor_time = current_time
            
                values = sensorlogger.single_read()
                selected_keys = [f'flow_{i}' for i in range(1, 5)] + [f'pressure_{i}' for i in range(1, 6)]
                flat_values = [values[k] for k in selected_keys]

                # Make prediction
                prediction = ai_prediction.predict(flat_values)
                # Insert prediction data into the database
                database_api.insert_simulation_row({
                    "flow_5": float(prediction[0][0]),
                    "pressure_6": float(prediction[0][1])
                })

            time.sleep(0.5)
    except Exception as e:
        print("Error:", e)
    

