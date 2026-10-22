"""Rare turns: engine events with a cause, rolled rarely, so seasons can swerve hard.

* A death pact: when the last call ends in silence, two lovers who have nothing left (both under 45 sanity, one under 35) choose to go together before the deadline chooses for them. Two deaths
  by their own hand: no trial, and the deadline is lifted for everyone else.
* A murder-suicide: a broken lover (sanity under 20) who has come to believe the other is betraying them, or found out an affair, kills
  them in the night and then themselves. No trial: the one responsible is dead.
* At the trial, just before the vote: a guilt-sick killer confesses; or someone who loves the killer takes the blame for them; or NeoVi,
  who saw it, stands up and names the killer (TereVi deals with her afterwards).
* An escapee comes back: a raft at sea is carried back to the island by the current.
* A hallucination that turns into a real killing is counted when a paranoid plot (innervoice.py) kills.
Each is counted in s["twists"] for the season report. TwistMixin is mixed into DayRunner (engine.py).
"""


class TwistMixin:
    def twist(self, k):
        t = self.s.setdefault("twists", {})
        t[k] = t.get(k, 0) + 1

    # ------------------------------------------------------------------ two deaths at once
    def two_deaths(self, tick, first, second, cause, how_second, text):
        """`first` dies by their own hand and `second` with them, in the same room; announced without a trial (cases.announce_body)."""
        w = self.world
        room = w.agents[first]["room"]
        w.agents[second]["room"] = room
        hour = self.s.get("_hour", tick.get("hour", 12))
        case = self.open_case(tick, "suicide", first, room=room, cause=cause, hour=hour)
        w.agents[second]["hp"] = 0
        w.end_agent(second, "dead", how_second)
        case["extra_victims"] = [second]
        self.log_event(tick, {"type": "system_notable", "who": first, "room": room, "vis": "viewer", "text": text}, actor=second)
        self.saga(text)
        return case

    def death_pact(self, tick, hour):
        """After a silent last call: lovers with nothing left may go together."""
        w, s = self.world, self.s
        if not self.revealed or s.get("case") or s.get("deadline_day") != self.day or hour < 18 or s.get("_pact_day") == self.day:
            return None
        s["_pact_day"] = self.day
        for a, b in sorted(self.lovers()):
            if max(w.agents[a]["sanity"], w.agents[b]["sanity"]) < 45 and min(w.agents[a]["sanity"], w.agents[b]["sanity"]) < 35 and self.rng.random() < 0.4:
                text = (f"{self.nm(a)} and {self.nm(b)} are found together, hands still linked. They chose to go before the deadline could choose for them, "
                        "and in doing so lifted it for everyone else.")
                self.two_deaths(tick, a, b, f"a pact: {self.nm(a)} and {self.nm(b)} took their own lives together", "took their own life (a pact)", text)
                self.twist("death_pact")
                return (a, b)
        return None

    def murder_suicide(self, tick):
        """At night: a broken lover who believes the worst kills the other, then themselves."""
        w, s = self.world, self.s
        if not self.revealed or s.get("case") or not self.murders:
            return None
        for a, b in sorted(self.lovers()):
            for x, y in ((a, b), (b, a)):
                if w.agents[x]["sanity"] >= 20:
                    continue
                believes = any((bl.get("hal") or bl.get("warp")) and bl.get("s") == y for bl in self.beliefs(x))
                betrayed = any(n.get("affair") == x for n in s.get("nights", []) if y in (n["a"], n["b"]))
                if (believes or betrayed) and self.rng.random() < 0.2:
                    text = (f"{self.nm(x)} goes to {self.nm(y)} in the dark, convinced of something that may never have been true. "
                            f"In the morning they are both dead: {self.nm(y)} at {self.nm(x)}'s hand, and {self.nm(x)} by their own.")
                    self.two_deaths(tick, x, y, f"{self.nm(x)} killed {self.nm(y)} and then themselves", "murdered by their lover", text)
                    self.twist("murder_suicide")
                    return (x, y)
        return None

    # ------------------------------------------------------------------ at the trial, before the vote
    def trial_twist(self, beats, ids, killer, meter, push, case):
        """At most one: a killer's confession, a lover taking the blame, or NeoVi naming the killer. Returns the kind or None."""
        w, s = self.world, self.s
        if not killer or killer not in ids:
            return None
        lead = max(ids, key=lambda p: (meter[p], p))
        victim = case.get("victim")
        guilt = (w.agents[killer]["sanity"] < 30 or self.facet(killer, "altruism") >= 60 or case.get("kind") == "manslaughter"
                 or (w.all_agents.get(killer) or {}).get("aff", {}).get(victim, 0) >= 3)
        if case.get("culprit_aware", True) and guilt and self.rng.random() < 0.1:
            self.trial_beat(beats, killer, f"Stop. Stop it. It was me. I killed {self.nm(victim)}. I can't let anyone else die for it.", "confess")
            push(killer, 12.0)
            self.moment(killer, f"confessed to killing {self.nm(victim)} at the trial")
            self.twist("confession")
            return "confession"
        if lead == killer:
            loves = [o for o in ids if o != killer and (self.partner_of(o) == killer or w.agents[o]["aff"].get(killer, 0) >= 8) and self.facet(o, "altruism") >= 50]
            if loves and self.rng.random() < 0.3:
                o = max(loves, key=lambda c: (w.agents[c]["aff"].get(killer, 0), c))
                self.trial_beat(beats, o, f"Leave {self.nm(killer)} alone. It was me. I did it. Vote for me.", "blame")
                push(o, meter[killer] + 4.0)
                push(killer, -3.0)
                self.moment(o, f"took the blame for {self.nm(killer)} at the trial")
                self.twist("took_blame")
                return "took_blame"
        nv = s["npcs"]["neovi"]
        if (self.neovi_maid() and lead != killer and case.get("neovi_facts") and self.neovi_arc().get("stage", 0) >= 2
                and nv["aff"].get(lead, 0) >= -2 and self.rng.random() < 0.35):
            self.trial_beat(beats, "neovi", f"...No. It wasn't {self.nm(lead)}. I saw {self.nm(killer)}. I saw them.", "defect")
            push(killer, 6.0)
            push(lead, -2.0)
            self.twist("neovi_defects")
            self._neovi_defected = True
            return "neovi_defects"
        return None

    def after_trial_twist(self, tick):
        """TereVi deals with a housemaid who spoke out of turn."""
        if self.__dict__.pop("_neovi_defected", False) and self.neovi_maid():
            self.neovi_caught(tick, None)

    # ------------------------------------------------------------------ out at sea
    def raft_returns(self, tick, crew):
        """The current carries a raft back to the island. Its crew are participants again, half drowned."""
        w, s = self.world, self.s
        back = [c for c in crew["alive"] if s["agents"].get(c, {}).get("status") == "escaped"]
        if not back:
            return False
        for c in back:
            a = s["agents"][c]
            a.update(status="alive", room="beach", hp=max(30, a.get("hp", 60) - 20), sanity=max(10, a.get("sanity", 50) - 15), activity="Washed up on the beach")
            a.pop("asleep", None)
            s["graveyard"] = [g for g in s["graveyard"] if g["id"] != c]
            vac = next((i for i, v in enumerate(s.get("vacancies", [])) if v["gender"] == w.cast[c]["gender"]), None)
            if vac is not None:
                del s["vacancies"][vac]
            self.moment(c, "was carried back to the island by the sea")
        crew["stage"] = "returned"
        crew["alive"] = []
        names = ", ".join(self.nm(c) for c in back)
        text = f"The tide brings the raft back. {names} crawl{'s' if len(back) == 1 else ''} up the beach, half drowned, back where they started."
        self.log_event(tick, {"type": "system_notable", "who": back[0], "room": "beach", "vis": "public", "text": text, "story_kind": "raft_return", "returned": list(back)}, witnesses=list(w.agents))
        self.terevi_says(tick, f"Welcome BACK, {names}! Did you miss us? We missed you. The ratings missed you. Hehe.")
        self.saga(text)
        self.twist("raft_returned")
        return True
