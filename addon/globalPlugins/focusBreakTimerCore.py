# -*- coding: UTF-8 -*-
"""Pure focus/break timer state machine.

This module intentionally has no NVDA imports so it can be unit-tested outside NVDA.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Phase(str, Enum):
    STOPPED = "stopped"
    FOCUS = "focus"
    BREAK = "break"
    PAUSED = "paused"


@dataclass(frozen=True)
class TimerEvent:
    kind: str
    cycle: int


@dataclass(frozen=True)
class TimerSnapshot:
    phase: Phase
    cycle: int
    remaining_seconds: int
    cycles_target: int
    paused_from: Phase | None


def minutes_from_hm(hour: int, minute: int) -> int:
    """Convert a 24-hour clock value to minutes since midnight."""
    if not 0 <= int(hour) <= 23:
        raise ValueError("hour must be between 0 and 23")
    if not 0 <= int(minute) <= 59:
        raise ValueError("minute must be between 0 and 59")
    return int(hour) * 60 + int(minute)


def is_minute_in_daily_window(current_minute: int, start_minute: int, end_minute: int) -> bool:
    """Return whether a local clock minute falls in a half-open daily window.

    ``start == end`` means the schedule is disabled for the whole day (zero-length
    window), not a 24-hour suspension. Windows that cross midnight are supported,
    e.g. 22:00 -> 06:00.
    """
    current = int(current_minute) % (24 * 60)
    start = int(start_minute) % (24 * 60)
    end = int(end_minute) % (24 * 60)
    if start == end:
        return False
    if start < end:
        return start <= current < end
    return current >= start or current < end


class FocusBreakEngine:
    """Deterministic state machine driven by a monotonic clock supplied by the caller."""

    def __init__(self, focus_seconds: int, break_seconds: int, cycles: int = 0):
        if focus_seconds <= 0 or break_seconds <= 0:
            raise ValueError("focus_seconds and break_seconds must be greater than zero")
        if cycles < 0:
            raise ValueError("cycles cannot be negative")
        self.focus_seconds = int(focus_seconds)
        self.break_seconds = int(break_seconds)
        self.cycles_target = int(cycles)
        self.phase = Phase.STOPPED
        self.cycle = 0
        self._deadline: float | None = None
        self._paused_from: Phase | None = None
        self._paused_remaining = 0.0

    def set_cycles_target(self, cycles: int) -> None:
        """Change the repetition target without resetting the current phase.

        ``0`` means repeat indefinitely. A positive value is the total cycle count.
        The caller is responsible for choosing a target that makes sense for the
        current cycle; the engine will stop at the next completed break once the
        current cycle reaches the target.
        """
        if cycles < 0:
            raise ValueError("cycles cannot be negative")
        self.cycles_target = int(cycles)

    def start(self, now: float) -> list[TimerEvent]:
        self.phase = Phase.FOCUS
        self.cycle = 1
        self._paused_from = None
        self._paused_remaining = 0.0
        self._deadline = now + self.focus_seconds
        return [TimerEvent("focus_started", self.cycle)]

    def stop(self) -> list[TimerEvent]:
        was_running = self.phase != Phase.STOPPED
        old_cycle = self.cycle
        self.phase = Phase.STOPPED
        self.cycle = 0
        self._deadline = None
        self._paused_from = None
        self._paused_remaining = 0.0
        return [TimerEvent("stopped", old_cycle)] if was_running else []

    def pause(self, now: float) -> list[TimerEvent]:
        if self.phase not in (Phase.FOCUS, Phase.BREAK):
            return []
        assert self._deadline is not None
        self._paused_from = self.phase
        self._paused_remaining = max(0.0, self._deadline - now)
        self.phase = Phase.PAUSED
        self._deadline = None
        return [TimerEvent("paused", self.cycle)]

    def resume(self, now: float) -> list[TimerEvent]:
        if self.phase != Phase.PAUSED or self._paused_from is None:
            return []
        restored = self._paused_from
        self.phase = restored
        self._deadline = now + self._paused_remaining
        self._paused_from = None
        self._paused_remaining = 0.0
        return [TimerEvent("resumed", self.cycle)]

    def tick(self, now: float) -> list[TimerEvent]:
        events: list[TimerEvent] = []
        # Catch up safely if the computer slept or the event loop was delayed.
        while self.phase in (Phase.FOCUS, Phase.BREAK) and self._deadline is not None and now >= self._deadline:
            transition_time = self._deadline
            if self.phase == Phase.FOCUS:
                self.phase = Phase.BREAK
                self._deadline = transition_time + self.break_seconds
                events.append(TimerEvent("break_started", self.cycle))
                continue

            # A break just finished.
            events.append(TimerEvent("break_finished", self.cycle))
            if self.cycles_target and self.cycle >= self.cycles_target:
                finished_cycle = self.cycle
                self.phase = Phase.STOPPED
                self.cycle = 0
                self._deadline = None
                events.append(TimerEvent("completed", finished_cycle))
                break

            self.cycle += 1
            self.phase = Phase.FOCUS
            self._deadline = transition_time + self.focus_seconds
            events.append(TimerEvent("focus_started", self.cycle))
        return events

    def remaining_seconds(self, now: float) -> int:
        if self.phase == Phase.PAUSED:
            return max(0, int(self._paused_remaining + 0.999))
        if self.phase in (Phase.FOCUS, Phase.BREAK) and self._deadline is not None:
            return max(0, int((self._deadline - now) + 0.999))
        return 0

    def snapshot(self, now: float) -> TimerSnapshot:
        return TimerSnapshot(
            phase=self.phase,
            cycle=self.cycle,
            remaining_seconds=self.remaining_seconds(now),
            cycles_target=self.cycles_target,
            paused_from=self._paused_from,
        )
