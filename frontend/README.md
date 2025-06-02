# Frontend - Project Vitens

This is a lightweight static dashboard UI built using plain HTML, CSS, and JavaScript. It queries the Flask backend for live sensor readings and displays them.

## Components

- index.html: Main web interface
- script.js: Fetches real-time data from the Flask API
- app.css: Stylesheet for the page
- img/, fonts/: UI assets and icons

## Run the Frontend

You can serve it using a basic Python web server:

cd frontend
python3 -m http.server 8080

Then visit:

http://localhost:8080 (on PC)
http://<raspberry-pi-ip>:8080 (on Raspberry Pi)

## API Integration

In script.js, update the API base URL:

const apiUrl = 'http://<raspberry-pi-ip>:5000/real_sensor_data/flow_1';

This fetches the latest flow rate from the backend. You can repeat similar calls for pressure sensors.

## Example API Response

{
  "id": 12,
  "timestamp": "2025-06-02T14:30:00",
  "sensor_id": "flow_1",
  "value": 3.42
}

This is parsed and displayed in real time by script.js.

## Features

- Live data display from Raspberry Pi sensors
- Simple and fast setup
- No Node.js or React needed
