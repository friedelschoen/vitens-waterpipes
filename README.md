# Vitens Sensor Dashboard — Quick Start Guide

This guide explains **exactly** how to run the Vitens sensor dashboard project, step by step, for both **fake/mock data** (for development) and real sensor data (on Raspberry Pi).  
It also lists all required Python libraries.

---

## 1. Prerequisites

- **Python 3.8+** installed
- **Git** (optional, for cloning)
- **Windows or Raspberry Pi** (for real sensors)

---

## 2. Install Required Python Libraries

Open a terminal in the `backend` folder and run:
pip install flask flask-cors


If you are running on a **Raspberry Pi with real sensors**, also install:
pip install adafruit-circuitpython-ads1x15 pigpio


## 3. Running the Project (with Fake Data — for Development)

### a. Open a terminal in the `backend` folder.

### b. Start the Sensor Data Generator

This will create the database and start writing random sensor data:
python run_sensor_data.py

Leave this terminal open.


### c. Open a **second terminal** in the `backend` folder.

### d. Start the Flask API Server

This will serve the latest sensor data to the frontend:
python api_server.py

Leave this terminal open.

### e. Open a **third terminal** in the `frontend` folder.

### f. Start the Frontend Web Server
python -m http.server 8080

### g. Open your browser and go to:
http://localhost:8080

You should see the dashboard updating live with fake sensor data.

---

## 4. Running with Real Sensors (Raspberry Pi)

- Make sure you have the required hardware and wiring.
- In `run_sensor_data.py`, the correct logger will be used automatically based on your platform.
- Start the backend and frontend as above.

---

## 5. Stopping the System

- To stop any process, press `Ctrl+C` in its terminal window.

---

## 6. Troubleshooting

- If you see "No data available", make sure all three processes are running.
- If you get CORS errors, ensure `flask-cors` is installed and `CORS(app)` is in `api_server.py`.
- If you get "Python was not found", make sure Python is installed and added to your PATH.

---

## 7. Required Python Libraries (Summary)

- `flask`
- `flask-cors`
- `adafruit-circuitpython-ads1x15` *(only for Raspberry Pi with real sensors)*
- `pigpio` *(only for Raspberry Pi with real sensors)*

---

## 8. File Overview

- `backend/run_sensor_data.py` — Starts fake or real sensor logging
- `backend/api_server.py` — Serves sensor data as an API
- `frontend/` — Contains the dashboard web files

---

**That's it!**  