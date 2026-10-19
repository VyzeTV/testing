"""Habits: one thing leading to the next, getting dirty and washing, and the small routines of a day.

Free time scores each activity mostly on its own, so without this a cook never sat down to the meal they made and someone back from a fight went straight to the chess board.
* Follow-ups: finishing some activities leaves a short-lived pull towards the natural next one (cook, then eat; a swim or a workout, then a shower; a meal, then washing up for the
  tidy). It is a pull, not a rule: a scream, a summons or a stronger need still wins. Kept in `a["next"]` and used once.
* Dirt: work on a way out, the garden, the woods, a fire and a killing leave someone muddy, sweaty, sandy, greasy, sooty or with blood on their hands (`a["dirt"]`). It shows in how they
  look (`looks_line`), it costs hygiene, and it pulls them to wash. A sink washes off sweat, sand and blood on the hands; mud, grease and soot need a shower or a bath. Scrubbing
  blood off at a sink in front of others is seen and remembered.
* Routines: a wash in the morning and before bed, more for the orderly, and one signature habit per person from their nature (a morning swim, tea at four, reading before bed),
  done once a day in its hours (`habit_of`).
HabitMixin is mixed into DayRunner (engine.py); free time calls `habit_options` and `habit_after` (freetime.py).
"""
from .gridnav import _h

# kind: (how it looks, hygiene it costs, washed off at a sink)
DIRT = {"sweat": ("sweaty", 12, True), "sand": ("sandy", 10, True), "mud": ("muddy", 25, False), "grease": ("streaked with grease", 20, False),
        "soot": ("smeared with soot", 30, False), "blood": ("with blood on their hands", 30, True)}
# act -> (dirt kind, chance), or a function of the room
DIRTY_WORK = {"tend": ("mud", 0.5), "fight": ("soot", 0.9), "rescue": ("soot", 0.9), "tinker": ("grease", 0.4), "exercise": ("sweat", 0.9), "dig": ("mud", 0.9)}
# act -> (next act, pull, minutes it lasts, why)
FOLLOW = {"cook": ("eat", 1.7, 75, "eating what they cooked"), "swim": ("shower", 1.5, 60, "rinsing off after a swim"),
          "exercise": ("shower", 1.4, 60, "a shower after a workout"), "eat": ("wash", 0.6, 30, "washing up after the meal")}
# signature habits: (act, hours of the day it belongs to, label, the facets that make it someone's)
HABITS = [("swim", (8, 10), "a morning swim", ("courage", "vanity")),
          ("exercise", (8, 10), "a morning workout", ("courage", "orderliness")),
          ("tend", (8, 10), "watering the plants first thing", ("altruism", "orderliness")),
          ("drink", (16,), "a cup of tea at four", ("orderliness", "humour")),
          ("stroll", (14, 16), "an afternoon walk alone", ("privacy", "curiosity")),
          ("music", (18, 20), "playing after dinner", ("vanity", "romantic")),
          ("sunset", (18,), "watching the sun go down", ("romantic", "curiosity")),
          ("read", (20,), "reading before bed", ("curiosity", "orderliness")),
          ("journal", (20,), "writing in a journal at night", ("romantic", "stress_vulnerability"))]


