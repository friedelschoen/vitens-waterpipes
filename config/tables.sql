CREATE TABLE IF NOT EXISTS sample (
  id            INTEGER PRIMARY KEY,
  timestamp     REAL NOT NULL,
  device        TEXT NOT NULL DEFAULT 'pi-01'
);

CREATE TABLE IF NOT EXISTS measurement (
  sample        INTEGER NOT NULL REFERENCES sample(id) ON DELETE CASCADE,
  algorithm     TEXT NOT NULL,
  name          TEXT NOT NULL,
  unit          TEXT,
  value         REAL NOT NULL,
  PRIMARY KEY (sample, algorithm, name)
);

CREATE TABLE IF NOT EXISTS valve (
  sample        INTEGER NOT NULL REFERENCES sample(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  state         INTEGER NOT NULL,
  wants         INTEGER NOT NULL,
  PRIMARY KEY (sample, name)
);

CREATE INDEX IF NOT EXISTS idx_sample_timestamp ON sample(timestamp);
CREATE INDEX IF NOT EXISTS idx_sample_device_id_desc ON sample(device, id DESC);
CREATE INDEX IF NOT EXISTS idx_measurement_sample_name_algo ON measurement(sample, name, algorithm);
CREATE INDEX IF NOT EXISTS idx_valve_sample ON valve(sample);
CREATE INDEX IF NOT EXISTS idx_valve_sample_name ON valve(sample, name);
