from flask import Flask, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

DB_PATH = "sensor_data.db"

@app.route('/api/real_sensor_data')
def get_real_sensor_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Get 10 newest, then reverse to oldest first
    c.execute("SELECT * FROM real_sensor_data ORDER BY timestamp DESC LIMIT 10")
    rows = c.fetchall()
    columns = [desc[0] for desc in c.description]
    data = [dict(zip(columns, row)) for row in rows]
    conn.close()
    # Reverse so oldest is first
    data.reverse()
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)