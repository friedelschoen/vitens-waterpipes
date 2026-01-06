# Vitens MQTT Dashboard + Storage + Replay

This project is a small distributed system around MQTT telemetry:

* A **sensor daemon** publishes live telemetry for a device (typically a Raspberry Pi).
* An **inserter** subscribes to telemetry, stores it in SQLite, and also stores “predicted” values from ML models.
* A **dashboard API server** serves a web UI and exposes REST endpoints for recent sensor data, valve states, and controlling collector/replay via MQTT.
* A **collector** can run a measurement campaign and outputs CSV files while driving valves through MQTT.
* A **replay** tool re-publishes historical SQLite samples back onto MQTT in (roughly) real-time.

## Architecture overview

```
[sensordaemon]  --MQTT-->  [inserter]  --SQLite--> vitens.db
      |                         ^
      |                         |
      +--MQTT--> [collector] ---+
      |
      +--MQTT--> [dashboard/api_server] <--HTTP--> browser
                             |
                             +--MQTT--> control collector/replay/valves
                             |
                             +--MQTT status subscriptions
```

## Components

### `sensordaemon/daemon.py`

Publishes telemetry every `LOOP_DELAY` seconds (default: 1s).

* Detects ADC devices (ADS1015) and GPIO flow sensors/valves when available.
* Falls back to randomized sensor values when hardware is not present.
* Tracks `last_valve_change` as seconds since the last valve state change.

Publishes:

* `vitens/pi/<device>/telemetry`

Subscribes:

* `vitens/pi/<device>/set_valves` (to apply desired valve state changes)

### `inserter/inserter.py`

Consumes telemetry and stores it in `vitens.db`:

* Inserts a row into `sample` with `timestamp` and `device`.
* Inserts valves into `valve`.
* Runs multiple predictors (including passthrough) and stores each result in `measurement` with an `algorithm` name.

Subscribes:

* `vitens/pi/+/telemetry`

Writes:

* SQLite database `vitens.db`

### `dashboard/api_server.py`

Flask server exposing:

* Static dashboard UI under `/` (serves `dashboard/static/index.html`)
* REST API endpoints
* MQTT control publishing + status subscriptions

It **only returns recent sensor data**: it clamps `since` to a rolling window:

* `SENSOR_FRAME = 5 * 60` seconds (5 minutes)

Subscribes:

* `vitens/#` (to receive status)

Publishes:

* valve control and collector/replay control messages

### `collector/collector.py`

Runs a collection routine per device:

* Learns valve grouping from incoming telemetry’s `valves` dict.
* Generates a sequence of valve configurations (0/1) with a constraint:

  * valves in the same group must **not** all be closed simultaneously.
* When active, on every telemetry message it:

  * pauses if valves aren’t yet in desired state (`wants != state`)
  * publishes the next desired valve configuration
  * logs measurements into a CSV file under `collect/`
  * publishes progress status

Subscribes:

* `vitens/pi/+/telemetry`
* `vitens/collector/activate`
* `vitens/collector/deactivate`

Publishes:

* `vitens/pi/<device>/set_valves`
* `vitens/collector/status`

### `replay/replay.py`

Replays stored database data back into MQTT:

* Reads `sample`, `measurement`, and `valve` from `vitens.db`
* For each sample >= `timestamp`, it publishes a telemetry message to a “virtual device”

  * device is prefixed as `replay!<device>`
* Sleeps according to timestamp deltas to mimic real-time pacing
* Emits replay status updates while running

Subscribes:

* `vitens/replay/activate`
* `vitens/replay/deactivate`

Publishes:

* `vitens/pi/replay!<device>/telemetry`
* `vitens/replay/status`

## MQTT topics and payloads

### Telemetry publish (from sensordaemon and replay)

**Topic**

* `vitens/pi/<device>/telemetry`

**Payload (JSON)**

```json
{
  "device": "raspberrypi",
  "measurements": {
    "sensor.flow0": [1.23, "L/min"],
    "sensor.pressure0": [2.34, "bar"],
    "valve.valve0": [1, null],
    "last_valve_change": [12.4, null]
  },
  "valves": {
    "valve0": { "group": -1, "wants": 1, "state": 1 },
    "bigvalve0": { "group": 0, "wants": 1, "state": 1 }
  }
}
```

Notes:

* `measurements` values are always `[value, unit]` pairs.
* Unit can be `null` for non-physical values.
* `valves` is a dict keyed by valve name, containing `group`, `wants`, `state`.

