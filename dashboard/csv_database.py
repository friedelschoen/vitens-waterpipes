import io
import os
import time
from typing import Any, Iterator


def unflatten_dict(columns: list[str], values: list[float]) -> dict[str, Any]:
    s = {}
    for i, key in enumerate(columns):
        cur = s
        *attrs, last = key.split('.')
        for attr in attrs:
            cur = cur.setdefault(attr, {})
        cur[last] = values[i]
    return s


def flatten_dict(d: dict[str, Any], prefix: str = "") -> dict[str, float]:
    flat = {}
    for key, value in d.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_dict(value, full_key))
        else:
            flat[full_key] = value
    return flat


class Cursor:
    def __init__(self, db: "CSVDatabase", fp: io.TextIOBase):
        self.db = db
        self.file = fp
        self._closed = False

    def __enter__(self) -> "Cursor":
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def close(self):
        if not self._closed:
            self.file.close()
            self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    def read(self) -> dict[str, Any] | None:
        line = self.file.readline()
        if line == "":
            return None
        values = [float(v) for v in line.rstrip("\r\n").split(',')]
        return unflatten_dict(self.db.columns, values)

    def read_many(self, count=-1) -> Iterator[dict[str, Any]]:
        done = 0
        while done < count:
            row = self.read()
            if row is None:
                break
            yield row

    def __iter__(self) -> Iterator[dict[str, Any]]:
        while True:
            row = self.read()
            if row is None:
                break
            yield row


class CSVDatabase:
    def __init__(self, filename: str, *, index_col="id", timestamp_col="timestamp"):
        self.filename = filename
        self.index_col = index_col
        self.timestamp_col = timestamp_col

        self.columns: list[str] = []
        self.begin_pos = 0
        self.next_index = 0
        self.read_cursor = 0

        try:
            self._find_header()
        except FileNotFoundError:
            # that's ok, we'll initalize later
            pass

    def _find_header(self):
        with open(self.filename) as f:
            header = f.readline()
            if not header:
                return  # leeg bestand

            self.columns = header.rstrip("\r\n").split(',')
            if self.index_col not in self.columns:
                raise KeyError(
                    f"database does not contain index column `{self.index_col}`")
            if self.timestamp_col not in self.columns:
                raise KeyError(
                    f"database does not contain timestamp column `{self.timestamp_col}`")

            self.begin_pos = f.tell()
            self.read_cursor = self.begin_pos

            idx_index = self.columns.index(self.index_col)

            last_id: int | None = None
            for line in f:
                parts = line.rstrip("\r\n").split(',')
                if len(parts) <= idx_index:
                    continue
                try:
                    last_id = int(parts[idx_index])
                except ValueError:
                    continue

            if last_id is not None:
                self.next_index = last_id + 1
            else:
                self.next_index = 0

    def _make_cursor(self, ts_index: int, target: float) -> Cursor:
        # begin_pos == 0 -> no header yet, empty file
        if self.begin_pos == 0:
            return Cursor(self, io.StringIO())

        f = open(self.filename)

        f.seek(0, os.SEEK_END)
        file_size = f.tell()

        lo = self.begin_pos
        hi = file_size

        # beste offset tot nu toe (ts <= target)
        best_pos = self.begin_pos

        while lo < hi:
            mid = (lo + hi) // 2
            f.seek(mid)

            # Spring naar begin van volgende regel (skip partial line)
            if mid != self.begin_pos:
                f.readline()

            pos = f.tell()
            line = f.readline()
            if not line:
                # We zaten voorbij het eind; schuif hi naar links
                hi = mid
                continue

            try:
                text = line.rstrip("\r\n")
                parts = text.split(",")
                ts = float(parts[ts_index])
            except Exception:
                # Rare regel → schuif wat naar links
                hi = mid
                continue

            if ts <= target:
                # Deze rij is geldig (<= target), onthouden en rechts verder zoeken
                best_pos = pos
                lo = f.tell()  # verder zoeken na deze regel
            else:
                # ts > target → links zoeken
                hi = mid

        f.seek(best_pos)
        return Cursor(self, f)

    def cursor_begin(self) -> Cursor:
        if self.begin_pos == 0:
            return Cursor(self, io.StringIO())

        f = open(self.filename)
        f.seek(self.begin_pos)
        return Cursor(self, f)

    def cursor_since(self, timestamp: float) -> Cursor:
        return self._make_cursor(self.columns.index(self.timestamp_col), timestamp)

    def cursor_index(self, index: float) -> Cursor:
        return self._make_cursor(self.columns.index(self.index_col), index)

    def insert(self, sensor_values: dict[str, Any]):
        sensor_values = flatten_dict(sensor_values)
        sensor_values[self.index_col] = self.next_index
        sensor_values[self.timestamp_col] = time.time()
        self.next_index += 1

        with open(self.filename, "a") as output:
            # no header?
            if self.begin_pos == 0:
                self.columns = [self.index_col, self.timestamp_col]
                for key in sensor_values.keys():
                    if key not in [self.index_col, self.timestamp_col]:
                        self.columns.append(key)

                line = ",".join(self.columns) + "\n"
                output.write(line)
                self.begin_pos = len(line)
                self.read_cursor = self.begin_pos

            values = [sensor_values.get(key, 0) for key in self.columns]
            output.write(",".join(str(v) for v in values) + "\n")

            notwrite = [c for c in sensor_values.keys()
                        if c not in self.columns]
            if len(notwrite):
                print("[warn] not writing values: " + ", ".join(notwrite))
