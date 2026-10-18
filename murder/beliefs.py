"""Belief bases: what each person thinks is true, and why.

A belief is a small record in `agent["beliefs"]`: a kind, who it is about, where and when (absolute hours, day * 24 + hour), how it was learned (seen with
their own eyes, heard by overhearing, told to their face, inferred) and how sure they are. Beliefs can be wrong: a lie told to someone, a rumour, a line half
heard at the edge of earshot. The engine always knows the truth (`true`); the characters only know their beliefs.

Kinds:
  at     `s` was in room `r` from `t0` to `t1`
  did    `s` did something (`o` = the event type) in room `r` at `t0`; `n` is what they saw
  rumor  `n` is a claim about `s` (a rumour or gossip)
  news   `n` is a piece of news passed around (meals)
  lied   `s` lied to them (`n` says about what): inferred when a claim contradicts what they saw

Where beliefs come from: sightings (sampled from everyone's real positions each turn), witnessed events, testimony heard in conversation (told to members,
overheard by listeners), rumours, and the news at meals. What they are used for: testimony (who you were with), lie detection (a claim about where someone
was that contradicts what you saw), suspicion, the decision prompt during a case, and the GM view.
"""
from .data_world import ROOMS

MAX_BELIEFS = 80
SIGHT_STEP = 15                     # minutes between sightings sampled in a turn
SRC_RANK = {"seen": 3, "heard": 2, "told": 1, "inferred": 0}
WITNESS_KINDS = {"attack", "assault", "body", "punish", "outburst", "madness", "betrayal", "discover", "leak", "fall", "theft", "steal", "take", "give",
                 "fire", "lock", "break", "hide", "experiment", "meal", "fetch"}


