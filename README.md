# Project Vitens

A complete Raspberry Pi-based system for monitoring water flow and pressure using sensors, saving the data locally, and displaying it on a web-based dashboard.

## Project Structure

Project-Vitens/

├── backend/      # Python API + sensor data collection

├── frontend/     # HTML/CSS/JS dashboard UI

├── systemd/      # Raspberry Pi auto-start service files

## Requirements

- Raspberry Pi with Raspberry Pi OS
- Python 3 (installed by default)
- pigpiod and i2c enabled
- Node.js (optional for advanced frontend hosting)

## Quick Start (Development)

### 1. Backend Setup
```
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python api_server.py
```
### 2. Run the Sensor Logger
```
source backend/venv/bin/activate
python backend/sensor_logger_runner.py
```
### 3. Launch the Frontend
```
cd frontend
python3 -m http.server 8080
```
# Visit http://<raspberry-pi-ip>:8080 in your browser

## Raspberry Pi Deployment

1. Enable I2C and pigpiod via raspi-config
2. Install project dependencies
3. Transfer this project to the Pi
4. Run manually or use systemd to auto-start everything on boot

## Enable Services on Boot (Optional)
```
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vitens_api.service
sudo systemctl enable vitens_logger.service
sudo systemctl enable vitens_frontend.service
```