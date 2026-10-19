"""The minute clock of a turn.

A turn is a stretch of game minutes (two hours in the day). Things happen at their minute: somebody arrives and does what they came for, an attacker strikes when they and their
target are in the same room, the environment steps every five minutes, free time is reconsidered every quarter of an hour, conversations start when people have gathered. The
Timeline holds what is due and runs it in order of minute (ties in the order they were scheduled), setting the engine's minute cursor before each, so every event is stamped
with the minute it really happened and every question about positions is answered for that minute.

This is discrete-event time rather than a loop over all 120 minutes: nothing is computed for minutes in which nothing is due, but the order is the same.
"""
import heapq


class Timeline:
    def __init__(self, eng, dur=120):
        self.eng = eng
        self.dur = dur
        self.q = []
        self.n = 0

    def at(self, m, fn, *args, prio=5):
        """Run fn(*args) at minute m (prio breaks ties: lower first)."""
        self.n += 1
        heapq.heappush(self.q, (float(m), prio, self.n, fn, args))

    def every(self, period, fn, start=None, until=None, prio=3):
        """Run fn(m) every `period` minutes from `start` (default: one period in) up to `until` (default: the end of the turn), as a cadence."""
        m = float(period if start is None else start)
        end = float(self.dur if until is None else until)

        def step(mm):
            fn(mm)
            if mm + period <= end:
                self.at(mm + period, step, mm + period, prio=prio)
        if m <= end:
            self.at(m, step, m, prio=prio)

    def run(self, until=None):
        """Run everything due up to minute `until` (default: all of it)."""
        while self.q and (until is None or self.q[0][0] <= until):
            m, _, _, fn, args = heapq.heappop(self.q)
            self.eng.clock_to(m)
            fn(*args)


class ClockMixin:
    """The engine's minute cursor within the current turn."""

    def clock_start(self):
        self._m, self._turn_clock = 0.0, True

    def clock_stop(self):
        self._m, self._turn_clock = 0.0, False

    def clock_to(self, m):
        """Move the cursor forward to minute m (never back: the turn's systems run in time order)."""
        self._m = max(float(self.__dict__.get("_m") or 0.0), float(m))
        sm = self.__dict__.get("_sim")
        if sm is not None and sm.forward:
            sm.frontier = self._m                                   # nothing is laid before the engine's minute (sim.py, forward mode)
        return self._m

    def minute(self):
        """The minute of the current turn the engine is at (a free-time slice can pin it), or None outside a turn."""
        m = getattr(self, "_slice_m", None)
        if m is not None:
            return float(m)
        return float(self._m) if self.__dict__.get("_turn_clock") else None
