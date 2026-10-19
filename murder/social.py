"""Social moves: what people do to each other when they talk, decided and resolved by the engine.

A conversation is a run of short exchanges. In each, somebody makes a move on somebody else (comfort them, joke, confide, probe, gossip, accuse, threaten, propose a pact,
lie...), the target reacts, and sometimes a third person chimes in. Every move has a willingness (how much the speaker wants to make it, from their nature, their feelings
and the situation) and is resolved against the target's receptivity (their feelings toward the speaker, their nature and their mood): it succeeds, fails, or backfires. The
outcome changes the world at once (affinity, special moments that restore sanity, secrets, rumours, pacts, testimonies, accomplices, gifts) through the same appliers the
game always used; a language model, when one is used, only puts words to the beats afterwards (voice.py). Nothing a model writes changes game state here.

Families (after Prom Week's social exchanges): bonding, status, information, conflict, alliance, deception.
"""
from .drama import GIFT_ITEMS
from .booth import MOVE_URGE

# move: (family, loudness, short topic used when somebody only half hears it)
HOLD_FLOOR = 0.2              # chance the last speaker goes on and opens the next exchange too

MOVES = {
    "chat":     ("bonding", "normal", "small talk"),
    "joke":     ("bonding", "normal", "a joke"),
    "comfort":  ("bonding", "quiet", "how someone is holding up"),
    "confide":  ("bonding", "whisper", "something personal"),
    "flirt":    ("bonding", "quiet", "something flirtatious"),
    "gift":     ("bonding", "normal", "a gift"),
    "boast":    ("status", "normal", "somebody bragging"),
    "mock":     ("status", "normal", "somebody being made fun of"),
    "putdown":  ("status", "heated", "an insult"),
    "probe":    ("information", "normal", "where people were"),
    "gossip":   ("information", "quiet", "gossip about {x}"),
    "warn":     ("information", "quiet", "a warning about {x}"),
    "reveal":   ("information", "whisper", "a secret about {x}"),
    "accuse":   ("conflict", "heated", "an accusation"),
    "threaten": ("conflict", "heated", "a threat"),
    "confront": ("conflict", "heated", "an old grievance"),
    "pact":     ("alliance", "whisper", "sticking together"),
    "recruit":  ("alliance", "whisper", "asking for help"),
    "teamwork": ("alliance", "normal", "the way out"),
    "incite":   ("deception", "whisper", "{x}"),
    "feign":    ("deception", "normal", "friendly talk"),
}
# replies the target gives (beats with no effects of their own)
REPLIES = ("agree", "warm", "laugh", "shrug", "rebuff", "snap", "testify", "lie", "deflect", "deny", "counter", "back_down", "stand_up", "accept", "refuse", "freeze")
LOUD_RANK = {"whisper": 0, "quiet": 1, "normal": 2, "heated": 3}


def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


