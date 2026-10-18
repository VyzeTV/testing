"""The claim-based trial: a contest of claims against beliefs, decided by the engine, voiced by the model.

Everyone states a claim (where they were when it happened: the truth, or for the culprit a lie). The engine checks every claim against every
participant's beliefs: a claim that conflicts with something another participant saw is a WEAK POINT, and that fact is the truth bullet. Whether
the holder dares to raise it is a WILLINGNESS roll (courage, how they feel about the speaker, how sure they are, whether they are protecting
someone). A proven lie halves the liar's CREDIBILITY. The culprit answers a challenge with the LIE PLANNER: a new story that fits what they think
the room knows; when none fits they are CORNERED (indignant, tearful, silent or lashing out, by temperament) and never confess.

Facts on the table move a public SUSPICION METER per suspect: a contradiction, a clue that names someone (prints on the weapon, stained clothes, a
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

TITLES = {"debate": "OPEN DEBATE", "hotseat": "THE HOT SEAT", "duel": "THE CLASH", "brainstorm": "BRAINSTORM", "closing": "CLOSING ARGUMENTS"}
CLUE_WEIGHT = {"weapon": 2.5, "stained": 2.5, "clothes": 2.0, "planted": 2.0, "framed_unconscious": 3.0, "decoy": 1.0, "ledger": 0.6, "drag_marks": 1.0, "staging": 1.0}
CORNERED = {"indignant": "How dare you. I have answered every question and you still want blood.", "tearful": "Please, I'm telling you, I didn't, I couldn't...",
            "silent": "...", "lashing": "Why is nobody looking at {other}? They had every reason!"}


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
            if kind == "weapon" and "Clear fingerprints" in c.get("text", ""):
                wt = 4.0
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
                    facts.append({"by": h, "about": b["s"], "kind": "has", "w": 1.0, "text": b.get("n", "")[:160], "true": b.get("true", True)})
                elif b["k"] == "lied" and b["s"] in ids:
                    facts.append({"by": h, "about": b["s"], "kind": "lied_before", "w": 1.5, "text": f"{self.nm(b['s'])} has lied to me before: {b.get('n', '')[:120]}", "true": b.get("true", True)})
        for wit in case.get("witnesses") or []:
            if wit in ids and case.get("killer") in ids and wit != case["killer"]:
                facts.append({"by": wit, "about": case["killer"], "kind": "witness", "w": 6.0, "text": f"I saw it happen. It was {self.nm(case['killer'])}.", "true": True})
        return facts

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
        cards = "\n".join(f"- {p} = {self.nm(p)}. Speech: {w.cast[p]['speech'][:90]}" for p in sorted({b['speaker'] for b in beats if b['speaker'] in w.cast}))
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
        raised, exposed, burnt, lies = set(), set(), {}, Counter()
        tr = {"claims": claims, "raised": [], "lies": lies, "cred": cred}
        self.suspicion, self.theory = {}, None
        n = 0

        def push(about, amount, why=None):
            if about in meter:
                meter[about] = max(0.0, meter[about] + amount)

        def raise_fact(f, beats):
            key = (f["by"], f["about"], f["text"])
            if key in raised or f["about"] not in ids or f["by"] not in ids:
                return False
            if f["w"] > 0 and self.rng.random() > self.willingness(f["by"], f["about"]):
                return False
            raised.add(key)
            tr["raised"].append(f)
            self.trial_beat(beats, f["by"], f["text"] if f["kind"] != "clue" else f"Look at this: {f['text']}", "evidence")
            push(f["about"], f["w"] * cred[f["by"]])
            return True

        def challenge(s, h, b, beats):
            """`h` raises what they saw against `s`'s claim; `s` answers (a liar is exposed, then the lie planner)."""
            cl = claims[s]
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
        for f in sorted([f for f in facts if f["kind"] in ("near_scene", "witness")], key=lambda f: -f["w"]):
            raise_fact(f, beats)
        self.update_trial_suspicion(ids, meter, facts, killer, case)
        self.publish_segment(tick, hour, "debate", n, beats, meter)

        # 2. the hot seat, the clash, the brainstorm, as the state of the room calls for them
        hot_done, clashed, brained = set(), False, False
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
                pending = [f for f in facts if f["about"] == lead and (f["by"], f["about"], f["text"]) not in raised and f["w"] > 0]
                for f in sorted(pending, key=lambda f: -f["w"])[:3]:
                    if raise_fact(f, beats):
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
            picks = Counter(self.suspicion.values())
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

        # 3. closing arguments and the vote
        top2 = sorted(ids, key=lambda p: -meter[p])[:2]
        self.withhold_trial(tick, hour, top2)
        self.trial_betrayals(tick, hour, top2)
        beats = []
        for p in top2:
            self.trial_beat(beats, p, "Look at the evidence, not at me. Vote with your heads." if p != killer else "You're making a terrible mistake. The one who did this is sitting right there.", "plea")
        self.publish_segment(tick, hour, "closing", n + 1, beats, meter, {"debaters": top2})
        votes = self.compute_votes(ids, meter, facts, killer, case)
        tick["claim_trial"] = {"meter": {k: round(v, 2) for k, v in meter.items()}, "lies_proven": dict(lies), "cred": {k: round(v, 2) for k, v in cred.items()},
                               "raised": len(tr["raised"]), "exposed": sorted(exposed)}
        return votes

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
