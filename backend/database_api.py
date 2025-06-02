import sqlite3
import logging
import os
import shutil
import schedule
import time
from datetime import datetime

DB_PATH = 'sensor_data.db'
BACKUP_FOLDER = "db_backups"

# Logging Setup
logging.basicConfig(
    filename="db_activity.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Database Connection Helper
def get_connection():
    return sqlite3.connect(DB_PATH)

# Create Database Tables
def create_tables():
    with get_connection() as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS real_sensor_data (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                sensor_id TEXT,
                value REAL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS simulation_data (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                simulation_id TEXT,
                predicted_value REAL
            )
        ''')
        conn.commit()
    logging.info("Database tables created or verified.")

# Insert Real Sensor Data
def insert_real_sensor_data(sensor_id, value):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO real_sensor_data (timestamp, sensor_id, value)
                VALUES (?, ?, ?)
            ''', (datetime.now().isoformat(), sensor_id, value))
            conn.commit()
        logging.info(f"Inserted real sensor data: sensor_id={sensor_id}, value={value}")
    except Exception as e:
        logging.error(f"Failed to insert real sensor data: {e}")

# Insert Simulation Data
def insert_simulation_data(simulation_id, predicted_value):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO simulation_data (timestamp, simulation_id, predicted_value)
                VALUES (?, ?, ?)
            ''', (datetime.now().isoformat(), simulation_id, predicted_value))
            conn.commit()
        logging.info(f"Inserted simulation data: simulation_id={simulation_id}, predicted_value={predicted_value}")
    except Exception as e:
        logging.error(f"Failed to insert simulation data: {e}")

# Get Latest Real Sensor Data
def get_latest_real_data(sensor_id):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT * FROM real_sensor_data
                WHERE sensor_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (sensor_id,))
            result = c.fetchone()
        logging.info(f"Fetched latest real sensor data for sensor_id={sensor_id}")
        return result
    except Exception as e:
        logging.error(f"Failed to fetch latest real sensor data: {e}")
        return None

# Get Latest Simulation Data
def get_latest_simulation_data(simulation_id):
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute('''
                SELECT * FROM simulation_data
                WHERE simulation_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (simulation_id,))
            result = c.fetchone()
        logging.info(f"Fetched latest simulation data for simulation_id={simulation_id}")
        return result
    except Exception as e:
        logging.error(f"Failed to fetch latest simulation data: {e}")
        return None

# Backup Database
def backup_database():
    try:
        os.makedirs(BACKUP_FOLDER, exist_ok=True)
        backup_file = os.path.join(
            BACKUP_FOLDER,
            f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        shutil.copy2(DB_PATH, backup_file)
        logging.info(f"Database backed up successfully to {backup_file}")
    except Exception as e:
        logging.error(f"Failed to backup database: {e}")

# (Optional) Schedule Backups Automatically
def start_auto_backup(interval_minutes=10):
    schedule.every(interval_minutes).minutes.do(backup_database)
    logging.info(f"Scheduled automatic database backups every {interval_minutes} minutes.")

    while True:
        schedule.run_pending()
        time.sleep(1)

# Example (delete this part later)
if __name__ == "__main__":
    create_tables()
    insert_real_sensor_data("sensor_1", 23.5)
    insert_simulation_data("sim_1", 24.0)
    print(get_latest_real_data("sensor_1"))
    print(get_latest_simulation_data("sim_1"))
    backup_database()

    # If you want auto-backup running:
    # start_auto_backup(interval_minutes=10)