class BeliefMixin:
    # ------------------------------------------------------------------ the store
    def beliefs(self, cid):
        a = self.world.agents.get(cid)
        return a.setdefault("beliefs", []) if a else []

    def believe(self, cid, b):
        """Add belief `b` to `cid` (merging with what they already hold). Returns the stored belief, or None."""
        a = self.world.agents.get(cid)
        if not a or b.get("s") == cid and b["k"] == "at" and b["src"] != "seen":
            return None
        bs = a.setdefault("beliefs", [])
        b = {k: v for k, v in b.items() if v is not None}
        b["c"] = round(max(0.05, min(1.0, float(b.get("c", 0.5)))), 2)
        if b["k"] == "at":
            b.setdefault("t1", b["t0"])
            gap = SIGHT_STEP / 60 + 0.01 if b["src"] == "seen" else 0.5      # consecutive sightings join up; a gap means they were out of sight
            for o in reversed(bs[-30:]):
                if o["k"] == "at" and o["s"] == b["s"] and o["r"] == b["r"] and o["src"] == b["src"] and o.get("by") == b.get("by") and b["t0"] <= o.get("t1", o["t0"]) + gap and b["t1"] >= o["t0"] - gap:
                    o["t0"], o["t1"] = min(o["t0"], b["t0"]), max(o.get("t1", o["t0"]), b["t1"])
                    o["c"] = max(o["c"], b["c"])
                    return o
        else:
            for o in bs:
                if o["k"] == b["k"] and o.get("s") == b.get("s") and o.get("n") == b.get("n"):
                    if SRC_RANK[b["src"]] > SRC_RANK[o["src"]] or b["c"] > o["c"]:
                        o.update(src=b["src"], c=max(o["c"], b["c"]), by=b.get("by", o.get("by")))
                    return o
        bs.append(b)
        if len(bs) > MAX_BELIEFS:
            now = self.abs_now()
            bs.sort(key=lambda x: (x["k"] == "lied", x["c"] - 0.02 * max(0.0, now - x.get("t1", x.get("t0", now)))), reverse=True)
            del bs[MAX_BELIEFS:]
        if b["src"] in ("told", "heard") and b["k"] == "at":
            self.check_claim(cid, b)
        return b

    def self_at(self, cid, room, t):
        """Where `cid` was themselves (kept apart from the other beliefs, three days back, so testimony never runs out of it)."""
        tr = self.world.agents[cid].setdefault("self_at", [])
        if tr and tr[-1][2] == room and t <= tr[-1][1] + SIGHT_STEP / 60 + 0.01:
            tr[-1][1] = max(tr[-1][1], t)
        else:
            tr.append([t, t, room])
        while tr and tr[0][1] < t - 72:
            tr.pop(0)

    def believed_at(self, cid, subj, t, slack=0.25):
        """Where `cid` believes `subj` was at absolute hour `t`: the surest matching belief, or None."""
        if subj == cid:
            for t0, t1, room in reversed(self.world.agents[cid].get("self_at") or []):
                if t0 - slack <= t <= t1 + slack:
                    return {"k": "at", "s": cid, "r": room, "t0": t0, "t1": t1, "src": "seen", "c": 1.0, "true": True}
            return None
        best = None
        for b in self.beliefs(cid):
            if b["k"] == "at" and b["s"] == subj and b["t0"] - slack <= t <= b.get("t1", b["t0"]) + slack:
                if not best or (SRC_RANK[b["src"]], b["c"]) > (SRC_RANK[best["src"]], best["c"]):
                    best = b
        return best

    def seen_with(self, cid, t, room, slack=0.5):
        """The people `cid` saw in `room` around absolute hour `t`."""
        return sorted({b["s"] for b in self.beliefs(cid) if b["k"] == "at" and b["src"] == "seen" and b["r"] == room
                       and b["t0"] - slack <= t <= b.get("t1", b["t0"]) + slack and b["s"] != cid and b["s"] in self.world.agents})

    # ------------------------------------------------------------------ lies
    def check_claim(self, cid, b):
        """A claim about where someone was, against what `cid` saw: a contradiction is a caught lie (if it came from the person it is about, or whoever told them)."""
        t = (b["t0"] + b.get("t1", b["t0"])) / 2
        mine = next((o for o in self.beliefs(cid) if o["k"] == "at" and o["src"] == "seen" and o["s"] == b["s"] and o["r"] != b["r"]
                     and o["t0"] - 0.1 <= t <= o.get("t1", o["t0"]) + 0.1), None)
        if not mine:
            return None
        liar = b.get("by") or b["s"]
        if liar not in self.world.agents or liar == cid:
            return None
        w = self.world
        what = f"said {self.nm(b['s'])} was in the {w.room_name(b['r'])}, but you saw them in the {w.room_name(mine['r'])}"
        self.believe(cid, {"k": "lied", "s": liar, "n": what, "src": "inferred", "c": 0.6 + 0.3 * mine["c"], "t0": self.abs_now(), "true": not b.get("true", True)})
        b["c"] = round(b["c"] * 0.3, 2)                                  # they no longer buy it
        if liar in w.agents[cid]["aff"]:
            w.adjust_aff(cid, liar, -2)
        w.remember(cid, f"{self.nm(liar)} {what}. They lied to you.")
        self.s.setdefault("lies_caught", []).append({"by": cid, "liar": liar, "about": b["s"], "day": self.day, "true_lie": not b.get("true", True)})
        del self.s["lies_caught"][:-30]
        self.booth_note(cid, "suspect", 2.5, liar)
        return liar

    def caught_liars(self, cid):
        return [b["s"] for b in self.beliefs(cid) if b["k"] == "lied" and b["c"] >= 0.5 and b["s"] in self.world.agents]

    # ------------------------------------------------------------------ feeds
    def belief_sightings(self, tick):
        """Everyone who is awake notes who they saw where, sampled from the real positions over the turn."""
        sm = self.__dict__.get("_sim")
        w = self.world
        if sm is None or not getattr(sm, "tracks", None):
            return
        nav = sm.nav
        perc = self.perc() if self.perception_on() else None
        base = self.day * 24 + float(tick["hour"])
        obs = [c for c in sorted(w.agents) if c in sm.tracks and not w.agents[c].get("out")]
        m = 0.0
        while m <= sm.dur:
            pos = {c: sm.pos_at(c, m) for c in obs}
            room = {c: nav.room_at(*p) if p else None for c, p in pos.items()}
            for o in obs:
                if w.agents[o].get("asleep") or not pos[o] or not room[o]:
                    continue
                light = self.light_of(room[o]) if room[o] in ROOMS else "lit"
                t = round(base + m / 60, 2)
                self.self_at(o, room[o], t)
                for c in obs:
                    if c == o or not pos[c] or not room[c] or w.agents[c].get("hiding"):
                        continue
                    if room[c] == room[o] or (perc and perc.sees(pos[o], pos[c], light)):
                        self.believe(o, {"k": "at", "s": c, "r": room[c], "t0": t, "t1": t, "src": "seen", "c": 0.9 if light == "lit" else 0.6, "true": True})
            m += SIGHT_STEP

    def belief_witness(self, evt, witnesses, actor):
        """A public event: whoever witnessed it believes it happened (and who did it)."""
        if evt.get("vis") != "public" or evt.get("type") not in WITNESS_KINDS or not witnesses:
            return
        w = self.world
        who = evt.get("who") if evt.get("who") in w.cast else actor
        t = self.abs_now() + (evt.get("m") or 0) / 60
        for c in witnesses:
            if c in w.agents and c != who:
                self.believe(c, {"k": "did", "s": who, "o": evt["type"], "r": evt.get("room"), "t0": round(t, 2), "n": str(evt.get("text", ""))[:140], "src": "seen", "c": 0.85, "true": True})

    def belief_from_talk(self, conv, lines, beats):
        """Testimony said in a conversation: the members are told it, listeners in earshot hear it (half-heard lines get the room wrong)."""
        w = self.world
        members = set(conv["members"]) | {x[1] for x in conv.get("joined", [])}
        for ln in lines:
            b = beats[ln["b"]] if 0 <= ln.get("b", -1) < len(beats) else {}
            cl = b.get("claim_at")
            if not cl:
                continue
            speaker = b["who"]
            base = {"k": "at", "s": cl["s"], "r": cl["r"], "t0": cl["t"], "t1": cl["t"], "by": speaker, "true": cl.get("true", True)}
            for c in members:
                if c != speaker and c in w.agents:
                    self.believe(c, {**base, "src": "told", "c": 0.35 + 0.3 * self.receptivity(c, speaker)})
            for c, lvl in (ln.get("heard") or {}).items():
                if c in w.agents and c not in members:
                    if lvl == "full":
                        self.believe(c, {**base, "src": "heard", "c": 0.55})
                    elif lvl == "part" and self.rng.random() < 0.5:
                        wrong = self.rng.choice([r for r in ROOMS if r != cl["r"]])           # caught the gist, got the room wrong
                        self.believe(c, {**base, "r": wrong, "src": "heard", "c": 0.25, "true": False})

    def belief_rumor(self, c, by, about, claim, lie):
        self.believe(c, {"k": "rumor", "s": about, "n": claim, "by": by if by in self.world.cast else None, "src": "told",
                         "c": 0.3 + 0.05 * max(-4, min(6, self.world.agents[c]["aff"].get(by, 0))) if by in self.world.agents else 0.3, "t0": self.abs_now(), "true": not lie})

    def belief_news(self, c, by, text):
        self.believe(c, {"k": "news", "s": by, "n": text, "by": by, "src": "told", "c": 0.7, "t0": self.abs_now(), "true": True})

    # ------------------------------------------------------------------ uses
    def belief_lines(self, cid):
        """For the decision prompt: what they saw around the death (during a case) and who they caught lying. Short, and only when it matters."""
        w, case = self.world, self.s.get("case")
        out = []
        if case and case.get("announced") and not case.get("resolved"):
            t = case.get("day", self.day) * 24 + case.get("hour", 12)
            seen = [b for b in self.beliefs(cid) if b["k"] == "at" and b["s"] in w.cast and b["t0"] - 1.5 <= t <= b.get("t1", b["t0"]) + 1.5]
            seen.sort(key=lambda b: (-SRC_RANK[b["src"]], -b["c"]))
            bits = [f"{self.nm(b['s'])} in the {w.room_name(b['r'])} ({'you saw' if b['src'] == 'seen' else 'you heard' if b['src'] == 'heard' else 'told by ' + self.nm(b.get('by'))})"
                    for b in seen[:5]]
            if bits:
                out.append("WHAT YOU KNOW about around the time of the death: " + "; ".join(bits) + ".")
        liars = self.caught_liars(cid)
        if liars:
            out.append("YOU CAUGHT LYING: " + ", ".join(self.nm(x) for x in liars[:3]) + ".")
        return out

    def beliefs_view(self, cid):
        """For the GM view: the latest beliefs, with how they were learned and whether they are wrong."""
        w = self.world
        out = []
        for b in self.beliefs(cid)[-8:][::-1]:
            if b["k"] == "at":
                text = f"{self.nm(b['s'])} in the {w.room_name(b['r'])} at {int(b['t0'] % 24):02d}:{int(b['t0'] % 1 * 60):02d}"
            elif b["k"] == "lied":
                text = f"{self.nm(b['s'])} lied: {b.get('n', '')}"
            else:
                text = b.get("n", "")
            out.append({"text": text[:120], "src": b["src"], "c": b["c"], "false": not b.get("true", True), "by": b.get("by")})
        return out
