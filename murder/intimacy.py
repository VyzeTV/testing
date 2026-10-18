"""Off-screen intimacy: nights together, the morning after, jealousy, affairs and rumours. Never explicit.

Lovers (a romance bond between two participants) may spend the night together after lights out; two people who feel strongly about each
other and click may fall into bed for the first time, and are lovers from then on. The feed implies it and cuts away; the
cameras find something urgent to look at in the corridor. Both sleep better for it (sanity, feelings). At dawn one of them is seen leaving
the other's room, and the house talks: whoever notices believes it, and anyone who wanted one of them for themselves is jealous (feelings
sour toward the rival, a little sanity lost, and the jealousy plot motive in plotting.py does the rest). Someone already in a romance who is
drawn hard to someone else may have an affair; if the partner finds out, the romance ends in a row. How often all this happens follows the
`flirt_level` dial (0 = never). IntimacyMixin is mixed into DayRunner (engine.py).
"""

NIGHT_P = {0: 0.0, 1: 0.15, 2: 0.3, 3: 0.45}
NIGHT_TEXT = ["{a} slips into {b}'s room after lights out. The camera develops a sudden interest in the corridor carpet.",
              "{a} knocks softly on {b}'s door at midnight. It opens before the second knock. Cut to: a very long shot of the moon.",
              "{a} and {b} say goodnight in the corridor, twice, and then not at all. The feed cuts to TereVi's screensaver.",
              "{a} turns up at {b}'s door with two glasses and no excuse. The door closes. The audience is left to its imagination."]
MORNING_TEXT = ["{a} leaves {b}'s room at dawn, hair a disaster, trying very hard to look like someone who was just passing.",
                "{a} tiptoes out of {b}'s room at sunrise with their shoes in their hand.",
                "{a} emerges from {b}'s room at dawn wearing one of {b}'s shirts and an expression of total innocence."]


