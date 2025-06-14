from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from database_api import set_valve_state

app = Flask(__name__)
CORS(app)

DB_PATH = "sensor_data.db"

@app.route('/api/real_sensor_data')
def get_real_sensor_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Get 100 newest, then reverse to oldest first
    c.execute("SELECT * FROM real_sensor_data ORDER BY timestamp DESC LIMIT 100")
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
    data = request.json
    valve_number = data.get('valve_number')
    state = data.get('state')
    set_valve_state(valve_number, state)
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)