### Valve control publish (from dashboard/collector → sensordaemon)

**Topic**

* `vitens/pi/<device>/set_valves`

**Payload (JSON)**

```json
{
  "valves": {
    "valve0": { "wants": 1 },
    "valve1": { "state": 0 }
  }
}
```

Meaning:

* `wants` indicates the desired state (controller intent).
* `state` indicates a forced/actual state (used for testing).

### Collector control

**Activate**

* Topic: `vitens/collector/activate`
* Payload:

```json
{ "device": "raspberrypi" }
```

**Deactivate**

* Topic: `vitens/collector/deactivate`
* Payload:

```json
{ "device": "raspberrypi" }
```

**Status**

* Topic: `vitens/collector/status`
* Payload (active example):

```json
{
  "device": "raspberrypi",
  "active": true,
  "dbname": "collect/collect-raspberrypi-2025-12-19_12:34:56.csv",
  "progress": 0.42,
  "time": 123.4
}
```

### Replay control

**Activate**

* Topic: `vitens/replay/activate`
* Payload:

```json
{ "device": "raspberrypi", "timestamp": 1734600000 }
```

**Deactivate**

* Topic: `vitens/replay/deactivate`
* Payload:

```json
{ "device": "raspberrypi" }
```

**Status**

* Topic: `vitens/replay/status`
* Payload:

```json
{
  "device": "raspberrypi",
  "active": true,
  "timestamp": 1734600123.45,
  "progress": 0.12
}
```

## HTTP API (Dashboard)

Base URL: `http://localhost:5000`

### `GET /`

Redirects to the static dashboard (`index.html`).

### `GET /api/sensors?since=<unix_seconds>`

Returns recent sensor history from SQLite for **all devices**, grouped by device → sensor_name → algorithm.

* If `since` is older than 5 minutes, the server clamps it to “now - 5 minutes”.

Response shape:

```json
{
  "raspberrypi": {
    "sensor.flow0": {
      "none": [
        { "timestamp": 1734600123.4, "value": 1.2, "unit": "L/min" }
      ],
      "ae": [
        { "timestamp": 1734600123.4, "value": 1.1, "unit": "L/min" }
      ]
    }
  }
}
```

### `GET /api/valves`

Returns the latest known valve state per device (based on latest `sample.id`).

Response shape:

```json
{
  "raspberrypi": {
    "valve0": { "timestamp": 1734600123.4, "state": 1, "wants": 1 }
  }
}
```

### `POST /api/valves`

Sets a single valve to `open` or `close` for a device, via MQTT.

Request:

```json
{ "device": "raspberrypi", "valve": "valve0", "state": "open" }
```

Response:

```json
{ "error": null }
```

### `GET /api/collector`

Returns current collector status map.

### `POST /api/collector`

Starts collector for a device (publishes MQTT activate message).

Request:

```json
{ "device": "raspberrypi" }
```

### `POST /api/collector/stop`

Stops collector for a device.

Request:

```json
{ "device": "raspberrypi" }
```

### `GET /api/replay`

Returns current replay status map.

### `POST /api/replay`

Starts replay from a given timestamp.

Request:

```json
{ "device": "raspberrypi", "timestamp": 1734600000 }
```

### `POST /api/replay/stop`

Stops replay for a device.

Request:

```json
{ "device": "raspberrypi" }
```

## Model training

### `modeltrainer/create_model.py`

Trains and exports multiple reconstruction models from a CSV dataset (`data.csv`).

Example:

```bash
python3 modeltrainer/create_model.py --csv modeltrainer/data.csv --output dashboard/model
```

This creates model artifacts under `dashboard/model/`:

* `ae.keras` + `ae.json`
* `rf.joblib` + `rf.json`
* `lin.joblib` + `lin.json`
* `ridge.joblib` + `ridge.json`
* `lasso.joblib` + `lasso.json`

These are loaded by `inserter/predictor.py` and used at ingest time.

## Running locally

Prereqs:

* Python 3
* SQLite 3
* yarnpkg webpack (bundle.js)
* MQTT broker (e.g. Mosquitto) on `localhost:1883`
* Install dependencies:

```bash
pip install -r requirements.txt
```

If not done yet, create a database:
```bash
sqlite3 data/vitens.db < config/tables.sql
```

Setup webpack:
```bash
cd dashboard
yarnpkg install
yarnpkg exec webpack
```

Running (testing/debugging):

```
docker compose --profile=debug up --build
```

Running (production):

```
docker compose up --build
```