class SocialMixin:
    # ------------------------------------------------------------------ small helpers
    def _aff(self, a, b):
        ag = self.world.agents.get(a)
        return ag["aff"].get(b, 0) if ag else 0

    def _fc(self, cid, name):
        return self.facet(cid, name) if self.mind_on() else 50

    def receptivity(self, t, a):
        """0..1: how open `t` is to whatever `a` tries now (feelings toward them, trust, mood)."""
        w = self.world
        ta = w.agents.get(t)
        if not ta:
            return 0.0
        r = 0.5 + 0.05 * self._aff(t, a) + 0.1 * (self._fc(t, "trust") - 50) / 50
        if ta["sanity"] < 35:
            r -= 0.12
        if any(x["a"] == t and x["b"] == a and x["kind"] in ("wronged", "betrayed") for x in self.s.get("ties", [])):
            r -= 0.15
        if a in (ta.get("distrust") or {}):
            r -= 0.15                                                  # they decided not to trust them (reflection.py)
        return _clamp(r)

    # ------------------------------------------------------------------ where people were (for testimonies)
    def log_whereabouts(self, tick):
        """Remember where everybody was this turn (kept a few days) so testimonies can be true, or lies."""
        log = self.s.setdefault("where_log", {})
        h = int(tick["hour"])
        for cid, a in self.world.agents.items():
            ent = log.setdefault(cid, [])
            if not ent or ent[-1][:2] != [self.day, h]:
                ent.append([self.day, h, a["room"]])
            del ent[:-36]

    def whereabouts(self, cid, day, hour):
        """The room `cid` was in at day/hour (the last record at or before it), or None."""
        best = None
        for d, h, r in self.s.get("where_log", {}).get(cid, []):
            if (d, h) <= (day, hour):
                best = r
        return best

    def testimony_for(self, cid):
        """What `cid` says about where they were when the death happened: the truth, or (for the culprit) a lie."""
        w, case = self.world, self.s.get("case")
        if not case:
            return None
        day, hour = case.get("day", self.day), case.get("hour", 12)
        hh = f"{int(hour) % 24:02d}:00"
        t = round(day * 24 + hour + case.get("m", 0.0) / 60, 2)
        if cid == case.get("killer"):
            pool = sorted({r for (d, h, r) in self.s.get("where_log", {}).get(cid, []) if d == day and r != case.get("room")}) or [w.cast[cid].get("home") or "garden"]
            room = self.rng.choice(pool)
            return {"claim": f"I was in the {w.room_name(room)} around {hh}, nowhere near the {w.room_name(case.get('room'))}.", "lie": True, "room": room, "t": t}
        mine = self.believed_at(cid, cid, t, slack=0.13)             # where they know they were (their own sighting)
        truth = mine["r"] if mine else None
        sm = self.__dict__.get("_sim")
        if not truth and sm is not None and cid in sm.tracks and (day, hour) == (self.day, self.s.get("_hour")):
            p = sm.pos_at(cid, case.get("m", 0.0))                    # it happened this turn: they know where they were a moment ago
            truth = sm.nav.room_at(*p) if p else None
        if not truth:
            return {"claim": f"I honestly don't remember where I was around {hh}.", "lie": False}
        with_ = self.seen_with(cid, t, truth)[:2]                     # the people they actually saw there
        claim = f"I was in the {w.room_name(truth)} around {hh}" + (f", with {' and '.join(self.nm(o) for o in with_)}." if with_ else ", on my own.")
        return {"claim": claim, "lie": False, "room": truth, "t": t}

    def suspects(self, cid):
        """Whom `cid` suspects, strongest first: hooks they hold a suspect for, the case evidence they have noted, people they hate during a case."""
        w, s = self.world, self.s
        out = list(self.caught_liars(cid))                          # someone caught lying to them comes first
        out += [b["s"] for b in self.beliefs(cid) if b["k"] == "has" and b["s"] in w.agents]      # then someone they know keeps a weapon
        for h in s.get("hooks", []):
            if not h.get("closed") and h.get("suspect", {}).get(cid) in w.agents:
                out.append(h["suspect"][cid])
        case = s.get("case")
        if case and case.get("announced") and not case.get("resolved"):
            a = w.agents.get(cid) or {}
            for e in (a.get("evidence") or [])[-12:]:
                for o in w.agents:
                    if o != cid and self.nm(o) in str(e.get("text", "")):
                        out.append(o)
            hated = sorted((o for o in w.agents if o != cid and self._aff(cid, o) <= -4), key=lambda o: self._aff(cid, o))
            out.extend(hated[:1])
        return [o for o in dict.fromkeys(out) if o != cid]

    # ------------------------------------------------------------------ what someone might do
    def move_options(self, conv, a, t):
        """[(weight, move, about)] for `a` making a move on `t` in this conversation."""
        w, s = self.world, self.s
        A, T = w.agents.get(a), w.agents.get(t)
        if not A or not T:
            return []
        f = lambda n: self._fc(a, n)
        aff, back = self._aff(a, t), self._aff(t, a)
        case = s.get("case")
        inv_case = bool(case and case.get("announced") and not case.get("resolved"))
        plots = s.get("plots", {})
        used = conv.setdefault("used", {})
        opts = [(1.0 + f("gregariousness") / 100, "chat", None)]
        if f("humour") >= 45 and aff >= -2:
            opts.append((f("humour") / 45, "joke", None))
        if (T["sanity"] < 55 or any(x.get("day") == self.day for x in T["memory"].get("lost", []))) and aff >= 0:
            opts.append((1.2 * f("altruism") / 50 * (1 + max(0, aff) / 5), "comfort", None))
        if aff >= 4 and back >= 2:
            opts.append(((f("trust") / 50) * (1.6 if A["sanity"] < 55 else 1.0), "confide", None))
        if f("romantic") >= 55 and aff >= 4:
            opts.append((f("romantic") / 60 * (1.5 if aff >= 6 else 1.0), "flirt", None))
        gift = next((k for k in A["inv"] if k in GIFT_ITEMS), None)
        if gift and aff >= 3 and not A.get("gave_today") == self.day:
            opts.append((0.8, "gift", gift))
        if f("vanity") >= 60:
            opts.append((f("vanity") / 70, "boast", None))
        if (f("humour") >= 60 and aff <= 1) or (f("cruelty") >= 55 and aff <= -1):
            opts.append(((f("cruelty") + f("humour")) / 120, "mock", None))
        if aff <= -4 and (f("anger") >= 55 or f("cruelty") >= 55):
            opts.append((1.0 + (f("anger") - 50) / 40, "putdown", None))
        if inv_case or f("curiosity") >= 65:
            opts.append(((2.5 if inv_case else 0.6) * f("curiosity") / 50, "probe", None))
        heard = [r for r in s.get("rumors", [])[-8:] if a in r.get("heard", []) and r["about"] not in (a, t)]
        hated = [o for o in w.agents if o not in (a, t) and self._aff(a, o) <= -3]
        if (heard or hated) and aff >= 0 and back >= 0:
            x = heard[-1]["about"] if heard else self.rng.choice(hated)
            opts.append((0.6 + (f("cunning") if "cunning" in self.mind(a)["facets"] else 50) / 100, "gossip", x))
        sus = [o for o in self.suspects(a) if o != t]
        if sus and aff >= 2:
            opts.append((0.9, "warn", sus[0]))
        secrets = [k["of"] for k in A.get("known_secrets", []) if k["of"] not in (a, t) and k["of"] in w.cast and t not in [x.get("by") for x in [k]]]
        tellable = [x for x in secrets if self._aff(a, x) <= -2 or (aff >= 5 and f("trust") >= 55)]
        if tellable:
            opts.append((0.5 + (0.6 if A["sanity"] < 40 else 0), "reveal", tellable[0]))
        if inv_case and t in self.suspects(a):
            opts.append((1.6 + f("assertiveness") / 60, "accuse", None))
        if aff <= -5 and (f("anger") >= 60 or a in plots):
            opts.append((0.8 + (f("anger") - 50) / 50, "threaten", None))
        if any(x["a"] == a and x["b"] == t and x["kind"] in ("wronged", "betrayed", "rebuffed") for x in s.get("ties", [])) or any(
                r["by"] == t and r["about"] == a and a in r.get("heard", []) for r in s.get("rumors", [])[-8:]):
            opts.append((1.3 * f("assertiveness") / 50, "confront", None))
        if aff >= 3 and back >= 3 and (self.dread_level() >= 2 or inv_case) and not any({b["a"], b["b"]} == {a, t} and b["kind"] == "pact" for b in s.get("bonds", [])):
            opts.append((0.9, "pact", None))
        plan = plots.get(a)
        if plan and plan.get("target") not in (t,) and back >= 5 and len(s.get("accomplices", {}).get(a, [])) < 2:
            opts.append((0.7, "recruit", plan.get("target")))
        if self.revealed and (A.get("worked") == self.day or T.get("worked") == self.day) and aff >= 1:
            opts.append((0.8, "teamwork", None))
        if self.murders and (plan or f("vengefulness") >= 65):
            victim = (plan or {}).get("target") or next((o for o in hated), None)
            if victim and victim not in (a, t) and self._aff(t, victim) <= -2:
                opts.append((0.7 + (0.5 if plan else 0), "incite", victim))
        if plan and plan.get("target") == t:
            opts.append((1.2, "feign", None))
        out = []
        for wgt, mv, about in opts:
            wgt = wgt / (1 + 1.5 * used.get(mv, 0))                     # people do not repeat themselves in one conversation
            if wgt > 0.05:
                out.append((wgt, mv, about))
        return out

    def pick_move(self, conv, a, t):
        pm = self.proposed_move_for(a, t)                         # a move the model proposed and the engine accepted (proposer.py)
        if pm and pm[0] in MOVES:
            return pm
        opts = self.move_options(conv, a, t)
        if not opts:
            return "chat", None
        tot = sum(o[0] for o in opts)
        r = self.rng.random() * tot
        for wgt, mv, about in opts:
            r -= wgt
            if r <= 0:
                return mv, about
        return opts[-1][1], opts[-1][2]

    # ------------------------------------------------------------------ resolving a move
    def resolve_move(self, tick, conv, a, t, move, about=None):
        """Roll the move against the target's receptivity, apply what happens, and return its beats: the move and the target's reply."""
        w = self.world
        r = self.receptivity(t, a)
        fam, loud, topic = MOVES[move]
        base = {"chat": 0.6, "joke": 0.55, "comfort": 0.55, "confide": 0.6, "flirt": 0.4, "gift": 0.85, "boast": 0.35, "mock": 0.45, "putdown": 0.55,
                "probe": 0.7, "gossip": 0.6, "warn": 0.55, "reveal": 0.9, "accuse": 0.45, "threaten": 0.5, "confront": 0.45, "pact": 0.5, "recruit": 0.4,
                "teamwork": 0.6, "incite": 0.5, "feign": 0.6}[move]
        p = _clamp(base * (0.4 + 1.2 * r))
        roll = self.rng.random()
        outcome = "ok" if roll < p else ("backfire" if roll > 1 - 0.25 * (1 - r) else "fail")
        fx = {}
        reply, claim, claim_at, shares = "shrug", None, None, None
        aff = lambda x, y, d: fx.setdefault("affinity", []).append({"from": x, "to": y, "delta": d})
        special = lambda kind, who, depth=1, why="": fx.setdefault("special", []).append({"kind": kind, "who": who, "depth": depth, "why": why or kind})
        hurt = lambda x, d, why: (fx.setdefault("sanity", {}).__setitem__(x, fx.get("sanity", {}).get(x, 0) - d), fx.setdefault("why", {}).__setitem__(x, why))
        depth = 1 + (1 if min(self._aff(a, t), self._aff(t, a)) >= 6 else 0) + (1 if min(self._aff(a, t), self._aff(t, a)) >= 8 else 0)
        if move == "chat":
            if outcome == "ok":
                aff(t, a, 1)
                reply = "warm"
            else:
                reply = "shrug"
        elif move == "joke":
            if outcome == "ok":
                aff(t, a, 1)
                aff(a, t, 1)
                reply = "laugh"
                if self._aff(t, a) >= 2 and self.rng.random() < 0.35:
                    special("laughter", [a, t], 1, "a shared laugh")
            elif outcome == "backfire":
                aff(t, a, -1)
                reply = "snap"
        elif move == "comfort":
            if outcome == "ok":
                special("comfort", [t, a], depth, "comforted")
                aff(t, a, 2)
                reply = "accept"
                self.add_tie(t, a, "helped", f"comforted them on day {self.day}")
            elif outcome == "backfire":
                aff(t, a, -1)
                reply = "snap"
            else:
                reply = "rebuff"
        elif move == "confide":
            if outcome != "ok" and self.close_pair(a, t) and self.rng.random() < 0.8:
                outcome = "ok"                                     # a partner or close friend rarely turns a confidence away
            shares = self.confidence_of(a, t, depth)
            if outcome == "ok":
                special("confession", [a, t], depth, "opened up")
                aff(t, a, 2)
                aff(a, t, 1)
                reply = "warm"
                if shares.startswith("their secret") or self._aff(a, t) >= 6 and self.rng.random() < 0.25:
                    fx["reveals"] = [{"by": a, "about": a, "to": [t]}]
            else:
                hurt(a, 1, "rebuffed")
                reply = "rebuff"
                self.add_tie(a, t, "rebuffed", f"turned them away when they opened up on day {self.day}")
        elif move == "flirt":
            if outcome == "ok":
                aff(t, a, 2)
                reply = "warm"
                if min(self._aff(a, t), self._aff(t, a)) >= 5:
                    special("romance", [a, t], depth, "a spark")
                    if min(self._aff(a, t), self._aff(t, a)) >= 6:
                        fx["bonds"] = [{"a": a, "b": t, "kind": "romance"}]
            elif outcome == "backfire":
                hurt(a, 2, "humiliated")
                aff(t, a, -1)
                reply = "rebuff"
            else:
                reply = "shrug"
        elif move == "gift":
            fx["gives"] = [{"from": a, "to": t, "item": about, "qty": 1}]
            w.agents[a]["gave_today"] = self.day
            special("gift", [t, a], 1, "a gift")
            aff(t, a, 2)
            reply, outcome = "accept", "ok"
        elif move == "boast":
            if self.has_trait(t, "no_talent"):
                hurt(t, 1, f"next to {self.nm(a)}, she feels she has no talent at all")
            if outcome == "ok":
                aff(t, a, 1 if self._fc(t, "gregariousness") >= 60 else 0) if self._fc(t, "gregariousness") >= 60 else None
                reply = "shrug"
            else:
                aff(t, a, -1)
                reply = "snap" if outcome == "backfire" else "shrug"
        elif move == "mock":
            if outcome == "ok":
                hurt(t, 1, f"mocked by {self.nm(a)}")
                aff(t, a, -1)
                reply = "back_down"
            else:
                hurt(a, 1, "the joke fell flat")
                for o in conv["members"]:
                    if o not in (a, t) and o in w.agents:
                        aff(o, a, -1)
                reply = "snap"
        elif move == "putdown":
            if outcome == "ok":
                hurt(t, 2, f"insulted by {self.nm(a)}")
                aff(t, a, -2)
                reply = "back_down"
                if self._aff(a, t) <= -4 and self._aff(t, a) <= -4:
                    fx["bonds"] = [{"a": a, "b": t, "kind": "feud"}]
            else:
                hurt(a, 1, "shot down")
                aff(t, a, -1)
                reply = "stand_up"
        elif move == "probe":
            tm = self.testimony_for(t) if self.s.get("case") and self.s["case"].get("announced") else None
            if tm and outcome != "backfire":
                claim = tm["claim"]
                fx["testimonies"] = [{"by": t, "claim": claim}]
                if tm.get("room"):
                    claim_at = {"s": t, "r": tm["room"], "t": tm["t"], "true": not tm["lie"]}
                reply = "lie" if tm["lie"] else "testify"
                outcome = "ok"
            elif self.s.get("case") and self.s["case"].get("killer") == t:
                reply, outcome = "deflect", "fail"
            else:
                reply = "deflect" if outcome != "ok" else "testify"
                if outcome == "backfire":
                    aff(t, a, -1)
        elif move == "gossip":
            if outcome != "backfire":
                tone = "bad" if self._aff(a, about) < 0 else "good"
                heard = next((r for r in reversed(self.s.get("rumors", [])) if r["about"] == about and a in r.get("heard", [])), None)
                claim = heard["claim"] if heard else (f"{self.nm(about)} is not who they say they are." if tone == "bad" else f"{self.nm(about)} has a good heart, whatever people say.")
                fx["rumors"] = [{"by": a, "about": about, "claim": claim, "tone": tone, "lie": not heard and self._fc(a, "trust") < 45}]
                reply = "agree" if outcome == "ok" else "shrug"
            else:
                aff(t, a, -1)
                reply = "rebuff"
        elif move == "warn":
            if outcome == "ok":
                aff(t, a, 1)
                if about in w.agents and t in w.agents and about in w.agents[t]["aff"]:
                    aff(t, about, -1)
                fx.setdefault("notes", {})[t] = f"{self.nm(a)} warned you about {self.nm(about)}."
                reply = "agree"
            else:
                reply = "shrug"
        elif move == "reveal":
            fx["reveals"] = [{"by": a, "about": about, "to": [t]}]
            outcome, reply = "ok", "agree"
        elif move == "accuse":
            fx["testimonies"] = [{"by": a, "claim": f"I think {self.nm(t)} did it."}]
            aff(t, a, -2)
            if self.has_trait(t, "trapped"):                        # challenged head-on, she freezes instead of answering
                hurt(t, 3, f"backed into a corner by {self.nm(a)}")
                reply = "freeze"
            elif outcome == "ok":
                hurt(t, 2, "accused")
                reply = "deny"
            else:
                for o in conv["members"]:
                    if o not in (a, t) and o in w.agents and self._aff(o, t) >= 3:
                        aff(o, a, -1)
                reply = "counter"
        elif move == "threaten":
            if outcome == "ok":
                hurt(t, 3, f"threatened by {self.nm(a)}")
                aff(t, a, -2)
                self.add_tie(t, a, "threatened", f"threatened them on day {self.day}")
                reply = "back_down"
            else:
                hurt(a, 1, "faced down")
                aff(t, a, -1)
                reply = "stand_up"
        elif move == "confront" and self.has_trait(t, "trapped") and outcome != "ok":
            hurt(t, 2, f"cornered by {self.nm(a)}")
            aff(a, t, -1)
            reply = "freeze"
        elif move == "confront":
            if outcome == "ok":
                aff(a, t, 1)
                aff(t, a, 1)
                reply = "accept"
            elif outcome == "backfire":
                aff(a, t, -2)
                aff(t, a, -2)
                hurt(a, 1, "a row")
                hurt(t, 1, "a row")
                reply = "snap"
                if self._aff(a, t) <= -4 and self._aff(t, a) <= -4:
                    fx["bonds"] = [{"a": a, "b": t, "kind": "feud"}]
            else:
                aff(a, t, -1)
                reply = "deny"
        elif move == "pact":
            if outcome == "ok":
                fx["bonds"] = [{"a": a, "b": t, "kind": "pact"}]
                aff(t, a, 1)
                reply = "accept"
            else:
                reply = "refuse"
        elif move == "recruit":
            plan = self.s.get("plots", {}).get(a)
            if plan and outcome == "ok":
                role = "alibi" if self.rng.random() < 0.5 else "lookout"
                fx["accomplice"] = [{"by": a, "helper": t, "role": role, "victim": plan["target"]}]
                reply = "accept"
            else:
                aff(t, a, -1)
                reply = "refuse"
        elif move == "teamwork":
            if outcome == "ok":
                special("teamwork", [a, t], 1, "working on the way out")
                aff(t, a, 1)
                reply = "agree"
            else:
                reply = "shrug"
        elif move == "incite":
            how = "blackmail" if any(k["of"] == t for k in w.agents[a].get("known_secrets", [])) else ("trick" if self._fc(a, "trust") < 45 else "persuade")
            claim = f"{self.nm(about)} is going to come for you. Better you move first."
            fx["incite"] = [{"by": a, "target": t, "victim": about, "how": how, "claim": claim}]
            reply = "shrug"
        elif move == "feign":
            if outcome != "backfire":
                aff(t, a, 1)
                reply = "warm"
            else:
                reply = "rebuff"
        conv["used"][move] = conv["used"].get(move, 0) + 1
        u = MOVE_URGE.get(move)
        if u and outcome != "fail":
            self.booth_note(t, u[0], u[1], a)                    # something to tell the camera about
        self.apply_talk_fx(tick, conv["room"], [m for m in conv["members"] if m in w.agents], fx, conv.get("hour", tick["hour"]))
        heated = loud == "heated" or outcome == "backfire" and fam == "conflict"
        loud_ = "heated" if heated else loud
        about_ = about if isinstance(about, str) and about in w.cast else None
        b1 = {"who": a, "to": t, "move": move, "about": about_, "item": about if move == "gift" else None, "outcome": outcome, "loud": loud_,
              "topic": topic.format(x=self.nm(about_) if about_ else "someone")}
        if move == "confide":
            b1["shares"] = shares
        b2 = {"who": t, "to": a, "move": reply, "reply_to": move, "outcome": outcome, "loud": "heated" if reply in ("snap", "stand_up", "counter") else ("quiet" if loud == "whisper" else loud),
              "topic": b1["topic"], **({"claim": claim} if claim else {}), **({"claim_at": claim_at} if claim_at else {})}
        return [b1, b2]

    def close_pair(self, a, t):
        """Partners, or friends who are close both ways."""
        return any({b["a"], b["b"]} == {a, t} and b["kind"] == "romance" for b in self.s.get("bonds", [])) or min(self._aff(a, t), self._aff(t, a)) >= 7

    def confidence_of(self, a, t, depth):
        """What `a` actually opens up about: their secret to someone very close, otherwise what weighs on them most right now."""
        w = self.world
        sec = (w.cast.get(a) or {}).get("secret") or ""
        if depth >= 3 and sec:
            return "their secret: " + sec.split(". ")[0].rstrip(".") + "."
        if self.mind_on():
            low = sorted((th for th in self.mind(a)["thoughts"] if th["w"] < 0), key=lambda th: th["w"] * th["t"] / th["t0"])
            if low:
                return f"what weighs on them: {low[0]['c']}"
        A = w.agents[a]
        if A["memory"].get("lost"):
            return "how much they miss someone they lost here"
        return "that they are more frightened than they let anyone see" if A["sanity"] < 60 else "how much they miss home and who is waiting there"

    def chime_in(self, tick, conv, a, t, c):
        """A third person takes a side after a move: warmer toward whoever they agree with."""
        side = a if self._aff(c, a) >= self._aff(c, t) else t
        other = t if side == a else a
        fx = {"affinity": [{"from": side, "to": c, "delta": 1}]}
        if self._aff(c, other) < 0:
            fx["affinity"].append({"from": other, "to": c, "delta": -1})
        self.apply_talk_fx(tick, conv["room"], [m for m in conv["members"] if m in self.world.agents], fx, conv.get("hour", tick["hour"]))
        return {"who": c, "to": side, "move": "side", "outcome": "ok", "loud": "normal", "topic": "", "against": other}

    def run_exchange(self, tick, conv):
        """One exchange: the next speaker makes a move on someone, they reply, and sometimes a third person sides with one of them. Returns the beats."""
        w = self.world
        members = [m for m in conv["members"] if m in w.agents and not w.agents[m].get("out")]
        if len(members) < 2:
            return []
        last = conv["beats"][-1]["who"] if conv.get("beats") else None
        opens = conv.setdefault("opens", {})
        if last is None:
            a = conv.get("initiator") if conv.get("initiator") in members else members[0]
        elif last in members and self.rng.random() < HOLD_FLOOR:
            a = last                                                # they hold the floor and go on; the voice is told it is not a reply
        else:
            a = min((m for m in members if m != last), key=lambda m: (opens.get(m, 0), members.index(m)))
        opens[a] = opens.get(a, 0) + 1
        want = (w.agents[a].get("want_talk") or {})
        pref = [x for x in want.get("who", []) if x in members and x != a] if want.get("day") == self.day else []
        others = [m for m in members if m != a]
        t = pref[0] if pref else max(others, key=lambda o: (abs(self._aff(a, o)), o))
        mv, about = self.pick_move(conv, a, t)
        beats = self.resolve_move(tick, conv, a, t, mv, about)
        if a == last:
            beats[0]["cont"] = True
        third = [m for m in members if m not in (a, t)]
        if third and MOVES[mv][0] in ("conflict", "status", "information") and self.rng.random() < 0.5:
            beats.append(self.chime_in(tick, conv, a, t, self.rng.choice(third)))
        return beats
