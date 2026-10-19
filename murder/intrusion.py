"""Intrusions and waking: who notices someone in their room, and what they do about it.

Sleepers are checked every quarter hour of a night block (not only when a block starts): a noise in their room or next door, or somebody awake standing in
their room, may wake them, more or less easily by how deeply they sleep (exhaustion and drink make it deep, stress and the observant trait light). When
someone arrives where a person is in their own bedroom or in the bath: an awake owner welcomes a friend, a partner or someone they wanted to see, and
confronts anyone else ("What are you doing in my room?"), who answers with an excuse or a lie; a hostile, hot-tempered owner throws them out. An asleep owner
may wake, by how the intruder came in (sneaking is quiet) and what they came to do. Snooping is careful (slower to give anyone away, finds everything) or
careless (wakes people, misses things), by temperament and skill. A woken person confronts, screams (waking the neighbours), pretends to sleep and watches,
or fights back, and always remembers who it was. A stalker who finds the target asleep and alone moves to strike, or loses their nerve, and the choice is
recorded. Counts in s["intrusions"]. IntrusionMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS

NOISE_WAKE = {"attack": 0.9, "assault": 0.9, "fight": 0.9, "fire": 0.9, "break": 0.7, "punish": 0.7, "outburst": 0.6, "fall": 0.6, "madness": 0.6,
              "flood": 0.6, "body": 0.5, "snoop": 0.2, "lock": 0.2, "door": 0.15}
PRESENCE_WAKE = 0.05            # per quarter hour, someone awake standing in a sleeper's room
ARRIVE_WAKE = 0.12              # someone coming into a sleeper's room
BATHING = ("bath", "shower")
WALK_IN = 0.3                   # most people lock the bathroom door or knock
SKILLED = ("Hacker", "Urban Explorer", "Former Housemaid")       # people used to going places quietly


class IntrusionMixin:
    def intrusion_stat(self, k):
        st = self.s.setdefault("intrusions", {})
        st[k] = st.get(k, 0) + 1

    def light_sleeper(self, cid):
        """How easily they wake (1.0 = normally; lower is deeper sleep)."""
        a = self.world.agents[cid]
        k = 1.0
        if self.has_cond(cid, "exhausted"):
            k *= 0.5
        if self.has_cond(cid, "drunk"):
            k *= 0.4
        if self.mind_on():
            k *= 1.0 + max(0, self.mind(cid)["stress"] - 50) / 100
        if a["sanity"] < 30:
            k *= 1.2
        if self.has_trait(cid, "observant"):
            k *= 1.3
        return k

    def belongs_with(self, cid, room, other):
        """`other` has a right to be in `cid`'s room: a roommate or a partner."""
        w = self.world
        return w.cast.get(other, {}).get("home") == room or any({b["a"], b["b"]} == {cid, other} and b["kind"] == "romance" for b in self.s.get("bonds", []))

    def snoop_care(self, cid):
        """'careful' or 'careless', by temperament and skill."""
        f = (lambda k: self.facet(cid, k)) if self.mind_on() else (lambda k: 50)
        score = (f("orderliness") + 100 - f("impulsiveness")) / 2 + (12 if self.world.cast[cid].get("role") in SKILLED else 0) - (10 if self.has_cond(cid, "drunk") else 0)
        return "careful" if score >= 52 else "careless"

    # ------------------------------------------------------------------ the night, a quarter hour at a time
    def night_watch(self, tick, m, span=15):
        """A noise, or someone standing in their room, may wake a sleeper (called every slice of a night block)."""
        w = self.world
        for cid in sorted(w.agents):
            a = w.agents[cid]
            if not a.get("asleep") or a.get("out") or self.restrained(cid):
                continue
            room = a["room"]
            near = {e["b"] if e["a"] == room else e["a"] for e in w.edges if room in (e["a"], e["b"])}
            p, why = 0.0, None
            for e in tick["events"]:
                em = e.get("m")
                k = NOISE_WAKE.get(e.get("type"))
                if not k or em is None or not (m - span < em <= m) or e.get("who") == cid:
                    continue
                k = k if e.get("room") == room else k * 0.35 if e.get("room") in near else 0
                if k > p:
                    p, why = k, "a noise" if e.get("room") == room else "a commotion nearby"
            intruders = [o for o in sorted(w.occupants(room)) if o in w.agents and o != cid and not w.agents[o].get("asleep") and not w.agents[o].get("out")
                         and not self.belongs_with(cid, room, o)]
            for o in intruders:
                q = PRESENCE_WAKE * (0.5 if w.agents[o].get("sneaking") else 1.0) * (1.8 if self.snoop_care(o) == "careless" else 1.0)
                if q > p:
                    p, why = q, "someone in the room"
            if p and self.rng.random() < min(0.95, p * self.light_sleeper(cid)):
                self.rouse(tick, cid, why, m)
                self.intrusion_stat("woke")
                if intruders:
                    self.woken_reaction(tick, cid, intruders[0], m)

    # ------------------------------------------------------------------ walking in on someone
    def arrival_reaction(self, tick, cid, room, act, m):
        """`cid` has just come into `room`. Returns True if they were sent away."""
        w = self.world
        if room not in ROOMS or cid not in w.agents:
            return False
        for o in sorted(w.occupants(room)):
            if o == cid or o not in w.agents or w.agents[o].get("out") or self.restrained(o):
                continue
            oa = w.agents[o]
            if w.cast[o].get("home") == room and not self.belongs_with(o, room, cid):
                if oa.get("asleep"):
                    q = ARRIVE_WAKE * (0.5 if w.agents[cid].get("sneaking") else 1.0) * (1.6 if act == "snoop" and self.snoop_care(cid) == "careless" else 1.0)
                    if self.rng.random() < min(0.9, q * self.light_sleeper(o)):
                        self.rouse(tick, o, "someone coming in", m)
                        self.intrusion_stat("woke")
                        return self.woken_reaction(tick, o, cid, m) in ("confront", "scream", "fight")
                    continue
                return self.confront_intruder(tick, o, cid, act, m)
            if room == "bathroom" and self.doing(tick, o, m) in BATHING and not self.belongs_with(o, room, cid) and self.rng.random() < WALK_IN:
                self.walked_in_on(tick, o, cid, m)
        return False

    def doing(self, tick, cid, m):
        sg = next((s for s in reversed((tick.get("free") or {}).get(cid) or []) if s["m0"] <= m < s["m1"]), None)
        return sg["act"] if sg else None

    def welcome(self, owner, cid):
        a = self.world.agents[owner]
        want = (a.get("want_talk") or {})
        return self._aff(owner, cid) >= 4 or (want.get("day") == self.day and cid in want.get("who", []))

    def confront_intruder(self, tick, owner, cid, act, m):
        """The owner is awake in their own room and someone walks in."""
        w = self.world
        if self.welcome(owner, cid):
            self.intrusion_stat("welcome")
            return False
        no, nc = self.nm(owner), self.nm(cid)
        shady = act in ("snoop", "stalk", "search", "steal", "take") or cid in (self.s.get("plots") or {})
        excuse = self.rng.choice(["was looking for someone", "took a wrong turn", "heard a noise and came to check", "wanted a word"])
        lie = shady
        believed = not lie or (self.rng.random() < 0.5 and not self.has_trait(owner, "observant"))
        text = f'{no} finds {nc} in their room: "What are you doing in my room?" {nc} says they {excuse}.'
        w.adjust_aff(owner, cid, -1 if believed else -2)
        tnow = round(self.abs_now() + m / 60, 2)
        if not believed:
            self.believe(owner, {"k": "lied", "s": cid, "n": f"{nc} lied about why they were in my room", "src": "inferred", "c": 0.6, "t0": tnow, "true": True})
            self.add_tie(owner, cid, "wronged", f"came into their room and lied about why on day {self.day}")
            text += " " + ("They do not believe a word of it." if lie else "")
        hostile = self._aff(owner, cid) <= -4 and (self.facet(owner, "anger") if self.mind_on() else 50) >= 60
        self.log_event(tick, {"type": "intrude", "who": owner, "room": w.agents[owner]["room"], "vis": "public", "m": float(m), "text": text.strip()},
                       witnesses=[owner, cid], actor=cid)
        w.remember(owner, f"{self.hh()} Caught {nc} in my room; they said they {excuse}.")
        self.intrusion_stat("confronted")
        if hostile:
            self.log_event(tick, {"type": "fight", "who": owner, "room": w.agents[owner]["room"], "vis": "public", "m": float(m),
                                  "text": f"{no} shoves {nc} back out of the door."}, witnesses=[owner, cid], actor=owner)
            self.stat(tick, cid, "hp", -2, f"shoved out by {no}")
            self.intrusion_stat("thrown_out")
            self.send_away(tick, cid, m, f"thrown out of {no}'s room")
            return True
        self.send_away(tick, cid, m, f"leaving {no}'s room") if lie else None
        return lie

    def walked_in_on(self, tick, o, cid, m):
        w = self.world
        no, nc = self.nm(o), self.nm(cid)
        shy = (self.facet(o, "vanity") if self.mind_on() else 50) < 60
        if shy:
            self.stat(tick, o, "sanity", -1, "walked in on")
        w.adjust_aff(o, cid, -1)
        self.log_event(tick, {"type": "intrude", "who": o, "room": "bathroom", "vis": "public", "m": float(m),
                              "text": f"{nc} walks in on {no} in the {'bath' if self.doing(tick, o, m) == 'bath' else 'shower'}" + (" and backs out, red-faced." if shy else "; {no} just laughs.".format(no=no))},
                       witnesses=[o, cid], actor=cid)
        self.intrusion_stat("walked_in")

    def send_away(self, tick, cid, m, why):
        """They leave the room for the nearest other one."""
        w = self.world
        a = w.agents.get(cid)
        if not a:
            return
        room = a["room"]
        nb = sorted({e["b"] if e["a"] == room else e["a"] for e in w.edges if room in (e["a"], e["b"])} - {room})
        nb = [r for r in nb if r in ROOMS and not self._unsafe(r)] if hasattr(self, "_unsafe") else nb
        if not nb:
            return
        dst = nb[0]
        mv = w.move(cid, dst, 400)
        pm = tick["moves"].setdefault(cid, {"from": room, "path": [room], "to": room})
        pm["path"] = list(pm.get("path") or [room]) + mv["path"][1:]
        pm["to"] = a["room"]
        if tick.get("free") is not None and hasattr(self, "_seg"):
            self._seg(tick, cid, m, m + 15, a["room"], "walk", why)
            if self.__dict__.get("_free_busy") is not None:
                self._free_busy[cid] = max(self._free_busy.get(cid, 0), m + 15)
        a.pop("heading", None)

    # ------------------------------------------------------------------ waking up to someone
    def woken_reaction(self, tick, cid, intruder, m, context=""):
        """A sleeper wakes to find `intruder` in the room. Returns 'confront', 'scream', 'pretend' or 'fight'."""
        w = self.world
        if cid not in w.agents or intruder not in w.agents:
            return None
        f = (lambda k: self.facet(cid, k)) if self.mind_on() else (lambda k: 50)
        nc, ni = self.nm(cid), self.nm(intruder)
        room = w.agents[cid]["room"]
        plot = (self.s.get("plots") or {}).get(intruder) or {}
        hunted = plot.get("target") == cid
        opts = [(0.4 + f("courage") / 100 + f("assertiveness") / 200, "confront"),
                (0.2 + f("stress_vulnerability") / 90 + (100 - f("courage")) / 200 + (0.4 if hunted else 0), "scream"),
                (0.15 + f("curiosity") / 150 + (100 - f("courage")) / 250 + (0.3 if self.has_trait(cid, "observant") else 0), "pretend"),
                (max(0.0, (f("anger") - 45) / 60 + (f("courage") - 50) / 80 + (0.5 if self._aff(cid, intruder) <= -4 else 0)), "fight")]
        tot = sum(x for x, _ in opts)
        r = self.rng.random() * tot
        kind = opts[-1][1]
        for wt, k in opts:
            r -= wt
            if r <= 0:
                kind = k
                break
        tnow = round(self.abs_now() + m / 60, 2)
        self.believe(cid, {"k": "did", "s": intruder, "o": context or "intrude", "r": room, "t0": tnow, "n": f"{ni} was in my room in the night", "src": "seen", "c": 0.9, "true": True})
        w.remember(cid, f"{self.hh()} Woke to find {ni} in my room.")
        w.adjust_aff(cid, intruder, -1 if self._aff(cid, intruder) >= 4 else -2)
        self.add_tie(cid, intruder, "wronged", f"was in their room in the night on day {self.day}")
        if hunted:
            self.believe(cid, {"k": "rumor", "s": intruder, "n": f"{ni} is dangerous; they came for me in the night", "src": "inferred", "c": 0.7, "t0": tnow, "true": True, "reread": True})
            plot["stage"], plot["stage_ticks"], plot["wait"] = "stalking", 0, 0
            self.plan_note(plot, "they woke up; had to get out")
        here = [o for o in w.occupants(room) if o in w.agents and not w.agents[o].get("asleep")]
        ev = lambda text, vis="public", typ="wake": self.log_event(tick, {"type": typ, "who": cid, "room": room, "vis": vis, "m": float(m), "text": text}, witnesses=here, actor=intruder)
        if kind == "confront":
            ev(f'{nc} wakes to find {ni} in the room. "What are you doing here?" {ni} backs out.')
            self.send_away(tick, intruder, m, f"caught in {nc}'s room")
        elif kind == "scream":
            ev(f"{nc} wakes to find {ni} in the room and screams.", typ="outburst")
            for e in w.edges:
                if room in (e["a"], e["b"]):
                    nb = e["b"] if e["a"] == room else e["a"]
                    for o in sorted(w.occupants(nb)) + sorted(w.occupants(room)):
                        if o in w.agents and w.agents[o].get("asleep") and self.rng.random() < 0.7:
                            self.rouse(tick, o, "a scream", m)
            self.send_away(tick, intruder, m, "running from a scream")
        elif kind == "pretend":
            ev(f"{nc} wakes, sees {ni} in the room, and lies still, watching.", "gm")
        else:
            ev(f"{nc} wakes to find {ni} in the room and goes for them.", typ="fight")
            self.stat(tick, intruder, "hp", -(3 + self.rng.randint(0, 5)), f"fought off by {nc}")
            w.adjust_aff(cid, intruder, -1)
            self.send_away(tick, intruder, m, f"beaten out of {nc}'s room")
        self.intrusion_stat(kind)
        return kind

    # ------------------------------------------------------------------ the stalker at the bedside
    def stalker_at_bedside(self, tick, cid, p, m):
        """A stalker alone with the target asleep: now or never. Returns True if they move to strike; otherwise they lose their nerve and leave."""
        w = self.world
        t = p["target"]
        a = w.agents[cid]
        f = (lambda k: self.facet(cid, k)) if self.mind_on() else (lambda k: 50)
        go = 0.55 + (f("cruelty") - 50) / 150 + max(0, -self._aff(cid, t)) / 30 + (0.15 if a["sanity"] < 40 else 0) - (0.15 if a["sanity"] > 75 else 0)
        if self.rng.random() < min(0.95, max(0.15, go)):
            p["stage"], p["stage_ticks"] = "striking", 0
            self.plan_note(p, f"found {self.nm(t)} asleep and alone: now or never")
            self.intrusion_stat("bedside_strike")
            return True
        p["held_back"] = self.day
        self.plan_note(p, f"stood over {self.nm(t)} asleep and could not do it")
        w.remember(cid, f"{self.hh()} Stood over {self.nm(t)} while they slept, and could not go through with it.")
        self.log_event(tick, {"type": "plot", "who": cid, "room": a["room"], "vis": "gm", "m": float(m),
                              "text": f"{self.nm(cid)} stands over the sleeping {self.nm(t)}, and loses their nerve."}, actor=cid)
        self.intrusion_stat("bedside_held_back")
        self.send_away(tick, cid, m, "slipping back out")
        return False
