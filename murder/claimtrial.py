"""The claim-based trial: a contest of claims against beliefs, decided by the engine, voiced by the model.

Everyone states a claim (where they were when it happened: the truth, or for the culprit a lie). The engine checks every claim against every
participant's beliefs: a claim that conflicts with something another participant saw is a WEAK POINT, and that fact is the truth bullet. Whether
the holder dares to raise it is a WILLINGNESS roll (courage, how they feel about the speaker, how sure they are, whether they are protecting
someone). A proven lie halves the liar's CREDIBILITY. The culprit answers a challenge with the LIE PLANNER: a new story that fits what they think
the room knows; when none fits they are CORNERED (indignant, tearful, silent or lashing out, by temperament) and never confess.

Facts on the table move a public SUSPICION METER per suspect: a contradiction, a clue that names someone (a handprint on the weapon, stained clothes, a
planted item), being seen near the scene, a caught lie; a corroborated alibi or a frame flaw lowers it. The sequences:
  open debate   everyone's alibi, the clues presented, the objections raised
  hot seat      the most suspected stands in the middle: attackers present facts, a defender counters, the accused answers
  clash         two people who suspect different people go head to head with their strongest facts; the loser concedes
  brainstorm    nobody stands out: the theory that whoever has no corroborated alibi could have done it
  closing       the last pleas
Then the VOTES are computed: each person weighs the public meter, what only they know, affinity and fear, and the lead of the people they trust.
The model writes only the lines (one voicing call per sequence; templates otherwise). ClaimTrialMixin is mixed into DayRunner (engine.py).
"""
from collections import Counter

TITLES = {"debate": "OPEN DEBATE", "hotseat": "THE HOT SEAT", "duel": "THE CLASH", "brainstorm": "BRAINSTORM", "closing": "CLOSING ARGUMENTS",
          "crossexam": "CROSS-EXAMINATION", "split": "SPLIT COURT", "climax": "THE CLIMAX"}
CLUE_WEIGHT = {"weapon": 2.5, "stained": 2.5, "clothes": 2.0, "planted": 2.0, "framed_unconscious": 3.0, "decoy": 1.0, "ledger": 0.6, "drag_marks": 1.0, "staging": 1.0}
CRIES = ["Objection!", "Hold it!", "That's wrong!", "No, that's not it!", "Wait a second!", "Liar!", "Contradiction!", "I'll cut through that!"]
CORNERED = {"indignant": "How dare you. I have answered every question and you still want blood.", "tearful": "Please, I'm telling you, I didn't, I couldn't...",
            "silent": "...", "lashing": "Why is nobody looking at {other}? They had every reason!"}


AGAIN = ("So did I. {who} was there.", "Same here: I saw {who} there too.", "I can back that up. I saw {who} there as well.", "Me too. {who}, right there.")


