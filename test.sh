#!/bin/bash
# Script to launch multiple Python applications in separate terminals on a Raspberry Pi
# Updated on June 17, 2024

echo "Starting applications in separate terminals..."

# Define the path to the activate script for the virtual environment
VENV_ACTIVATE="/home/Vitens/Waterpipes/backend/venv/bin/activate"

# Define the base directory for the python scripts
BASE_DIR="/home/Vitens/Waterpipes/backend"

# --- Start pigpio daemon ---
# This is required for controlling GPIO pins.
echo "Starting pigpio daemon..."
sudo pigpiod
# Add a small delay to ensure the daemon is fully running before the script that needs it starts
sleep 1

# --- Command 1 (Previously Command 2): Launch the Water Network Control ---
# A new terminal will open, activate the venv, and then run the water_network_control.py script.
lxterminal --title="Water Network Control" -e bash -c "echo 'Activating virtual environment...'; \
. $VENV_ACTIVATE; \
echo 'Starting Water Network Control...'; \
python3 $BASE_DIR/water_network_control.py; \
exec bash" &

# --- Command 2 (Previously Command 1): Launch the API server ---
# A new terminal will open, activate the venv, and then run the api_server.py script.
lxterminal --title="API Server" -e bash -c "echo 'Activating virtual environment...'; \
. $VENV_ACTIVATE; \
echo 'Starting API server...'; \
python3 $BASE_DIR/api_server.py; \
exec bash" &

# --- Command 3: Launch the HTTP Server ---
# A new terminal will open, activate the venv, and then run the http.server module.
lxterminal --title="HTTP Server" -e bash -c "echo 'Activating virtual environment...'; \
. $VENV_ACTIVATE; \
echo 'Starting HTTP server on port 8080...'; \
python -m http.server 8080; \
exec bash" &

echo "All applications have been launched."