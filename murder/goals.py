"""Goal-based nudges: the GM states a goal and the director works toward it over several days, through the engine.

The GM picks a goal from a short menu (Director panel, "Goal"): make two people enemies, friends or lovers, a betrayal, get the evidence
found, keep someone alive, a breakdown, a death, a way out. Each turn the director may make one move toward each active goal, using only
engine moves: a rumour, an unsigned note, a person someone wants to talk to, a secret learned, NeoVi's inspection, TereVi pointed at
someone, a summons on the schedule (adding a draw that puts people in one room), and shifted odds on the rolls that decide things (a
plotter's strike, a betrayal, a new plot, work on a way out). Nudges change odds and opportunities only: the outcome is still rolled.
A goal is met when the state shows it (feelings, a bond, a betrayal, a found clue, a death...), fails when its days run out or it becomes
impossible, and the GM can drop it. GoalsMixin is mixed into DayRunner (engine.py).
"""

KINDS = {   # kind: (people needed, label)
    "enemies": (2, "make {a} and {b} enemies"), "friends": (2, "make {a} and {b} friends"), "romance": (2, "bring {a} and {b} together"),
    "betrayal": (2, "{a} betrays {b}"), "find": (0, "get the evidence found"), "protect": (1, "keep {a} alive"),
    "breakdown": (1, "a breakdown for {a}"), "death": (0, "someone dies"), "escape": (0, "get a way out finished"),
}
MAX_GOALS = 4


