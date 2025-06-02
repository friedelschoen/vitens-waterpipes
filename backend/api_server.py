from flask import Flask, jsonify
import database_api  # Import your database functions

app = Flask(__name__)

# Serve latest real sensor data as JSON
@app.route('/real_sensor_data/<sensor_id>', methods=['GET'])
def real_sensor_data(sensor_id):
    data = database_api.get_latest_real_data(sensor_id)
    if data:
        response = {
            "id": data[0],
            "timestamp": data[1],
            "sensor_id": data[2],
            "value": data[3]
        }
    else:
        response = {"error": "No data found"}
    return jsonify(response)

# Serve latest simulation data as JSON
@app.route('/simulation_data/<simulation_id>', methods=['GET'])
def simulation_data(simulation_id):
    data = database_api.get_latest_simulation_data(simulation_id)
    if data:
        response = {
            "id": data[0],
            "timestamp": data[1],
            "simulation_id": data[2],
            "predicted_value": data[3]
        }
    else:
        response = {"error": "No data found"}
    return jsonify(response)

# Start the Flask server
if __name__ == '__main__':
    database_api.create_tables()  # Ensure tables are created when server starts
    app.run(host='0.0.0.0', port=5000, debug=True)