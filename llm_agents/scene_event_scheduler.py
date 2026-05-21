"""
Scene Event Scheduler

A tiny utility to schedule time-based scene events (e.g., train/bus arrivals) based on
simulation time (seconds). MAIN orchestrates decisions; this module only stores and
retrieves due events.
"""
from __future__ import annotations
from typing import List, Dict


class SceneEventScheduler:
    def __init__(self) -> None:
        self._events: List[Dict] = []

    def schedule_arrival(self, label: str, after_minutes: int, now_seconds: int) -> None:
        """Schedule an arrival event after N minutes from now_seconds."""
        trigger = int(now_seconds) + int(after_minutes * 60)
        self._events.append({
            'type': 'arrival',
            'label': label,
            'trigger': trigger,
        })

    def reschedule_arrival(self, label: str, after_minutes: int, now_seconds: int) -> None:
        """Convenience to schedule another arrival in the future (e.g., next stop)."""
        self.schedule_arrival(label, after_minutes, now_seconds)

    def check_due(self, now_seconds: int) -> List[Dict]:
        """Return a list of events that are due at or before now_seconds, and remove them from the queue."""
        due: List[Dict] = []
        remaining: List[Dict] = []
        for ev in self._events:
            if int(ev.get('trigger', 0)) <= int(now_seconds):
                due.append(ev)
            else:
                remaining.append(ev)
        self._events = remaining
        return due

    def clear(self) -> None:
        self._events.clear()