class HabitMixin:
    # ------------------------------------------------------------------ dirt
    def get_dirty(self, cid, kind):
        a = self.world.agents.get(cid)
        if not a or kind not in DIRT:
            return
        old = (a.get("dirt") or {}).get("kind")
        if old and DIRT[old][1] > DIRT[kind][1] and old != "sweat":
            kind = old                                                  # the worse dirt is what shows
        a["dirt"] = {"kind": kind, "day": self.day}
        b = self.body(cid)
        b["hygiene"] = max(0, b["hygiene"] - DIRT[kind][1])

    def dirt_look(self, cid):
        """How the dirt looks ('muddy'), or ''."""
        d = (self.world.agents.get(cid) or {}).get("dirt")
        return DIRT[d["kind"]][0] if d and d.get("kind") in DIRT else ""

    def wash_off(self, tick, cid, act, m):
        """A wash, a shower or a bath takes the dirt off (a sink only the light kinds). Blood scrubbed off at a sink in company is seen."""
        w = self.world
        a = w.agents[cid]
        d = a.get("dirt")
        if not d:
            return
        if act == "wash" and not DIRT[d["kind"]][2]:
            return
        a.pop("dirt", None)
        if d["kind"] == "blood" and act == "wash":
            here = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid and not w.agents[o].get("asleep")]
            if here:
                when = f"{(tick['hour'] * 60 + int(m)) // 60 % 24:02d}:{int(m) % 60:02d}"
                self._fev(tick, cid, m, f"{self.nm(cid)} scrubs blood off their hands at the sink in the {w.room_name(a['room'])}.", "free", "public", witnesses=here)
                for o in here:
                    w.remember(o, f"{when} (saw) {self.nm(cid)} scrubbing blood off their hands at the sink in the {w.room_name(a['room'])}.")

    # ------------------------------------------------------------------ signature habits
    def habit_of(self, cid):
        """This person's one small daily habit: (act, hours, label). From their nature, with a fixed tie-break per person."""
        a = self.world.agents.get(cid)
        if a is None:
            return None
        if a.get("habit") and a["habit"][0] in [h[0] for h in HABITS]:
            return next(((h[0], h[1], h[2]) for h in HABITS if h[0] == a["habit"][0] and h[2] == a["habit"][1]), None)
        f = (lambda k: self.facet(cid, k)) if self.mind_on() else (lambda k: 50)
        scored = sorted(HABITS, key=lambda h: -(sum(f(k) if k != "privacy" else 100 - f("gregariousness") for k in h[3]) + _h(cid, h[2], "habit") % 30))
        h = scored[0]
        a["habit"] = [h[0], h[2]]
        return h[0], h[1], h[2]

    # ------------------------------------------------------------------ free time
    def habit_options(self, tick, cid, hour, m, add, f, b):
        """The pulls of habit for someone choosing what to do next: dirt, a pending follow-up, the morning and evening wash, and their signature habit."""
        w = self.world
        a = w.agents[cid]
        now = int(hour) * 60 + m
        night = tick.get("phase") == "night"
        d = a.get("dirt")
        if d and d.get("kind") in DIRT:
            heavy = not DIRT[d["kind"]][2]
            push = 1.3 + (f("orderliness") - 50) / 100 + (0.8 if d["kind"] == "blood" else 0) + (0.4 if heavy else 0)
            add(push, "shower", why=f"getting clean ({DIRT[d['kind']][0]})")
            if not heavy:
                add(push - 0.2, "wash", why=f"washing ({DIRT[d['kind']][0]})")
        nx = a.get("next")
        if nx:
            if nx.get("day") == self.day and nx["from"] <= now <= nx["until"] and nx["act"] in self._acts():
                add(nx["w"], nx["act"], why=nx["why"])
            elif nx.get("day") != self.day or now > nx["until"]:
                a.pop("next", None)
        ws = a.get("washed") or {}
        tidy = (f("orderliness") - 50) / 120
        if (int(hour) == 8 or int(hour) == 10 and m < 60) and ws.get("am") != self.day:
            add(1.0 + tidy + (0.3 if int(hour) == 10 else 0), "wash", why="a morning wash")
        if (int(hour) >= 20 or night) and ws.get("pm") != self.day and not a.get("asleep"):
            add(0.8 + tidy + (0.9 if night else 0), "wash", why="washing before bed")
        h = self.habit_of(cid)
        if h and int(hour) % 24 in h[1] and (a.get("habit_done") or {}).get("day") != self.day and not night:
            add(1.1 + (_h(cid, self.day, "habit") % 30) / 100, h[0], why=h[2])

    def _acts(self):
        from .freetime import ACTS
        return ACTS

    def habit_after(self, tick, cid, act, room, m, end):
        """Something has just been started: it may leave dirt, a follow-up, a done habit or a washed routine behind."""
        w = self.world
        a = w.agents.get(cid)
        if not a:
            return
        hour = int(tick["hour"])
        if act in ("wash", "shower", "bath"):
            self.wash_off(tick, cid, act, m)
            ws = a.setdefault("washed", {})
            if hour in (8, 10):
                ws["am"] = self.day
            if hour >= 20 or tick.get("phase") == "night":
                ws["pm"] = self.day
        if act == "escape":
            kind = "grease" if room in ("generator_shed", "boathouse", "boiler_room", "lighthouse") else "sand" if room == "beach" else "sweat"
            if self.rng.random() < 0.7:
                self.get_dirty(cid, kind)
        elif act in DIRTY_WORK:
            kind, p = DIRTY_WORK[act]
            if self.rng.random() < p:
                self.get_dirty(cid, kind)
        elif act in ("stroll", "explore") and room == "woods" and self.rng.random() < 0.3:
            self.get_dirty(cid, "mud")
        nx = a.get("next")
        if nx and nx["act"] == act:
            a.pop("next", None)                                          # done what they meant to do next
        if act in FOLLOW:
            nact, pull, mins, why = FOLLOW[act]
            if act != "eat" or self.facet(cid, "orderliness") >= 55:
                a["next"] = {"act": nact, "w": pull, "from": hour * 60 + int(end) - 5, "until": hour * 60 + int(end) + mins, "why": why, "day": self.day}
        h = self.habit_of(cid)
        if h and act == h[0] and hour % 24 in h[1]:
            a["habit_done"] = {"day": self.day}
