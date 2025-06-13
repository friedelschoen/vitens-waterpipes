# Backend - Project Vitens

This folder contains all backend logic for reading sensors, storing values into a SQLite database, and serving the data using a Flask API.

## Components

- SensorDataLogger.py: Reads flow and pressure sensors via GPIO and I2C
- database_api.py: Creates and writes to a local SQLite database
- api_server.py: Flask API that serves latest sensor readings as JSON
- sensor_logger_runner.py: Continuously polls sensors and pushes data to DB

## Setup

1. Create and activate a virtual environment:

python3 -m venv venv
source venv/bin/activate

2. Install dependencies:

pip install -r requirements.txt

## Run the API Server

python api_server.py

The API will be available at http://<pi-ip>:5000

## Run the Sensor Logger

python sensor_logger_runner.py

This script:
- Continuously reads data from connected sensors
- Stores each reading in the real_sensor_data table of sensor_data.db
