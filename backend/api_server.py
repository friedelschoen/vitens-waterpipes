from typing import Dict
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from .database_api import set_valve_state

app = Flask(__name__, static_url_path='', static_folder='../frontend')
CORS(app)

DB_PATH = "sensor_data.db"


@app.route('/api/real_sensor_data')
def get_real_sensor_data():
    limit = request.args.get('limit', default=100, type=int)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Get newest 'limit' rows, then reverse to oldest first
    c.execute("SELECT * FROM real_sensor_data ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    columns = [desc[0] for desc in c.description]
    data = [dict(zip(columns, row)) for row in rows]
    conn.close()
    # Reverse so oldest is first
    data.reverse()
    return jsonify(data)

# Example Flask route (add to your Flask app)
@app.route('/api/valve_state', methods=['POST'])
def update_valve_state():
    data: Dict[str, int] | None = request.json
    if type(data) is not dict:
        return jsonify(success=False)

    valve_number = data.get('valve_number', 0)
    state = data.get('state', 0)
    set_valve_state(valve_number, state)
    return jsonify(success=True)

@app.route('/api/get_valve_states', methods=['GET'])
def get_valve_states():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT valve_number, state FROM valve_states")
    rows = c.fetchall()
    conn.close()
    valve_states = [{"valve_number": row[0], "state": row[1]} for row in rows]
    return jsonify(valve_states)

@app.route('/api/simulation_data')
def get_simulation_data():
    limit = request.args.get('limit', default=100, type=int)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM simulation_data ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    columns = [desc[0] for desc in c.description]
    data = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return jsonify(data)
