"""The confessional booth: a curtained box at the end of the first-floor gallery where people talk to the audience.

Things that happen to people leave them with something to get off their chest (being mocked or threatened, a moment with someone they like, a body, a plot coming
together, a loss, a secret weighing on them). When the urge is strong enough, they walk to the booth in their free time (or slip in at the end of a turn) and record: one to
three short lines, straight to the camera, to "you", the audience. The engine picks what the confession is about; the voice only words it (one call per turn for all the
entries, or the template lines below). The booth is a real place: someone passing on the gallery, or standing in the foyer under its open floor, can overhear a confession.
"""

BOOTH_KIND = "booth"
EVENT_URGE = {"punish": ("hurt", 3), "attack": ("fear", 3), "body": ("fear", 3), "madness": ("fear", 2), "assault": ("hurt", 3), "betrayal": ("hurt", 3),
              "leak": ("hurt", 2), "outburst": ("hurt", 2), "experiment": ("day", 1.5), "tease": ("day", 1.5), "occasion": ("warm", 1), "fall": ("fear", 2),
              "system_notable": ("day", 1.5), "discover": ("day", 1), "mercy": ("warm", 2)}
MOVE_URGE = {"mock": ("hurt", 2), "putdown": ("hurt", 2.5), "threaten": ("hurt", 3), "accuse": ("hurt", 2.5), "comfort": ("warm", 1.5), "confide": ("warm", 1.5),
             "flirt": ("warm", 2), "gift": ("warm", 1.5), "reveal": ("suspect", 2), "warn": ("suspect", 1.5), "gossip": ("suspect", 1)}
TEMPLATES = {
    "hurt": ["Did you see what {x} just did? Unbelievable.", "{x} thinks that was funny. Watch me.", "Note to self: never turn my back on {x}.", "I smiled. I wanted to scream."],
    "warm": ["Okay. {x} is kind of great. Don't tell them.", "For the record? {x} is the only reason I'm still smiling.", "I think I like {x}. Great timing, me."],
    "suspect": ["Keep your eyes on {x}. Just trust me.", "{x} is hiding something. I can feel it.", "Everyone's looking the wrong way. Look at {x}."],
    "plot": ["Patience. Everything is falling into place.", "You'll see. Soon.", "They have no idea. None of them."],
    "fear": ["I'm not sleeping tonight. Would you?", "Every creak in this house sounds like footsteps.", "I just want to go home. Is that too much to ask?"],
    "grief": ["I keep looking for {x} at breakfast.", "{x} deserved so much better than this island.", "Someone's chair is empty. Nobody says anything.",
              "We're supposed to just carry on? Like that?"],
    "secret": ["Here's something nobody here knows. Yet.", "If they find out what I did back home, I'm done."],
    "day": ["Honestly? Weird day. Even for here.", "Smile for the camera, right? Like this?", "Another day in paradise. Ha."],
}
FOLLOW = ["Anyway. Back out there.", "Don't judge me.", "You'd do the same.", "Okay. Deep breath.", ""]


