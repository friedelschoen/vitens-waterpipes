from flask import Flask, jsonify
import database_api  # Your custom module for DB operations

app = Flask(__name__)

# REAL SENSOR DATA
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
        response = {"error": "No real data found"}
    return jsonify(response)

# SIMULATED SENSOR DATA
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
        response = {"error": "No simulated data found"}
    return jsonify(response)

# VALVE STATE DATA
@app.route('/valve_state/<valve_id>', methods=['GET'])
def valve_state(valve_id):
    data = database_api.get_latest_valve_state(valve_id)
    if data:
        response = {
            "id": data[0],
            "timestamp": data[1],
            "valve_id": data[2],
            "state": data[3]  # Should be "ON" or "OFF"
        }
    else:
        response = {"error": "No valve data found"}
    return jsonify(response)

# FRONTEND CHART DATA (REAL DATA)
@app.route('/api/data', methods=['GET'])
def get_all_chart_data():
    # You can extend this to fetch multiple sensor kinds
    sensor_ids = database_api.get_all_sensor_ids()
    chart_data = []

    for sensor_id in sensor_ids:
        values = database_api.get_recent_real_data(sensor_id, limit=10)
        if not values:
            continue

        chart_data.append({
            "type": "line",
            "data": {
                "labels": [row[1] for row in values],  # timestamps
                "datasets": [
                    {
                        "label": f"Sensor {sensor_id}",
                        "data": [row[3] for row in values],  # sensor values
                        "borderColor": "blue",
                        "fill": False
                    }
                ]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "y": {
                        "beginAtZero": True
                    }
                }
            }
        })

    return jsonify(chart_data)

# Set valve state from frontend
@app.route('/valve_state/<valve_id>', methods=['POST'])
def update_valve_state(valve_id):
    data = request.get_json()
    state = data.get("state")
    if state not in ["ON", "OFF"]:
        return jsonify({"error": "Invalid state"}), 400

    database_api.set_valve_state(valve_id, state)
    return jsonify({"valve_id": valve_id, "new_state": state, "status": "updated"})

# Get latest valve state
@app.route('/valve_state/<valve_id>', methods=['GET'])
def get_valve_state(valve_id):
    state = database_api.get_latest_valve_state(valve_id)
    if state is None:
        return jsonify({"error": "No state found"}), 404
    return jsonify({"valve_id": valve_id, "state": state})

# START SERVER
if __name__ == '__main__':
    database_api.create_tables()  # Ensure DB schema is initialized
    app.run(host='0.0.0.0', port=5000, debug=True)
