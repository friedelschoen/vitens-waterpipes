import sqlite3
from datetime import datetime

DB_PATH = "sensor_data.db"

# Create tables
def create_tables():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS real_sensor_data (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                flow_1, flow_2, flow_3, flow_4, flow_5,
                pressure_1, pressure_2, pressure_3,
                pressure_4, pressure_5, pressure_6
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS simulation_data (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                flow_5, pressure_6
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS valve_states (
                id INTEGER PRIMARY KEY,
                valve_number INTEGER UNIQUE,
                state INTEGER, -- 0 = closed, 1 = open
                updated_at TEXT
            )
        """)
        conn.commit()
    
def insert_real_sensor_row(sensor_values: dict):
    sensor_values = dict(sensor_values)
    sensor_values.pop("timestamp", None)
    if not sensor_values:
        raise ValueError("sensor_values cannot be empty")
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        columns = ', '.join(sensor_values.keys())
        placeholders = ', '.join(['?'] * len(sensor_values))
        values = list(sensor_values.values())
        c.execute(f"""
            INSERT INTO real_sensor_data (timestamp, {columns})
            VALUES (?, {placeholders})
        """, [datetime.now().isoformat()] + values)
        conn.commit()

def insert_simulation_row(sensor_values: dict):
    sensor_values = dict(sensor_values)
    sensor_values.pop("timestamp", None)
    if not sensor_values:
        raise ValueError("sensor_values cannot be empty")
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        columns = ', '.join(sensor_values.keys())
        placeholders = ', '.join(['?'] * len(sensor_values))
        values = list(sensor_values.values())
        c.execute(f"""
            INSERT INTO simulation_data (timestamp, {columns})
            VALUES (?, {placeholders})
        """, [datetime.now().isoformat()] + values)
        conn.commit()

# Get the latest real data row
def get_latest_real_row():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM real_sensor_data ORDER BY timestamp DESC LIMIT 1")
        return c.fetchone()

# Get the latest simulated data row
def get_latest_simulation_row():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM simulation_data ORDER BY timestamp DESC LIMIT 1")
        return c.fetchone()

def set_valve_state(valve_number: int, state: int):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO valve_states (valve_number, state, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(valve_number) DO UPDATE SET
                state=excluded.state,
                updated_at=excluded.updated_at
        """, (valve_number, state, datetime.now().isoformat()))
        conn.commit()

def get_valve_states():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT valve_number, state FROM valve_states ORDER BY valve_number")
        return dict(c.fetchall())
