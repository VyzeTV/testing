"""Pacing: an escape-attempt quota, and pressure that turns a warm cast hostile as the deadline closes.

Left alone, the models drift into tea parties (no experiments, no feuds). So the engine picks someone to lead an escape attempt a few times a day, and adds
sanity pressure and small frictions that grow with the day and with how close the deadline is.
PaceMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ESCAPE_ROUTES, ROOMS

SLIGHTS = [
    ("snaps at {b} over something petty", 1),
    ("accuses {b} of hoarding supplies", 2),
    ("brushes off {b}'s attempt to help, loudly", 1),
    ("mocks {b} in front of the others", 2),
    ("catches {b} in a small lie about where they were", 2),
    ("blames {b} for the mood in the house", 1),
    ("says what everyone is thinking about {b}, and it is not kind", 2),
    ("shoves past {b} without a word", 1),
    ("takes the last of something {b} was saving, and does not apologise", 2),
    ("repeats something {b} said in confidence, to get a laugh", 3),
]
AGGRESSIVE = {"avenger", "saboteur", "schemer", "nihilist"}


def _hh(h):
    return f"{int(h):02d}:00"


class PaceMixin:
    # ------------------------------------------------------------------ pressure
    def pressure(self):
        """0 at the start of a deadline period, 1 on the deadline day itself."""
        s = self.s
        if not self.revealed:
            return 0.0
        n = max(3, s.get("week_len", 7))
        left = max(0, s["deadline_day"] - self.day)
        return max(0.0, min(1.0, 1.0 - left / max(1, n - 1)))

    def pressure_drain(self, tick, hour):
        pr = self.pressure()
        if pr <= 0 or self.aftermath_active():
            return
        for cid in list(self.world.agents):
            if self.rng.random() < (0.08 + 0.4 * pr) * self.tune("dread_mult"):
                self.stat(tick, cid, "sanity", -1, "dread")

    def friction_tick(self, tick, hour):
        """Small, specific slights between people in the same room; they stack into grudges, feuds and, eventually, plots."""
        w, s = self.world, self.s
        if self.day < 2 or s.get("case") or s.get("spree") or self.aftermath_active():
            return
        pr = self.pressure()
        mean_san = sum(a["sanity"] for a in w.agents.values()) / max(1, len(w.agents))
        rate = (0.25 + min(0.5, 0.08 * self.day) + 0.9 * pr + (0.4 if mean_san < 50 else 0.0)) * self.tune("friction_rate")
        n = 0
        while n < 3 and self.rng.random() < rate:
            rate *= 0.55
            n += 1
            pairs = []
            for room in ROOMS:
                hs = [o for o in w.occupants(room) if o in w.agents]
                if len(hs) < 2 or room in ("voting_grounds",):
                    continue
                for x in hs:
                    for y in hs:
                        if x == y:
                            continue
                        ax, ay = w.agents[x], w.agents[y]
                        wt = 1.0 + (2.0 if ax["aff"].get(y, 0) <= 0 else 0.0) + (1.0 if ax["drive"]["id"] in AGGRESSIVE else 0.0) \
                            + (1.0 if ax["sanity"] < 50 else 0.0) - (1.5 if ax["aff"].get(y, 0) >= 6 else 0.0)
                        pairs.append((max(0.05, wt), x, y, room))
            if not pairs:
                return
            tot = sum(p[0] for p in pairs)
            r = self.rng.uniform(0, tot)
            for wt, x, y, room in pairs:
                r -= wt
                if r <= 0:
                    break
            text, sev = self.rng.choice(SLIGHTS)
            line = text.format(b=self.nm(y))
            self.add_tie(y, x, "slighted", f"{self.nm(x)} {line} (day {self.day})", 0)
            self.adjust_any_aff(y, x, -sev)
            self.adjust_any_aff(x, y, -max(1, sev - 1))
            self.stat(tick, y, "sanity", -1, "a slight")
            witnesses = [o for o in w.occupants(room) if o in w.agents and o not in (x, y)]
            w.remember(y, f"{_hh(hour)} (slight) {self.nm(x)} {line}.")
            self.log_event(tick, {"type": "friction", "who": x, "room": room, "vis": "public", "text": f"{self.nm(x)} {line}."}, witnesses=witnesses, actor=x)

    # ------------------------------------------------------------------ escape quota
    def exp_expected(self, hour):
        return int(round({10: 1, 12: 1, 14: 2, 16: 2, 18: 3}.get(hour, 0) * self.tune("experiment_quota")))

    def pick_focus(self, hour):
        """Choose one person to lead an escape attempt this turn if the day is running short of them."""
        w, s = self.world, self.s
        self.focus = None
        if (not self.revealed or s.get("case") or s.get("spree") or s["escape"].get("progress", 0) >= 100
                or self.exp_today >= self.exp_expected(hour)):
            return
        cands = []
        for cid, a in w.agents.items():
            if a["sanity"] < 30 or a["hp"] < 30 or a["room"] in ("cold_store", "voting_grounds") or a.get("hiding"):
                continue
            pl = s.get("plots", {}).get(cid)
            if pl and pl.get("stage") in ("stalking", "striking"):
                continue
            wt = 1.0 + (2.0 if a["drive"]["id"] in ("seeker", "survivor", "protector") else 0.0) + (0.5 if a["sanity"] > 60 else 0.0)
            cands.append((wt, cid))
        if not cands:
            return
        r = self.rng.uniform(0, sum(c[0] for c in cands))
        for wt, cid in cands:
            r -= wt
            if r <= 0:
                break
        self.focus = cid
        self.focus_idea = self.focus_task(cid)

    def focus_task(self, cid):
        s, w = self.s, self.world
        fav = w.agents[cid].get("route")
        order = ([fav] if fav in ESCAPE_ROUTES else []) + [r for r in ESCAPE_ROUTES if r != fav]
        best = None
        for rid in order:
            plan = s["escape"]["routes"][rid]["plan"]
            open_steps = [(v, k) for k, v in plan.items() if v < 100]
            if not open_steps:
                continue
            v, k = min(open_steps)
            if best is None or (rid == fav):
                best = (rid, k, v)
                if rid == fav:
                    break
        if not best:
            return None
        rid, k, v = best
        r = ESCAPE_ROUTES[rid]
        return {"route": rid, "step": k, "text": f"{r['title']}: {r['steps'][k]}"}

    def focus_lines(self, cid):
        if getattr(self, "focus", None) != cid or not getattr(self, "focus_idea", None):
            return []
        return [f"ESCAPE ATTEMPT: the group has agreed you should lead an attempt this turn. Next step on the plan: {self.focus_idea['text']}. "
                "Take action 'experiment' with a concrete 'idea' (where, with what, how). A failed attempt still teaches the group something."]

    def focus_override(self, decisions):
        """If the chosen person drifted into something idle, turn their turn into the attempt."""
        cid = getattr(self, "focus", None)
        if not cid or cid not in decisions or not getattr(self, "focus_idea", None):
            return
        d = decisions[cid]
        if d["action"] == "experiment" or d["action"] not in ("stay", "search", "take", "rest", "use", "give", "drop") or self.rng.random() > 0.85:
            return
        d["_src"] = "engine"
        d["action"] = "experiment"
        d["idea"] = d["idea"] or ("Try this: " + self.focus_idea["text"])[:200]
        d["activity"] = "Leading an escape attempt"
