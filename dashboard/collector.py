from itertools import product
import time
from typing import Any, Iterable

from dashboard.csv_database import CSVDatabase
from dashboard.valve import ValveState


class Collector:
    interval: int
    todo: list[dict[str, ValveState]]
    next_run: float
    db: CSVDatabase | None
    path: str
    done: int

    def __init__(self, interval: int, path: str):
        self.interval = interval
        self.done = 0
        self.todo = []
        self.next_run = 0
        self.path = path
        self.db = None

    @property
    def active(self) -> bool:
        return len(self.todo) > 0 or self.next_run > 0

    @property
    def progress(self) -> float:
        curtime = time.time()
        # hoe lang nog in huidige interval?
        if self.next_run > 0:
            remain_current = max(0.0, self.next_run - curtime)
            elapsed_current = self.interval - remain_current
        else:
            remain_current = 0.0
            elapsed_current = 0.0

        doing = remain_current + len(self.todo) * self.interval
        timedone = self.done * self.interval + \
            max(0.0, min(self.interval, elapsed_current))

        total = doing + timedone
        if total <= 0:
            return 0.0

        return timedone / total

    @property
    def timeleft(self) -> float:
        curtime = time.time()
        return (self.next_run - curtime) + len(self.todo)*self.interval

    def start(self, valves: list[str]):
        self.todo = [
            dict(zip(valves, states)) for states in product(ValveState, repeat=len(valves))
        ]
        self.next_run = time.time() + self.interval
        timestr = time.strftime('%Y-%m-%d_%H:%M:%S')
        self.db = CSVDatabase(self.path.replace("%", timestr), read=False)
        self.done = 0

    def cancel(self):
        self.db = None
        self.todo = []
        self.next_run = 0

    def pop(self) -> dict[str, ValveState]:
        curtime = time.time()
        if self.next_run > 0 and curtime > self.next_run:
            if len(self.todo) == 0:
                self.next_run = 0
                self.db = None
                return {}
            self.done += 1
            self.next_run = curtime + self.interval
            todo = self.todo.pop(0)
            print(
                f"[collect] doing {todo}, still to do {len(self.todo)}")
            return todo
        return {}