class BoothMixin:
    # ------------------------------------------------------------------ the urge
    def booth_note(self, cid, kind, weight, other=None):
        a = self.world.agents.get(cid)
        if not a or not self.confessionals:
            return
        notes = a.setdefault("booth", {})
        if notes.get("day") != self.day:
            notes.clear()
            notes.update(day=self.day, why=[], visits=0)
        notes["why"].append([kind, float(weight), other])
        del notes["why"][:-10]

    def booth_note_event(self, evt):
        u = EVENT_URGE.get(evt.get("type"))
        if u and evt.get("who") in self.world.agents:
            self.booth_note(evt["who"], u[0], u[1])

    def booth_urge(self, cid):
        """(how strongly they want to talk to the camera, what about, about whom)."""
        w, s = self.world, self.s
        a = w.agents.get(cid)
        if not a or not self.confessionals:
            return 0.0, None, None
        notes = a.get("booth") or {}
        why = list(notes.get("why") or []) if notes.get("day") == self.day else []
        pl = s.get("plots", {}).get(cid)
        if pl and pl.get("stage") in ("stalking", "striking", "preparing"):
            why.append(["plot", 2.5 if pl["stage"] != "preparing" else 1.5, None])
        lost = [x for x in a["memory"].get("lost", []) if x.get("day", 0) == self.day]
        if lost:
            why.append(["grief", 2.0, lost[-1].get("id") if lost[-1].get("id") in w.cast else None])
        if a["sanity"] < 35:
            why.append(["fear", 1.5, None])
        sus = self.suspects(cid)
        if sus:
            why.append(["suspect", 1.0, sus[0]])
        if not why:
            return 0.0, None, None
        total = sum(x[1] for x in why) / (1 + 1.5 * (notes.get("visits", 0) if notes.get("day") == self.day else 0))
        top = max(why, key=lambda x: x[1])
        return total, top[0], top[2]

    # ------------------------------------------------------------------ going in
    def booth_tile(self):
        f = next((f for f in self.nav().gm["furniture"] if f["k"] == BOOTH_KIND), None)
        return (f["plane"], f["x"], f["y"], f["room"]) if f else None

    def booth_visit(self, tick, cid, m):
        """`cid` is at the booth at minute m: record what they want to say (worded when the turn is voiced)."""
        w = self.world
        a = w.agents[cid]
        _, kind, other = self.booth_urge(cid)
        notes = a.setdefault("booth", {"day": self.day, "why": [], "visits": 0})
        notes["visits"] = notes.get("visits", 0) + 1 if notes.get("day") == self.day else 1
        entry = {"id": cid, "m": round(float(m), 1), "topic": kind or "day", "about": other if other in w.cast else None, "room": a["room"]}
        self.__dict__.setdefault("_booth", []).append(entry)
        self._fev(tick, cid, m, f"{self.nm(cid)} slips into the confessional booth.", "free", "viewer")
        return entry

    def booth_turn(self, tick, hour, kind):
        """Outside free time: whoever most needs it slips into the booth near the end of the turn."""
        if not self.confessionals or kind == "free" or any(e for e in self.__dict__.get("_booth", []) if e.get("tick") == id(tick)):
            return
        w = self.world
        bt = self.booth_tile()
        if not bt:
            return
        best = max(((self.booth_urge(c)[0], c) for c in sorted(w.agents) if not w.agents[c].get("out") and not w.agents[c].get("asleep") and not self.restrained(c)), default=(0, None))
        if best[0] < 3.0 or self.rng.random() > 0.6:
            return
        cid = best[1]
        m = max(self._m, 100.0)
        if w.agents[cid]["room"] != bt[3]:
            mv = w.move(cid, bt[3], 400)
            if w.agents[cid]["room"] != bt[3]:
                return
            pm = tick["moves"].setdefault(cid, {"from": mv["path"][0], "path": [mv["path"][0]], "to": bt[3]})
            pm["path"] = list(pm.get("path") or []) + mv["path"][1:]
            pm["to"] = bt[3]
        sm = self.sim_turn(tick)
        near = sm.nav.stand_near(bt[0], bt[1], bt[2], sm.occupied(cid), bt[3])
        t = sm.walk(cid, near, m, deadline=min(sm.dur - 2.0, m + 10.0), speed=self.move_factor(cid)) if near else m
        self.booth_visit(tick, cid, min(sm.dur - 1.5, t + 0.3))["tick"] = id(tick)

    # ------------------------------------------------------------------ the recording
    def voice_booth(self, tick, hour):
        """Word every booth entry of the turn (one call), check it is short and spoken to the audience, and let anyone close enough overhear it."""
        w = self.world
        entries = [e for e in self.__dict__.get("_booth", []) if e["id"] in w.agents]
        self._booth = []
        if not entries:
            return
        cards = []
        for e in entries:
            c, a = w.cast[e["id"]], w.agents[e["id"]]
            topic = {"hurt": f"what {self.nm(e['about'])} did to them" if e.get("about") else "being humiliated", "warm": f"their feelings about {self.nm(e['about'])}" if e.get("about") else "a good moment",
                     "suspect": f"their suspicion of {self.nm(e['about'])}" if e.get("about") else "who they suspect", "fear": "being afraid",
                     "grief": f"missing {self.nm(e['about'])}" if e.get("about") else "who they have lost", "secret": f"their secret ({c['secret']})",
                     "day": "how today went"}.get(e["topic"], "how today went")
            if e["topic"] == "plot":
                pl = self.s.get("plots", {}).get(e["id"]) or {}
                topic = f"their secret plan to kill {self.nm(pl.get('target'))} (stage: {pl.get('stage')}); hint at it, gloat or shake, never spell out the method" if pl else "a plan"
            cards.append(f"- {e['id']} = {c['name']}. Looks: {self.looks_line(e['id'], short=True)}. Speech: {c['speech']} Mood: {self.mood_text(a)}. TALKS ABOUT: {topic}.")
        sysm = (f"{self.bible()}\nCONFESSIONAL BOOTH of a reality show: one person alone in a curtained box, talking STRAIGHT TO THE AUDIENCE watching at home. "
                "Reply with a single JSON object and nothing else.")
        user = (f"Day {self.day}. Write a booth confessional for each person below. Each is 1 to 3 SHORT lines, each line at most 14 words, spoken to the viewers "
                "(\"you\", \"you saw that, right?\", \"don't tell them\"): punchy, candid, in their own voice. No narration, no stage directions, no quotation marks, no long speeches. "
                "Talk only about the given subject.\n" + "\n".join(cards) + '\nReply as JSON: {"entries": [{"id": "<person id>", "lines": ["...", "..."]}]}')
        try:
            r = self.llm.confess(sysm, user, {"ids": [e["id"] for e in entries], "booth": True})
        except Exception as e:
            if getattr(e, "fatal", False):
                raise
            r = {}
        got = {}
        for en in (r or {}).get("entries") or []:
            if isinstance(en, dict) and en.get("id") in w.agents:
                ls = en.get("lines") if isinstance(en.get("lines"), list) else ([en["text"]] if en.get("text") else [])
                ls = [str(x).strip().strip('"')[:110] for x in ls if str(x).strip()]
                ls = [x for x in ls if len(x.split()) <= 18][:3]
                if ls:
                    got[en["id"]] = ls
        out = []
        for e in entries:
            lines = got.get(e["id"]) or self.booth_template(e)
            ent = {"id": e["id"], "text": " ".join(lines), "lines": lines, "m": e["m"], "topic": e["topic"], "room": e["room"], "hour": int(hour)}
            out.append(ent)
        tick["confessionals"] = (tick.get("confessionals") or []) + out

    def booth_hearing(self, tick):
        """Somebody on the gallery, or in the foyer under its open floor, may overhear a confession (checked once the turn's walks are final)."""
        w = self.world
        sm = self.__dict__.get("_sim")
        for ent in tick.get("confessionals") or []:
            if "m" not in ent or sm is None or ent["id"] not in sm.tracks:
                continue
            conv = {"members": [ent["id"]], "room": ent.get("room"), "seen_by": set(), "wary": True}
            beat = {"who": ent["id"], "m": ent["m"], "loud": "quiet", "room": ent.get("room"), "move": "confide"}
            self.overhear(tick, conv, [beat], notice=False)
            heard = beat.get("heard") or {}
            ent.pop("heard", None)
            if heard:
                ent["heard"] = heard
            hh = f"{int(ent.get('hour', tick['hour'])):02d}:00"
            for o, lvl in heard.items():
                if lvl == "full":
                    w.remember(o, f"{hh} (overheard {self.nm(ent['id'])} in the confessional booth) \"{ent['text'][:120]}\"")
                elif lvl == "part":
                    w.remember(o, f"{hh} (heard {self.nm(ent['id'])} muttering in the confessional booth, could not make it out)")

    def booth_template(self, e):
        pool = TEMPLATES.get(e["topic"]) or TEMPLATES["day"]
        if not e.get("about"):
            pool = [p for p in pool if "{x}" not in p] or TEMPLATES["fear" if e["topic"] in ("grief", "hurt") else "day"]
        lines = [self.rng.choice(pool).format(x=self.nm(e["about"]) if e.get("about") else "")]
        tail = self.rng.choice(FOLLOW)
        if tail:
            lines.append(tail)
        return lines
