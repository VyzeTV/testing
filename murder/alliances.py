"""Alliances and betrayals.

Two or three people who trust each other and face the same pressure can ally. Allies share what they learn during an investigation, vouch for each other (truthfully, or not: a killer's
ally lies for them), and warn each other when something is wrong. Alliances grow stronger while the allies stay close and help each other, and weaken with distance and quarrels. Under pressure
a member can break faith: by leaking the ally's secret, by denouncing them publicly, or, at a trial, by withdrawing the alibi they gave and testifying against them.
AllianceMixin is mixed into DayRunner (engine.py).
"""
MAX_ALLIANCES = 2
MAX_MEMBERS = 3


def _hh(h):
    return f"{int(h):02d}:00"


class AllianceMixin:
    # ------------------------------------------------------------------ queries
    def active_alliances(self):
        return [al for al in self.s.get("alliances", []) if al["status"] == "active"]

    def alliance_of(self, cid):
        return next((al for al in self.active_alliances() if cid in al["members"]), None)

    def allies_of(self, cid):
        al = self.alliance_of(cid)
        return [m for m in al["members"] if m != cid and m in self.world.agents] if al else []

    # ------------------------------------------------------------------ forming
    def maybe_form_alliances(self, tick, hour):
        w, s = self.world, self.s
        if not self.revealed or len(self.active_alliances()) >= MAX_ALLIANCES or s.get("spree") or hour not in (12, 16, 20):
            return
        pr = self.pressure()
        pairs = []
        for room in sorted({a["room"] for a in w.agents.values()}):
            hs = [o for o in w.occupants(room) if o in w.agents]
            for i, x in enumerate(hs):
                for y in hs[i + 1:]:
                    if self.alliance_of(x) or self.alliance_of(y):
                        continue
                    ax, ay = w.agents[x]["aff"].get(y, 0), w.agents[y]["aff"].get(x, 0)
                    if min(ax, ay) < 3:
                        continue
                    enemy = any(w.agents[x]["aff"].get(z, 0) <= -3 and w.agents[y]["aff"].get(z, 0) <= -3 for z in w.agents if z not in (x, y))
                    pact = any(b["kind"] == "pact" and {b["a"], b["b"]} == {x, y} for b in s.get("bonds", []))
                    wt = 0.15 + 0.35 * pr + (0.25 if enemy else 0) + (0.4 if pact else 0) + 0.03 * (min(ax, ay) - 3)
                    pairs.append((wt, x, y, room))
        self.rng.shuffle(pairs)
        for wt, x, y, room in pairs:
            if self.rng.random() < min(0.6, wt) * 0.5 * self.tune("alliance_rate"):
                self.form_alliance(tick, [x, y], room, hour)
                return

    def form_alliance(self, tick, members, room, hour):
        w, s = self.world, self.s
        alid = max([a["id"] for a in s.setdefault("alliances", [])] + [0]) + 1
        secret = self.rng.random() < 0.5
        al = {"id": alid, "members": list(members), "day": self.day, "strength": 3, "status": "active", "secret": secret, "apart": 0}
        s["alliances"].append(al)
        del s["alliances"][:-12]
        names = " and ".join(self.nm(m) for m in members)
        for m in members:
            others = [o for o in members if o != m]
            w.remember(m, f"{_hh(hour)} (private) You and {', '.join(self.nm(o) for o in others)} agreed to look out for each other: you share what you learn and you vouch for each other.")
            for o in others:
                self.add_tie(m, o, "allied", f"we agreed to stand by each other (day {self.day})", 1)
        here = [o for o in w.occupants(room) if o in w.agents and o not in members]
        if not secret:
            for o in here:
                w.remember(o, f"{_hh(hour)} (you saw) {names} openly agreeing to stick together.")
        self.log_event(tick, {"type": "alliance", "who": members[0], "room": room, "vis": "viewer", "text": f"{names} form an alliance" + (" in secret." if secret else ".")}, actor=members[0])
        self.tally(members[0], "alliances")

    # ------------------------------------------------------------------ living with it
    def alliance_tick(self, tick, hour):
        """Strength grows when allies are together and help each other, and fades when they are apart or quarrel; a member who is gone ends it."""
        w = self.world
        for al in self.active_alliances():
            al["members"] = [m for m in al["members"] if m in w.agents]
            if len(al["members"]) < 2:
                al["status"] = "ended"
                continue
            rooms = {w.agents[m]["room"] for m in al["members"]}
            if len(rooms) == 1:
                al["strength"] = min(10, al["strength"] + 0.25)
                al["apart"] = 0
            else:
                al["apart"] += 1
                if al["apart"] >= 4:
                    al["strength"] = max(0, al["strength"] - 0.25)
            for x in al["members"]:
                for y in al["members"]:
                    if x != y and w.agents[x]["aff"].get(y, 0) <= 0:
                        al["strength"] -= 0.5
            if al["strength"] <= 0:
                al["status"] = "ended"
                for m in al["members"]:
                    w.remember(m, f"{_hh(hour)} (private) The understanding you had has faded; nobody is standing by anyone.")
        self.check_betrayals(tick, hour)

    def share_with_allies(self, cid, kind, text, by):
        """What one ally learns about a case, the others learn too."""
        if getattr(self, "_sharing", False) or kind not in ("clue", "testimony"):
            return
        self._sharing = True
        try:
            for o in self.allies_of(cid):
                nb = self.world.agents[o].setdefault("notebook", [])
                if not any(e["text"] == text for e in nb):
                    self.note_evidence(o, kind, text, by)
        finally:
            self._sharing = False

    def alliance_lines(self, cid):
        al = self.alliance_of(cid)
        if not al:
            return []
        allies = ", ".join(self.nm(m) for m in al["members"] if m != cid)
        return [f"YOUR ALLIANCE with {allies} (strength {int(al['strength'])}/10{', secret' if al['secret'] else ''}): you share what you learn and vouch for each other. "
                "It holds as long as it is worth it: if pressure, fear or a better offer makes you want out, you can break with them (\"betray\": their id)."]

    # ------------------------------------------------------------------ breaking faith
    def betrayal_score(self, m, ally):
        w = self.world
        a = w.agents[m]
        pr = self.pressure()
        sc = 0.01 + 0.06 * pr + (0.05 if a["sanity"] < 35 else 0) + (0.03 if a["drive"]["id"] in ("survivor", "schemer") else 0) - 0.01 * max(0, a["aff"].get(ally, 0) - 4)
        if any(h["status"] == "solved" and h["culprit"] == ally and m in h["victims"] for h in self.s.get("hooks", [])):
            sc += 0.2
        if a["aff"].get(ally, 0) <= 0:
            sc += 0.1
        return max(0.0, sc)

    def check_betrayals(self, tick, hour):
        for al in self.active_alliances():
            if al["day"] >= self.day:
                continue                                   # nobody turns on an ally the day they swear to stand by them
            for m in list(al["members"]):
                for ally in [x for x in al["members"] if x != m]:
                    if self.rng.random() < self.goal_odds("betray", self.betrayal_score(m, ally) * (1.0 - al["strength"] / 14) * self.tune("betrayal_rate"), m, ally):
                        self.betray(tick, m, ally, al, hour)
                        break
                if al["status"] != "active":
                    break

    def betray(self, tick, m, ally, al, hour, how=None):
        """m breaks faith with ally: leaks their secret to the room, or renounces them in public. The alliance ends."""
        w = self.world
        if m not in w.agents or ally not in w.agents:
            return
        room = w.agents[m]["room"]
        here = [o for o in w.occupants(room) if o in w.agents and o not in (m, ally)]
        knows = any(k.get("of") == ally for k in w.agents[m].get("known_secrets", []))
        how = how or ("leaks" if knows and here and self.rng.random() < 0.6 else "renounces")
        if how == "leaks" and here:
            self.reveal_secret(tick, m, ally, here, "betrays their ally and tells")
            txt = f"{self.nm(m)} betrays {self.nm(ally)}: their secret is out."
        else:
            txt = f"{self.nm(m)} breaks with {self.nm(ally)} in front of everyone and walks away."
            for o in here:
                w.remember(o, f"{_hh(hour)} (you saw) {self.nm(m)} publicly cut {self.nm(ally)} loose.")
        al["status"] = "broken"
        self.adjust_any_aff(ally, m, -6)
        self.adjust_any_aff(m, ally, -2)
        self.add_tie(ally, m, "betrayed", f"{self.nm(m)} turned on them when it mattered (day {self.day})", 0)
        w.remember(ally, f"{_hh(hour)} (private) {self.nm(m)} betrayed you.")
        self.stat(tick, ally, "sanity", -6, "betrayed by an ally")
        self.stat(tick, m, "sanity", -2, "betraying an ally")
        self.moment(ally, f"was betrayed by {self.nm(m)}")
        self.tally(m, "betrayals")
        self.log_event(tick, {"type": "betrayal", "who": m, "room": room, "vis": "public", "text": txt}, witnesses=here, actor=m)

    # ------------------------------------------------------------------ at a death and at the trial
    def ally_alibis(self, case, hour):
        """Allies of a killer swear to where they were; the loyal lie."""
        w, s = self.world, self.s
        culprit = case.get("killer")
        if not culprit or culprit not in w.agents:
            return
        al = self.alliance_of(culprit)
        if not al:
            return
        for m in al["members"]:
            if m == culprit or m not in w.agents:
                continue
            if self.rng.random() < 0.35 + 0.05 * al["strength"]:
                claim = f"{self.nm(culprit)} was with me the whole time, nowhere near the {w.room_name(case['room'])}."
                case.setdefault("testimonies", []).append({"by": m, "claim": claim, "day": self.day, "hour": hour, "false": True, "ally": True})
                for o in w.agents:
                    if o != m:
                        self.note_evidence(o, "testimony", f"{self.nm(m)} says: {claim}", m)
                w.remember(m, f"{_hh(hour)} (private) You swore {self.nm(culprit)} was with you. You are protecting your ally.")
                self.add_tie(m, culprit, "allied", "I lied for them", 0)

    def trial_betrayals(self, tick, hour, subjects):
        """When the vote closes in on someone's ally, the ally may withdraw the alibi and testify against them."""
        w, s = self.world, self.s
        case = s.get("case")
        if not case:
            return
        for al in self.active_alliances():
            for target in [x for x in al["members"] if x in subjects]:
                for m in [x for x in al["members"] if x != target and x in w.agents]:
                    p = 0.4 - 0.04 * al["strength"] + 0.2 * self.pressure() + (0.15 if w.agents[m]["aff"].get(target, 0) <= 1 else 0)
                    if m == case.get("killer") or self.rng.random() >= max(0.05, p):
                        continue
                    for t in case.get("testimonies", []):
                        if t["by"] == m and t.get("ally"):
                            t["claim"] = f"I lied earlier: {self.nm(target)} was NOT with me."
                            t["false"] = False
                            t["late"] = True
                            t["betrayal"] = True
                    case.setdefault("testimonies", []).append({"by": m, "claim": f"{self.nm(target)} was not with me when I said, and I stopped covering for them.", "day": self.day,
                                                               "hour": hour, "late": True, "betrayal": True})
                    for o in w.agents:
                        if o != m:
                            self.note_evidence(o, "contradiction", f"{self.nm(m)} withdrew the alibi they gave {self.nm(target)}.")
                    self.betray(tick, m, target, al, hour, how="renounces")
                    break