class IntimacyMixin:
    def lovers(self):
        w = self.world
        return [(b["a"], b["b"]) for b in self.s.get("bonds", []) if b.get("kind") == "romance" and b["a"] in w.agents and b["b"] in w.agents]

    def partner_of(self, cid):
        return next((b if a == cid else a for a, b in self.lovers() if cid in (a, b)), None)

    def free_tonight(self, cid):
        a = self.world.agents.get(cid)
        return bool(a) and not a.get("out") and a["room"] not in ("cold_store",) and not a.get("hiding") and not (self.s.get("plots") or {}).get(cid, {}).get("stage") == "striking"

    def intimacy_night(self, tick):
        """After lights out: which lovers spend the night together, and whether anyone strays."""
        w, s = self.world, self.s
        lvl = int(self.tune("flirt_level"))
        if lvl <= 0 or not self.revealed or s.get("case"):
            return []
        p = NIGHT_P[min(3, lvl)]
        out = []
        busy = set()
        for a, b in sorted(self.lovers()):
            if a in busy or b in busy or not (self.free_tonight(a) and self.free_tonight(b)):
                continue
            stray = self.affair_candidate(a) or self.affair_candidate(b)
            if stray and self.rng.random() < 0.06 * lvl:
                x, y = stray
                if y not in busy:
                    self.night_together(tick, x, y, affair=self.partner_of(x))
                    busy |= {x, y}
                    out.append((x, y, "affair"))
                    continue
            if self.rng.random() < p * (1.2 if self.dread_level() >= 2 else 1.0):       # fear makes people reach for each other
                host, guest = sorted((a, b), key=lambda c: (self.rng.random(), c))
                self.night_together(tick, guest, host)
                busy |= {a, b}
                out.append((guest, host, "night"))
        for a, b in self.drawn_pairs():
            if a in busy or b in busy or self.partner_of(a) or self.partner_of(b) or self.rng.random() >= 0.08 * lvl:
                continue
            host, guest = sorted((a, b), key=lambda c: (self.rng.random(), c))
            self.night_together(tick, guest, host)
            s.setdefault("bonds", []).append({"a": a, "b": b, "kind": "romance", "since": self.day})
            self.log_event(tick, {"type": "system_notable", "who": a, "room": w.cast[host]["home"], "vis": "viewer",
                                  "text": f"Whatever {self.nm(a)} and {self.nm(b)} were before tonight, they are something else now."}, actor=b)
            busy |= {a, b}
            out.append((guest, host, "first"))
        return out

    def drawn_pairs(self):
        """Two free people, not lovers yet, who feel strongly about each other and click."""
        w = self.world
        ids = [c for c in sorted(w.agents) if self.free_tonight(c)]
        out = []
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                if min(w.agents[a]["aff"].get(b, 0), w.agents[b]["aff"].get(a, 0)) >= 7 and self.attraction(a, b) * (0.5 + self.chemistry(a, b)) >= 0.5:
                    out.append((a, b))
        return out

    def affair_candidate(self, cid):
        """Someone in a romance, drawn hard to someone else who feels the same."""
        w = self.world
        partner = self.partner_of(cid)
        if not partner or not self.free_tonight(cid):
            return None
        if self.facet(cid, "romantic") < 60 and w.agents[cid]["drive"]["id"] not in ("thrill", "romantic"):
            return None
        a = w.agents[cid]
        pool = [o for o in sorted(w.agents) if o not in (cid, partner) and self.free_tonight(o) and min(a["aff"].get(o, 0), w.agents[o]["aff"].get(cid, 0)) >= 7
                and a["aff"].get(o, 0) > a["aff"].get(partner, 0) - 2]
        return (cid, max(pool, key=lambda o: (a["aff"][o], o))) if pool else None

    def night_together(self, tick, guest, host, affair=None):
        w, s = self.world, self.s
        text = self.rng.choice(NIGHT_TEXT).format(a=self.nm(guest), b=self.nm(host))
        self.log_event(tick, {"type": "romance", "who": guest, "room": w.cast[host]["home"], "vis": "viewer", "text": text}, actor=guest)
        for c, o in ((guest, host), (host, guest)):
            self.stat(tick, c, "sanity", 4, f"a night with {self.nm(o)}")
            w.adjust_aff(c, o, 1)
            w.remember(c, f"(private) You spent the night with {self.nm(o)}." + (f" {self.nm(affair)} must never find out." if affair and c == guest else ""))
        first = not any(n for n in s.get("nights", []) if {n["a"], n["b"]} == {guest, host})
        if first:
            self.moment(guest, f"spent a first night with {self.nm(host)}")
            self.moment(host, f"spent a first night with {self.nm(guest)}")
        s.setdefault("nights", []).append({"a": guest, "b": host, "day": self.day, "affair": affair})
        del s["nights"][:-40]
        self.intimacy_stat("affairs" if affair else "nights")

    def intimacy_dawn(self, tick):
        """The morning after: someone is seen leaving, rumours spread, jealousy bites, and an affair may come out."""
        w, s = self.world, self.s
        for n in [n for n in s.get("nights", []) if n["day"] == self.day and not n.get("dawn")]:
            n["dawn"] = True
            a, b = n["a"], n["b"]
            if a not in w.agents or b not in w.agents:
                continue
            if self.rng.random() < 0.6:
                text = self.rng.choice(MORNING_TEXT).format(a=self.nm(a), b=self.nm(b))
                seen = [o for o in sorted(w.agents) if o not in (a, b) and self.rng.random() < 0.3]
                self.log_event(tick, {"type": "romance", "who": a, "room": w.cast[b]["home"], "vis": "viewer", "text": text}, witnesses=seen, actor=a)
                for o in seen:
                    self.belief_rumor(o, None, a, f"{self.nm(a)} spent the night in {self.nm(b)}'s room", lie=False)
                    self.jealousy(tick, o, a, b)
                    if n.get("affair") == o:
                        self.affair_found(tick, o, a, b)
                if n.get("affair") and n["affair"] in w.agents and n["affair"] not in seen and self.rng.random() < 0.25:
                    self.affair_found(tick, n["affair"], a, b)                    # the house talks, and it gets back to them
            self.booth_note(a, "warm", 2, b)
            self.booth_note(b, "warm", 2, a)

    def jealousy(self, tick, cid, a, b):
        """`cid` wanted `a` or `b` for themselves."""
        w = self.world
        if cid in (a, b) or self.partner_of(cid) in (a, b):
            return
        for want, rival in ((a, b), (b, a)):
            if w.agents[cid]["aff"].get(want, 0) >= 7 and self.facet(cid, "romantic") >= 45:
                w.adjust_aff(cid, rival, -2)
                self.stat(tick, cid, "sanity", -3, f"jealousy over {self.nm(want)}")
                self.add_tie(cid, rival, "jealous", f"spent the night with {self.nm(want)}")
                self.booth_note(cid, "hurt", 2.5, rival)
                self.intimacy_stat("jealousy")
                return

    def affair_found(self, tick, partner, cheat, other):
        w, s = self.world, self.s
        if partner not in w.agents or cheat not in w.agents:
            return
        w.adjust_aff(partner, cheat, -6)
        w.adjust_aff(partner, other, -4)
        self.stat(tick, partner, "sanity", -8, f"finding out about {self.nm(cheat)} and {self.nm(other)}")
        s["bonds"] = [x for x in s.get("bonds", []) if not (x.get("kind") == "romance" and {x["a"], x["b"]} == {partner, cheat})]
        self.add_tie(partner, cheat, "betrayed", f"cheated on them with {self.nm(other)}")
        self.moment(partner, f"found out {self.nm(cheat)} cheated with {self.nm(other)}")
        self.log_event(tick, {"type": "outburst", "who": partner, "room": w.agents[partner]["room"], "vis": "public",
                              "text": f"{self.nm(partner)} finds out about {self.nm(cheat)} and {self.nm(other)}. The row can be heard on every floor."}, actor=cheat)
        self.intimacy_stat("affairs_found")

    def intimacy_stat(self, k):
        st = self.s.setdefault("intimacy", {})
        st[k] = st.get(k, 0) + 1