class GoalsMixin:
    def goals(self, active=True):
        return [g for g in self.s.get("goals", []) if not active or g["status"] == "active"]

    def goal_label(self, g):
        return KINDS[g["kind"]][1].format(a=self.nm(g.get("a")) if g.get("a") else "", b=self.nm(g.get("b")) if g.get("b") else "")

    def set_goal(self, tick, it, hour):
        """A GM action {"type": "goal", "kind", "a", "b", "days"} or {"type": "goal", "op": "drop", "id"}."""
        w, s = self.world, self.s
        gs = s.setdefault("goals", [])
        if it.get("op") == "drop":
            for g in gs:
                if str(g["id"]) == str(it.get("id")) and g["status"] == "active":
                    g["status"] = "dropped"
            return None
        kind = it.get("kind")
        if kind not in KINDS:
            return None
        need = KINDS[kind][0]
        a, b = it.get("a"), it.get("b")
        if need >= 1 and a not in w.agents or need >= 2 and (b not in w.agents or b == a):
            return None
        if len(self.goals()) >= MAX_GOALS:
            return None
        try:
            days = max(1, min(14, int(it.get("days") or 3)))
        except (TypeError, ValueError):
            days = 3
        g = {"id": max([x["id"] for x in gs] + [0]) + 1, "kind": kind, "a": a if need >= 1 else None, "b": b if need >= 2 else None,
             "set": [self.day, hour], "until": self.day + days, "status": "active", "moves": [],
             "base": {"dead": len(s.get("graveyard", [])), "clues": self.found_clues()}}
        gs.append(g)
        del gs[:-20]
        self.log_event(tick, {"type": "director", "who": "terevi", "room": "foyer", "vis": "gm", "text": f"GM goal set: {self.goal_label(g)} (by Day {g['until']})."})
        return g

    def found_clues(self):
        case = self.s.get("case")
        return sum(1 for c in (case or {}).get("clues", []) if c.get("found_by")) if case else 0

    # ------------------------------------------------------------------ progress
    def goal_met(self, g):
        """True met, False failed, None still open."""
        w, s = self.world, self.s
        A = w.agents
        a, b, k = g.get("a"), g.get("b"), g["kind"]
        aff = lambda x, y: A[x]["aff"].get(y, 0) if x in A else 0
        if k in ("enemies", "friends", "romance", "betrayal", "breakdown") and (a not in A or (b and b not in A)):
            return False
        if k == "enemies":
            return True if aff(a, b) <= -5 and aff(b, a) <= -5 else None
        if k == "friends":
            return True if aff(a, b) >= 6 and aff(b, a) >= 6 else None
        if k == "romance":
            return True if any(x.get("kind") == "romance" and {x["a"], x["b"]} == {a, b} for x in s.get("bonds", [])) else None
        if k == "betrayal":
            return True if any(t["a"] == b and t["b"] == a and t["kind"] in ("betrayed", "wronged") and t.get("day", 0) >= g["set"][0] for t in s.get("ties", [])) else None
        if k == "find":
            return True if self.found_clues() >= g["base"]["clues"] + 2 else None
        if k == "protect":
            return False if a not in A else None                         # met when the time runs out with them alive
        if k == "breakdown":
            return True if A[a]["sanity"] < 20 or any(c in (A[a].get("conds") or {}) for c in ("panicking", "deranged")) else None
        if k == "death":
            return True if len(s.get("graveyard", [])) > g["base"]["dead"] else None
        if k == "escape":
            tried = sum(r.get("attempts", 0) for r in s["escape"]["routes"].values())
            return True if tried > g.get("_att0", tried) else None          # a finale was attempted
        return None

    def goals_tick(self, tick, hour):
        """Check every active goal, and make at most one move toward each (two in all per turn)."""
        if not self.revealed or self.s.get("over"):
            return
        moved = 0
        for g in self.goals():
            if g["kind"] == "escape" and g.get("_att0") is None:
                g["_att0"] = sum(r.get("attempts", 0) for r in self.s["escape"]["routes"].values())
            res = self.goal_met(g)
            if res is None and self.day > g["until"]:
                res = g["kind"] == "protect"
            if res is not None:
                g["status"] = "met" if res else "failed"
                g["ended"] = [self.day, hour]
                self.log_event(tick, {"type": "director", "who": "terevi", "room": "foyer", "vis": "gm",
                                      "text": f"GM goal {'met' if res else 'failed'}: {self.goal_label(g)}."})
                continue
            if moved < 2 and self.rng.random() < 0.5 * self.tune("goal_push"):
                text = self.goal_move(tick, hour, g)
                if text:
                    moved += 1
                    g["moves"].append([self.day, hour, text])
                    del g["moves"][:-12]
                    self.log_event(tick, {"type": "director", "who": "terevi", "room": "foyer", "vis": "gm", "text": f"Toward the goal ({self.goal_label(g)}): {text}."})

    # ------------------------------------------------------------------ the moves
    def goal_move(self, tick, hour, g):
        w, s = self.world, self.s
        A = w.agents
        a, b, k = g.get("a"), g.get("b"), g["kind"]
        nm = self.nm
        done = {m[2].split(":")[0] for m in g["moves"][-3:]}
        note = lambda who, text: (w.remember(who, f"{hour % 24:02d}:00 You find an unsigned note: \"{text}\""), self.moment(who, f"found an unsigned note: {text[:60]}"))
        opts = []
        if k == "enemies":
            opts = [("rumour", lambda: self.spread_rumor(tick, "unknown", b, f"{nm(b)} has been mocking {nm(a)} behind their back", "bad", True, [a], A[a]["room"], hour)
                     and f"rumour: {nm(a)} hears {nm(b)} mocks them"),
                    ("secret", lambda: self.goal_secret(a, b) and f"secret: {nm(a)} learns what {nm(b)} is hiding"),
                    ("confront", lambda: self.goal_talk(a, b, f"have it out with {nm(b)}") and f"confront: {nm(a)} wants words with {nm(b)}"),
                    ("summons", lambda: self.goal_summons(tick, hour, "lounge", "TereVi's seating chart") and "summons: everyone to the Lounge, seated by TereVi")]
        elif k in ("friends", "romance"):
            opts = [("rumour", lambda: self.spread_rumor(tick, "unknown", b, f"{nm(b)} said {nm(a)} is the only one here worth trusting", "good", False, [a], A[a]["room"], hour)
                     and f"rumour: {nm(a)} hears {nm(b)} trusts them"),
                    ("talk", lambda: self.goal_talk(a, b, f"spend some time with {nm(b)}") and self.goal_talk(b, a, f"get to know {nm(a)}") and f"talk: {nm(a)} and {nm(b)} seek each other out"),
                    ("pair", lambda: setattr(self, "force_tease", f"Pair {nm(a)} and {nm(b)} for a silly game on air: they have to work together, and look like they are enjoying it.") or f"pair: TereVi pairs {nm(a)} and {nm(b)}")]
        elif k == "betrayal":
            opts = [("secret", lambda: self.goal_secret(a, b) and f"secret: {nm(a)} learns what {nm(b)} is hiding"),
                    ("note", lambda: note(a, f"Only one of you two walks out of here. {nm(b)} already knows which one.") or f"note: {nm(a)} is told only one of them walks out"),
                    ("rumour", lambda: self.spread_rumor(tick, "unknown", b, f"{nm(b)} has been planning to sell {nm(a)} out", "bad", True, [a], A[a]["room"], hour)
                     and f"rumour: {nm(a)} hears {nm(b)} plans to sell them out")]
        elif k == "find":
            case = s.get("case")
            if case and case.get("killer") in A:
                kr = w.cast[case["killer"]]["home"]
                cur = max([c for c in A], key=lambda c: (self.facet(c, "curiosity"), c))
                opts = [("inspect", lambda: s.__setitem__("_inspect", {"day": self.day, "hour": min(18, hour + 2), "room": kr}) or f"inspect: NeoVi will inspect the {w.room_name(kr)}"),
                        ("note", lambda: note(cur, "Before the trial, search everyone's room. Everyone's.") or f"note: {nm(cur)} is told to search the rooms")]
        elif k == "protect" and a in A:
            guard = max([o for o in A if o != a] or [None], key=lambda o: (A[o]["aff"].get(a, 0), o) if o else 0)
            opts = [("note", lambda: note(a, "Don't go anywhere alone tonight. Not anywhere.") or f"note: {nm(a)} is warned not to be alone")]
            if guard:
                opts.append(("guard", lambda: self.goal_talk(guard, a, f"keep an eye on {nm(a)}") and f"guard: {nm(guard)} sticks close to {nm(a)}"))
        elif k == "breakdown" and a in A:
            lost = (A[a]["memory"].get("lost") or [{}])[-1].get("name")
            opts = [("memory", lambda: (w.remember(a, f"(private) You can't stop thinking about {lost or 'everyone who is gone'}."), self.stat(tick, a, "sanity", -4, "a painful memory"))
                     and f"memory: a painful memory surfaces for {nm(a)}"),
                    ("tease", lambda: setattr(self, "force_tease", f"Remind {nm(a)}, on air, of what they have lost and what they still could. Twist the knife, smiling.") or f"tease: TereVi turns on {nm(a)}")]
        elif k == "death":
            opts = [("tease", lambda: setattr(self, "force_tease", "Announce a prize for the first person to break the deadline: a way off the island, for one. Wink at the camera.") or "tease: TereVi dangles a prize for a killing")]
        elif k == "escape":
            from .data_world import ESCAPE_ROUTES
            rid = max(ESCAPE_ROUTES, key=lambda r: (self.route_pct(r), r))
            room = ESCAPE_ROUTES[rid]["room"]
            opts = [("unlock", lambda: (s.get("locks") or {}).pop(room, None) is not None and f"unlock: the {w.room_name(room)} is open again")]
            team = [c for c in s["escape"]["routes"][rid].get("contributors", []) if c in A]
            if team:
                opts.append(("note", lambda: note(team[0], "TereVi's cameras on the way out stutter every night at three. Use it.") or f"note: {nm(team[0])} learns when the cameras stutter"))
        opts = [o for o in opts if o[0] not in done] or opts
        self.rng.shuffle(opts)
        for _, fn in opts:
            r = fn()
            if r:
                return r
        return ""

    def goal_secret(self, a, b):
        w = self.world
        sec = w.cast.get(b, {}).get("secret")
        ks = w.agents[a].setdefault("known_secrets", [])
        if not sec or any(x.get("of") == b for x in ks):
            return False
        ks.append({"of": b, "text": sec})
        w.remember(a, f"(private) You found out {self.nm(b)}'s secret: {sec}")
        return True

    def goal_talk(self, a, b, why):
        w = self.world
        if a not in w.agents or b not in w.agents:
            return False
        w.agents[a]["want_talk"] = {"who": [b], "day": self.day, "why": why}
        return True

    def goal_summons(self, tick, hour, room, label):
        if self.s.get("_goal_summons") == self.day or hour >= 18:
            return False
        self.s["_goal_summons"] = self.day
        return bool(self.gm_schedule(tick, {"op": "add", "at": (hour + 2) * 60 + 30, "room": room, "text": label}, hour))

    # ------------------------------------------------------------------ odds
    def goal_odds(self, roll, p, who=None, about=None):
        """Shift a decisive roll toward (or away from) the active goals. Never forces it: the result is clamped short of certain."""
        q = p
        for g in self.goals():
            k, a, b = g["kind"], g.get("a"), g.get("b")
            if roll == "strike":
                if k == "protect" and about == a:
                    q *= 0.5
                elif k == "death":
                    q *= 1.25
            elif roll == "betray" and k == "betrayal" and who == a and about == b:
                q += 0.15
            elif roll == "plot":
                if k == "death":
                    q *= 1.6
                elif k == "protect" and about == a:
                    q *= 0.5
            elif roll == "escape" and k == "escape":
                q += 0.3
        return max(0.0, min(0.97, q)) if roll != "escape" else q