class ClaimTrialMixin:
    # ------------------------------------------------------------------ the facts each person holds
    def case_time(self, case):
        return round(case.get("day", self.day) * 24 + case.get("hour", 12) + case.get("m", 0.0) / 60, 2)

    def trial_claims(self, case, ids):
        """Everyone's alibi for the moment of the death: {cid: {"r", "t", "text", "lie"}} (the culprit's from the lie planner)."""
        out = {}
        t = self.case_time(case)
        for cid in ids:
            tm = self.testimony_for(cid) or {}
            out[cid] = {"r": tm.get("room"), "t": tm.get("t", t), "text": tm.get("claim") or "I don't remember.", "lie": bool(tm.get("lie"))}
        return out

    def trial_facts(self, case, ids):
        """[{"by", "about", "kind", "w", "text", "true"}]: what participants know that bears on who did it (positive w accuses, negative clears)."""
        w = self.world
        t = self.case_time(case)
        room = case.get("room")
        facts = []
        for c in case.get("clues", []):
            if not c.get("found_by") or not self.clue_on_table(c):
                continue
            by = next((f for f in c["found_by"] if f in ids), None)
            if not by:
                continue
            named = [p for p in ids if self.nm(p) in c.get("text", "")]
            kind = c.get("kind") or "clue"
            wt = CLUE_WEIGHT.get(kind, 1.2)
            text = c.get("text", "")
            for p in named:
                sign = 1.0
                if kind == "frame_flaw":
                    sign = -1.0                                     # a sign they were put out of action clears them
                elif kind == "ledger":
                    cleared = text.split("Not placed")[0]
                    sign = -1.5 if self.nm(p) in cleared else 1.0       # placed elsewhere by the cameras, or not placed at all
                facts.append({"by": by, "about": p, "kind": "clue", "w": sign * wt, "text": text[:200], "true": kind not in ("planted", "decoy")})
        for h in ids:
            for b in self.beliefs(h):
                if b["k"] == "at" and b["s"] in ids and b["s"] != h and b.get("r") == room and b["t0"] - 0.75 <= t <= b.get("t1", b["t0"]) + 0.75:
                    facts.append({"by": h, "about": b["s"], "kind": "near_scene", "w": 2.0 * b["c"], "text": f"I saw {self.nm(b['s'])} in the {w.room_name(room)} around {int(t % 24):02d}:00.",
                                  "true": b.get("true", True)})
                elif b["k"] == "has" and b["s"] in ids:
                    wt = self.weapon_match(b.get("o"), case.get("weapon"))
                    if wt:
                        facts.append({"by": h, "about": b["s"], "kind": "has", "w": wt, "text": b.get("n", "")[:160], "true": b.get("true", True)})
                elif b["k"] == "lied" and b["s"] in ids:
                    what = b.get("n", "")[:120].replace("you saw", "I saw")
                    facts.append({"by": h, "about": b["s"], "kind": "lied_before", "w": 1.5, "text": f"{self.nm(b['s'])} has lied to me before: they {what}.", "true": b.get("true", True)})
        seen_it = 0
        for wit in case.get("witnesses") or []:
            if wit in ids and case.get("killer") in ids and wit != case["killer"]:
                text = f"I saw it happen. It was {self.nm(case['killer'])}." if not seen_it else f"I saw it too. It was {self.nm(case['killer'])}."
                facts.append({"by": wit, "about": case["killer"], "kind": "witness", "w": 6.0, "text": text, "true": True})
                seen_it += 1
        return facts + self.mark_facts(case, ids) + self.look_facts(case, ids)

    def compare_marks(self, beats, marks, case, ids, killer, raise_fact, push):
        """What the body and the weapon show, compared by eye: hands on the table, who uses which hand, who is taller, whose hands are scratched."""
        if not marks:
            return
        def names(ps, by):
            ns = [self.nm(p) for p in ps if p != by] + (["me"] if by in ps else [])
            return ", ".join(ns[:-1]) + (" and " if len(ns) > 1 else "") + ns[-1] if ns else "nobody"
        inf = case.get("marks") or {}
        for key in ("hand", "handed", "taller"):
            group = [f for f in marks if f["mark"] == key]
            if not group:
                continue
            by = group[0]["by"]
            for f in group:
                raise_fact(f, beats, quiet=True)
            fit = [f["about"] for f in group if f["fits"]]
            if key == "hand":
                size = inf.get("hand") or case.get("handmark")
                self.trial_beat(beats, by, "Everyone, put your hands on the table.", "compare")
                self.trial_beat(beats, by, f"The mark was left by a {size} hand. That's {names(fit, by)}." if fit else f"The mark was left by a {size} hand. Nobody here has one... so who?", "compare")
            elif key == "handed":
                self.trial_beat(beats, by, f"Whoever did it used their {inf['handed']} hand. That's {names(fit, by)}.", "compare")
            else:
                self.trial_beat(beats, by, f"The blows came from {'above' if inf['taller'] else 'level'}. That fits {names(fit, by)}.", "compare")
        for f in [f for f in marks if f["mark"] == "scratched"]:
            p = f["about"]
            if not raise_fact(f, beats, quiet=True):
                continue
            self.trial_beat(beats, f["by"], f"Look at {self.nm(p)}'s hands. Fresh scratches. The victim had skin under their nails.", "compare")
            thorns, seen = self.thorn_alibi(p, ids)
            if p == killer and not thorns:
                self.trial_beat(beats, p, "Thorns. From the garden. That's all.", "deny")
                push(p, 0.5 if not seen else -0.5)                    # a story nobody can back up
            elif thorns:
                self.trial_beat(beats, p, "Thorns! I was tending the garden." + (" Ask anyone who saw me there." if seen else ""), "deny")
                push(p, -2.0 if seen else -0.8)
            else:
                self.trial_beat(beats, p, "That's old. It has nothing to do with this.", "deny")
                push(p, -0.5)

    def compare_looks(self, beats, looks, case, raise_fact):
        """Hair, fibres, a lost accessory and glimpses in the dark, held up against how everyone looks."""
        def names(ps, by):
            ns = [self.nm(p) for p in ps if p != by] + (["me"] if by in ps else [])
            return ", ".join(ns[:-1]) + (" and " if len(ns) > 1 else "") + ns[-1] if ns else "nobody here"
        clue = {c["kind"]: c for c in case.get("clues", []) if c.get("kind") in ("hair", "fibres")}
        for key in ("hair", "fibres", "glimpse"):
            for by in sorted({f["by"] for f in looks if f["look"] == key}):
                group = [f for f in looks if f["look"] == key and f["by"] == by]
                for f in group:
                    raise_fact(f, beats, quiet=True)
                fit = [f["about"] for f in group if f["fits"]]
                if key == "hair":
                    self.trial_beat(beats, by, f"{clue['hair']['text']} Whose hair is that? {names(fit, by)}.", "compare")
                elif key == "fibres":
                    self.trial_beat(beats, by, f"{clue['fibres']['text']} Who wears that? {names(fit, by)}.", "compare")
                else:
                    feat = next((g["feature"] for g in case.get("glimpses") or [] if g["by"] == by), "a shape")
                    self.trial_beat(beats, by, f"It was dark, but I saw a figure: {feat}. That fits {names(fit, by)}.", "compare")
        for f in [f for f in looks if f["look"] == "accessory"]:
            if raise_fact(f, beats, quiet=True):
                self.trial_beat(beats, f["by"], f"This was lying near the body. {f['text']}", "compare")

    def weapon_match(self, item, weapon):
        """How much being seen with `item` says about a death by `weapon`: the weapon itself counts, the same kind of weapon a little, anything else not at all."""
        if not item or not weapon:
            return 0.0
        if item == weapon:
            return 2.5
        does = lambda k: {"cut", "bludgeon"} & set(self.item_caps(k)["does"])
        return 0.6 if does(item) & does(weapon) else 0.0

    def weak_points(self, claims, ids, exposed):
        """[(speaker, holder, belief)]: claims that conflict with what someone else saw."""
        out = []
        for s, cl in claims.items():
            if not cl.get("r") or s in exposed:
                continue
            for h in ids:
                if h == s:
                    continue
                b = self.believed_at(h, s, cl["t"], slack=0.15)
                if b and b["src"] == "seen" and b["r"] != cl["r"]:
                    out.append((s, h, b))
        return out

    def corroborations(self, claims, ids):
        """[(speaker, holder)]: someone saw them where they say they were."""
        out = []
        for s, cl in claims.items():
            if not cl.get("r"):
                continue
            for h in ids:
                if h != s:
                    b = self.believed_at(h, s, cl["t"], slack=0.15)
                    if b and b["src"] == "seen" and b["r"] == cl["r"]:
                        out.append((s, h))
                        break
        return out

    # ------------------------------------------------------------------ who dares, and the liar's way out
    def willingness(self, holder, about, conf=0.9):
        """How likely `holder` is to say out loud what they know against `about` (0..1)."""
        w, s = self.world, self.s
        if holder == (s.get("case") or {}).get("killer"):
            return 0.9                                              # the culprit is happy to point at others
        a = w.agents[holder]
        p = 0.45 + 0.3 * (self.facet(holder, "courage") - 50) / 50 + 0.25 * conf
        aff = a["aff"].get(about, 0)
        p += 0.15 if aff < 0 else -0.06 * max(0, aff - 2)
        if about in self.allies_of(holder):
            p -= 0.25
        if any(x.get("helper") == holder for x in (s.get("accomplices") or {}).get(about, [])):
            p = 0.0                                                 # an accomplice never gives them away
        return max(0.0, min(0.95, p))

    def lie_planner(self, liar, case, ids, burnt):
        """A new story for the culprit: a room they were in that day, not the scene, that none of what they think the room knows contradicts.
        Returns the claim, or None (cornered)."""
        w = self.world
        t = self.case_time(case)
        seen_by_me = {b["s"] for b in self.beliefs(liar) if b["k"] == "at" and b["src"] == "seen" and b["t0"] - 0.5 <= t <= b.get("t1", b["t0"]) + 0.5}
        rooms = sorted({r for (d, h, r) in self.s.get("where_log", {}).get(liar, []) if d == case.get("day", self.day)} | {w.cast[liar].get("home")})
        for r in rooms:
            if not r or r == case.get("room") or r in burnt:
                continue
            # they think it is safe if nobody they saw at that time was in that room (they cannot know who saw them elsewhere)
            if any(self.believed_at(liar, o, t) and self.believed_at(liar, o, t)["r"] == r for o in seen_by_me if o in ids):
                continue
            return {"r": r, "t": t, "text": f"All right, I wasn't where I said. I was in the {w.room_name(r)}. That's the truth.", "lie": True}
        return None

    def objection_cry(self, cid):
        """What someone shouts when they catch a contradiction: their own signature cry (a cast field, or from their temperament), now and then another."""
        c = self.world.cast.get(cid, {})
        if c.get("objection") and self.rng.random() < 0.8:
            return c["objection"]
        if self.rng.random() < 0.3:
            return self.rng.choice(CRIES)
        f = self.facet
        if f(cid, "anger") >= 60:
            return "That's wrong!"
        if f(cid, "vanity") >= 60:
            return "Objection!"
        if f(cid, "courage") < 40:
            return "W-wait a second!"
        return CRIES[sum(map(ord, cid)) % len(CRIES)]

    def cornered_mode(self, cid):
        f = self.facet
        if f(cid, "anger") >= 65:
            return "lashing"
        if f(cid, "vanity") >= 60:
            return "indignant"
        if f(cid, "stress_vulnerability") >= 60:
            return "tearful"
        return "silent"

    # ------------------------------------------------------------------ voicing
    def voice_trial_lines(self, tick, beats, seg):
        """One voicing call per sequence: the model rewrites each beat in the speaker's voice; anything missing keeps the template line."""
        w = self.world
        if not beats:
            return []
        cards = "\n".join(f"- {p} = {self.nm(p)}. Looks: {self.looks_line(p, short=True)}. Speech: {w.cast[p]['speech'][:90]}" for p in sorted({b['speaker'] for b in beats if b['speaker'] in w.cast}))
        listing = "\n".join(f"{i}. {b['speaker']}: {b['text']}" for i, b in enumerate(beats))
        sysm = f"{self.bible()}\nYou voice lines at a class trial. The engine has decided what is said; you only put it in each speaker's own words. Reply with JSON only."
        user = (f"{TITLES.get(seg['kind'], 'TRIAL')}. Rewrite each numbered line in the speaker's voice: same facts, same accusation or answer, max 25 words, no new facts, "
                f"no camera footage unless the line already cites a recording of their own.\nSPEAKERS:\n{cards}\nLINES:\n{listing}\n"
                'Reply as JSON: {"lines": [{"i": <number>, "text": "..."}]}')
        try:
            res = self.llm.voice(sysm, user, {"beats": len(beats), "trial": True}) or {}
        except Exception as e:
            if getattr(e, "fatal", False):
                raise
            res = {}
        got = {}
        for ln in res.get("lines") or []:
            if isinstance(ln, dict) and isinstance(ln.get("i"), int) and 0 <= ln["i"] < len(beats) and str(ln.get("text", "")).strip():
                got[ln["i"]] = str(ln["text"]).strip()[:260]
        out = []
        for i, b in enumerate(beats):
            if b.get("move") == "cry":
                out.append({"speaker": b["speaker"], "kind": "say", "text": b["text"], "move": "cry"})      # a cry is never reworded
                continue
            text = self.clean_line(b["speaker"], b.get("kind", "say"), got.get(i, b["text"]))
            out.append({"speaker": b["speaker"], "kind": b.get("kind", "say"), "text": text or b["text"], "move": b.get("move")})
        return out

    def trial_beat(self, beats, speaker, text, move, kind="say"):
        beats.append({"speaker": speaker, "text": text, "move": move, "kind": kind})

    def publish_segment(self, tick, hour, kind, n, beats, meter, extra=None):
        w = self.world
        seg = {"kind": kind, "title": TITLES[kind], "n": n, "of": 6, **(extra or {})}
        seg["meter"] = {k: round(v, 1) for k, v in sorted(meter.items(), key=lambda kv: -kv[1]) if v > 0.05}
        seg["susp"] = dict(self.suspicion)
        seg["theory"] = self.theory
        lines = self.voice_trial_lines(tick, beats, seg)
        if lines:
            tick["talk"].append({"room": "voting_grounds", "lines": lines, "segment": seg})
            for cid in w.agents:
                for ln in lines[:8]:
                    who = "You" if cid == ln["speaker"] else self.nm(ln["speaker"])
                    w.remember(cid, f"{hour % 24:02d}:00 (trial) {who}: {ln['text'][:100]}")
        tick.setdefault("segments", []).append(seg)

    # ------------------------------------------------------------------ the trial itself
    def run_claim_trial(self, tick, hour, case):
        """Play the sequences and compute the votes. Returns the votes [{"voter", "target", "reason"}]."""
        w = self.world
        ids = sorted(w.agents)
        killer = case.get("killer")
        claims = self.trial_claims(case, ids)
        facts = self.trial_facts(case, ids)
        cred = {p: (0.75 if any(p in self.caught_liars(o) for o in ids if o != p) else 1.0) for p in ids}
        meter = {p: 0.0 for p in ids}
        raised, exposed, burnt, lies, spoken = set(), set(), {}, Counter(), set()
        tr = {"claims": claims, "raised": [], "lies": lies, "cred": cred}
        self.suspicion, self.theory = {}, None
        n = 0

        def push(about, amount, why=None):
            if about in meter:
                meter[about] = max(0.0, meter[about] + amount)

        def raise_fact(f, beats, quiet=False):
            key = (f["by"], f["about"], f["text"])
            if key in raised or f["about"] not in ids or f["by"] not in ids:
                return False
            if f["w"] > 0 and self.rng.random() > self.willingness(f["by"], f["about"]):
                return False
            raised.add(key)
            tr["raised"].append(f)
            if not quiet and f["text"] not in spoken:              # one clue naming several people is shown once
                spoken.add(f["text"])
                self.trial_beat(beats, f["by"], f["text"] if f["kind"] != "clue" else f"Look at this: {f['text']}", "evidence")
            push(f["about"], f["w"] * cred[f["by"]])
            return True

        def raise_sightings(pool, beats):
            """Each person says once who they saw near the scene, not once per name."""
            for by in sorted({f["by"] for f in pool}):
                named = [f["about"] for f in sorted(pool, key=lambda f: -f["w"]) if f["by"] == by and raise_fact(f, beats, quiet=True)]
                if named:
                    names = [self.nm(p) for p in named]
                    who = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
                    text = f"I saw {who} in the {w.room_name(case.get('room'))} around {int(self.case_time(case) % 24):02d}:00."
                    if text in spoken:
                        text = AGAIN[len(spoken) % len(AGAIN)].format(who=who)
                    spoken.add(text)
                    self.trial_beat(beats, by, text, "evidence")

        def challenge(s, h, b, beats):
            """`h` raises what they saw against `s`'s claim; `s` answers (a liar is exposed, then the lie planner)."""
            cl = claims[s]
            self.trial_beat(beats, h, self.objection_cry(h), "cry")
            self.trial_beat(beats, h, f"That's not true. I saw {self.nm(s)} in the {w.room_name(b['r'])} at that time, not the {w.room_name(cl['r'])}.", "objection")
            push(s, 2.0 * cred[h] * b["c"])
            raised.add((h, s, "contradiction"))
            if cl["lie"]:
                lies[s] += 1
                cred[s] *= 0.5
                push(s, 1.5)
                burnt.setdefault(s, set()).add(cl["r"])
                new = self.lie_planner(s, case, ids, burnt[s]) if s == killer else None
                if new and lies[s] < 3:
                    claims[s] = new
                    self.trial_beat(beats, s, new["text"], "new_story")
                else:
                    exposed.add(s)
                    mode = self.cornered_mode(s)
                    other = max((p for p in ids if p not in (s,)), key=lambda p: meter[p] if p != s else -1)
                    self.trial_beat(beats, s, CORNERED[mode].format(other=self.nm(other)), "cornered", "say" if mode != "silent" else "act")
            else:
                self.trial_beat(beats, s, f"You're mistaken. I was in the {w.room_name(cl['r'])}.", "deny")
            return True

        # 1. open debate: the alibis, the clues, the objections
        n += 1
        beats = []
        for p in ids:
            self.trial_beat(beats, p, claims[p]["text"], "alibi")
        for s, h in self.corroborations(claims, ids):
            if self.rng.random() < 0.7:
                self.trial_beat(beats, h, f"I can vouch for {self.nm(s)}: I saw them there.", "corroborate")
                push(s, -1.5 * cred[h])
        for f in sorted([f for f in facts if f["kind"] == "clue"], key=lambda f: -abs(f["w"])):
            raise_fact(f, beats)
        for s, h, b in self.weak_points(claims, ids, exposed):
            if (h, s, "contradiction") not in raised and self.rng.random() < self.willingness(h, s, b["c"]):
                challenge(s, h, b, beats)
        for f in sorted([f for f in facts if f["kind"] == "witness"], key=lambda f: -f["w"]):
            raise_fact(f, beats)
        raise_sightings([f for f in facts if f["kind"] == "near_scene"], beats)
        self.compare_marks(beats, [f for f in facts if f["kind"] == "mark"], case, ids, killer, raise_fact, push)
        self.compare_looks(beats, [f for f in facts if f["kind"] == "look"], case, raise_fact)
        self.update_trial_suspicion(ids, meter, facts, killer, case)
        self.publish_segment(tick, hour, "debate", n, beats, meter)

        # 2. the hot seat, the clash, the brainstorm, as the state of the room calls for them
        hot_done, clashed, brained, crossed, split_done = set(), False, False, set(), False
        while n < 5:
            if self.should_stop():
                raise self.StopExc()
            top = sorted(ids, key=lambda p: -meter[p])
            lead = top[0]
            n += 1
            beats = []
            if meter[lead] >= 3.0 and lead not in hot_done:
                hot_done.add(lead)
                self.trial_beat(beats, lead, "Fine. Ask me anything. I have nothing to hide.", "hotseat_open")
                pending = [f for f in facts if f["about"] == lead and (f["by"], f["about"], f["text"]) not in raised and f["w"] > 0 and f["text"] not in spoken]
                for f in sorted(pending, key=lambda f: -f["w"])[:3]:
                    said = len(beats)
                    if raise_fact(f, beats) and len(beats) > said:
                        self.trial_beat(beats, lead, "That proves nothing." if lead != killer or lead not in exposed else "...", "answer")
                for s, h, b in self.weak_points({lead: claims[lead]}, ids, exposed):
                    if (h, s, "contradiction") not in raised and self.rng.random() < min(0.95, self.willingness(h, s, b["c"]) + 0.15):
                        challenge(s, h, b, beats)
                friend = max((p for p in ids if p != lead), key=lambda p: w.agents[p]["aff"].get(lead, 0))
                if w.agents[friend]["aff"].get(lead, 0) >= 3 and friend != killer:
                    self.trial_beat(beats, friend, f"I know {self.nm(lead)}. They wouldn't do this.", "defend")
                    push(lead, -0.6)
                self.update_trial_suspicion(ids, meter, facts, killer, case)
                self.publish_segment(tick, hour, "hotseat", n, beats, meter, {"subject": lead})
                continue
            wit = max([f for f in tr["raised"] if f["about"] == lead and f["kind"] in ("near_scene", "witness") and f["by"] != lead],
                      key=lambda f: f["w"] * cred[f["by"]], default=None)
            if wit and lead not in crossed:
                crossed.add(lead)
                self.cross_examine(beats, lead, wit, cred, push, case, ids)
                self.update_trial_suspicion(ids, meter, facts, killer, case)
                self.publish_segment(tick, hour, "crossexam", n, beats, meter, {"subject": wit["by"]})
                continue
            picks = Counter(self.suspicion.values())
            if not split_done and len(picks) >= 2 and sorted(picks.values())[-2] >= 3:
                split_done = clashed = True
                (ta, _), (tb, _) = picks.most_common(2)
                sides = self.split_court(beats, ta, tb, facts, cred, push, ids)
                self.update_trial_suspicion(ids, meter, facts, killer, case)
                self.publish_segment(tick, hour, "split", n, beats, meter, {"sides": sides, "debaters": [ta, tb]})
                continue
            if not clashed and len(picks) >= 2:
                (ta, _), (tb, _) = picks.most_common(2)
                a = next((v for v, x in sorted(self.suspicion.items()) if x == ta and v != ta), None)
                b = next((v for v, x in sorted(self.suspicion.items()) if x == tb and v not in (tb, a)), None)
                if a and b:
                    clashed = True
                    fa = max([f for f in facts if f["about"] == ta and f["by"] == a] or [{"w": 0.5, "text": f"{self.nm(ta)} had the chance and the reason."}], key=lambda f: f["w"])
                    fb = max([f for f in facts if f["about"] == tb and f["by"] == b] or [{"w": 0.5, "text": f"{self.nm(tb)} had the chance and the reason."}], key=lambda f: f["w"])
                    self.trial_beat(beats, a, f"It was {self.nm(ta)}. {fa['text']}", "clash")
                    self.trial_beat(beats, b, f"No, it was {self.nm(tb)}. {fb['text']}", "clash")
                    sa, sb = fa["w"] * cred[a], fb["w"] * cred[b]
                    win, lose, wt, lt = (a, b, ta, tb) if sa >= sb else (b, a, tb, ta)
                    self.trial_beat(beats, lose, "...I can't answer that. Maybe you're right.", "concede")
                    push(wt, 1.0)
                    push(lt, -1.0)
                    cred[lose] *= 0.85
                    self.theory = f"{self.nm(wt)} did it"
                    self.update_trial_suspicion(ids, meter, facts, killer, case)
                    self.publish_segment(tick, hour, "duel", n, beats, meter, {"debaters": [a, b]})
                    continue
            if not brained and meter[lead] < 2.0:
                brained = True
                t = self.case_time(case)
                unvouched = [p for p in ids if p not in {s for s, _ in self.corroborations(claims, ids)}]
                speaker = max(ids, key=lambda p: self.facet(p, "curiosity"))
                self.trial_beat(beats, speaker, f"Let's think. Whoever did this was alone with {self.nm(case['victim'])} around {int(t % 24):02d}:00. "
                                f"Who can't prove where they were? {', '.join(self.nm(p) for p in unvouched[:4]) or 'Nobody?'}", "theory")
                for p in unvouched:
                    push(p, 0.7)
                self.theory = "whoever has no witness for the time of the death"
                self.update_trial_suspicion(ids, meter, facts, killer, case)
                self.publish_segment(tick, hour, "brainstorm", n, beats, meter)
                continue
            # an open round: anything left unsaid comes out
            left = [f for f in facts if (f["by"], f["about"], f["text"]) not in raised]
            got = False
            for f in sorted(left, key=lambda f: -abs(f["w"]))[:4]:
                got = raise_fact(f, beats) or got
            if not got:
                n -= 1
                break
            self.update_trial_suspicion(ids, meter, facts, killer, case)
            self.publish_segment(tick, hour, "debate", n, beats, meter)

        # 3. the climax (the accuser tells the whole story), closing arguments and the vote
        lead = max(ids, key=lambda p: (meter[p], p))
        if meter[lead] >= 4.0:
            beats = []
            steps = self.climax(beats, lead, tr, facts, cred, push, case, ids, exposed, lies)
            self.update_trial_suspicion(ids, meter, facts, killer, case)
            self.publish_segment(tick, hour, "climax", n + 1, beats, meter, {"subject": lead, "steps": steps})
            n += 1
        top2 = sorted(ids, key=lambda p: -meter[p])[:2]
        self.withhold_trial(tick, hour, top2)
        self.trial_betrayals(tick, hour, top2)
        beats = []
        for p in top2:
            self.trial_beat(beats, p, "Look at the evidence, not at me. Vote with your heads." if p != killer else "You're making a terrible mistake. The one who did this is sitting right there.", "plea")
        self.publish_segment(tick, hour, "closing", n + 1, beats, meter, {"debaters": top2})
        votes = self.compute_votes(ids, meter, facts, killer, case)
        self._trial_state = {"facts": facts, "raised": tr["raised"], "lies": lies, "meter": meter}
        tick["claim_trial"] = {"meter": {k: round(v, 2) for k, v in meter.items()}, "lies_proven": dict(lies), "cred": {k: round(v, 2) for k, v in cred.items()},
                               "raised": len(tr["raised"]), "exposed": sorted(exposed)}
        return votes

    # ------------------------------------------------------------------ the trial as a live practice on the map
    def begin_practice(self, tick):
        """A special scene runs on the live map: start the clock and the positions before anyone is sent there, so they walk in."""
        self.clock_start()
        self.sim_turn(tick)

    def walk_in(self, tick, ids):
        """Everyone sent to the scene walks there from where they were. Returns {cid: minute they arrive}."""
        out = {}
        for cid in ids:
            if cid in self.world.agents:
                out[cid] = float(self.sim_go(tick, cid, 0.0) or 0.0)
        return out

    def stage_trial_live(self, tick, arrivals):
        """Put every trial line on the clock after people have arrived (nobody speaks before they are there), then the side business:
        whispers between allies (overheard by whoever is close), and now and then someone slipping out for a moment."""
        sm = self.sim_turn(tick)
        room = "voting_grounds"
        groups = [g for g in tick.get("talk") or [] if g.get("segment") and g.get("room") == room]
        n = sum(len(g["lines"]) for g in groups)
        if not n:
            return
        t0 = min(40.0, max(list(arrivals.values()) or [0.0]) + 1.5)
        step = max(0.5, min(2.0, (sm.dur - 8 - t0) / (n + len(groups))))
        m = t0
        spoken = {}
        for g in groups:
            g["live"], g["m"] = True, round(m, 1)
            g.setdefault("ended", "trial")
            g.setdefault("joined", [])
            g.setdefault("left", [])
            g["members"] = sorted({l["speaker"] for l in g["lines"]})
            for ln in g["lines"]:
                m = max(m, arrivals.get(ln["speaker"], 0.0) + 0.3)
                ln["m"], ln["room"] = round(min(sm.dur - 1.0, m), 2), room
                spoken.setdefault(ln["speaker"], []).append(ln["m"])
                m += step * (0.5 if ln.get("move") == "cry" else 1.0)
            m += step
        self.trial_whispers(tick, t0, min(m, sm.dur - 4), spoken)
        self.trial_slip_out(tick, t0, min(m, sm.dur - 10), spoken)
        tick["practice"] = {"room": room, "t0": round(t0, 1), "end": round(min(m, sm.dur), 1), "arrive": {c: round(v, 1) for c, v in sorted(arrivals.items())}}

    def trial_whispers(self, tick, t0, t1, spoken):
        w = self.world
        room = "voting_grounds"
        ids = sorted(w.agents)
        pairs = []
        for a in ids:
            b = max((o for o in ids if o != a), key=lambda o: (w.agents[a]["aff"].get(o, 0), o), default=None)
            if b and w.agents[a]["aff"].get(b, 0) >= 3 and (b, a) not in pairs:
                pairs.append((a, b))
        self.rng.shuffle(pairs)
        for a, b in pairs[:2]:
            if t1 - t0 < 4:
                break
            x = round(t0 + self.rng.random() * (t1 - t0 - 2), 2)
            sus = self.suspicion.get(a)
            lines = [{"speaker": a, "kind": "say", "text": f"(whispering) It's {self.nm(sus)}, isn't it?" if sus else "(whispering) What do you think?", "m": x, "room": room, "move": "whisper"},
                     {"speaker": b, "kind": "say", "text": "(whispering) Not now. Later.", "m": round(x + 0.6, 2), "room": room, "move": "whisper"}]
            conv = {"members": [a, b], "room": room, "seen_by": set(), "wary": True}
            beats = [{"who": l["speaker"], "m": l["m"], "loud": "whisper", "room": room, "move": "confide"} for l in lines]
            self.overhear(tick, conv, beats, notice=False)
            for l, bt in zip(lines, beats):
                if bt.get("heard"):
                    l["heard"] = bt["heard"]
                    for o, lvl in bt["heard"].items():
                        if lvl == "full":
                            w.remember(o, f"At the trial you overheard {self.nm(l['speaker'])} whisper: {l['text'][12:]}")
            tick["talk"].append({"room": room, "lines": lines, "live": True, "m": x, "members": [a, b], "whisper": True, "ended": "whisper", "joined": [], "left": []})

    def trial_slip_out(self, tick, t0, t1, spoken):
        """The most rattled person who is not on the spot steps out for a few minutes and comes back."""
        w = self.world
        sm = self.sim_turn(tick)
        if t1 - t0 < 12 or self.rng.random() > 0.35:
            return None
        top = max(self.suspicion.values(), key=lambda x: list(self.suspicion.values()).count(x)) if self.suspicion else None
        for cid in sorted(w.agents, key=lambda c: -(self.mind(c)["stress"] if self.mind_on() else 0)):
            if cid == top or cid not in sm.tracks:
                continue
            x = round(t0 + self.rng.random() * (t1 - t0 - 10), 2)
            if any(x - 1 <= m <= x + 9 for m in spoken.get(cid, [])):
                continue
            exits = sorted(e["room"] for e in w.adjacent(cid, "voting_grounds") if e["ok"])
            if not exits:
                return None
            out = exits[0]
            sm.go_room(cid, out, x, salt=5, force=True)
            back = sm.go_room(cid, "voting_grounds", x + 5.0, salt=6, force=True)
            self.log_event(tick, {"type": "practice", "who": cid, "room": "voting_grounds", "vis": "viewer", "m": x, "text": f"{self.nm(cid)} slips out of the trial for a moment."})
            self.log_event(tick, {"type": "practice", "who": cid, "room": "voting_grounds", "vis": "viewer", "m": round(float(back or x + 6), 1), "text": f"{self.nm(cid)} comes back in."})
            return cid
        return None

    # ------------------------------------------------------------------ after the verdict
    def trial_report(self, tick, case, votes, accused, hour):
        """Truth against belief: what really happened, and for each person what they believed, how they voted, and what they knew but never said.
        Those who held a fact against the culprit, kept it to themselves and saw the vote go wrong remember it."""
        w = self.world
        st = self.__dict__.pop("_trial_state", None) or {}
        killer = case.get("killer")
        raised = {(f["by"], f["about"], f["text"]) for f in st.get("raised", [])}
        truth = (f"{self.nm(killer)} killed {self.nm(case['victim'])} in the {w.room_name(case['room'])} around {int(self.case_time(case) % 24):02d}:00"
                 + (f" ({case.get('method')})" if case.get("method") else "") + ".")
        rows = []
        for v in votes:
            p = v["voter"]
            held = [f for f in st.get("facts", []) if f["by"] == p and f["about"] == killer and f["w"] > 0]
            silent = [f for f in held if (f["by"], f["about"], f["text"]) not in raised]
            rows.append({"id": p, "voted": v["target"], "right": v["target"] == killer, "believed": self.suspicion.get(p), "held": len(held), "silent": len(silent),
                         "lied": int((st.get("lies") or {}).get(p, 0))})
            if silent and accused != killer and p in w.agents and p != killer:
                w.remember(p, f"You knew something against {self.nm(killer)} and never said it. The vote went wrong.")
                self.stat(tick, p, "sanity", -3, "kept quiet at the trial")
        return {"truth": truth, "rows": rows, "right": sum(r["right"] for r in rows), "of": len(rows)}

    # ------------------------------------------------------------------ the later sequences
    def cross_examine(self, beats, accused, wit, cred, push, case, ids):
        """The accused (or their friend) tests the witness against them: could they see, have they lied before, do they hate the accused?"""
        w = self.world
        h = wit["by"]
        self.trial_beat(beats, h, f"I'll say it again: {wit['text']}", "testimony")
        asker = accused
        weak = []
        b = self.believed_at(h, accused, self.case_time(case), slack=0.8)
        if b and b.get("c", 1) < 0.8:
            weak.append(("light", f"It was dark. How can you be sure it was me you saw?", 0.6))
        if any(h in self.caught_liars(o) for o in ids if o != h):
            weak.append(("liar", f"You've lied to people here before. Why should anyone believe you now?", 0.5))
        if w.agents[h]["aff"].get(accused, 0) <= -4:
            weak.append(("grudge", f"You've hated me from the start. Of course you'd say that.", 0.7))
        if not weak:
            self.trial_beat(beats, asker, "Where exactly were you standing? ...Fine.", "probe")
            self.trial_beat(beats, h, "Right there. I know what I saw.", "stands")
            push(accused, 1.0)                                          # the testimony survives the test
            return False
        kind, line, hit = weak[0]
        self.trial_beat(beats, asker, line, "crossexam")
        self.trial_beat(beats, h, {"light": "I... I think it was. It looked like them.", "liar": "That was different!", "grudge": "This isn't about that!"}[kind], "falter")
        cred[h] *= 0.8
        push(accused, -hit * 2)
        return True

    def split_court(self, beats, ta, tb, facts, cred, push, ids):
        """The room has split between two suspects: two sides argue in turn, and people can cross over."""
        sides = {ta: sorted(v for v, x in self.suspicion.items() if x == ta), tb: sorted(v for v, x in self.suspicion.items() if x == tb)}
        score = {ta: 0.0, tb: 0.0}
        for rnd in range(2):
            for t, other in ((ta, tb), (tb, ta)):
                team = [m for m in sides[t] if m != t]
                pool = [f for f in facts if f["about"] == t and f["by"] in team and f["w"] > 0]
                if not team:
                    continue
                f = sorted(pool, key=lambda f: -f["w"] * cred[f["by"]])[rnd] if len(pool) > rnd else None
                sp = f["by"] if f else team[rnd % len(team)]
                self.trial_beat(beats, sp, f"It's {self.nm(t)}. " + (f["text"] if f else f"Nobody can say where {self.nm(t)} really was."), "split")
                score[t] += (f["w"] * cred[f["by"]]) if f else 0.4
        win, lose = (ta, tb) if score[ta] >= score[tb] else (tb, ta)
        moved = [m for m in sides[lose] if m != lose][: max(0, int(abs(score[ta] - score[tb]) // 1.5))]
        for m in moved:
            self.trial_beat(beats, m, f"...No. I think they're right about {self.nm(win)}.", "switch")
            sides[lose].remove(m)
            sides[win].append(m)
        push(win, 1.0)
        push(lose, -0.8)
        return {k: v for k, v in sides.items()}

    def climax(self, beats, lead, tr, facts, cred, push, case, ids, exposed, lies):
        """The accuser tells the crime from start to end from the facts on the table; every step without a fact is a gap, and gaps weaken the case."""
        w = self.world
        accuser = max((p for p in ids if p != lead), key=lambda p: (sum(f["w"] for f in tr["raised"] if f["by"] == p and f["about"] == lead) * cred[p], p))
        raised = [f for f in tr["raised"] if f["about"] == lead and f["w"] > 0]
        t = self.case_time(case)
        pick = lambda kinds: next((f for f in raised if f["kind"] in kinds), None)
        steps = [
            ("opportunity", pick(("near_scene", "witness")), f"{self.nm(lead)} was near the {w.room_name(case['room'])} around {int(t % 24):02d}:00."),
            ("weapon", next((f for f in raised if f["kind"] in ("clue", "has") and ("knife" in f["text"].lower() or "weapon" in f["text"].lower() or "handprint" in f["text"].lower() or f["kind"] == "has")), None),
             f"They had the means: {(pick(('has',)) or {}).get('text', 'the weapon')}"),
            ("the deed", pick(("witness",)) or next((f for f in raised if f["kind"] == "mark" and f["mark"] == "scratched"), None) or (pick(("clue",)) if case.get("weapon") else None),
             f"They killed {self.nm(case['victim'])} there" + (", and the scratches on their hands are where the victim fought back." if any(f["kind"] == "mark" and f["mark"] == "scratched" for f in raised) else ".")),
            ("the cover-up", True if lies.get(lead) else None, f"Then {self.nm(lead)} lied about where they were, and we caught the lie."),
        ]
        self.trial_beat(beats, accuser, f"Let me tell you what happened, from the start.", "climax_open")
        out, gaps, interrupted = [], 0, False
        for name, fact, text in steps:
            if fact:
                self.trial_beat(beats, accuser, text, "climax_step")
                out.append({"step": name, "text": text, "gap": False})
            else:
                gaps += 1
                self.trial_beat(beats, accuser, f"And then... {name}: that part we don't know yet.", "climax_gap")
                out.append({"step": name, "text": f"{name}: unknown", "gap": True})
                if not interrupted:
                    interrupted = True
                    self.trial_beat(beats, lead, "You can't prove any of that!", "interrupt")
        push(lead, -0.5 * gaps)
        if not gaps:
            self.trial_beat(beats, accuser, f"That's how it happened. Isn't it, {self.nm(lead)}?", "climax_end")
            push(lead, 1.0)
        return out

    def personal_suspicion(self, voter, ids, meter, facts, killer, case):
        """How suspicious each candidate looks to `voter`: the public meter, what only they know, affinity and fear."""
        w = self.world
        a = w.agents[voter]
        sc = {}
        for c in ids:
            if c == voter:
                continue
            v = meter[c]
            v += sum(f["w"] for f in facts if f["by"] == voter and f["about"] == c)        # what they know themselves counts fully for them
            v -= 0.12 * a["aff"].get(c, 0)
            sc[c] = v
        return sc

    def update_trial_suspicion(self, ids, meter, facts, killer, case):
        """Who each person currently suspects (the room's picture; the clash and the vote read it)."""
        self.suspicion = {}
        for v in ids:
            sc = self.personal_suspicion(v, ids, meter, facts, killer, case)
            if v == killer and case.get("culprit_aware", True):
                sc = {c: x for c, x in sc.items()}                     # the culprit points wherever suspicion already leans
            best = max(sc, key=lambda c: (sc[c], c)) if sc else None
            if best and sc[best] > 0.4:
                self.suspicion[v] = best

    def compute_votes(self, ids, meter, facts, killer, case):
        """Each person votes for the one they find most suspicious, swayed by the lead of the people they trust."""
        w = self.world
        votes = []
        first = {}
        for v in ids:
            sc = self.personal_suspicion(v, ids, meter, facts, killer, case)
            if v == killer and case.get("culprit_aware", True):
                sc.pop(v, None)
                framed = case.get("framed")
                if framed in sc:
                    sc[framed] += 3.0
            first[v] = (sc, max(sc, key=lambda c: (sc[c], c)) if sc else None)
        for v in ids:
            sc, pick = first[v]
            if not sc:
                continue
            sway = Counter(first[o][1] for o in ids if o != v and w.agents[v]["aff"].get(o, 0) >= 4 and first[o][1] and first[o][1] != v)
            final = {c: x + 0.8 * sway.get(c, 0) for c, x in sc.items()}
            if any(x.get("helper") == v for x in (self.s.get("accomplices") or {}).get(killer, [])):
                final.pop(killer, None)                                # an accomplice never votes for the one they helped
            if self.rng.random() < self.slip_chance(v) * 0.3:
                target = self.rng.choice(sorted(final))
                reason = "(muddled, went with a gut feeling)"
            else:
                target = max(final, key=lambda c: (final[c], c))
                why = max([f for f in facts if f["about"] == target and f["w"] > 0], key=lambda f: f["w"], default=None)
                reason = (why["text"][:160] if why else f"{self.nm(target)} never accounted for where they were.")
            votes.append({"voter": v, "target": target, "reason": reason})
        return votes
