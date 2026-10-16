"""The auto-director: when the island goes quiet, it nudges the story along (a TereVi dare, a rumour, an unsigned note or an island event).

DirectorMixin is mixed into DayRunner (engine.py). It can be switched on and off while a day is running.
"""

NOTABLE = {"attack", "assault", "betrayal", "leak", "madness", "body", "punish", "sabotage", "outburst", "incite", "rumor", "mishap", "island", "director"}
RUMORS = ["{x} has been going through other people's things when nobody is looking",
          "{x} was seen near the Study in the middle of the night",
          "{x} told someone they would rather another person took the fall",
          "{x} has been planning something with someone and keeps it from the rest",
          "{x} is not nearly as scared as they pretend to be"]
NOTES = ["Someone in this house is counting on you being the first to break.",
         "Not everyone you trust has earned it. Watch who stops looking you in the eye.",
         "You are being watched, and not only by the cameras.",
         "One of the people you call a friend has already decided what to do about you."]
PROVOKE = ["Nothing has happened for hours and the audience is bored. Stir things up: dare someone to do something unwise, or announce a game with real stakes.",
           "The house is too calm. Offer someone a tempting bargain with a cruel price, on air, and watch who bites.",
           "The mood is flat. Announce a surprise that forces two people who dislike each other into the same room."]
EVENTS = ["fog", "package", "power", "storm", "cat"]


def _hh(h):
    return f"{h:02d}:00"


class DirectorMixin:
    def director_init(self, enabled=False, getter=None):
        self._autodir = bool(enabled)
        self._autodir_get = getter
        self.quiet = 0
        self.dir_used = 0

    @property
    def auto_dir(self):
        return bool(self._autodir_get()) if self._autodir_get else self._autodir

    def director_after_tick(self, tick, hour):
        """Count quiet turns; after a few, step in (at most twice a day, never during a case, a spree or the evening)."""
        if not self.auto_dir or not self.revealed or self.s.get("over"):
            return
        busy = sum(1 for e in tick["events"] if e["type"] in NOTABLE)
        self.quiet = max(0, self.quiet - 1) if busy else self.quiet + 1
        if (self.quiet < 3 or self.dir_used >= 2 or self.s.get("case") or self.s.get("spree") or hour >= 20 or len(self.world.agents) < 4):
            return
        self.quiet = 0
        self.dir_used += 1
        self.director_act(tick, hour)

    def director_act(self, tick, hour):
        w = self.world
        ids = list(w.agents)
        san, aff = self.collapse_metrics()
        opts = [("provoke", 3.0), ("rumor", 3.0 if aff > -1 else 1.0), ("note", 2.0), ("event", 1.5)]
        r = self.rng.random() * sum(x[1] for x in opts)
        kind = opts[0][0]
        for k, wt in opts:
            r -= wt
            if r <= 0:
                kind = k
                break
        text = ""
        if kind == "provoke":
            self.force_tease = self.rng.choice(PROVOKE)
            text = "TereVi is told the island is too quiet and sets out to stir things up."
        elif kind == "rumor" and len(ids) >= 3:
            x, y, z = self.rng.sample(ids, 3)
            claim = self.rng.choice(RUMORS).format(x=self.nm(x))
            ok = self.spread_rumor(tick, "unknown", x, claim, "bad", self.rng.random() < 0.5, [y, z], w.agents[y]["room"], hour)
            text = f"An anonymous rumour about {self.nm(x)} starts to circulate." if ok else ""
        elif kind == "note":
            tgt = min(ids, key=lambda c: sum(w.agents[c]["aff"].get(o, 0) for o in ids if o != c) + w.agents[c]["sanity"] * 0.05)
            note = self.rng.choice(NOTES)
            w.remember(tgt, f"{_hh(hour)} You find an unsigned note: \"{note}\"")
            self.moment(tgt, f"found an unsigned note: {note[:60]}")
            text = f"An unsigned note turns up for {self.nm(tgt)}."
        else:
            self.force_island = self.rng.choice(EVENTS)
            text = f"The island itself is nudged: a {self.force_island} is coming."
        if not text:
            self.force_tease = self.rng.choice(PROVOKE)
            text = "TereVi is told the island is too quiet and sets out to stir things up."
        self.log_event(tick, {"type": "director", "who": "terevi", "room": "foyer", "vis": "viewer", "text": "Auto-director: " + text})
        self.day_notable.append("The auto-director stepped in: " + text[:80])
