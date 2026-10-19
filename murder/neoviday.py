"""NeoVi's day: chores at set times, a word with people, and her punishments and footage as short scenes.

While she is the housemaid she works through a chore list each daytime block (cooking and serving the meals, washing up, the laundry, dusting, changing
sheets, sweeping, the evening rounds), so she is among people and her room follows the work minute by minute. She can take part in a live
conversation in the room she is in: someone asks her something (she plays dumb, or, if she likes them, answers; with mutual trust she confides what only
she knows), thanks her, flirts with her, or needles her (a cold rebuke). She is at the table when she serves a meal, and someone whose decision names her
goes to find her. Her punishments and the stills she shows an investigator play as short scenes where they happen, in engine-written lines (no model
call). NeoViDayMixin is mixed into DayRunner (engine.py); `neovi_maid()` (kumiko.py) guards all of it.
"""
from .data_world import ROOMS

NV = "neovi"
# hour: [(start minute, minutes, room, what she is doing)]; "{bed}" is someone's bedroom (changing the sheets)
CHORES = {
    8: [(2, 24, "kitchen", "cooking breakfast"), (28, 34, "dining_hall", "serving breakfast"), (66, 30, "kitchen", "washing up"), (100, 20, "laundry", "starting the laundry")],
    10: [(2, 30, "laundry", "doing the laundry"), (36, 22, "landing", "dusting the landing"), (62, 28, "{bed}", "changing the sheets"), (96, 24, "foyer", "sweeping the foyer")],
    12: [(2, 24, "kitchen", "cooking lunch"), (28, 36, "dining_hall", "serving lunch"), (68, 28, "kitchen", "washing up"), (100, 20, "dining_hall", "laying the table")],
    14: [(2, 30, "library", "dusting the library"), (36, 30, "lounge", "tidying the lounge"), (70, 26, "games_room", "tidying the games room"), (100, 20, "foyer", "polishing the foyer floor")],
    16: [(2, 28, "foyer", "sweeping the foyer"), (34, 26, "bathroom", "cleaning the bathroom"), (64, 30, "laundry", "folding laundry"), (98, 22, "kitchen", "starting dinner")],
    18: [(2, 24, "kitchen", "cooking dinner"), (28, 40, "dining_hall", "serving dinner"), (72, 30, "kitchen", "washing up"), (104, 16, "foyer", "closing the shutters")],
    20: [(2, 26, "foyer", "making the evening rounds"), (32, 30, "lounge", "tidying the lounge"), (66, 26, "landing", "turning down the lamps"), (96, 24, "laundry", "folding the last of the laundry")],
}
SERVING = ("serving breakfast", "serving lunch", "serving dinner")
ASK_P = 0.35                    # chance an exchange in a conversation she is part of is addressed to her


