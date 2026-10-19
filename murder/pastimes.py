"""Pastimes: things people do together or alone in free time that the engine resolves without a model call, each with small feelings and sanity at stake.

Shared: a film in the lounge, the sunset, karaoke, cards, a campfire on the beach, taking pictures, a proper meal cooked for everyone. The one who starts it
invites idle friends nearby; how it goes is decided at the end from who is there and what they are like (a shy person dreads karaoke, a rival spoils the film,
the grieving get through a sunset, a couple gets closer). Talks: two people talk about a subject, a person or something that happened on the island, and the
engine decides how it went (they agree, swap stories, grumble together, or fall out); it is a feed line, not voiced lines, so it costs nothing. Alone: a journal,
a workout, sitting quietly, practising their talent, crying where nobody sees, pacing, fishing, a letter home, sunbathing. Counts in s["pastimes"].
PastimeMixin is mixed into DayRunner (engine.py); the acts are part of freetime.ACTS.
"""

# act: (label, minutes, rooms, furniture, verb) - merged into freetime.ACTS
PASTIME_ACTS = {
    "film":     ("watching a film", 60, ["lounge"], ["sofa", "armchair"], "puts an old film on the projector"),
    "sunset":   ("watching the sunset", 30, ["lookout", "beach", "pool"], ["bench", "deckChair"], "watches the sun go down"),
    "karaoke":  ("singing karaoke", 30, ["lounge"], ["jukebox"], "starts a karaoke round"),
    "cards":    ("playing cards", 30, ["lounge", "dining_hall", "games_room"], ["table"], "deals a hand of cards"),
    "campfire": ("sitting by the fire", 45, ["beach"], ["firepit"], "lights the fire pit"),
    "photos":   ("taking pictures", 30, ["beach", "lookout", "garden", "greenhouse"], [], "takes pictures"),
    "feast":    ("cooking for everyone", 60, ["kitchen"], ["stove"], "cooks a proper meal for everyone"),
    "talk":     ("talking", 20, [], [], "falls to talking"),
    "journal":  ("writing in their journal", 30, [], ["desk"], "writes in a journal"),
    "exercise": ("working out", 30, ["beach", "garden", "pool"], [], "works out"),
    "meditate": ("sitting quietly with their thoughts", 20, ["greenhouse", "garden", "lookout", "observatory"], [], "closes their eyes and breathes"),
    "practise": ("practising their talent", 45, [], [], "practises"),
    "cry":      ("crying quietly", 15, [], [], "cries quietly where nobody can see"),
    "pace":     ("pacing", 15, [], [], "paces back and forth"),
    "fish":     ("fishing off the rocks", 45, ["beach"], [], "fishes off the rocks"),
    "letter":   ("writing a letter home", 30, [], ["desk"], "writes a letter home"),
    "sunbathe": ("sunbathing", 30, ["pool", "beach"], ["deckChair"], "lies in the sun"),
}
SHARED = {"film": 5, "sunset": 4, "karaoke": 5, "cards": 4, "campfire": 5, "photos": 3}       # act: most people
PREOCCUPIED = 0.3          # pastimes (other than talks) count for this much while a death is investigated
QUIET = {"journal", "letter", "cry", "pace", "meditate"}                                       # fine at night
SUBJECTS = ("home", "the food they miss", "music", "what they will do when they get out", "the way out", "their talents", "TereVi", "the audience watching",
            "old friends", "first loves", "their families", "the worst job they ever had")
TALENT = {"Urban Explorer": "climbing the rocks behind the house", "Competitive Gamer": "running drills on a handheld", "Hacker": "picking at the house's wiring",
          "Musician": "working out a new song", "Photographer": "framing shots of the island", "Artist": "sketching", "Prodigy Student": "working through a proof in the margins of a book",
          "Internet Celebrity": "filming a video for followers who will never see it", "Former Housemaid": "folding everything in sight"}


