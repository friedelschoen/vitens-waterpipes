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

```sh
pip install -r requirements.txt
```

This will install all required libraries for both development (mock data) and real sensors (on Raspberry Pi).  
On Windows, only the relevant packages will be installed.

---

## 3. Running the Project (with Fake Data — for Development)

### a. Open a terminal in the `backend` folder.

### b. Start the Sensor Data Generator

This will create the database and start writing random sensor data:
```sh
python run_sensor_data.py
```

Leave this terminal open.


### c. Open a **second terminal** in the `backend` folder.

### d. Start the Flask API Server

This will serve the latest sensor data to the frontend:
```sh
python api_server.py
```

Leave this terminal open.

### e. Open a **third terminal** in the `frontend` folder.

### f. Start the Frontend Web Server
```sh
python -m http.server 8080
```

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
- `backend/database_api.py` — Handles SQLite database operations  
- `backend/fake_sensor_data.py` — Generates and logs mock sensor data (for development)  
- `backend/sensor_data.py` — Reads and logs real sensor data (for Raspberry Pi)  
- `frontend/index.html` — Main dashboard web page  
- `frontend/valves.html` — Additional dashboard page (e.g., for valve data)  
- `frontend/script.js` — Fetches and displays live data in the dashboard  
- `frontend/app.css` — Stylesheet for the dashboard UI  
- `frontend/data.json` — Example or cached chart data (for development/testing)  
- `frontend/README.md` — Frontend-specific instructions  
- `.gitignore` — Files and folders ignored by git  
- `requirements.txt` — List of required Python libraries  
- `README.md` — Main project instructions

---

**That's it!**