from itertools import product
import time

from .csv_database import CSVDatabase
from .valve import ValveState


class Collector:
    interval: int
    todo: list[dict[str, ValveState]]
    next_run: float
    db: CSVDatabase | None
    path: str
    done: int
    pause_since: float | None
    group: dict[str, int]

    def __init__(self, interval: int, path: str, groups: dict[str, int]):
        self.interval = interval
        self.done = 0
        self.todo = []
        self.next_run = 0
        self.path = path
        self.db = None
        self.pause_since = None
        self.groups = groups

    @property
    def active(self) -> bool:
        return len(self.todo) > 0 or self.next_run > 0

    @property
    def progress(self) -> float:
        curtime = time.time()

        # Als we gepauzeerd zijn: freeze progress
        if self.pause_since is not None:
            curtime = self.pause_since

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
        if self.pause_since is not None:
            curtime = self.pause_since

        return (self.next_run - curtime) + len(self.todo) * self.interval

    def pause(self, flag: bool):
        if flag and self.pause_since is None:
            self.pause_since = time.time()
            print("[collect] paused")

        elif not flag and self.pause_since is not None:
            # Einde pauze → verschuif next_run
            paused_for = time.time() - self.pause_since
            self.next_run += paused_for

            self.pause_since = None
            print(f"[collect] resumed after {paused_for:.2f}s pause")

    def check_group_closed(self, valves: list[str], states: tuple[ValveState, ...]):
        groups = {}
        for i, valve in enumerate(valves):
            if valve not in self.groups:
                continue
            state = states[i]
            group = self.groups[valve]
            if group not in groups:
                groups[group] = 0
            if state != ValveState.CLOSED:
                groups[group] += 1
        return not any(n == 0 for n in groups.values())

    def start(self, valves: list[str]):
        self.todo = [
            dict(zip(valves, states))
            for states in product(ValveState, repeat=len(valves))
            if self.check_group_closed(valves, states)
        ]
        self.next_run = time.time()
        timestr = time.strftime('%Y-%m-%d_%H:%M:%S')
        self.db = CSVDatabase(self.path.replace("%", timestr))
        self.done = 0
        self.pause_since = None

    def cancel(self):
        self.db = None
        self.todo = []
        self.next_run = 0
        self.pause_since = None

    def pop(self) -> dict[str, ValveState]:
        # Als collector gepauzeerd is → doe niets
        if self.pause_since is not None:
            return {}

        curtime = time.time()
        if self.next_run > 0 and curtime > self.next_run:
            if len(self.todo) == 0:
                self.next_run = 0
                self.db = None
                return {}

            self.done += 1
            self.next_run = curtime + self.interval
            todo = self.todo.pop(0)
            print(f"[collect] doing {todo}, still to do {len(self.todo)}")
            return todo

        return {}
