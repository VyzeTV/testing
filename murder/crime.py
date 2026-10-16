"""The crime pipeline on the event log: pursuit and ambush instead of missed attacks, what witnesses actually saw (from the chronicle), interrogation that depends on who is asking and
who is answering (facets and values), and the digest of what the cast saw that the trial works from.

Nothing here names a culprit: it only turns recorded, witnessed events into evidence and statements. The tuning dial `crime_pipeline` (World group) switches the changes to old
behaviour off (0): attacks on someone who has left simply fail, a spree always waives the trial, and the trial sees no chronicle digest.
CrimeMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS

CRIME_TYPES = {"attack", "assault", "breakin", "frame", "rob", "carry", "faint", "fire", "flood", "wreck", "door", "take", "give", "move", "arrive", "friction", "plot", "frisk", "stash", "hide"}
APPROACHES = ("appeals to their friendship", "leans on them", "reasons with them")


def _hh(h):
    return f"{int(h):02d}:00"


class CrimeMixin:
    def crime_on(self):
        return bool(self.tune("crime_pipeline"))

    # ------------------------------------------------------------------ pursuit: the target moved away, the attacker follows
    def pursue_target(self, tick, cid, t):
        """An attacker whose target slipped into another room follows and strikes on arrival, if the way is short and open."""
        w = self.world
        a, ta = w.agents[cid], w.agents[t]
        if not self.crime_on() or a.get("out") or a.get("restrained") or ta.get("hiding") or t == cid:
            return False
        steps = w.path(cid, a["room"], ta["room"])
        if not steps:
            return False
        cost = sum(c for _, _, c in steps)
        if cost > 30:
            return False
        p = (0.75 if cost <= 12 else 0.5) + 0.1 * (self.facet(cid, "assertiveness") - 50) / 50
        if self.rng.random() >= p:
            return False
        start = a["room"]
        mv = tick["moves"].setdefault(cid, {"from": start, "path": [start], "to": start})
        mv["path"] = list(mv.get("path") or [start]) + [r for r, _, _ in steps]
        mv["to"] = ta["room"]
        a["room"] = ta["room"]
        self.log_event(tick, {"type": "move", "who": cid, "room": ta["room"], "vis": "public", "text": f"{self.nm(cid)} follows {self.nm(t)} into the {w.room_name(ta['room'])}, close behind."},
                       witnesses=[o for o in w.occupants(ta["room"]) if o in w.agents and o != cid], actor=cid)
        return True

    # ------------------------------------------------------------------ what was seen, from the chronicle
    def seen_near(self, room, hours_before, until_hour=None, case=None):
        """Chronicle entries in or next to `room` in the hours before now that someone witnessed (not GM-only)."""
        s = self.s
        now = self.day * 24 + (until_hour if until_hour is not None else s.get("_hour", 12))
        edges = {room}
        for e in self.world.edges:
            if not e.get("hidden"):
                if e["a"] == room:
                    edges.add(e["b"])
                elif e["b"] == room:
                    edges.add(e["a"])
        out = []
        for e in s.get("chronicle", []):
            t = e["day"] * 24 + e["hour"]
            if e["vis"] == "gm" or t < now - hours_before or t > now + 1 or e.get("room") not in edges or e["type"] not in CRIME_TYPES:
                continue
            if not e.get("seen") and e["type"] not in ("attack", "assault"):
                continue
            out.append(e)
        return out

    def chronicle_digest(self, case, limit=12):
        """Lines for the trial: who was seen where in the hours before the death, in or next to the scene."""
        if not self.crime_on() or not case:
            return ""
        w = self.world
        ents = self.seen_near(case["room"], 9, case["hour"], case)
        ents = [e for e in ents if e["type"] in ("move", "arrive", "door", "breakin", "take", "give", "carry", "frame", "rob", "faint", "attack", "assault", "fire", "wreck", "friction", "hide", "stash")]
        # keep the freshest and the most telling
        ents = sorted(ents, key=lambda e: (e["cls"] not in ("critical", "important"), -(e["day"] * 24 + e["hour"])))[:limit]
        ents.sort(key=lambda e: (e["day"], e["hour"], e["id"]))
        lines = []
        for e in ents:
            by = ", ".join(self.nm(c) for c in e.get("seen", [])[:3] if c in w.cast)
            lines.append(f"Day {e['day']} {_hh(e['hour'])}: {e['text'][:140]}" + (f" (seen by {by})" if by else ""))
        return "\n".join(lines)

    def seen_of(self, cid, case, limit=4):
        """What others witnessed of this person in the hours before the death (so a suspect knows what can be said against them)."""
        if not self.crime_on() or not case:
            return []
        out = []
        for e in self.seen_near(case["room"], 9, case["hour"], case):
            if e.get("who") == cid and e.get("seen"):
                by = ", ".join(self.nm(c) for c in e["seen"][:3] if c in self.world.cast)
                out.append(f"{_hh(e['hour'])}: {e['text'][:90]} (seen by {by})")
        return out[-limit:]

    # ------------------------------------------------------------------ interrogation
    def interrogation_odds(self, asker, target):
        """(approach, chance) for the best way the asker can lean on this target, from facets, values and how they get on."""
        a, t = self.world.agents[asker], self.world.agents[target]
        f, g = self.facet, self.mind(target)["values"]
        aff = max(-3, min(5, t["aff"].get(asker, 0)))
        trust, cooperative, truthful, stubborn = f(target, "trust"), g["cooperation"], g["truth"], 100 - f(target, "stress_vulnerability") * 0.5
        appeal = 0.12 + 0.05 * aff + 0.3 * (trust - 50) / 100 + 0.2 * (g["friendship"] - 50) / 100 + 0.1 * (f(asker, "altruism") - 50) / 100
        lean = 0.10 + 0.4 * (f(asker, "assertiveness") + f(asker, "cruelty") - 100) / 200 - 0.35 * (f(target, "courage") - 50) / 100 + 0.2 * (f(target, "stress_vulnerability") - 50) / 100
        reason = 0.10 + 0.3 * (truthful - 50) / 100 + 0.25 * (cooperative - 50) / 100 + 0.2 * (f(asker, "curiosity") - 50) / 100 + 0.1 * (g["law"] - 50) / 100
        options = list(zip(APPROACHES, (appeal, lean, reason)))
        best = max(options, key=lambda o: o[1])
        bonus = (0.2 if t["sanity"] < 40 else 0.0) + 0.15 * self.sharpness(asker) - 0.1 * (stubborn - 60) / 100
        return best[0], max(0.03, min(0.85, best[1] + bonus))

    def interrogate_witness(self, tick, asker, target, hour):
        """The asker questions the target about the case: an honest witness who is willing tells what they saw near the scene; the killer deflects; a cagey one gives nothing."""
        w, s = self.world, self.s
        case = s.get("case")
        if not self.crime_on() or not case or not case.get("announced") or asker not in w.agents or target not in w.agents:
            return
        how, p = self.interrogation_odds(asker, target)
        a, t = w.agents[asker], w.agents[target]
        name, tname = self.nm(asker), self.nm(target)
        if target == case.get("killer"):
            p *= 0.25
        if self.rng.random() >= p:
            w.remember(asker, f"{_hh(hour)} You tried to get something from {tname} ({how}); they stayed closed.")
            self.chron_add(tick, "interrogation", asker, a["room"], "gm", f"{name} questioned {tname} ({how}) and got nothing.")
            return
        seen = [e for e in self.seen_near(case["room"], 9, case["hour"], case) if target in (e.get("seen") or []) and e.get("who") != target]
        if not seen:
            w.remember(asker, f"{_hh(hour)} {tname} answered you ({how}) but had seen nothing useful.")
            self.chron_add(tick, "interrogation", asker, a["room"], "gm", f"{name} questioned {tname} ({how}): they had seen nothing useful.")
            return
        e = seen[-1]
        who = self.nm(e["who"]) if e.get("who") in w.cast else "someone"
        claim = f"{who} {e['text'].split(' ', 1)[1] if e['text'].startswith(who) else e['text']}"[:150] if e.get("who") in w.cast else e["text"][:150]
        self.note_evidence(asker, "testimony", f"{tname} says they saw this around {_hh(e['hour'])}: {e['text'][:140]}", by=target)
        case.setdefault("testimonies", []).append({"by": target, "day": e["day"], "hour": e["hour"], "claim": e["text"][:150], "late": False})
        del case["testimonies"][:-12]
        w.remember(asker, f"{_hh(hour)} {tname} told you ({how}): {e['text'][:120]}")
        self.chron_add(tick, "interrogation", asker, a["room"], "gm", f"{name} questioned {tname} ({how}): {tname} described what they saw: {e['text'][:100]}")
        self.tally(asker, "interrogations")
