"""NeoVi as a person: Kumiko Akimoto.

NeoVi is human. Her real name is Kumiko Akimoto, and the cast does not know it until she trusts someone enough to say it. In the first week she
mostly watches. After that, at night, while the house sleeps, she does her rounds and stops at one door: the person she feels most for, or
the one she is drawn to. Feelings go both ways there (the cast's feelings toward her are kept apart from their feelings for each other, in
`nv_aff`). When the trust is mutual she confides what only she knows: her name, a camera's blind spot, where TereVi keeps something, what
she saw in the dark, or a warning of TereVi's next move. A slow romance can grow with someone she trusts deeply (nights together are
implied, never shown), and it pulls her arc harder than anything else.

Each night she chooses: obey; help (slip someone a part for the way out, unlock a door, blind a camera, warn of a counter); or betray (report
a plan to TereVi). The choice comes from her fear, her feelings, a lover, how far her resolve has come, and a little chance. Helping is risky:
if TereVi catches her, TereVi decides the punishment: a humiliation on air, re-education (her sanity is drained hard and her feelings are
pushed back toward obedience), or making her a participant. As a participant she is a contestant like the rest, under her own name; nobody
is left to replace a housemaid, so no newcomers arrive for the rest of the season. Out of uniform she is herself: reserved, observant, undecided, a
little cat-like, and liable to freeze when her views are challenged (cast `traits`, read by the engine through `has_trait`).
KumikoMixin is mixed into DayRunner (engine.py).
"""
from .data_cast import HOSTS
from .world import BEDROOMS

KUMIKO_ID = "kumiko"
KUMIKO = {"name": "Kumiko Akimoto", "short": "Kumiko", "role": "Former Housemaid", "gender": "female", "age": 24, "origin": "Japan",
          "persona": "Reserved but not shy; people find her a bit odd because she loves the mysteries of life itself. Intelligent, observant and very good at "
                     "reading people. Otherwise an ordinary young woman who knows her pop culture, anime and video games. Does cat-like things without "
                     "noticing. Tries to make enemies of no one, yet tries to do good and to stand up for what she thinks is right. Her weaknesses: she is "
                     "badly undecided, relies too much on herself, and can break when the weight of a situation is too much to bear. Among successful "
                     "celebrities she worries she has no talent at all.",
          "secret": "She was TereVi's housemaid NeoVi: she cleaned up after every death on the island and knows where TereVi keeps her secrets.",
          "likes": "cats, mysteries, anime, video games", "dislikes": "making choices, being put on the spot, TereVi",
          "speech": "Quiet and even, a little deadpan; odd questions about life out of nowhere, the occasional game or anime reference, and long pauses when she cannot decide.",
          "candor": "Polite to everyone and slow to pick a side; when her view is flipped hard or challenged directly she freezes, trapped, and goes quiet.",
          "goals": "Survive, never be anyone's servant again, find out what she is actually good at, and do the right thing if she can work out what it is.",
          "objection": "Wait. That doesn't add up.",
          "traits": ["observant", "undecided", "self_reliant", "catlike", "trapped", "no_talent"],
          "facets": {"anger": 20, "vengefulness": 20, "trust": 45, "gregariousness": 35, "altruism": 70, "assertiveness": 30, "courage": 50, "cruelty": 8,
                     "impulsiveness": 25, "stress_vulnerability": 70, "vanity": 15, "ambition": 30, "curiosity": 88, "orderliness": 60, "humour": 45, "romantic": 50},
          "values": {"truth": 70, "independence": 75, "knowledge": 82, "tranquility": 62, "cooperation": 45, "cunning": 30, "competition": 20}}
CONFIDE = ("name", "blindspot", "cache", "seen", "warning")