class PastimeMixin:
    def pastime_stat(self, act, how="done"):
        st = self.s.setdefault("pastimes", {})
        k = f"{act}_{how}"
        st[k] = st.get(k, 0) + 1

    def pastime_options(self, tick, cid, hour, m, add, f, mi, here):
        """What pastimes suit this person right now (added to the free-time choice)."""
        w = self.world
        a = w.agents[cid]
        case = self.s.get("case")
        if case and case.get("announced") and not case.get("resolved"):
            add0 = add                                           # a death under investigation: nobody is in the mood for films and karaoke
            add = lambda score, act, *x, **k: add0(score * (1.0 if act == "talk" else PREOCCUPIED), act, *x, **k)
        night = tick.get("phase") == "night"
        clock = hour + m / 60
        gr, cur, rom = f("gregariousness"), f("curiosity"), f("romantic")
        stress = self.mind(cid)["stress"] if self.mind_on() else 30
        fun = (100 - mi["purpose"]) / 70 + (100 - mi["social"]) / 90
        lost = any(x.get("day", 0) >= self.day - 2 for x in a["memory"].get("lost", []))
        if not night:
            add(0.3 + fun * 0.35 + (0.35 if hour >= 16 else 0) + (gr - 45) / 220, "film", why="a film")
            if 18.4 <= clock <= 19.8:
                add(0.75 + (rom - 40) / 110 + (0.4 if lost else 0), "sunset", why="the sunset")
            add(0.1 + (gr - 50) / 70 + (f("vanity") - 50) / 120 + (0.3 if hour >= 18 else 0) - (0.4 if stress >= 60 else 0), "karaoke", why="karaoke")
            add(0.32 + fun * 0.3 + (f("impulsiveness") - 45) / 200, "cards", why="a game of cards")
            if clock >= 19:
                add(0.4 + (gr - 40) / 150 + (rom - 45) / 200, "campfire", why="a fire on the beach")
            if any(a["inv"].get(k, 0) > 0 for k in ("gopro", "dslr")) or w.cast[cid].get("role") == "Photographer":
                add(0.45 + (cur - 40) / 120, "photos", why="pictures")
            if 10 <= hour <= 17:
                add(0.28 + 0.35 * (f("altruism") - 45) / 55 + 0.2 * (f("orderliness") - 45) / 55, "feast", why="a proper meal for everyone")
            add(0.3 + (f("courage") - 45) / 140 + stress / 260, "exercise", why="burning off nerves")
            add(0.34 + (100 - mi["purpose"]) / 80, "practise", why="keeping their talent sharp")
            add(0.32 + (100 - mi["privacy"]) / 150 + (0.25 if a.get("hunger", 0) >= 40 else 0), "fish", why="fishing")
            if 10 <= hour <= 16:
                add(0.3 + (f("vanity") - 45) / 150, "sunbathe", why="the sun")
        add(0.22 + (100 - mi["privacy"]) / 130 + (0.25 if a["sanity"] < 60 else 0) + (f("orderliness") - 45) / 220, "journal", home_only=True, why="their journal")
        add(0.28 + stress / 160 + (f("orderliness") - 50) / 250, "meditate", why="some quiet")
        add(0.22 + (100 - mi["purpose"]) / 160 + (0.3 if lost else 0), "letter", home_only=True, why="a letter home")
        if a["sanity"] < 45 or lost:
            add((45 - min(a["sanity"], 45)) / 25 + (0.6 if lost else 0), "cry", rooms=[w.cast[cid]["home"], "bathroom"], why="needs to cry where nobody sees")
        if stress >= 60:
            add((stress - 55) / 40, "pace", room=here, why="too wound up to sit")
        self.talk_options(tick, cid, m, add, f, mi, here)

    # ------------------------------------------------------------------ an unvoiced talk
    def talk_options(self, tick, cid, m, add, f, mi, here):
        w = self.world
        busy = self._free_busy or {}
        mates = [o for o in sorted(w.occupants(here)) if o in w.agents and o != cid and self._aff(cid, o) >= 0 and self._available(tick, o, m, busy)
                 and not w.agents[o].get("asleep") and not w.agents[o].get("out")]
        if not mates:
            return
        o = max(mates, key=lambda x: (self._aff(cid, x), x))
        add(0.5 + (100 - mi["social"]) / 90 + self._aff(cid, o) / 14 + (f("gregariousness") - 50) / 150, "talk", room=here, why=f"a talk with {self.nm(o)}", partner=o)

    def talk_topic(self, a, b):
        """(kind, about, text) for what two people talk about."""
        w, s = self.world, self.s
        recent = [g for g in s.get("graveyard", []) if g.get("day", 0) >= self.day - 1 and g.get("id") in w.cast]
        case = s.get("case")
        if recent and self.rng.random() < (0.85 if case and case.get("announced") and not case.get("resolved") else 0.5):
            v = recent[-1]["id"]
            return "death", v, f"what happened to {self.nm(v)}"
        absent = [x for x in sorted(w.agents) if x not in (a, b) and x not in w.occupants(w.agents[a]["room"])]
        strong = [x for x in absent if abs(self._aff(a, x)) >= 4 and abs(self._aff(b, x)) >= 3]
        if strong and self.rng.random() < 0.45:
            x = self.rng.choice(strong)
            fa, fb = self._aff(a, x), self._aff(b, x)
            if fa > 0 and fb > 0:
                return "stories", x, self.nm(x)
            if fa < 0 and fb < 0:
                return "gripe", x, self.nm(x)
            return "split", x, self.nm(x)
        return "subject", None, self.rng.choice(SUBJECTS)

    def start_talk(self, tick, cid, partner, m, dur):
        """Two people fall to talking (not voiced): the outcome is decided when the talk ends."""
        w = self.world
        if partner not in w.agents or not self._available(tick, partner, m, self._free_busy or {}):
            return False
        room = w.agents[cid]["room"]
        kind, about, text = self.talk_topic(cid, partner)
        label = f"talking about {text}" if kind != "gripe" else f"grumbling about {text}"
        for c in (cid, partner):
            self._seg(tick, c, m, m + dur, room, "talk", label, "free")
            if self._free_busy is not None:
                self._free_busy[c] = m + dur
        if getattr(self, "_tl", None) is not None:
            self._tl.at(m + dur - 0.5, self.end_talk, tick, cid, partner, kind, about, text, prio=7)
        return True

    def end_talk(self, tick, a, b, kind, about, text):
        w = self.world
        if a not in w.agents or b not in w.agents or w.agents[a]["room"] != w.agents[b]["room"]:
            return
        m, na, nb = self._m, self.nm(a), self.nm(b)
        here = [o for o in w.occupants(w.agents[a]["room"]) if o in w.agents]
        f = (lambda c, k: self.facet(c, k)) if self.mind_on() else (lambda c, k: 50)
        both = lambda d: (w.adjust_aff(a, b, d), w.adjust_aff(b, a, d))
        if kind == "death":
            self.talk_testimony(tick, a, b)
            if a in self.suspects(b) or b in self.suspects(a):
                both(-1)
                line, how = f"{na} and {nb} talk about what happened to {self.nm(about)}; it turns into careful questions, and neither likes the other's answers.", "tense"
            else:
                both(1)
                for c in (a, b):
                    self.stat(tick, c, "sanity", 1, "talking it through")
                line, how = f"{na} and {nb} talk quietly about {self.nm(about)}. It helps, a little.", "good"
        elif kind == "stories":
            both(1)
            for c in (a, b):
                self.stat(tick, c, "sanity", 1, "a good talk")
            line, how = f"{na} and {nb} swap stories about {text} and end up laughing.", "good"
        elif kind == "gripe":
            both(1)
            line, how = f"{na} and {nb} grumble about {text} together; it brings them a little closer.", "good"
        elif kind == "split":
            both(-1)
            soft = a if f(a, "stress_vulnerability") >= f(b, "stress_vulnerability") else b
            self.stat(tick, soft, "sanity", -1, "an argument")
            line, how = f"{na} and {nb} fall out over {text}: one of them will not hear a word against them.", "sour"
        else:
            p = 0.55 + 0.04 * min(self._aff(a, b), self._aff(b, a)) - abs(f(a, "assertiveness") - f(b, "assertiveness")) / 300
            if self.rng.random() < p:
                both(1)
                self.mind_relief(a, "social", 10)
                self.mind_relief(b, "social", 10)
                line, how = f"{na} and {nb} talk about {text} for a while and find they agree more than they thought.", "good"
            elif f(a, "anger") >= 60 or f(b, "anger") >= 60:
                both(-1)
                line, how = f"{na} and {nb} argue about {text} until one of them walks off.", "sour"
            else:
                line, how = f"{na} and {nb} talk about {text}; it goes nowhere much.", "flat"
        for c, o in ((a, b), (b, a)):
            w.remember(c, f"{self.hh()} Talked with {self.nm(o)} about {text} ({how}).")
        self.pastime_stat("talk", how)
        self._fev(tick, a, m, line, "free", "viewer", witnesses=here)

    def talk_testimony(self, tick, a, b):
        """Talking about a death under investigation, each asks the other where they were: testimonies and what they believe, as in a voiced conversation."""
        w, case = self.world, self.s.get("case")
        if not case or not case.get("announced") or case.get("resolved"):
            return
        tes = []
        for asker, teller in ((a, b), (b, a)):
            tm = self.testimony_for(teller)
            if not tm:
                continue
            tes.append({"by": teller, "claim": tm["claim"]})
            if tm.get("room"):
                self.believe(asker, {"k": "at", "s": teller, "r": tm["room"], "t0": tm["t"], "t1": tm["t"], "by": teller, "true": not tm["lie"],
                                     "src": "told", "c": 0.35 + 0.3 * self.receptivity(asker, teller)})
        if tes:
            self.apply_talk_fx(tick, w.agents[a]["room"], [a, b], {"testimonies": tes}, tick["hour"])

    # ------------------------------------------------------------------ starting a pastime
    def start_pastime(self, tick, cid, act, room, m, end):
        """At the start: solo pastimes pay out now; shared ones invite idle friends nearby and are settled at the end."""
        w = self.world
        a = w.agents[cid]
        name = self.nm(cid)
        here = [o for o in w.occupants(room) if o in w.agents and o != cid]
        note = lambda text: self._fev(tick, cid, m, text, "free", "viewer", witnesses=here)
        if act in SHARED:
            going = self.__dict__.setdefault("_ongoing", {})
            on = going.get((id(tick), room, act))
            if on and on["end"] > m + 5 and cid not in on["group"] and len(on["group"]) < SHARED[act]:
                on["group"].append(cid)                                        # it is already going on here: they join in
                self._seg(tick, cid, m, on["end"], room, act, PASTIME_ACTS[act][0], "free")
                if self._free_busy is not None:
                    self._free_busy[cid] = on["end"]
                return note(f"{name} joins in.")
            group = [cid] + self.invite(tick, cid, act, room, m, end)
            going[(id(tick), room, act)] = {"end": end, "group": group}
            self._tl.at(end - 0.5, self.end_pastime, tick, act, room, group, prio=7) if getattr(self, "_tl", None) is not None else None
            if len(group) > 1:
                note(f"{name} {PASTIME_ACTS[act][4]}; {', '.join(self.nm(o) for o in group[1:])} join{'s' if len(group) == 2 else ''} in.")
            return
        if act == "feast":
            self._tl.at(end - 0.5, self.end_feast, tick, cid, prio=7) if getattr(self, "_tl", None) is not None else None
            note(f"{name} {PASTIME_ACTS[act][4]}.")
            return
        if act == "journal":
            self.stat(tick, cid, "sanity", 2, "their journal")
            self.mind_relief(cid, "privacy", 15)
            w.remember(cid, f"{self.hh()} Wrote in my journal: {self.mood_text(a)}.")
        elif act == "exercise":
            self.stat(tick, cid, "sanity", 1, "a workout")
            if self.mind_on():
                self.mind(cid)["stress"] = max(0, self.mind(cid)["stress"] - 8)
            self.body(cid)["hygiene"] = max(0, self.body(cid)["hygiene"] - 10)
        elif act == "meditate":
            calm = (self.facet(cid, "orderliness") if self.mind_on() else 50) >= 45 or self.rng.random() < 0.5
            self.stat(tick, cid, "sanity", 2 if calm else 0, "some quiet")
            if self.mind_on():
                self.mind(cid)["stress"] = max(0, self.mind(cid)["stress"] - (10 if calm else 3))
            if not calm:
                note(f"{name} tries to sit still with their thoughts and cannot.")
                self.pastime_stat(act, "sour")
                return
        elif act == "practise":
            what = TALENT.get(w.cast[cid].get("role"), "working at whatever it was that made them known")
            self.stat(tick, cid, "sanity", 2, "being themselves for an hour")
            self.mind_relief(cid, "purpose", 15)
            self.pastime_stat(act)
            return note(f"{name} spends a while {what}.")
        elif act == "cry":
            self.stat(tick, cid, "sanity", 2, "a good cry")
            if here:
                for o in here:
                    w.remember(o, f"{self.hh()} Saw {name} crying alone.")
                self.pastime_stat(act, "seen")
                return note(f"{name} is crying quietly and thinks nobody sees.")
        elif act == "pace":
            self.pastime_stat(act)
            return note(f"{name} {PASTIME_ACTS[act][4]}, unable to settle.") if here else None
        elif act == "fish":
            if self.rng.random() < 0.35:
                a["hunger"] = max(0, a.get("hunger", 0) - 20)
                self.stat(tick, cid, "sanity", 2, "a catch")
                self.pastime_stat(act, "caught")
                return note(f"{name} catches a fish off the rocks and grills it on the spot.")
            self.stat(tick, cid, "sanity", 1, "the sea")
        elif act == "letter":
            self.stat(tick, cid, "sanity", 1, "a letter home")
            self.mind_relief(cid, "purpose", 8)
            w.remember(cid, f"{self.hh()} Wrote a letter home that nobody will deliver.")
        elif act == "sunbathe":
            self.stat(tick, cid, "sanity", 1, "the sun")
        self.pastime_stat(act)
        note(f"{name} {PASTIME_ACTS[act][4]}.")

    def invite(self, tick, host, act, room, m, end):
        """Idle friends nearby come along to a shared pastime."""
        w = self.world
        busy = self._free_busy or {}
        reach = w.reachable_rooms(host, 14)
        out = []
        for o in sorted(w.agents):
            if len(out) + 1 >= SHARED[act] or o == host:
                continue
            ao = w.agents[o]
            if ao.get("asleep") or ao.get("out") or self.restrained(o) or (ao["room"] != room and ao["room"] not in reach) or not self._available(tick, o, m, busy):
                continue
            if self._aff(o, host) < 1 or any(self._aff(o, x) <= -4 for x in [host] + out):
                continue
            p = 0.3 + self._aff(o, host) / 20 + ((100 - self.mind(o)["needs"]["social"]) / 200 if self.mind_on() else 0.1)
            if act == "karaoke" and self.mind_on() and self.facet(o, "gregariousness") < 40:
                p -= 0.25
            if self.rng.random() < p and self._walk(tick, o, room, m) and o in w.agents:
                out.append(o)
                busy[o] = end
                self._seg(tick, o, m, end, room, act, PASTIME_ACTS[act][0], "free")
        return out

    # ------------------------------------------------------------------ how it went
    def end_pastime(self, tick, act, room, group):
        w = self.world
        m = self._m
        group = [c for c in group if c in w.agents and w.agents[c]["room"] == room]
        if not group:
            return
        here = [o for o in w.occupants(room) if o in w.agents]
        f = (lambda c, k: self.facet(c, k)) if self.mind_on() else (lambda c, k: 50)
        names = lambda cs: ", ".join(self.nm(c) for c in cs[:-1]) + (" and " if len(cs) > 1 else "") + self.nm(cs[-1])
        rival = next(((x, y) for x in group for y in group if x < y and min(self._aff(x, y), self._aff(y, x)) <= -3), None)
        warm = lambda: [w.adjust_aff(x, y, 1) for x in group for y in group if x != y and self.rng.random() < 0.5]
        lines, how = [], "good"
        if rival and len(group) > 2:
            x, y = rival
            w.adjust_aff(x, y, -1)
            w.adjust_aff(y, x, -1)
            for c in group:
                self.stat(tick, c, "sanity", -1, "a spoiled evening")
            lines.append({"film": f"{self.nm(x)} talks through the whole film to needle {self.nm(y)}; nobody enjoys it much.",
                          "karaoke": f"{self.nm(x)} heckles {self.nm(y)}'s song until the music stops.",
                          "cards": f"{self.nm(x)} accuses {self.nm(y)} of cheating at cards; the game breaks up.",
                          "campfire": f"{self.nm(x)} and {self.nm(y)} snipe at each other across the fire until the others drift off.",
                          "sunset": f"{self.nm(x)} and {self.nm(y)} cannot even watch the sunset without a dig.",
                          "photos": f"{self.nm(x)} ruins every picture with {self.nm(y)} in it."}[act])
            how = "sour"
        elif act == "film":
            warm()
            for c in group:
                self.stat(tick, c, "sanity", 2, "a film")
            lines.append(f"{names(group)} watch an old film; they laugh at the same bad line." if len(group) > 1
                         else f"{names(group)} watches an old film alone; it is a relief to be somewhere else for an hour.")
        elif act == "sunset":
            for c in group:
                lost = [x for x in self.world.agents[c]["memory"].get("lost", []) if x.get("day", 0) >= self.day - 2]
                self.stat(tick, c, "sanity", 3 + (2 if lost else 0), "the sunset")
                if lost:
                    lines.append(f"{self.nm(c)} watches the sun go down and thinks of {lost[-1].get('name') or 'the dead'}.")
            if len(group) > 1:
                warm()
                pair = next(((x, y) for x in group for y in group if x < y and any({b["a"], b["b"]} == {x, y} and b["kind"] == "romance" for b in self.s.get("bonds", []))), None)
                if pair:
                    w.adjust_aff(pair[0], pair[1], 1)
                    w.adjust_aff(pair[1], pair[0], 1)
                    lines.append(f"{self.nm(pair[0])} and {self.nm(pair[1])} watch the sunset together, close.")
                else:
                    lines.append(f"{names(group)} watch the sun sink into the sea. Nobody says much.")
            elif not lines:
                lines.append(f"{self.nm(group[0])} watches the sun sink into the sea alone.")
        elif act == "karaoke":
            for c in group:
                shy = f(c, "gregariousness") < 40
                friend = any(self._aff(c, o) >= 6 for o in group if o != c)
                self.stat(tick, c, "sanity", (1 if friend else -2) if shy else 3, "karaoke")
            star = max(group, key=lambda c: (f(c, "vanity") + f(c, "gregariousness"), c))
            warm()
            lines.append(f"{names(group)} sing karaoke; {self.nm(star)} takes the microphone and will not give it back." if len(group) > 1
                         else f"{self.nm(star)} sings karaoke alone, badly and loudly.")
        elif act == "cards":
            win = self.rng.choice(group)
            warm()
            for c in group:
                self.stat(tick, c, "sanity", 1, "a game of cards")
            lines.append(f"{self.nm(win)} wins the hand of cards against {names([c for c in group if c != win])}." if len(group) > 1 else f"{self.nm(win)} plays patience alone.")
        elif act == "campfire":
            warm()
            for c in group:
                self.stat(tick, c, "sanity", 2, "the fire")
            teller = max(group, key=lambda c: (f(c, "humour"), c))
            lines.append(f"{names(group)} sit round the fire on the beach; {self.nm(teller)} tells a ghost story badly." if len(group) > 1
                         else f"{self.nm(teller)} sits alone by the fire, watching the sparks.")
        elif act == "photos":
            for c in group:
                self.stat(tick, c, "sanity", 1, "pictures")
                self.mind_relief(c, "purpose", 6)
            if len(group) > 1:
                warm()
                lines.append(f"{names(group)} take pictures of each other by the {w.room_name(room).lower()}; one of them is actually good.")
            else:
                lines.append(f"{self.nm(group[0])} takes pictures of the island as if it were somewhere worth remembering.")
        for c in group:
            w.remember(c, f"{self.hh()} {PASTIME_ACTS[act][0].capitalize()} with {', '.join(self.nm(o) for o in group if o != c) or 'nobody'} ({how}).")
        self.pastime_stat(act, how if len(group) > 1 else "alone")
        for line in lines[:2]:
            self._fev(tick, group[0], m, line, "free", "viewer", witnesses=here)

    def end_feast(self, tick, cook):
        """A proper meal for everyone: whoever is in the kitchen or the dining hall eats, and thinks better of the cook."""
        w = self.world
        if cook not in w.agents:
            return
        eaters = sorted({o for r in ("kitchen", "dining_hall") for o in w.occupants(r) if o in w.agents and o != cook and not w.agents[o].get("asleep")})
        w.agents[cook]["hunger"] = max(0, w.agents[cook].get("hunger", 0) - 35)
        self.mind_relief(cook, "purpose", 12)
        for o in eaters:
            w.agents[o]["hunger"] = max(0, w.agents[o].get("hunger", 0) - 30)
            self.stat(tick, o, "sanity", 2, "a proper meal")
            w.adjust_aff(o, cook, 1)
        skill = (self.facet(cook, "orderliness") if self.mind_on() else 50) + self.rng.randint(-20, 20)
        here = [o for o in w.occupants(w.agents[cook]["room"]) if o in w.agents]
        text = (f"{self.nm(cook)} serves a proper meal" + (f"; {', '.join(self.nm(o) for o in eaters[:4])} eat{'s' if len(eaters) == 1 else ''} it" if eaters else ", and nobody comes")
                + (" and ask for more." if eaters and skill >= 55 else "." if skill >= 35 else ", though half of it is burnt."))
        self.pastime_stat("feast", "good" if eaters else "alone")
        self._fev(tick, cook, self._m, text, "free", "viewer", witnesses=here)
