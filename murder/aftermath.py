"""After a death: recovery comes first.

A trial leaves the survivors with heavy losses (a body, a verdict, an execution, mourning) and the old economy gave back less than a person lost in a day, so the
cast stalled at low sanity for days. Now, once a case is closed (or a no-culprit death is announced) there is a calm window: the remaining hours of that day and the whole
next day. In it the daily drain, the deadline's dread, friction, and new plots are off; restorative moments count for more; people who are low lean on whoever they trust;
nights restore more; and the survivors hold a remembrance together (a real scene with NeoVi at the door, and a guaranteed lift for everyone who comes).
AftermathMixin is mixed into DayRunner (engine.py).
"""

ROOM = "lounge"
NIGHT_GAIN = 4
COMFORT_CAP = 10          # sanity a person can regain per day from leaning on others in the calm window


def _hh(h):
    return f"{int(h):02d}:00"


class AftermathMixin:
    # ------------------------------------------------------------------ state
    def aftermath_active(self):
        aft = self.s.get("aftermath")
        return bool(aft and aft.get("since") is not None and not self.s.get("case") and self.day <= aft["until"])

    def note_loss(self, victim):
        """Every death is remembered by the aftermath (called by mourn)."""
        aft = self.s.get("aftermath") or {"victims": [], "since": None, "until": 0, "vigil_done": True}
        if victim not in aft["victims"]:
            aft["victims"].append(victim)
        aft["vigil_done"] = False
        self.s["aftermath"] = aft

    def begin_aftermath(self, tick, hour):
        """The case is closed (verdict carried out, or a no-culprit death announced): the calm window opens."""
        aft = self.s.get("aftermath")
        if not aft or not aft["victims"] or not self.world.agents:
            return
        if self.tune("calm_days") <= 0:
            return
        aft["since"] = [self.day, hour]
        aft["until"] = self.day + int(self.tune("calm_days"))
        aft["vigil_done"] = False
        self.log_event(tick, {"type": "system", "who": "terevi", "room": "foyer", "vis": "viewer",
                              "text": "AFTERMATH: the survivors get a calm window to recover (no drain, no dread, no new quarrels or plots) until the end of tomorrow."})

    def drain_factor(self):
        """0 in the calm window, then two days of half-strength drain as things settle, then normal."""
        aft = self.s.get("aftermath")
        if not aft or aft.get("since") is None or self.s.get("case"):
            return 1.0
        if self.day <= aft["until"]:
            return 0.0
        return 0.5 if self.day <= aft["until"] + 2 else 1.0

    def special_scale(self):
        return (2.0, 1.5) if self.aftermath_active() else (1.0, 1.0)

    # ------------------------------------------------------------------ small, reliable recovery
    def aftermath_comfort(self, tick, hour):
        """People who are low and near someone they trust lean on each other; this does not depend on the model producing a 'special moment'."""
        if not self.aftermath_active():
            return
        w = self.world
        for cid, a in list(w.agents.items()):
            if a["sanity"] >= 70 or a.get("asleep"):
                continue
            got = a.get("comfort_today", 0)
            if got >= COMFORT_CAP:
                continue
            mates = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid and a["aff"].get(o, 0) >= 2]
            if not mates:
                continue
            gain = min(2 + (1 if a["sanity"] < 35 else 0), COMFORT_CAP - got)
            a["comfort_today"] = got + gain
            self.stat(tick, cid, "sanity", gain, f"leaning on {self.nm(max(mates, key=lambda o: a['aff'].get(o, 0)))}")

    def aftermath_night(self, tick):
        """A night after a death restores more."""
        if not self.aftermath_active():
            return
        for cid, a in self.world.agents.items():
            if a["sanity"] < 90 and a.get("slept", True):
                self.stat(tick, cid, "sanity", NIGHT_GAIN, "rest after the loss")

    # ------------------------------------------------------------------ the remembrance
    def vigil_due(self, hour):
        aft = self.s.get("aftermath")
        if not aft or aft.get("vigil_done") or aft.get("since") is None or self.s.get("case") or self.s.get("over") or self.s.get("spree"):
            return False
        if len(self.world.agents) < 2 or self.endgame_due() or not self.revealed:
            return False
        sd, sh = aft["since"]
        return (self.day > sd and hour >= 10) or (self.day == sd and hour >= max(16, sh + 2))

    def run_vigil(self, hour):
        w, s = self.world, self.s
        aft = s["aftermath"]
        aft["vigil_done"] = True
        tick = self.new_tick(hour)
        self.begin_practice(tick)                                # people walk in on the live map (claimtrial.py)
        s["_hour"] = hour
        ids = [c for c in w.agents if not w.agents[c].get("out")]
        dead = [v for v in aft["victims"] if v in w.cast]
        names = ", ".join(self.nm(v) for v in dead) or "the dead"
        self.fetch_stragglers(tick, ids, ROOM, "the remembrance")
        self.clear_hiding()
        for cid in ids:
            a = w.agents[cid]
            start = a["room"]
            steps = w.path(cid, start, ROOM) if start != ROOM else []
            tick["moves"][cid] = {"from": start, "path": [start] + ([r for r, _, _ in steps] if steps else ([ROOM] if start != ROOM else [])), "to": ROOM}
            a["room"] = ROOM
            a["activity"] = "At the remembrance"
            w.remember(cid, f"{_hh(hour)} The survivors gathered in the {w.room_name(ROOM)} to remember {names}.")
        self.log_event(tick, {"type": "vigil", "who": ids[0], "room": ROOM, "vis": "public",
                              "text": f"The survivors gather to remember {names}."}, witnesses=ids)
        self.neovi_attend(tick, ROOM)
        self.run_scene_live(tick, "vigil", ROOM, ids, hour, self.vigil_beats(ids, dead))       # the engine decides, the model voices (scenes.py)
        for cid in ids:
            a = w.agents[cid]
            loved = any(a["aff"].get(v, 0) >= 3 for v in dead) or any(x.get("id") in dead and x.get("close") for x in a["memory"].get("lost", []))
            gain = int(self.tune("vigil_gain")) + (3 if loved else 0)
            if dead and max(a["aff"].get(v, 0) for v in dead) <= -5:
                gain //= 2                                            # hard to grieve someone you hated
            self.stat(tick, cid, "sanity", gain, "remembering the dead together")
            a["comfort_today"] = a.get("comfort_today", 0)
        for i, x in enumerate(ids):
            for y in ids[i + 1:]:
                if w.agents[x]["aff"].get(y, 0) >= -3 and w.agents[y]["aff"].get(x, 0) >= -3:
                    w.adjust_aff(x, y, 1)
                    w.adjust_aff(y, x, 1)
        for cid in ids:
            self.moment(cid, f"mourned {names} with the others")
        return tick