class KumikoMixin:
    def nv_feel(self, cid):
        """How someone feels about NeoVi (kept apart from feelings toward the cast)."""
        return (self.world.agents.get(cid) or {}).get("nv_aff", 0)

    def nv_feel_add(self, cid, d):
        a = self.world.agents.get(cid)
        if a is not None:
            a["nv_aff"] = max(-10, min(10, a.get("nv_aff", 0) + int(d)))

    def neovi_maid(self):
        """Is NeoVi still the housemaid (not gone, not a participant)?"""
        nv = self.s["npcs"]["neovi"]
        return nv.get("room") not in (None, "none") and not nv.get("participant")

    def neovi_lover(self):
        """Her lover, kept on her own record (bonds are between participants only); it cools when either side does."""
        nv = self.s["npcs"]["neovi"]
        o = nv.get("lover")
        if o and (o not in self.world.agents or min(nv["aff"].get(o, 0), self.nv_feel(o)) < 3):
            if o not in self.world.agents and self.world.state["agents"].get(o, {}).get("status") == "dead":
                nv["sanity"] = max(0, nv.get("sanity", 70) - 15)          # she grieves where nobody can see
            nv["lover"] = None
            o = None
        return o

    # ------------------------------------------------------------------ the night visit
    def neovi_visit(self, tick):
        """Her rounds at night: one door, a few quiet words, feelings both ways; confidences once trust is mutual."""
        w, s = self.world, self.s
        if not self.revealed or not self.neovi_maid() or not w.agents:
            return None
        nv = s["npcs"]["neovi"]
        nv.setdefault("sanity", 70)
        if self.day <= 2 and self.rng.random() < 0.7:
            return None                                       # the first week she mostly watches
        lover = self.neovi_lover()
        cid = lover or max(sorted(w.agents), key=lambda c: (nv["aff"].get(c, 0) + self.nv_feel(c) + self.rng.random() * 3, c))
        name = self.nm(cid)
        mine, theirs = nv["aff"].get(cid, 0), self.nv_feel(cid)
        warm = theirs >= 0 and self.facet(cid, "altruism") + self.facet(cid, "curiosity") > 90
        if theirs < -3:
            text = f"NeoVi stops at {name}'s door, hears them stir, and walks on."
            self.neovi_event(tick, cid, text)
            return {"who": cid, "kind": "passed"}
        self.adjust_any_aff("neovi", cid, 1)
        self.nv_feel_add(cid, 1 if warm or mine >= 3 else 0)
        mine, theirs = nv["aff"].get(cid, 0), self.nv_feel(cid)
        out = {"who": cid, "kind": "talk"}
        if lover == cid:
            text = f"NeoVi slips into {name}'s room after midnight and locks the door behind her. What happens next, the cameras are not allowed to see."
            self.nv_feel_add(cid, 1)
            self.stat(tick, cid, "sanity", 3, "a night with Kumiko")
            nv["sanity"] = min(100, nv["sanity"] + 4)
            out["kind"] = "night"
        else:
            text = self.rng.choice([f"NeoVi lingers at {name}'s door with a stack of towels. They talk, quietly, for longer than either meant to.",
                                    f"NeoVi brings {name} a cup of tea nobody asked for and sits on the end of the bed for a while.",
                                    f"{name} catches NeoVi mid-round, and for once she does not hurry away."])
        self.neovi_event(tick, cid, text)
        if mine >= 5 and theirs >= 5:
            out["confided"] = self.neovi_confide(tick, cid)
        if lover is None and mine >= 7 and theirs >= 7 and self.facet(cid, "romantic") >= 45 and self.rng.random() < 0.35:
            nv["lover"] = cid
            nv.setdefault("lovers", []).append(cid)
            self.neovi_event(tick, cid, f"Something changes between {name} and NeoVi tonight. Neither of them says what.")
            self.moment(cid, "fell for NeoVi (Kumiko)")
            out["romance"] = True
        return out

    def neovi_confide(self, tick, cid):
        """One thing only she knows, handed over as a real belief or a real step on the way out."""
        w, s = self.world, self.s
        nv = s["npcs"]["neovi"]
        told = nv.setdefault("told", {}).setdefault(cid, [])
        kinds = [k for k in CONFIDE if k not in told or k in ("seen", "warning")]
        if nv["aff"].get(cid, 0) < 6 or self.nv_feel(cid) < 6:
            kinds = [k for k in kinds if k != "name"]
        if not kinds:
            return None
        kind = "name" if "name" in kinds and self.rng.random() < 0.5 else self.rng.choice(kinds)
        name = self.nm(cid)
        rid = w.agents[cid].get("route") or "transmit"
        rt = s["escape"]["routes"].get(rid)
        if kind == "name":
            text = f"NeoVi tells {name} her real name: Kumiko. Kumiko Akimoto. She has not said it out loud in years."
            w.remember(cid, "NeoVi's real name is Kumiko Akimoto. She trusted you with it.")
            self.moment(cid, "learned NeoVi's real name: Kumiko Akimoto")
        elif kind == "blindspot" and rt:
            rt.setdefault("parts", {})["blind_aid"] = rt.get("parts", {}).get("blind_aid", 0) + 1
            text = f"NeoVi shows {name} a blind spot between two cameras, and the minute every night when the feed stutters."
        elif kind == "cache" and rt:
            step = self.escape_step_for(rid) or next(iter(rt["plan"]))
            rt.setdefault("parts", {})[step] = rt.get("parts", {}).get(step, 0) + 1
            text = f"NeoVi tells {name} where TereVi keeps the spare parts she confiscated, and how to get at them."
        elif kind == "seen" and nv.get("seen"):
            e = nv["seen"][-1]
            if e["who"] in w.agents:
                self.believe(cid, {"k": "has" if e.get("kind") == "weapon" else "rumor", "s": e["who"], "n": f"NeoVi saw {self.nm(e['who'])} {e['what']}",
                                   "src": "told", "by": None, "c": 0.8, "t0": self.abs_now(), "true": True})
            text = f"NeoVi tells {name} what she saw in the dark: {self.nm(e['who'])} {e['what']}."
        else:
            nv["warned"] = rid
            text = f"NeoVi warns {name}: TereVi knows about the way out. She will strike at it soon."
        told.append(kind)
        self.neovi_event(tick, cid, text, vis="viewer")
        return kind

    def neovi_event(self, tick, cid, text, vis="viewer"):
        self.log_event(tick, {"type": "neovi", "who": "neovi", "room": self.world.agents[cid]["room"] if cid in self.world.agents else "laundry",
                              "vis": vis, "text": text}, actor=cid)

    # ------------------------------------------------------------------ the nightly choice
    def neovi_choice(self, tick):
        """Obey, help or betray tonight. Returns the choice."""
        w, s = self.world, self.s
        if not self.revealed or not self.neovi_maid() or not w.agents:
            return None
        nv = s["npcs"]["neovi"]
        nv.setdefault("sanity", 70)
        arc = self.neovi_arc()
        lover = self.neovi_lover()
        friends = sorted([c for c in w.agents if nv["aff"].get(c, 0) >= 5], key=lambda c: (-nv["aff"].get(c, 0), c))
        help_w = 0.1 + 0.15 * arc.get("stage", 0) + (0.35 if lover else 0) + (0.05 * len(friends)) - nv["fear"] / 25 \
            + (0.04 * (nv["aff"][friends[0]] - 5) if friends else 0)
        betray_w = nv["fear"] / 18 + (0.25 if nv["sanity"] < 30 else 0) - (0.5 if lover else 0) - 0.05 * len(friends)
        roll = self.rng.random()
        if friends and roll < max(0.0, help_w):
            return self.neovi_help(tick, lover or friends[0])
        if roll > 1 - max(0.0, betray_w) * 0.5:
            return self.neovi_betray(tick)
        return "obey"

    def neovi_help(self, tick, ally):
        w, s = self.world, self.s
        nv = s["npcs"]["neovi"]
        rid = w.agents[ally].get("route") or "transmit"
        rt = s["escape"]["routes"].get(rid)
        kind = self.rng.choice(["part", "door", "camera", "cover"])
        if kind == "part" and rt:
            step = self.escape_step_for(rid) or next(iter(rt["plan"]))
            rt.setdefault("parts", {})[step] = rt.get("parts", {}).get(step, 0) + 1
            text = f"NeoVi leaves something under {self.nm(ally)}'s pillow: exactly the part they were missing."
        elif kind == "door":
            s.setdefault("unlocked", [])
            s["locks"] = {r: v for r, v in (s.get("locks") or {}).items() if v.get("by") != "terevi"}
            text = f"Every door TereVi locked is quietly open again by morning. NeoVi's master key, {self.nm(ally)} guesses."
        elif kind == "camera" and rt:
            rt.setdefault("parts", {})["blind_aid"] = rt.get("parts", {}).get("blind_aid", 0) + 1
            text = f"For an hour tonight one camera shows only a looped corridor. NeoVi did that, for {self.nm(ally)}."
        else:
            nv["warned"] = rid
            text = f"NeoVi covers for {self.nm(ally)}: her report to TereVi tonight leaves out where they were."
        self.neovi_event(tick, ally, text)
        self.adjust_any_aff("neovi", ally, 1)
        self.nv_feel_add(ally, 2)
        nv["helped"] = nv.get("helped", 0) + 1
        if self.rng.random() < min(0.3, 0.08 + 0.03 * nv["helped"] - 0.02 * self.neovi_arc().get("stage", 0)):
            self.neovi_caught(tick, ally)
            return "caught"
        return "help"

    def neovi_betray(self, tick):
        w, s = self.world, self.s
        nv = s["npcs"]["neovi"]
        from .data_world import ESCAPE_ROUTES
        top = max(ESCAPE_ROUTES, key=lambda r: (self.route_pct(r), r))
        if self.route_pct(top) >= 20:
            self.terevi_reinforce(tick, top, "NeoVi reported it")
            text = "NeoVi makes her report to TereVi tonight, and leaves nothing out."
        else:
            text = "NeoVi tells TereVi who has been talking behind her back."
            for c in sorted(w.agents):
                if self.nv_feel(c) >= 3:
                    self.stat(tick, c, "sanity", -2, "TereVi seems to know everything")
        nv["fear"] = max(0, nv["fear"] - 1)
        self.log_event(tick, {"type": "neovi", "who": "neovi", "room": nv["room"], "vis": "viewer", "text": text})
        return "betray"

    # ------------------------------------------------------------------ caught: TereVi decides
    def neovi_caught(self, tick, ally):
        w, s = self.world, self.s
        nv = s["npcs"]["neovi"]
        nv["caught"] = nv.get("caught", 0) + 1
        p_join = 0.1 + 0.15 * (nv["caught"] - 1) + (0.15 if self.neovi_lover() else 0)
        r = self.rng.random()
        if r < p_join and not s.get("over"):
            nv.setdefault("punished", []).append({"day": self.day, "kind": "participant"})
            return self.make_participant(tick)
        if r < p_join + 0.4:
            nv["sanity"] = max(0, nv.get("sanity", 70) - 25)
            nv["fear"] = min(10, nv["fear"] + 4)
            for c in nv["aff"]:
                nv["aff"][c] = nv["aff"][c] // 2
            arc = self.neovi_arc()
            arc["resolve"] = max(0, arc.get("resolve", 0) - 30)
            text = ("TereVi caught NeoVi helping. She is taken away for 're-education'. When she comes back the next morning she does not look at anyone, "
                    "and she answers to nothing but 'NeoVi'.")
            kind = "re-education"
        else:
            nv["sanity"] = max(0, nv.get("sanity", 70) - 10)
            nv["fear"] = min(10, nv["fear"] + 2)
            text = "TereVi caught NeoVi helping and makes an example of her on air: on her knees in the Foyer, apologising to the audience, again and again."
            kind = "humiliation"
        nv.setdefault("punished", []).append({"day": self.day, "kind": kind})
        self.terevi_says(tick, text if kind == "humiliation" else "Our housemaid has been a naughty girl. She's getting a little... refresher. Hehe.")
        self.log_event(tick, {"type": "system_notable", "who": "neovi", "room": "foyer", "vis": "public", "text": text}, witnesses=list(w.agents))
        for c in sorted(w.agents):
            if self.nv_feel(c) >= 3 or c == ally:
                self.stat(tick, c, "sanity", -3, "what TereVi did to NeoVi")
        return "caught"

    def make_participant(self, tick):
        """TereVi's harshest punishment: the housemaid becomes a contestant. Nobody can replace her, so no newcomers arrive after this."""
        w, s = self.world, self.s
        nv = s["npcs"]["neovi"]
        spec = dict(KUMIKO)
        cast = dict(spec)
        taken = {}
        for c in w.agents:
            taken[s["cast"][c]["home"]] = taken.get(s["cast"][c]["home"], 0) + 1
        home = min(BEDROOMS, key=lambda r: (taken.get(r, 0), r))
        cast.update({"pron": "she", "color": HOSTS["neovi"]["color"], "card": "", "home": home,
                     "mock_lines": ["I know this house. Every inch.", "Do you ever wonder why any of us are here? Not here here. Here.",
                                    "...I can't decide. Give me a minute.", "Everyone here is famous for something. I fold towels.",
                                    "You blinked twice before you answered. Just saying."]})
        s["cast"][KUMIKO_ID] = cast
        aff = {c: nv["aff"].get(c, 0) for c in w.agents}
        s["agents"][KUMIKO_ID] = {"status": "alive", "room": nv.get("room") if nv.get("room") not in (None, "none") else "foyer", "hp": 90,
                                  "sanity": nv.get("sanity", 60), "inv": {"bandages": 1}, "known": list(s.get("found_edges", [])),
                                  "route": "shutdown", "drive": {"id": "survivor", "target": None, "arc": ""}, "known_secrets": [],
                                  "activity": "Back in her own clothes for the first time in years, rabbit in hand", "aff": aff,
                                  "memory": {"diary": [f"Day {self.day}: TereVi made me one of them. My name is Kumiko Akimoto."], "recent": [], "notes": [], "lost": [], "moments": []}}
        for c in list(w.agents):
            if c != KUMIKO_ID:
                w.agents[c]["aff"][KUMIKO_ID] = self.nv_feel(c)
        lover = self.neovi_lover()
        if lover:
            s.setdefault("bonds", []).append({"a": lover, "b": KUMIKO_ID, "kind": "romance", "since": self.day})
        nv["room"] = "none"
        nv["participant"] = True
        self.neovi_arc()["fate"] = "participant"
        s["no_newcomers"] = True
        vac = next((i for i, v in enumerate(s.get("vacancies", [])) if v["gender"] == "female"), None)
        if vac is not None:
            del s["vacancies"][vac]
        text = ("TereVi strips NeoVi of her uniform and her keys in front of everyone. \"Congratulations, darling. You're a contestant now.\" "
                "For the first time, the cast hears her real name: Kumiko Akimoto.")
        self.terevi_says(tick, "Let's give a warm welcome to our newest contestant! Say hello, Kumiko. Hehe.")
        self.log_event(tick, {"type": "system_notable", "who": KUMIKO_ID, "room": "foyer", "vis": "public", "text": text}, witnesses=list(w.agents))
        for c in sorted(w.agents):
            w.remember(c, text)
            if c != KUMIKO_ID and self.nv_feel(c) >= 3:
                self.moment(c, "watched TereVi make NeoVi (Kumiko) a contestant")
        self.saga("TereVi made NeoVi a contestant: Kumiko Akimoto. No newcomers will come after her.")
        return "participant"