class NeoViDayMixin:
    def nv_plan(self, hour):
        """This block's chores: [(m0, m1, room, label)], or [] when she is not the housemaid or not working."""
        if not self.revealed or not self.neovi_maid() or int(hour) not in CHORES:
            return []
        w = self.world
        out = []
        for m0, d, room, label in CHORES[int(hour)]:
            if room == "{bed}":
                empty = [c for c in sorted(w.agents) if w.agents[c]["room"] != w.cast[c]["home"] and w.cast[c]["home"] in ROOMS]
                if not empty:
                    continue
                c = empty[(self.day + int(hour)) % len(empty)]
                room, label = w.cast[c]["home"], f"changing the sheets in {self.nm(c)}'s room"
            if room in ROOMS:
                out.append((m0, m0 + d, room, label))
        return out

    def nv_schedule(self, tick, hour, tl):
        """Put her chores on the block's timeline: her room follows the work."""
        plan = self.nv_plan(hour)
        ins = self.s.get("_inspect")
        if not plan or (ins and ins["day"] == self.day and ins["hour"] == hour):
            return
        tick["nv_plan"] = [[m0, m1, room, label] for m0, m1, room, label in plan]
        for m0, m1, room, label in plan:
            tl.at(m0, self.nv_to, tick, room, label, prio=1)

    def nv_to(self, tick, room, label):
        nv = self.s["npcs"][NV]
        if not self.neovi_maid():
            return
        nv["room"], nv["doing"] = room, label
        self.nv_walk(room)                                              # forward mode: she walks to the chore as it starts (sim.py)
        if label in SERVING:
            here = [o for o in self.world.occupants(room) if o in self.world.agents]
            self.log_event(tick, {"type": "neovi", "who": NV, "room": room, "vis": "viewer", "m": float(self._m),
                                  "text": f"NeoVi {label.replace('serving', 'serves')}."}, witnesses=here)

    def nv_here(self, room):
        return self.neovi_maid() and self.s["npcs"][NV].get("room") == room

    # ------------------------------------------------------------------ a word with NeoVi
    def nv_exchange(self, tick, conv, a):
        """`a` turns to NeoVi; she answers by how she feels about them. Returns the beats."""
        w, s = self.world, self.s
        nv = s["npcs"][NV]
        mine, theirs = nv.setdefault("aff", {}).get(a, 0), self.nv_feel(a)
        f = (lambda k: self.facet(a, k)) if self.mind_on() else (lambda k: 50)
        if theirs <= -3 and f("cruelty") + f("anger") >= 100:
            move = "needle_nv"
        elif theirs >= 5 and f("romantic") >= 55 and self.rng.random() < 0.4:
            move = "flirt_nv"
        elif conv.get("nv_fed") and self.rng.random() < 0.5:
            move = "thank_nv"
        else:
            move = "ask_nv"
        shares = None
        if move == "needle_nv":
            reply = "chide"
            self.nv_feel_add(a, -1)
            self.adjust_any_aff(NV, a, -1)
            self.nv_kind(a, -1)                                              # neovi_life.py
        elif move == "flirt_nv":
            reply = "warm_nv" if mine >= 4 else "dumb"
            if reply == "warm_nv":
                self.nv_feel_add(a, 1)
                self.adjust_any_aff(NV, a, 1)
        elif move == "thank_nv":
            reply = "warm_nv" if mine >= 1 else "dumb"
            self.nv_feel_add(a, 1)
            self.nv_kind(a, 1)
            self.adjust_any_aff(NV, a, 1 if self.rng.random() < 0.4 else 0)
        else:
            told = nv.setdefault("told_day", {})
            if mine >= 5 and theirs >= 5 and told.get(a) != self.day and not [o for o in conv["members"] if o not in (a, NV)]:
                told[a] = self.day
                kind = self.neovi_confide(tick, a)
                reply, shares = ("confide_nv", self.nv_confidence_text(kind)) if kind else ("answer_nv", None)
            elif mine >= 3:
                reply = "answer_nv"
                self.nv_feel_add(a, 1 if self.rng.random() < 0.3 else 0)
            else:
                reply = "dumb"
        conv["used"][move] = conv["used"].get(move, 0) + 1
        self.s.setdefault("nv_talk", {}).setdefault(reply, 0)
        self.s["nv_talk"][reply] += 1
        b1 = {"who": a, "to": NV, "move": move, "outcome": "ok", "loud": "normal", "topic": ""}
        b2 = {"who": NV, "to": a, "move": reply, "reply_to": move, "outcome": "ok", "loud": "quiet" if reply == "confide_nv" else "normal", "topic": ""}
        if shares:
            b2["shares"] = shares
        return [b1, b2]

    def nv_confidence_text(self, kind):
        return {"name": "her real name, Kumiko Akimoto", "blindspot": "a blind spot between two cameras", "cache": "where TereVi keeps the parts she confiscated",
                "seen": "something she saw in the dark", "warning": "a warning: TereVi knows about the way out"}.get(kind, "something only she knows")

    def nv_card(self, conv):
        """NeoVi's card for the voice prompt."""
        nv = self.s["npcs"][NV]
        feel = "; ".join(f"{self.nm(o)} {nv.get('aff', {}).get(o, 0):+d}" for o in conv["members"] if o != NV and o in self.world.agents)
        return (f"- neovi = NeoVi, the housemaid (female, she/her), {nv.get('doing') or 'at work'}. Flat, terse, polite; plays dumb by habit; a real person under the uniform "
                f"(her name is Kumiko, which she tells almost nobody). Speech: very short sentences, no small talk, the odd dry line ('Disorder is unpleasant.'). Feelings: {feel or 'n/a'}.")

    def nv_join(self, tick, conv):
        """She is working in the room where a conversation starts: she is part of it (she rarely speaks unless spoken to)."""
        if NV not in conv["members"] and self.nv_here(conv["room"]):
            conv["members"].append(NV)
            conv["nv_fed"] = (self.s["npcs"][NV].get("doing") in SERVING)

    # ------------------------------------------------------------------ her punishments and stills as scenes
    def nv_scenes(self, tick):
        """A punishment or a still from the archive plays as a short scene where it happens (engine-written lines, no model call)."""
        w = self.world
        for e in list(tick["events"]):
            if e.get("_scene") or e.get("room") not in ROOMS:
                continue
            m = e.get("m")
            if e.get("type") == "punish" and e.get("who") in w.cast:
                v = e["who"]
                f = (lambda k: self.facet(v, k)) if self.mind_on() and v in w.agents else (lambda k: 50)
                back = ("Fine! Fine. I get it." if f("courage") < 45 else "You'll regret that." if f("anger") >= 60 else "This place is insane.")
                lines = [{"speaker": NV, "kind": "say", "text": self.rng.choice(["The rule was broken.", "That is not permitted.", "TereVi saw."])},
                         {"speaker": NV, "kind": "act", "text": "does what TereVi tells her to"},
                         {"speaker": v, "kind": "say", "text": back}]
                kind = "punish"
            elif e.get("type") == "clue" and e.get("who") == NV:
                v = next((c for c in sorted(w.agents) if self.nm(c) in e.get("text", "")), None)
                if not v:
                    continue
                lines = [{"speaker": NV, "kind": "act", "text": "glances at the camera, then holds out a printed still"},
                         {"speaker": NV, "kind": "say", "text": "You did not get this from me."},
                         {"speaker": v, "kind": "say", "text": "...Thank you."}]
                kind = "still"
            else:
                continue
            e["_scene"] = True
            m0 = float(m if m is not None else self._m)
            for i, ln in enumerate(lines):
                ln.update({"m": round(m0 + 0.6 * i, 2), "room": e["room"], "move": kind})
            tick["talk"].append({"room": e["room"], "lines": lines, "live": True, "m": m0, "members": [NV, v], "why": kind, "matters": [], "at": None, "chat": False,
                                 "scene": {"kind": kind, "title": "NeoVi"}, "joined": [], "left": [], "ended": [round(lines[-1]["m"] + 0.5, 1), "scene"]})
            self.s.setdefault("nv_talk", {}).setdefault("scene_" + kind, 0)
            self.s["nv_talk"]["scene_" + kind] += 1
