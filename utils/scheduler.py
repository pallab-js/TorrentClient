"""
Simple bandwidth scheduler.
Define schedules in config as a list of entries:
[{"start": "23:00", "end": "07:00", "dl": 200, "ul": 50}]
Times are local 24h. Limits in KiB/s.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, time
from typing import List, Optional


def _parse_time(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


@dataclass
class ScheduleEntry:
    start: time
    end: time
    dl: int
    ul: int

    @classmethod
    def from_dict(cls, d: dict) -> "ScheduleEntry":
        return cls(start=_parse_time(d["start"]), end=_parse_time(d["end"]), dl=int(d["dl"]), ul=int(d["ul"]))


def pick_limits(now: Optional[datetime], schedules: List[dict]) -> Optional[ScheduleEntry]:
    """Pick active schedule entry for 'now'. Returns None if none match."""
    if now is None:
        now = datetime.now()
    current = now.time()
    entries = [ScheduleEntry.from_dict(d) for d in schedules]
    for e in entries:
        if e.start <= e.end:
            # same-day window
            if e.start <= current <= e.end:
                return e
        else:
            # overnight window (e.g., 23:00-07:00)
            if current >= e.start or current <= e.end:
                return e
    return None
