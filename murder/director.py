"""The auto-director: when the island goes quiet, it nudges the story along (a TereVi dare, a rumour, an unsigned note or an island event).
Most of the time it pushes the hottest story already forming (sifting.py) one step, aimed at the people in it.

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
        if self.dares_failed() and not self.s.get("case") and hour < 20 and self.rng.random() < 0.5:     # someone ignored TereVi's dare (torments.py)
            who = self.dares_failed()[0]["who"]
            kind = self.torment_auto(tick)
            if kind:
                self.log_event(tick, {"type": "director", "who": "terevi", "room": "foyer", "vis": "viewer",
                                      "text": f"Auto-director: {self.nm(who)} ignored TereVi's dare, so TereVi torments them ({kind})."})
        busy = sum(1 for e in tick["events"] if e["type"] in NOTABLE)
        self.quiet = max(0, self.quiet - 1) if busy else self.quiet + 1
        if (self.quiet < 3 or self.dir_used >= 2 or self.s.get("case") or self.s.get("spree") or hour >= 20 or len(self.world.agents) < 4):
            return
        self.quiet = 0
        self.dir_used += 1
        self.director_act(tick, hour)

    def story_move(self, tick, hour, st):
        """Push the hottest story in play one step: a rumour, an unsigned note or a TereVi provocation aimed at its people. Returns the text, or ''."""
        w = self.world
        p = [c for c in st["people"] if c in w.agents]
        if not p:
            return ""
        k, a = st["kind"], p[0]
        b = p[1] if len(p) > 1 else None
        c = p[2] if len(p) > 2 else None
        note = lambda who, text: (w.remember(who, f"{_hh(hour)} You find an unsigned note: \"{text}\""), self.moment(who, f"found an unsigned note: {text[:60]}"))
        if k == "triangle" and c:
            ok = self.spread_rumor(tick, "unknown", b, f"{self.nm(b)} and {self.nm(c)} were seen together very late last night", "bad", True, [a], w.agents[a]["room"], hour)
            return f"a rumour about {self.nm(b)} and {self.nm(c)} reaches {self.nm(a)}" if ok else ""
        if k in ("enemies_alone", "lovers_breaking", "near_freedom") and b:
            self.force_tease = (f"Dare {self.nm(a)} and {self.nm(b)} to settle what is between them, tonight, alone." if k == "enemies_alone" else
                                f"Offer {self.nm(a)} and {self.nm(b)} a cruel bargain on air: one of them can sleep safe tonight, if the other volunteers for something." if k == "lovers_breaking" else
                                "Let it slip that you know exactly how close they are to a way out, and that you are looking forward to it.")
            return f"TereVi is pointed at {self.nm(a)} and {self.nm(b)}"
        if k in ("betrayed_protector", "grudge") and b:
            note(b if k == "betrayed_protector" else a, f"You know what {self.nm(a if k == 'betrayed_protector' else b)} did. So does everyone else.")
            return f"an unsigned note stirs up {self.nm(b if k == 'betrayed_protector' else a)}"
        if k == "contradiction_fear" and b:
            note(a, f"Tell the others what you know about {self.nm(b)}. Or keep quiet, and wait to see what {self.nm(b)} does about you.")
            return f"an unsigned note pushes {self.nm(a)} to speak up about {self.nm(b)}"
        if k == "secret_held" and b:
            note(b, f"{self.nm(a)} knows. And {self.nm(a)} is not your friend.")
            return f"an unsigned note tells {self.nm(b)} that {self.nm(a)} knows their secret"
        if k == "alliance_strain" and b:
            ok = self.spread_rumor(tick, "unknown", b, f"{self.nm(b)} has been talking about {self.nm(a)} behind their back", "bad", True, [a], w.agents[a]["room"], hour)
            return f"a rumour strains the alliance of {self.nm(a)} and {self.nm(b)}" if ok else ""
        if k in ("plot_suspected", "silent_witness", "plot") and b:
            who = b if k in ("plot_suspected", "plot") else a
            note(who, "Someone in this house is watching you very closely. Don't go anywhere alone.")
            return f"an unsigned note warns {self.nm(who)}"
        if k == "unrequited" and b:
            note(a, f"{self.nm(b)} laughs about you when you leave the room.")
            return f"an unsigned note hurts {self.nm(a)}"
        return ""

    def director_act(self, tick, hour):
        w = self.world
        stories = self.stories_in_play(3)
        if stories and self.rng.random() < 0.65:                  # most of the time, push a story already forming (sifting.py)
            st = stories[0]
            text = self.story_move(tick, hour, st)
            if text:
                st["pushed"] = st.get("pushed", 0) + 1
                self.log_event(tick, {"type": "director", "who": "terevi", "room": "foyer", "vis": "viewer", "text": f"Auto-director (story: {st['text']}): {text}."})
                self.day_notable.append("The auto-director pushed a story: " + text[:80])
                return
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
