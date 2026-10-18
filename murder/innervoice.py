"""The inner voice: thought bubbles, thinking aloud, and minds that bend and break.

Now and then the viewer sees what someone is thinking, over their head on the map and in the feed, marked as a thought. It is more likely right
after something big happened to them, and more likely the lower their sanity. The engine picks the thought from their state (a plot, a loss,
someone who lied to them, a crush, the way out, a need, a hallucination); no model call is made. Sometimes a thought is said out loud: when
alone, or, once sanity is low, muttered in company. A mutter can be overheard like any line, so a careless plotter can give themselves away.

Low sanity bends beliefs (`beliefs.py`):
* below 40, now and then a belief is reread through fear: a sighting gets the wrong person, a rumour hardens into certainty, a friend's
  kindness becomes a trap;
* below 25, hallucinations: the dead walking a corridor, someone standing over their bed with a knife, TereVi whispering a name, someone
  where they never were; after a body is found, a false memory of seeing someone at the scene. Each is a false belief held with confidence,
  and it feeds testimony, fear and plans like any other;
* below 10, they act on them: hiding, or deciding to strike first.
When sanity recovers (to 35 and 15 above where it was), hallucinations are recognised for what they were, which has its own sting. InnerVoiceMixin is mixed into DayRunner.
"""
from .data_world import ESCAPE_ROUTES, ROOMS

MAX_PER_TURN = 3
LINES = {
    "plot": ["Patience. {x} won't see it coming.", "Not yet. Soon. {x}, you lucky thing.", "Smile at {x}. Keep smiling."],
    "grief": ["{x} should still be here.", "I keep turning to tell {x} something.", "Who sits in {x}'s chair now?"],
    "liar": ["{x} lied to me. Why would {x} lie?", "Watch {x}. Just watch.", "Everything {x} says, check it twice."],
    "crush": ["{x}... focus. Focus.", "Did {x} just smile at me? At me?", "Don't be weird around {x}. Don't be weird."],
    "route": ["A bit more work and the {x} might actually happen.", "If the {x} works, we all go home.", "Don't tell TereVi about the {x}. Obviously."],
    "hungry": ["I'd kill for a sandwich. Poor choice of words.", "When did I last eat?"],
    "tired": ["If I close my eyes for one second...", "Sleep. I remember sleep."],
    "hurt": ["{x}. Still stings.", "Can't stop replaying it: {x}.", "Let it go. ...Nope. {x}."],
    "fear": ["Every creak is someone on the stairs.", "Who's next? Don't answer that.", "Keep your back to the wall.", "Sleep with the chair under the door handle. Again.",
             "Count the people at breakfast. Count them again.", "Somebody here has already decided. Who?", "Don't eat anything you didn't open yourself.",
             "If I scream, would anyone even come?", "Smile for the cameras. Smile, smile, smile."],
    "undecided": ["Left or right. Left. No. Right? ...Left.", "Should I say something? I should say something. Should I?"],
    "catlike": ["That sunbeam is mine.", "If I sit very still, nobody will notice me."],
    "no_talent": ["Everyone here is famous for something. What am I for?", "They all have a thing. I fold towels."],
    "low": ["The walls are breathing. They're definitely breathing.", "Count the doors. Count them again.", "Somebody keeps saying my name."],
    "calm": ["Okay. Today is okay.", "Breathe in. Breathe out.", "Nobody died today. Yet.", "I could murder a coffee. Bad choice of words.",
             "The view is gorgeous. Shame about the homicide.", "Five stars for the pool. Minus several for the killing."],
}
HAL = {
    "ghost": "{x} walking down the corridor, as if nothing happened",
    "knife": "{x} standing over the bed in the dark, holding a knife",
    "voice": "TereVi whispering that {x} is coming for them",
    "sight": "{x} in the {r}, right there, watching",
}


