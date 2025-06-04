from flask import Flask, jsonify
from flask_cors import CORS
import random
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Generate dummy time labels
def generate_time_labels(n):
    now = datetime.now()
    return [(now - timedelta(minutes=i)).strftime("%H:%M") for i in reversed(range(n))]

# Generate a single sensor chart object
def generate_sensor_chart(sensor_id, kind="Flow"):
    num_points = 10
    labels = generate_time_labels(num_points)
    values = [round(random.uniform(0.5, 2.5), 2) if kind == "Flow" else round(random.uniform(1.0, 5.0), 2) for _ in range(num_points)]

    return {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": f"{kind} Sensor {sensor_id + 1}",
                    "data": values,
                    "borderColor": "blue" if kind == "Flow" else "green",
                    "fill": False,
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
    }

@app.route("/api/data")
def get_data():
    # Could dynamically choose flow vs. pressure here
    kind = "Flow"  # Or change to "Pressure" if needed
    data = [generate_sensor_chart(i, kind=kind) for i in range(5)]
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
