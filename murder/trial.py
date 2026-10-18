"""Investigation notebooks, interrogations and the class trial at the Voting Grounds.

The investigation is about collecting evidence and testimonies; the trial is a limited-time argument in which special sequences
can occur: the Hot Seat (suspicion falls heavily on one person), the Clash (two people with contradicting ideas argue
one-on-one while the others judge) and the Brainstorm (something baffling: people float theories and pick the most plausible).
There is no "nobody" vote: a death with a culprit always has someone guilty. Deaths with no culprit never reach a trial.
"""
from collections import Counter

from .llm import LLMError
from .world import clamp
from .data_world import ROOMS

TRIAL_ROOM = "voting_grounds"
MAX_SEGMENTS = 5            # the opening plus up to four more: time is limited
TITLES = {"debate": "OPEN DEBATE", "hotseat": "THE HOT SEAT", "duel": "THE CLASH", "brainstorm": "BRAINSTORM", "closing": "CLOSING ARGUMENTS"}


def _hh(h):
    return f"{h:02d}:00"


class TrialMixin:
    def trial_init(self):
        self.suspicion = {}
        self.theory = None

    def clean_line(self, sp, kind, tx):
        """Tidy model quirks: stray asterisks and an action line that starts with the speaker's own name."""
        tx = tx.strip().strip("*").strip()
        if kind == "say":
            tx = self.scrub_footage(sp, tx)                         # nobody cites camera footage they cannot have
        if kind == "act":
            nm = self.nm(sp)
            for pref in (nm, nm.lower()):
                if tx.startswith(pref + " ") or tx.startswith(pref + "*"):
                    tx = tx[len(pref):].lstrip("* ").strip()
                    break
            if len(tx) > 1 and tx[0].isupper() and not tx[1].isupper():
                tx = tx[0].lower() + tx[1:]
        return tx

    # ------------------------------------------------------------------ the evidence notebook
    def garble_text(self, text):
        names = [self.nm(c) for c in self.world.all_agents if c in self.world.cast]
        for n in names:
            if n in text:
                others = [x for x in names if x != n]
                return text.replace(n, self.rng.choice(others), 1) if others else text
        return text + " (you may have misread something)"

    def note_evidence(self, cid, kind, text, by=None):
        a = self.world.agents.get(cid)
        if not a:
            return
        if kind in ("clue", "testimony") and self.rng.random() < self.slip_chance(cid) * 0.4:
            text = self.garble_text(text)
        nb = a.setdefault("notebook", [])
        if any(e["text"] == text for e in nb):
            return
        nb.append({"kind": kind, "text": text, "by": by, "day": self.day})
        del nb[:-20]
        self.share_with_allies(cid, kind, text, by)

    def notebook_lines(self, cid):
        w, s = self.world, self.s
        case = s.get("case")
        if not case or not case.get("announced"):
            return []
        nb = w.agents[cid].get("notebook", [])
        out = []
        if nb:
            out.append("YOUR CASE NOTEBOOK (the evidence and testimonies you have gathered; accounts can be lies, memories can be wrong): "
                       + " | ".join(f"[{e['kind']}] {e['text'][:140]}" for e in nb[-(5 if self.lean else 10):]))
        others = [o for o in w.agents if o != cid]
        if others and sum(w.agents[cid]["aff"].get(o, 0) for o in others) / len(others) <= -2:
            out.append("You trust almost nobody here: when pressed by people you dislike you may refuse to answer, answer vaguely, or lie, and you doubt what they tell you.")
        out.append("INVESTIGATE: gather evidence by searching rooms (action 'investigate') and testimonies by questioning people (action 'interrogate' with a target and your question in 'idea'): "
                   "where they were, what they saw, who they saw leave or enter, what they carried. Compare accounts, look for contradictions and for who was unaccounted for. "
                   "The trial will be a limited-time argument, so go in with facts.")
        return out

    def apply_testimonies(self, tick, items, group, hour):
        w, s = self.world, self.s
        case = s.get("case")
        if not case or not case.get("announced"):
            return
        for it in (items or [])[:3]:
            if not isinstance(it, dict):
                continue
            by, claim = it.get("by"), str(it.get("claim") or "").strip()[:170]
            if by not in w.agents or by not in group or not claim:
                continue
            ts = case.setdefault("testimonies", [])
            if any(t["by"] == by and t["claim"] == claim for t in ts):
                continue
            ts.append({"by": by, "claim": claim, "day": self.day, "hour": hour})
            del ts[:-24]
            for o in group:
                if o in w.agents and o != by:
                    self.note_evidence(o, "testimony", f"{self.nm(by)} says: {claim}", by)

    def clear_notebooks(self):
        for a in self.world.agents.values():
            a.pop("notebook", None)

    # ------------------------------------------------------------------ realization
    def realize(self, tick, cid, hour):
        w, s = self.world, self.s
        case = s.get("case")
        if not case or case.get("culprit_aware", True) or cid != case["killer"] or cid not in w.agents:
            return
        case["culprit_aware"] = True
        name, vname = self.nm(cid), self.nm(case["victim"])
        w.remember(cid, f"{_hh(hour)} (private) It hits you with horror: it was YOU. Your own hands killed {vname}, and you did not know.")
        self.stat(tick, cid, "sanity", -12, "realized they killed")
        self.moment(cid, f"realized you killed {vname}")
        self.log_event(tick, {"type": "madness", "who": cid, "room": w.agents[cid]["room"], "vis": "viewer",
                              "text": f"{name} slowly realizes, with dawning horror, that it was their own hands that killed {vname}."}, actor=cid)

    def check_contradictions(self):
        """Lies can be caught: if a testimony places someone where the archives say they were not, whoever holds both notes the contradiction."""
        w, s = self.world, self.s
        case = s.get("case")
        led = case.get("ledger") if case else None
        if not led or not case.get("announced"):
            return
        where = {**led.get("cam", {}), **led.get("door", {})}
        for t in case.get("testimonies", []):
            if t.get("checked"):
                continue
            t["checked"] = True
            placed = where.get(t["by"])
            claim = t["claim"].lower()
            claimed = [rid for rid, r in ROOMS.items() if r[0].lower() in claim or rid.replace("_", " ") in claim]
            if not placed or not claimed or placed in claimed:
                continue
            msg = f"{self.nm(t['by'])} said they were in the {w.room_name(claimed[0])}, but the archives place them in the {w.room_name(placed)}."
            case.setdefault("contradictions", []).append({"by": t["by"], "text": msg})
            for cid in w.agents:
                has_t = any(t["claim"] in e["text"] for e in w.agents[cid].get("notebook", []))
                has_l = any(c["kind"] in ("ledger", "ledger_door") and cid in c["found_by"] for c in case["clues"])
                if has_t and has_l:
                    self.note_evidence(cid, "contradiction", msg)

    def investigation_upkeep(self, tick, hour):
        s = self.s
        self.check_contradictions()
        case = s.get("case")
        if not case or not case.get("announced") or case.get("culprit_aware", True) or case["killer"] not in self.world.agents:
            return
        hits = sum(1 for c in case["clues"] if c["found_by"] and c.get("kind") in ("bruises", "weapon", "trace", "ledger"))
        if self.rng.random() < min(0.25, 0.04 * hits):
            self.realize(tick, case["killer"], hour)

    # ------------------------------------------------------------------ trial prompts
    def suspicion_summary(self):
        w = self.world
        tally = Counter(self.suspicion.values())
        if not tally:
            return "nobody has settled on a suspect yet"
        return "; ".join(f"{self.nm(t)} ({n} suspect them: {', '.join(self.nm(v) for v, x in self.suspicion.items() if x == t)})" for t, n in tally.most_common())

    def trial_cards(self, case):
        w = self.world
        cards = []
        for cid, a in w.agents.items():
            c = w.cast[cid]
            role = ""
            if cid == case["killer"]:
                if case.get("culprit_aware", True):
                    role = (" YOU DELIVERED THE KILLING BLOW and you know it. Never reveal or confess: deflect, deny, shift the blame, use the evidence against others, "
                            "frame someone if you can; panic and get defensive if cornered, but never say it was you."
                            + (" You acted in self-defence against an attacker who is now dead; say so only if it helps, but TereVi's rule still condemns whoever struck the blow." if case.get("self_defense") else ""))
                else:
                    role = (" YOU DELIVERED THE KILLING BLOW WITHOUT KNOWING IT (you do not understand that you killed anyone). You honestly try to solve the case. "
                            "If the evidence points at you, you may slowly realise it (denial first, then horror).")
            if cid == case.get("framed"):
                role += (" YOU WERE FRAMED: you were knocked out or drugged, and woke beside the body with the weapon in your hand. You are innocent. Say how you came to be there, "
                         "use the signs that you were put out of action, and press whoever had a reason to hurt you. You may not know who did it.")
            elif case.get("framed") and cid == case["killer"]:
                role += f" You set {self.nm(case['framed'])} up beside the body; keep the suspicion on them without seeming eager."
            if cid == case.get("killer") and (sf := self.seen_of(cid, case)):
                role += " PEOPLE SAW YOU: " + "; ".join(sf) + ". Explain it away, shift the focus or use it to say you were only passing."
            nb = "; ".join(e["text"][:80] for e in a.get("notebook", [])[-3:])
            sus = self.nm(self.suspicion[cid]) if self.suspicion.get(cid) else "nobody yet"
            hazy = " Memory hazy and thoughts muddled." if self.slip_chance(cid) > 0.2 else ""
            cards.append(f"- {cid} = {c['name']}, {c['role']}. Voice: {c['speech'][:100]} Sanity {a['sanity']}, health {a['hp']}.{hazy} Suspects: {sus}. "
                         f"Notebook: {nb or 'little'}.{role}")
        return "\n".join(cards)

    def trial_prompt(self, case, kind, **kw):
        w = self.world
        victim = self.nm(case["victim"])
        head = (f"CLASS TRIAL at the Voting Grounds, with limited time. {victim} is dead. Someone among the living delivered the killing blow (whoever did it, planned or not): "
                "the cast must work out who. The culprit never confesses outright. A wrong accusation executes an innocent while the real culprit walks free.\n"
                f"EVIDENCE ON THE TABLE:\n{self.evidence_text(case)}\n"
                + (f"WHAT THE CAST SAW IN THE HOURS BEFORE (who was seen where; none of it proves anything alone):\n{dig}\n" if (dig := self.chronicle_digest(case)) else "") +
                f"WORKING THEORY: {self.theory or 'none yet'}\nSUSPICION SO FAR: {self.suspicion_summary()}\n"
                f"PARTICIPANTS:\n{self.trial_cards(case)}\n")
        if kind == "debate":
            body = ((self.neovi_hint_block(case) if kw.get("neovi") else "") + f"OPEN DEBATE: people present evidence, press each other's alibis and testimonies, catch contradictions and say who they suspect and why. "
                    "The culprit deflects. 8 to 12 lines, each max 25 words.")
        elif kind == "hotseat":
            s_ = self.nm(kw["subject"])
            body = (f"THE HOT SEAT: suspicion has fallen heavily on {s_}. {s_} stands alone in the middle and must explain themselves (where they were, the evidence against them) "
                    f"while the others attack and defend, citing the evidence. This continues only until the question is settled: set \"clarified\": true once the exchange has made it clear "
                    f"whether {s_} is guilty (a collapse, a contradiction, a lie exposed) or innocent (a solid alibi or explanation backed by evidence); otherwise false. "
                    "Once {s_}'s position has been properly tested it IS clear enough: do not drag it out. "
                    "10 to 14 lines, each max 25 words." + (" (This is a continuation: the argument is still not settled.)" if kw.get("round", 0) else ""))
        elif kind == "duel":
            a_, b_ = self.nm(kw["a"]), self.nm(kw["b"])
            body = (f"THE CLASH: {a_} argues that {self.nm(kw['ta'])} did it; {b_} argues that {self.nm(kw['tb'])} did it. Their ideas contradict each other, so they go head to head, "
                    "one on one, using the evidence; the others may interject briefly but mostly watch. 8 to 10 lines, each max 25 words. "
                    f"Then every OTHER participant decides who was more convincing, taking the evidence and the exchange into account: add \"jury\": {{\"<id>\": \"{kw['a']}\" or \"{kw['b']}\"}}.")
        elif kind == "closing":
            names = " and ".join(self.nm(x) for x in kw["subjects"])
            body = (f"CLOSING ARGUMENTS: the time is nearly up. The most suspected ({names}) each deliver a short, desperate or defiant final plea to the room: what the evidence really shows, who they think did it, "
                    "and why they should not be the one condemned. The others may interject one line each. 6 to 9 lines, each max 25 words. A culprit still never confesses.")
        else:
            body = (f"BRAINSTORM: something in the case is baffling: {kw.get('topic') or 'how it all fits together'}. People throw out ideas about what could have happened "
                    "(several competing theories, some wild), 8 to 10 lines. Then add \"theories\": [{\"by\": \"<id>\", \"text\": \"<theory, max 25 words>\"}] (2 to 4) and "
                    "\"picks\": {\"<id>\": <index of the theory that person finds most plausible>} for everyone.")
        schema = ('Reply as JSON: {"lines": [{"speaker": "<person id>", "kind": "say|act", "text": "..."}], '
                  '"suspicion": {"<person id>": "<id of who they now suspect, or empty>"}, "clarified": true|false, '
                  '"confused": "<one sentence about what is still baffling, or empty>", "realized": ["<id of anyone who just realised that THEY did it>"]'
                  + (', "jury": {}' if kind == "duel" else ', "theories": [], "picks": {}' if kind == "brainstorm" else "") + "}. "
                  "Speak only as the participants; no narrator. Mix a few action lines. Stay consistent with what each person actually knows.")
        return head + body + "\n" + schema

    def trial_segment(self, tick, hour, kind, n, **kw):
        w, s = self.world, self.s
        case = s["case"]
        ids = list(w.agents)
        neovi_ok = kind == "debate" and n == 1 and self.neovi_hint_ok()
        prompt = self.trial_prompt(case, kind, neovi=neovi_ok, **kw)
        speakers = ids + (["neovi"] if neovi_ok else [])
        ctx = {"people": [{"id": p, "name": self.nm(p), "human": True, "lines": w.cast[p].get("mock_lines", [])} for p in ids],
               "mode": "t_" + kind, "killer": case["killer"], "kw": kw}
        try:
            res = self.llm.converse(self.talk_system(), prompt, ctx)
        except LLMError as e:
            if e.fatal:
                raise
            tick["errors"].append(f"trial segment failed: {str(e)[:80]}")
            return False
        lines = []
        neovi_spoke = False
        for ln in (res.get("lines") or [])[:16]:
            sp, tx = ln.get("speaker"), str(ln.get("text", "")).strip()
            if sp == "neovi":
                if neovi_spoke or not neovi_ok:
                    continue
                neovi_spoke = True
            if sp in speakers and tx:
                k = "act" if ln.get("kind") == "act" else "say"
                tx = self.clean_line(sp, k, tx)
                if tx:
                    lines.append({"speaker": sp, "kind": k, "text": tx[:260]})
        seg = {"kind": kind, "title": TITLES[kind], "n": n, "of": MAX_SEGMENTS, "subject": kw.get("subject"), "debaters": ([kw.get("a"), kw.get("b")] if kind == "duel" else (kw.get("subjects") if kind == "closing" else None))}
        if lines:
            tick["talk"].append({"room": TRIAL_ROOM, "lines": lines, "segment": seg})
            for cid in ids:
                for ln in lines[:8]:
                    who = "You" if cid == ln["speaker"] else self.nm(ln["speaker"])
                    w.remember(cid, f"{_hh(hour)} (trial) {who}: {ln['text'][:100]}")
        tick.setdefault("segments", []).append(seg)
        for k, v in (res.get("suspicion") or {}).items():
            if k in ids:
                if v in ids and v != k:
                    self.suspicion[k] = v
                elif not v:
                    self.suspicion.pop(k, None)
        self.confused = str(res.get("confused") or "").strip()[:200]
        if kind == "duel":
            for j, side in (res.get("jury") or {}).items():
                if j in ids and j not in (kw["a"], kw["b"]):
                    if side == kw["a"]:
                        self.suspicion[j] = kw["ta"]
                    elif side == kw["b"]:
                        self.suspicion[j] = kw["tb"]
            self.suspicion[kw["a"]], self.suspicion[kw["b"]] = kw["ta"], kw["tb"]
        elif kind == "brainstorm":
            th = [t for t in (res.get("theories") or []) if isinstance(t, dict) and str(t.get("text", "")).strip()][:4]
            if th:
                picks = Counter(p for p in (res.get("picks") or {}).values() if isinstance(p, int) and 0 <= p < len(th))
                best = picks.most_common(1)[0][0] if picks else 0
                self.theory = str(th[best]["text"]).strip()[:240]
                tick["talk"].append({"room": TRIAL_ROOM, "segment": dict(seg, title="THEORY CHOSEN"), "lines": [
                    {"speaker": th[best].get("by") if th[best].get("by") in ids else ids[0], "kind": "say", "text": f"The theory most of us find plausible: {self.theory}"}]})
            self.confused = ""
        if case["killer"] in [x for x in (res.get("realized") or []) if isinstance(x, str)] and not case.get("culprit_aware", True):
            self.realize(tick, case["killer"], hour)
        seg["susp"] = dict(self.suspicion)
        seg["theory"] = self.theory
        return bool(res.get("clarified"))

    def next_segment(self, used, hot_done, duels, brain):
        ids = list(self.world.agents)
        tally = Counter(self.suspicion.values())
        total = max(1, len(self.suspicion))
        top, cnt = tally.most_common(1)[0] if tally else (None, 0)
        share = cnt / total
        if self.confused and not brain:
            return "brainstorm", {"topic": self.confused}
        if top and share >= 0.5 and cnt >= 3 and top not in hot_done:
            return "hotseat", {"subject": top}
        if duels < 2 and len(tally) >= 2:
            (t1, c1), (t2, c2) = tally.most_common(2)
            if c1 >= 2 and c2 >= 2:
                a = next((v for v, x in self.suspicion.items() if x == t1 and v != t1), None)
                b = next((v for v, x in self.suspicion.items() if x == t2 and v != t2 and v != a), None)
                if a and b:
                    return "duel", {"a": a, "b": b, "ta": t1, "tb": t2}
        if used < MAX_SEGMENTS and (share < 0.75 or top not in hot_done):
            return "debate", {}
        return None

    # ------------------------------------------------------------------ the trial
    def run_trial(self, hour):
        w, s = self.world, self.s
        case = s["case"]
        victim, killer = case["victim"], case["killer"]
        tick = self.new_tick(hour, phase="trial")
        tick["type"] = "trial"
        self.begin_practice(tick)                                    # the trial runs on the live map: people walk in (claimtrial.py)
        ids = list(w.agents.keys())
        opening = self.make_broadcast("trial_open", {"victim": victim})
        tick["broadcasts"].append({"speaker": "terevi", "kind": "trial", "text": opening})
        self.bonus_clue(tick, hour)
        for line in self.blackout_alibis(case):
            self.file_add(case, line)
        self.fetch_stragglers(tick, ids, TRIAL_ROOM, "the class trial")
        for cid in ids:
            a = w.agents[cid]
            if a.get("out"):
                a.pop("out", None)                                   # the trial is not held without them: TereVi has them revived and brought
                a["activity"] = "Groggy"
            start = a["room"]
            steps = w.path(cid, start, TRIAL_ROOM) if start != TRIAL_ROOM else []
            tick["moves"][cid] = {"from": start, "path": [start] + ([r for r, _, _ in steps] if steps else ([TRIAL_ROOM] if start != TRIAL_ROOM else [])), "to": TRIAL_ROOM}
            a["room"] = TRIAL_ROOM
            a["activity"] = "At the class trial"
            w.remember(cid, f"{_hh(hour)} The class trial began at the Voting Grounds.")
        self.neovi_attend(tick, TRIAL_ROOM)
        arrivals = self.walk_in(tick, ids)
        self.suspicion, self.theory, self.confused = {}, None, ""
        used, hot_done, duels, brain = 0, set(), 0, False
        claim_votes = self.run_claim_trial(tick, hour, case) if self.tune("claim_trial") else None      # the engine decides, the model voices (claimtrial.py)
        used = MAX_SEGMENTS if claim_votes is not None else used + 1
        if claim_votes is None:
            self.trial_segment(tick, hour, "debate", used)
        while used < MAX_SEGMENTS:
            if self.should_stop():
                raise self.StopExc()
            nxt = self.next_segment(used, hot_done, duels, brain)
            if not nxt:
                break
            kind, kw = nxt
            used += 1
            if kind == "hotseat":
                hot_done.add(kw["subject"])
                for rnd in range(2):
                    clar = self.trial_segment(tick, hour, "hotseat", used, round=rnd, **kw)
                    if clar:
                        break
                tally = Counter(self.suspicion.values())
                if kw["subject"] == killer and not case.get("culprit_aware", True) and tally.get(kw["subject"], 0) >= max(2, len(ids) // 2):
                    self.realize(tick, killer, hour)
            elif kind == "duel":
                duels += 1
                self.trial_segment(tick, hour, "duel", used, **kw)
            elif kind == "brainstorm":
                brain = True
                self.trial_segment(tick, hour, "brainstorm", used, **kw)
            else:
                self.trial_segment(tick, hour, "debate", used)
        top2 = [t_ for t_, _ in Counter(self.suspicion.values()).most_common(2)]
        if top2 and not self.should_stop() and claim_votes is None:
            self.withhold_trial(tick, hour, top2)
            self.trial_betrayals(tick, hour, top2)
            self.trial_segment(tick, hour, "closing", used, subjects=top2)
        debate = " / ".join(f"{self.nm(l['speaker'])}: {l['text']}" for g in tick["talk"] for l in g["lines"])[-1700:]
        evidence = self.evidence_text(case)

        def vote_prompt(cid):
            """A muddled voter's gut-feeling vote, or the prompt for a considered one (asked afterwards, in parallel)."""
            a = w.agents[cid]
            cands = ", ".join(f"{k}={self.nm(k)}" for k in ids if k != cid)
            mem = a["memory"]
            if cid == killer and case.get("culprit_aware", True):
                killer_note = " YOU DELIVERED THE KILLING BLOW: steer the vote away from yourself and never reveal it."
            elif cid == killer:
                killer_note = " You do not know that you killed anyone; vote for whoever you honestly think did it."
            else:
                killer_note = ""
            hazy = " Your memory is hazy and your thinking is muddled; you may mix up details." if self.slip_chance(cid) > 0.2 else ""
            nb = " | ".join(e["text"][:100] for e in a.get("notebook", [])[-8:])
            user = (f"CLASS TRIAL VOTE. {self.nm(victim)} is dead and whoever delivered the killing blow (planned or not) is one of the people present. Candidates: {cands}.\n"
                    f"EVIDENCE ON THE TABLE:\n{evidence}\nYour notebook: {nb or 'little'}\nWorking theory: {self.theory or 'none'}\n"
                    f"What you remember: {' | '.join(mem['recent'][-12:]) or 'little'}\nThe arguments just now: {debate}\n"
                    f"You currently suspect: {self.nm(self.suspicion[cid]) if self.suspicion.get(cid) else 'nobody in particular'}.{killer_note}{hazy}\n"
                    "Remember: if you accuse an innocent, THEY are executed and the real culprit walks free. You must vote for exactly one candidate.\n"
                    'Reply as JSON: {"vote": "<person id>", "reason": "<max 25 words, in your voice>"}')
            ctx = {"voter": cid, "candidates": [k for k in ids if k != cid], "killer": killer}
            if self.rng.random() < self.slip_chance(cid) * 0.3:
                return {"voter": cid, "target": self.rng.choice(ctx["candidates"]), "reason": "(muddled, went with a gut feeling)"}, None
            return None, (self.system_prompt(cid), user, ctx)

        if claim_votes is not None:
            self.stage_trial_live(tick, arrivals)
        prepared = {cid: vote_prompt(cid) for cid in ids} if claim_votes is None else {}
        answers = self.ask_parallel([(cid, lambda q=q: self.llm.vote(*q)) for cid, (done, q) in prepared.items() if q]) if prepared else {}
        votes = list(claim_votes or [])
        for cid in (ids if claim_votes is None else []):
            done, q = prepared[cid]
            if done:
                votes.append(done)
                continue
            r, err = answers[cid]
            v = r.get("vote") if isinstance(r, dict) else None
            if err is None and v in q[2]["candidates"]:
                votes.append({"voter": cid, "target": v, "reason": str(r.get("reason", ""))[:200]})
            else:
                votes.append({"voter": cid, "target": self.rng.choice(q[2]["candidates"]), "reason": "(abstained into a random guess)"})
        for v in votes:
            self.betrayal(tick, v["voter"], v["target"], "voted against")
        tally = Counter(v["target"] for v in votes)
        for v in votes:
            self.tally(v["voter"], "votes_right" if v["target"] == killer else "votes_wrong")
        top = tally.most_common()
        accused = top[0][0] if top and (len(top) == 1 or top[0][1] > top[1][1]) else None
        found = accused is not None and accused == killer
        wrongful = accused is not None and accused != killer
        tick["trial"] = {"victim": victim, "killer": killer, "votes": votes, "tally": dict(tally), "accused": accused, "found": found,
                         "wrongful": wrongful, "kind": case["kind"], "segments": tick.get("segments", []), "aware": case.get("culprit_aware", True)}
        if tick.get("claim_trial"):
            tick["trial"]["report"] = self.trial_report(tick, case, votes, accused, hour)      # truth against belief (claimtrial.py)
        self.trial_farewells(tick, hour, case, votes, accused, found, wrongful)       # last words before they go (departures.py)
        kname = self.nm(killer)
        gone = [victim] + list(case.get("extra_victims", []))
        instig = case.get("instigator")
        manip = f" (manipulated by {self.nm(instig)}, who walks free)" if instig and instig in w.all_agents else ""
        shock = 4
        if found:
            scene = self.make_broadcast("execution", {"neovi": self.neovi_enforce(tick, killer, hour), "victim": killer, "reason": "verdict", "cause": case["method"], "murdered": victim, "case_kind": case["kind"]})
            tick["execution"] = {"id": killer, "scene": scene, "reason": "verdict"}
            w.end_agent(killer, "executed", "executed after the trial")
            gone.append(killer)
            result = f"{kname} was found guilty and executed{manip}."
            self.mourn(tick, killer, "executed after the trial", hour, weight=0.5)
        elif wrongful:
            scene = self.make_broadcast("execution", {"neovi": self.neovi_enforce(tick, accused, hour), "victim": accused, "reason": "wrongful", "murdered": victim, "killer": killer})
            tick["execution"] = {"id": accused, "scene": scene, "reason": "wrongful"}
            w.end_agent(accused, "executed", "wrongly executed")
            self.tally(accused, "wrongly_accused")
            gone.append(accused)
            text = self.make_broadcast("escape", {"victim": killer, "murdered": victim, "accused": accused})
            tick["escape"] = {"id": killer, "text": text}
            w.end_agent(killer, "escaped", "escaped the island")
            self.escapee_free(tick, killer, case)
            gone.append(killer)
            result = f"The cast voted wrongly: innocent {self.nm(accused)} was executed and {kname}, the real culprit, escapes the island{manip}."
            shock = 8
            self.mourn(tick, accused, "wrongly executed", hour, weight=1.0)
            for v in votes:
                if v["target"] == accused:
                    for cid, a in w.agents.items():
                        if cid != v["voter"] and a["aff"].get(accused, 0) >= 5 and v["voter"] in a["aff"]:
                            self.adjust_any_aff(cid, v["voter"], -3)
                            self.add_tie(cid, v["voter"], "wronged", f"voted to send {self.nm(accused)} to their death, and {self.nm(accused)} was innocent", 0)
                    self.moment(v["voter"], f"voted to execute {self.nm(accused)}, an innocent")
        else:
            text = self.make_broadcast("escape", {"victim": killer, "murdered": victim, "accused": None})
            tick["escape"] = {"id": killer, "text": text}
            w.end_agent(killer, "escaped", "escaped the island")
            self.escapee_free(tick, killer, case)
            gone.append(killer)
            result = f"The cast could not agree. {kname}, the culprit, escapes the island{manip}."
            shock = 5
        if instig and (instig in w.agents) and killer:
            for cid in w.agents:
                w.remember(cid, f"{_hh(hour)} It came out that {self.nm(instig)} had manipulated {kname} into it.")
                if cid != instig:
                    self.adjust_any_aff(cid, instig, -3)
            self.stat(tick, instig, "sanity", -4, "exposed as the manipulator")
            self.moment(instig, f"was exposed for manipulating {kname}")
            result += f" It came out that {self.nm(instig)} pulled the strings."
        result = self.expose_accomplices(tick, case, result, hour)
        tick["events"].append({"type": "system_notable", "who": killer, "room": TRIAL_ROOM, "vis": "public", "text": result})
        self.day_notable.append(result)
        self.saga(result)
        for k in gone:
            s["vacancies"].append({"gender": w.cast[k]["gender"], "reason": f"{w.cast[k]['name']} left the show"})
        for cid in list(w.agents.keys()):
            w.remember(cid, f"{_hh(hour)} Trial result: {result}")
            w.agents[cid]["sanity"] = clamp(w.agents[cid]["sanity"] - shock)
            if any(min(w.agents[cid]["aff"].get(o, 0), w.agents[o]["aff"].get(cid, 0)) >= 4 for o in w.agents if o != cid):
                self.special_boost(tick, cid, 3, "relief of not being alone", "comfort")
            lost = w.agents[cid]["memory"].setdefault("lost", [])
            if killer in gone and not found and not any(x["id"] == killer for x in lost):
                lost.append({"id": killer, "name": kname, "day": self.day, "how": "escaped the island", "close": "the one who got away"})
        s.setdefault("vote_log", []).append({"accused": accused, "voters": [v["voter"] for v in votes if v["target"] == accused], "wrongful": bool(wrongful), "day": self.day})
        del s["vote_log"][:-8]
        self.withhold_aftermath(tick, hour, wrongful)
        self.clear_notebooks()
        s["case"] = None
        s["incitements"] = []
        self.begin_aftermath(tick, hour)
        self.after_trial_twist(tick)
        self.after_trial_count(tick)
        return tick