class InnerVoiceMixin:
    # ------------------------------------------------------------------ what someone is thinking
    def inner_topic(self, cid):
        """(topic, about) for a thought, from the state; the first that applies, with a little chance between the softer ones."""
        w, s = self.world, self.s
        a = w.agents[cid]
        hal = [b for b in self.beliefs(cid) if b.get("hal") and b.get("fresh")]
        if hal:
            return "hal", hal[-1]
        p = (s.get("plots") or {}).get(cid)
        if p and p.get("target") in w.agents and self.inner_rng.random() < 0.6:
            return "plot", p["target"]
        dead = [g for g in s.get("graveyard", []) if g.get("day", 0) >= self.day - 1 and a["aff"].get(g["id"], 0) >= 4]
        if dead and self.inner_rng.random() < 0.7:
            return "grief", dead[-1]["id"]
        soft = []
        liars = self.caught_liars(cid)
        if liars:
            soft.append(("liar", liars[-1]))
        crush = max((o for o in a["aff"] if o in w.agents), key=lambda o: (a["aff"][o], o), default=None)
        if crush and a["aff"][crush] >= 7:
            soft.append(("crush", crush))
        rid = a.get("route")
        if rid in ESCAPE_ROUTES and cid in s["escape"]["routes"][rid].get("contributors", []) and self.route_pct(rid) >= 25:
            soft.append(("route", ESCAPE_ROUTES[rid]["title"].lower()))
        m = self.mind(cid)
        if m["needs"].get("rest", 70) < 25:
            soft.append(("tired", None))
        if a.get("hunger", 0) >= 60:
            soft.append(("hungry", None))
        worst = min((t for t in m["thoughts"] if t["w"] <= -4 and t["c"] not in ("events", "")), key=lambda t: (t["w"] * t["t"] / t["t0"], t["c"]), default=None)
        if worst:
            soft.append(("hurt", worst["c"]))
        for tr in ("undecided", "catlike", "no_talent"):
            if self.has_trait(cid, tr):
                soft.append((tr, None))
        if a["sanity"] < 30:
            soft += [("low", None)] * 2
        elif self.dread_level() >= 2:
            soft.append(("fear", None))
        return self.inner_rng.choice(soft) if soft else ("calm", None)

    def inner_text(self, cid, topic, about):
        if topic == "hal":
            what = about.get("what") or about["n"]
            return self.inner_rng.choice(["Did I just see {t}? I did. I did.", "{t}. Nobody else saw it. Why did nobody else see it?"]).format(t=what)
        x = self.nm(about) if about in self.world.cast else (about or "")
        if topic == "hurt":
            x = x[:1].upper() + x[1:]
        return self.inner_rng.choice(LINES.get(topic) or LINES["calm"]).format(x=x)

    def inner_turn(self, tick, hour):
        """A few thoughts per turn, some said out loud. Stored in tick["inner"]; heard (if muttered) once the turn's walks are final."""
        w = self.world
        if not self.revealed or not w.agents:
            return
        self.distort_minds(tick, hour)
        dur = self.sim_turn(tick).dur
        cands = []
        for cid in sorted(w.agents):
            a = w.agents[cid]
            if a.get("asleep") or a.get("out"):
                continue
            m = self.mind(cid)
            shock = sum(-t["w"] for t in m["thoughts"] if t["w"] < 0 and t["t"] == t["t0"])
            fresh = any(b.get("hal") and b.get("fresh") for b in self.beliefs(cid))
            p = 0.12 + min(0.3, shock / 40) + max(0, 50 - a["sanity"]) / 200 + (1.0 if fresh else 0)
            if self.inner_rng.random() < p:
                cands.append((-(p + self.inner_rng.random() * 0.1), cid))
        out = []
        for _, cid in sorted(cands)[:MAX_PER_TURN]:
            a = w.agents[cid]
            topic, about = self.inner_topic(cid)
            text = self.inner_text(cid, topic, about)
            alone = not [o for o in w.occupants(a["room"]) if o in w.agents and o != cid]
            aloud = self.inner_rng.random() < (0.3 + max(0, 40 - a["sanity"]) / 80 if alone else max(0, 40 - a["sanity"]) / 60)
            ent = {"id": cid, "m": round(self.inner_rng.uniform(4, max(5, dur - 8)), 1), "kind": "mutter" if aloud else "think", "text": text, "topic": topic,
                   "hour": int(hour)}
            if topic == "plot":
                ent["about"] = about
            out.append(ent)
            self.s.setdefault("mind_stats", {}).setdefault("thoughts", 0)
            self.s["mind_stats"]["thoughts"] += 1
        for cid in w.agents:
            for b in self.beliefs(cid):
                b.pop("fresh", None)
        if out:
            tick["inner"] = (tick.get("inner") or []) + out

    def inner_hearing(self, tick):
        """A mutter can be overheard like a quiet line (checked once the turn's walks are final)."""
        w = self.world
        sm = self.__dict__.get("_sim")
        for ent in tick.get("inner") or []:
            cid = ent["id"]
            if sm is None or cid not in sm.tracks:
                continue
            pos = sm.pos_at(cid, ent["m"])
            room = sm.nav.room_at(*pos) if pos else None
            ent["room"] = room if room in ROOMS else (w.agents[cid]["room"] if cid in w.agents else None)
            if ent["kind"] != "mutter" or cid not in w.agents:
                continue
            conv = {"members": [cid], "room": ent["room"], "seen_by": set(), "wary": True}
            beat = {"who": cid, "m": ent["m"], "loud": "quiet", "room": ent["room"], "move": "confide"}
            self.overhear(tick, conv, [beat], notice=False)
            heard = {o: v for o, v in (beat.get("heard") or {}).items() if v in ("full", "part")}
            if not heard:
                continue
            ent["heard"] = heard
            hh = f"{int(ent['hour']) % 24:02d}:00"
            for o, lvl in heard.items():
                if lvl == "part":
                    w.remember(o, f"{hh} You heard {self.nm(cid)} muttering to themselves; you could not make it out.")
                    continue
                w.remember(o, f"{hh} You overheard {self.nm(cid)} muttering to themselves: \"{ent['text']}\"")
                if ent["topic"] == "plot" and ent.get("about") in w.agents and o != ent["about"]:
                    self.belief_rumor(o, cid, cid, f"{self.nm(cid)} muttered about {self.nm(ent['about'])} in a way that sounded like a threat", lie=False)
                    self.booth_note(o, "suspect", 2.5, cid)
                    self.s["mind_stats"]["plots_overheard"] = self.s["mind_stats"].get("plots_overheard", 0) + 1

    # ------------------------------------------------------------------ minds that bend
    def distort_minds(self, tick, hour):
        """Below 40 beliefs warp, below 25 people hallucinate, below 10 they act on it. Rolled per person per turn."""
        w, s = self.world, self.s
        if not self.mind_on() or not self.tune("hallucinations"):
            return
        for cid in sorted(w.agents):
            a = w.agents[cid]
            if a.get("out"):
                continue
            san = a["sanity"]
            if san < 40 and self.rng.random() < (40 - san) / 160:
                self.warp_belief(cid)
            if san < 25 and self.rng.random() < (25 - san) / 60:
                self.hallucinate(tick, cid)
            if san < 30:
                self.false_memory(cid)
            if san < 10:
                self.act_on_fear(tick, cid, hour)

    def _dislike(self, cid, pool):
        a = self.world.agents[cid]
        return min(pool, key=lambda o: (a["aff"].get(o, 0) + self.rng.random() * 3, o)) if pool else None

    def warp_belief(self, cid):
        w = self.world
        others = [o for o in sorted(w.agents) if o != cid]
        if not others:
            return None
        bs = self.beliefs(cid)
        sights = [b for b in bs if b["k"] == "at" and b["src"] == "seen" and b["s"] in w.agents and not b.get("warp")]
        rumors = [b for b in bs if b["k"] == "rumor" and b["c"] < 0.85]
        friends = [o for o in others if w.agents[cid]["aff"].get(o, 0) >= 4]
        kinds = (["sight"] if sights else []) + (["rumor"] if rumors else []) + (["friend"] if friends else [])
        if not kinds:
            return None
        kind = self.rng.choice(kinds)
        if kind == "sight":
            b = self.rng.choice(sights[-10:])
            new = self._dislike(cid, [o for o in others if o != b["s"]])
            if not new:
                return None
            b.update(s=new, true=False, warp=True)
        elif kind == "rumor":
            b = self.rng.choice(rumors)
            b.update(c=0.9, warp=True)
        else:
            f = self.rng.choice(friends)
            self.believe(cid, {"k": "rumor", "s": f, "n": f"{self.nm(f)} is only being nice to set me up", "src": "inferred", "c": 0.7,
                               "t0": self.abs_now(), "true": False, "warp": True})
        self._mstat("warped")
        return kind

    def hallucinate(self, tick, cid):
        """A false belief held with confidence: something seen or heard that was never there."""
        w, s = self.world, self.s
        a = w.agents[cid]
        others = [o for o in sorted(w.agents) if o != cid]
        dead = [g["id"] for g in s.get("graveyard", []) if g["id"] in w.cast and a["aff"].get(g["id"], 0) != 0]
        kinds = (["ghost"] if dead else []) + (["knife", "voice", "sight"] if others else [])
        if not kinds:
            return None
        kind = self.rng.choice(kinds)
        now = self.abs_now()
        if kind == "ghost":
            x = self.rng.choice(dead)
            b = {"k": "rumor", "s": x, "n": "they saw " + HAL["ghost"].format(x=self.nm(x))}
        elif kind == "knife":
            x = self._dislike(cid, others)
            b = {"k": "has", "s": x, "o": "kitchen_knife", "n": f"I saw {HAL['knife'].format(x=self.nm(x))}"}
        elif kind == "voice":
            x = self._dislike(cid, others)
            b = {"k": "rumor", "s": x, "by": "terevi", "n": "they heard " + HAL["voice"].format(x=self.nm(x))}
        else:
            x = self._dislike(cid, [o for o in others if w.agents[o]["room"] != a["room"]] or others)
            b = {"k": "at", "s": x, "r": a["room"], "t0": now, "t1": now, "n": HAL["sight"].format(x=self.nm(x), r=w.room_name(a["room"]))}
        what = HAL[kind].format(x=self.nm(x), r=w.room_name(a["room"])) if kind != "voice" else "TereVi in the walls, whispering that " + self.nm(x) + " is coming for me"
        b.update(src="seen", c=0.85, t0=b.get("t0", now), true=False, hal=True, fresh=True, kind=kind, about=x, san=a["sanity"], what=what)
        n = b["n"]
        got = self.believe(cid, b)
        if got is not None:
            got.update(hal=True, fresh=True, n=n, kind=kind, san=a["sanity"], what=what)
        self.stat(tick, cid, "sanity", -1, "seeing things")
        w.remember(cid, f"(private) You are sure of it: {n.replace('they saw ', 'you saw ').replace('they heard ', 'you heard ')}.")
        self.log_event(tick, {"type": "drive", "who": cid, "room": a["room"], "vis": "gm",
                              "text": f"{self.nm(cid)} hallucinates: {n} (not real)."}, actor=cid)
        self._mstat("hallucinations")
        return kind

    def false_memory(self, cid):
        """After a body is found, a broken mind may 'remember' seeing someone at the scene. It goes into their testimony."""
        w, s_ = self.world, self.s
        case = s_.get("case")
        if not case or not case.get("announced") or case.get("resolved") or not case.get("room"):
            return None
        done = case.setdefault("false_memories", [])
        if cid in done or self.rng.random() > (30 - w.agents[cid]["sanity"]) / 60:
            return None
        pool = [o for o in sorted(w.agents) if o != cid and o != case.get("victim")]
        x = self._dislike(cid, pool)
        if not x:
            return None
        t = self.case_time(case)
        self.believe(cid, {"k": "at", "s": x, "r": case["room"], "t0": t, "t1": t, "src": "seen", "c": 0.7, "true": False, "hal": True, "fresh": True, "san": w.agents[cid]["sanity"],
                           "what": f"{self.nm(x)} near the {w.room_name(case['room'])} when it happened",
                           "n": f"{self.nm(x)} near the {w.room_name(case['room'])} when it happened"})
        done.append(cid)
        self._mstat("false_memories")
        return x

    def act_on_fear(self, tick, cid, hour):
        """Below 10 sanity a false threat is acted on: hide from it, or strike first."""
        w, s = self.world, self.s
        threat = next((b for b in reversed(self.beliefs(cid)) if (b.get("hal") or b.get("warp")) and b.get("s") in w.agents and b["s"] != cid
                       and b["k"] in ("has", "rumor", "at")), None)
        if not threat:
            return None
        x = threat["s"]
        if self.murders and cid not in (s.get("plots") or {}) and not s.get("case") and self.rng.random() < 0.25:
            self.plot_start(tick, cid, x, f"convinced {self.nm(x)} is coming for them", hour, "paranoia")
            self._mstat("paranoid_plots")
            return "strike"
        if not w.agents[cid].get("hiding") and self.rng.random() < 0.3:
            self.do_hide(tick, cid, {})
            self._mstat("hid")
            return "hide"
        return None

    def recover_minds(self, tick):
        """At dawn, someone whose sanity has come back may see a hallucination for what it was."""
        w = self.world
        for cid in sorted(w.agents):
            san = w.agents[cid]["sanity"]
            for b in self.beliefs(cid):
                if b.get("hal") and not b.get("seen_through") and san >= max(35, b.get("san", 30) + 15) and self.rng.random() < 0.4:
                    b["seen_through"] = True
                    b["c"] = 0.05
                    w.remember(cid, f"(private) It wasn't real. {b.get('n', 'What you saw')}: it never happened.")
                    self.stat(tick, cid, "sanity", -2, "realising they had been seeing things")
                    self._mstat("seen_through")

    def _mstat(self, k):
        st = self.s.setdefault("mind_stats", {})
        st[k] = st.get(k, 0) + 1
