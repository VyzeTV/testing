"""The model as a proposer: now and then the model suggests a murder plan or a social move, and the engine checks it before using it.

When: a plot that has stalled (stalking or striking for several turns with no opening), a character in crisis (sanity under 20, no plot),
or a GM request (Director panel, "Propose"). Input: the character's beliefs, relationships, goal, and what they know of the world (rooms
with a drop, water, where useful items lie, what they carry). Output: a plan in the planner's own format (a scheme kind, the room, the item,
when, a cover story, and steps) or a single social move toward one person. Check: every part must map to something the engine can do: the
scheme kind exists, the room exists and can be reached, a push needs a real drop, a drowning needs water, an item must exist in their hands
or in a room, a sleeping target must be in their own bedroom, a plan that waits for the target somewhere (alone, a push, a drowning) needs
a place the plotter believes the target goes to (as the engine's own planner does), and each step is a known verb on a real object.
Anything impossible rejects the whole proposal and the engine's own choice stands. Budget: the `proposer_calls` dial caps calls per day (0 = off). The mock backend selects
from checked offers; forced invalid proposals belong in regression tests. ProposerMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS
from .planner import COMBOS, ROPES

SCHEMES = ("asleep", "alone", "height", "drown", "lure", "trap", "hang", "bath", "shock", "poison")
STEP_VERBS = ("go", "fetch", "wait", "watch", "lure", "rig", "strike", "hide", "clean", "alibi")
WATER = ("pool", "bathroom", "beach", "water_tower")
SOCIAL = ("comfort", "confide", "flirt", "gift", "warn", "reveal", "accuse", "confront", "pact", "recruit", "probe", "gossip", "threaten", "putdown")


class ProposerMixin:
    def proposer_budget(self):
        cap = int(self.tune("proposer_calls"))
        return cap - int(self.__dict__.get("_proposed_today", 0))

    def proposer_tick(self, tick, hour):
        """After a turn: one proposal at most, for a GM request first, then a stalled plot, then a crisis."""
        w, s = self.world, self.s
        if not self.revealed or s.get("over") or self.proposer_budget() <= 0:
            return None
        req = [r for r in s.get("propose_requests", []) if r.get("who") in w.agents]
        s["propose_requests"] = []
        if req:
            cid = req[0]["who"]
            return self.propose_plan(tick, cid) if cid in (s.get("plots") or {}) else self.propose_move(tick, cid)
        for cid, p in sorted((s.get("plots") or {}).items()):
            if cid in w.agents and p.get("target") in w.agents and not p.get("proposed") and (
                    (p.get("stage") == "striking" and p.get("stage_ticks", 0) >= 4) or (p.get("stage") == "stalking" and p.get("stage_ticks", 0) >= 6)):
                return self.propose_plan(tick, cid)
        for cid in sorted(w.agents):
            a = w.agents[cid]
            if a["sanity"] < 20 and cid not in (s.get("plots") or {}) and a.get("_proposed_day") != self.day:
                a["_proposed_day"] = self.day
                return self.propose_move(tick, cid)
        return None

    def world_offers(self, cid):
        """What this character knows of the world that a plan could use."""
        w, s = self.world, self.s
        a = w.agents[cid]
        drops = sorted(r for r in ROOMS if self.drop_edges(r))[:8]
        useful = lambda k: k in ROPES or bool(set(w.item_spec(k).get("tags", [])) & {"weapon", "poison", "drug"})
        items = sorted({k for its in s["room_items"].values() for k, q in its.items() if q > 0 and useful(k)})[:14]
        return {"drops": drops, "water": list(WATER), "items": items, "carrying": sorted(k for k, q in a["inv"].items() if q > 0)[:10]}

    def seen_target_in(self, cid, t):
        return sorted({b["r"] for b in self.beliefs(cid) if b["k"] == "at" and b["s"] == t})

    # ------------------------------------------------------------------ a murder plan
    def propose_plan(self, tick, cid):
        w, s = self.world, self.s
        p = s["plots"][cid]
        t = p["target"]
        self._proposed_today = self.__dict__.get("_proposed_today", 0) + 1
        p["proposed"] = True
        offers = self.world_offers(cid)
        offers["seen"] = self.seen_target_in(cid, t)
        beliefs = "; ".join(b.get("n") or f"{self.nm(b['s'])} in the {w.room_name(b['r'])}" for b in self.beliefs(cid)[-8:] if b.get("s") == t or b["k"] != "at")[:600]
        sysm = f"{self.bible()}\nYou propose how a character carries out a murder plan, in the game's own plan format. The engine checks every part; reply with JSON only."
        user = (f"{self.nm(cid)} wants {self.nm(t)} dead ({p.get('reason', '')}). The current plan has stalled: {(p.get('scheme') or {}).get('why', 'no plan')}.\n"
                f"Target's bedroom: {w.cast[t]['home']}. What {self.nm(cid)} believes: {beliefs or 'little'}.\n"
                f"Where {self.nm(cid)} has seen {self.nm(t)}: {', '.join(offers['seen']) or 'nowhere yet'} (alone, height and drown must use one of these). "
                f"Rooms with a drop: {', '.join(offers['drops'])}. Water: {', '.join(offers['water'])}. Useful items lying about: {', '.join(offers['items']) or 'none known'}. "
                f"Carrying: {', '.join(offers['carrying']) or 'nothing'}.\n"
                f"Schemes: {', '.join(SCHEMES)}. Step verbs: {', '.join(STEP_VERBS)}. Room and item ids only.\n"
                'Reply as JSON: {"scheme": "<scheme>", "room": "<room id>", "item": "<item id or empty>", "when": "day|night|any", "cover": "<their story>", '
                '"steps": [{"do": "<verb>", "room": "<room id or empty>", "item": "<item id or empty>"}], "reason": "<private first-person motive, max 25 words>"}. '
                + self.commitments.context(cid) + " " + self.emotions.context(cid) + " " + self.decisions.context(cid))
        try:
            ctx = {"kind": "plan", "cid": cid, "target": t, "offers": offers, "home": w.cast[t]["home"]}
            if self.llm.mock:
                from .mock_policy import actor_context
                ctx["actor"] = actor_context(self, cid)
                candidates = [{"scheme": "asleep", "room": w.cast[t]["home"], "when": "night", "steps": [{"do": "wait"}]}]
                for room in offers["seen"]:
                    for kind in ("alone", "height", "drown"):
                        candidates.append({"scheme": kind, "room": room, "when": "any", "steps": [{"do": "watch", "room": room}]})
                ctx["plans"] = [c for c in candidates if self.check_plan(cid, t, c)[0]]
            r = self.llm.propose(sysm, user, ctx) or {}
        except Exception as e:  # noqa: BLE001
            if getattr(e, "fatal", False):
                raise
            r = {}
        ok, why, sc = self.check_plan(cid, t, r)
        self.proposer_log(tick, cid, "plan", ok, why if not ok else sc["why"])
        if ok:
            self.revise_scheme(tick, cid, p, sc, "the previous plan stalled; a checked proposal offers " + sc["why"])
            if r.get("cover"):
                p["cover"] = str(r["cover"])[:120]
            self.plan_note(p, "changed plans: " + sc["why"])
        if isinstance(r, dict):
            request = dict(action='propose_plan', target=t, target_room=r.get('room') or '')
            rec = self.decisions.record(cid, tick['hour'], r, request)
            rec.update(kind='proposal', status='proposal accepted' if ok else 'rejected')
            if not ok:
                rec['change'] = why
        return ok

    def check_plan(self, cid, t, r):
        """(ok, reason, scheme) for a proposed plan."""
        w, s = self.world, self.s
        if not isinstance(r, dict) or r.get("scheme") not in SCHEMES:
            return False, "not a known scheme", None
        kind, room, item = r["scheme"], r.get("room") or None, r.get("item") or None
        if room is not None and room not in ROOMS:
            return False, f"no such room ({room})", None
        if room and w.path(cid, w.agents[cid]["room"], room) is None and room != w.agents[cid]["room"]:
            return False, f"cannot reach the {room}", None
        exists = lambda k: k in w.agents[cid]["inv"] or any(its.get(k, 0) > 0 for its in s["room_items"].values())
        if item and (not w.item_spec(item) or not exists(item)):
            return False, f"no {item} to be had", None
        if kind == "height" and not (room and self.drop_edges(room)):
            return False, "no drop to push anyone from there", None
        if kind == "drown" and room not in WATER:
            return False, "no water there", None
        if kind == "asleep" and room != w.cast[t]["home"]:
            return False, "the target does not sleep there", None
        if kind == "poison" and not (item and set(w.item_spec(item).get("tags", [])) & {"poison", "drug"}):
            return False, "no poison", None
        if kind in COMBOS and not any(exists(k) for k in COMBOS[kind][0]):
            return False, f"nothing to {kind} with", None
        from .electric import ELECTRIC
        if kind == "shock" and not any(exists(k) for k in ELECTRIC):
            return False, "nothing live to drop into a bath", None
        if kind in ("alone", "trap") and not room:
            return False, "no place given", None
        if kind in ("alone", "height", "drown") and room not in self.seen_target_in(cid, t):
            return False, f"they have never seen {self.nm(t)} in the {w.room_name(room)}", None
        for st in r.get("steps") or []:
            if not isinstance(st, dict) or st.get("do") not in STEP_VERBS:
                return False, "a step the engine cannot do", None
            if st.get("room") and st["room"] not in ROOMS or st.get("item") and not w.item_spec(st["item"]):
                return False, "a step about something that does not exist", None
        why = {"asleep": f"{self.nm(t)} asleep in their room", "alone": f"catch {self.nm(t)} alone in the {w.room_name(room) if room else '?'}",
               "height": f"push {self.nm(t)} from the {w.room_name(room)}", "drown": f"drown {self.nm(t)} in the {w.room_name(room)}",
               "lure": f"lure {self.nm(t)} somewhere quiet at night", "trap": f"rig a trap in the {w.room_name(room)}",
               "hang": f"hang {self.nm(t)} and make it look like suicide", "bath": f"drug {self.nm(t)} and drown them in the bath",
               "shock": f"drop something live into {self.nm(t)}'s bath", "poison": f"poison {self.nm(t)} with the {w.item_name(item)}"}[kind]
        sc = {"kind": kind, "room": room, "when": r.get("when") if r.get("when") in ("day", "night", "any") else "any", "why": why + " (the model's idea)",
              "proposed": True}
        if kind == "poison":
            sc["item"] = item
            sc["needs"] = [item]
        if kind == "trap":
            rig = self.rig_options(cid)
            if not rig:
                return False, "nothing to rig a trap with", None
            sc["rig"] = rig[0]
        if kind in COMBOS:
            sc.update(needs=list(COMBOS[kind][0]), staged=COMBOS[kind][1])
        if kind == "shock":
            sc.update(room="bathroom", needs=list(ELECTRIC), staged="accident")
        return True, "", sc

    # ------------------------------------------------------------------ a social move
    def propose_move(self, tick, cid):
        w = self.world
        a = w.agents[cid]
        self._proposed_today = self.__dict__.get("_proposed_today", 0) + 1
        others = sorted(o for o in w.agents if o != cid)
        if not others:
            return False
        feel = ", ".join(f"{o}={self.nm(o)} {a['aff'].get(o, 0):+d}" for o in others)
        sysm = f"{self.bible()}\nYou propose one social move a character makes tomorrow. The engine checks it; reply with JSON only."
        user = (f"{self.nm(cid)} (sanity {a['sanity']}, {a['drive']['id']}). Feelings: {feel}. Moves: {', '.join(SOCIAL)}.\n"
                'Reply as JSON: {"move": "<move>", "to": "<person id>", "about": "<person id or empty>", "reason": "<private first-person motive, max 25 words>"}. '
                + self.commitments.context(cid) + " " + self.emotions.context(cid) + " " + self.decisions.context(cid))
        try:
            ctx = {"kind": "move", "cid": cid, "ids": others}
            if self.llm.mock:
                from .mock_policy import actor_context
                ctx["actor"] = actor_context(self, cid)
            r = self.llm.propose(sysm, user, ctx) or {}
        except Exception as e:  # noqa: BLE001
            if getattr(e, "fatal", False):
                raise
            r = {}
        ok = isinstance(r, dict) and r.get("move") in SOCIAL and r.get("to") in w.agents and r.get("to") != cid and (not r.get("about") or r["about"] in w.cast)
        if ok:
            a["proposed_move"] = {"move": r["move"], "to": r["to"], "about": r.get("about") or None, "day": self.day + 1}
            a["want_talk"] = {"who": [r["to"]], "day": self.day + 1, "why": f"{r['move']} {self.nm(r['to'])}"}
        self.proposer_log(tick, cid, "move", ok, f"{r.get('move')} toward {self.nm(r['to'])}" if ok else "not a move the engine knows")
        if isinstance(r, dict):
            request = dict(action='propose_' + str(r.get('move') or 'move')[:30], target=str(r.get('to') or '')[:60])
            rec = self.decisions.record(cid, tick['hour'], r, request)
            rec.update(kind='proposal', status='proposal accepted' if ok else 'rejected')
        return ok

    def proposed_move_for(self, a, t):
        """A proposed move `a` makes toward `t` in a conversation today (used once)."""
        pm = (self.world.agents.get(a) or {}).get("proposed_move")
        if pm and pm.get("day") == self.day and pm.get("to") == t:
            self.world.agents[a].pop("proposed_move", None)
            return pm["move"], pm.get("about")
        return None

    def proposer_log(self, tick, cid, kind, ok, text):
        st = self.s.setdefault("proposer_stats", {})
        key = f"{kind}_{'ok' if ok else 'rejected'}"
        st[key] = st.get(key, 0) + 1
        self.log_event(tick, {"type": "director", "who": cid, "room": self.world.agents[cid]["room"], "vis": "gm",
                              "text": f"Model proposal for {self.nm(cid)} ({kind}): " + ("accepted: " if ok else "rejected: ") + text + "."})
