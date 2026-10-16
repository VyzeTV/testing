"""Concealed carry, frisking, and withheld evidence and testimony.

Concealed carry: a small item can be kept out of sight on a person. Observers only see it if they are sharp and the concealment is poor; a frisk may find it.
Withholding: a character who finds a clue or knows something can keep it to themselves for a reason (protect someone, protect themselves, leverage, distrust).
It stays out of the shared evidence until it is pressed out of them, their reason disappears, they crack, time runs out, or they choose to come clean.
SecretsMixin is mixed into DayRunner (engine.py).
"""
from .life import BIG_ITEMS


def _hh(h):
    return f"{h:02d}:00"


def _cl(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


MAX_CONCEALED = 3
MAX_HELD = 3


class SecretsMixin:
    # ------------------------------------------------------------------ concealed carry
    def prune_concealed(self, cid):
        a = self.world.agents.get(cid)
        if a and a.get("concealed"):
            for k in [k for k in a["concealed"] if a["inv"].get(k, 0) <= 0]:
                del a["concealed"][k]
            if not a["concealed"]:
                a.pop("concealed", None)

    def sees_concealed(self, observer, subject, item):
        """Does this observer spot an item the subject is carrying out of sight?"""
        a = self.world.all_agents.get(subject)
        q = (a or {}).get("concealed", {}).get(item)
        if q is None:
            return True
        if observer is None:
            return False
        twitchy = 0.12 if a["sanity"] < 30 or a["hp"] < 40 else 0.0
        return self.rng.random() < _cl(0.04 + 0.55 * self.sharpness(observer) * (1 - q) + twitchy, 0.02, 0.8)

    def do_conceal(self, tick, cid, spec):
        w = self.world
        a = w.agents[cid]
        if not isinstance(spec, dict):
            return
        item, on = str(spec.get("item") or ""), spec.get("on", True)
        self.prune_concealed(cid)
        con = a.setdefault("concealed", {})
        name = self.nm(cid)
        if not on:
            if con.pop(item, None) is not None:
                self.log_event(tick, {"type": "conceal", "who": cid, "room": a["room"], "vis": "gm", "text": f"{name} stops hiding the {w.item_name(item)} and carries it openly."}, actor=cid)
            if not con:
                a.pop("concealed", None)
            return
        if a["inv"].get(item, 0) <= 0 or item in BIG_ITEMS or item in con or len(con) >= MAX_CONCEALED:
            if not con:
                a.pop("concealed", None)
            return
        good, _ = self.roll(cid, 0.88)
        q = _cl(0.25 + 0.5 * self.stealth(cid) + self.rng.uniform(-0.1, 0.1))
        if not good:
            q *= 0.5
        con[item] = round(q, 2)
        self.log_event(tick, {"type": "conceal", "who": cid, "room": a["room"], "vis": "viewer",
                              "text": f"{name} tucks the {w.item_name(item)} out of sight on their person" + ("" if good else " (clumsily)") + "."}, actor=cid)
        for o in [x for x in w.occupants(a["room"]) if x in w.agents and x != cid]:
            if self.rng.random() < _cl(self.notice_p(o, cid, bonus=0.0 if good else 0.25) * 0.7):
                w.remember(o, f"{_hh(tick['hour'])} (you saw) {name} slip " + (f"the {w.item_name(item)}" if not good else "something") + " out of sight under their clothes.")

    # ------------------------------------------------------------------ frisking
    def do_frisk(self, tick, cid, tid):
        w = self.world
        a = w.agents[cid]
        t = w.agents.get(tid)
        if not t or tid == cid or t["room"] != a["room"] or t.get("hiding"):
            return
        name, tname = self.nm(cid), self.nm(tid)
        self.prune_concealed(tid)
        con = t.get("concealed", {})
        refuse = _cl(0.05 + (0.35 if con else 0.0) + 0.025 * max(0, -t["aff"].get(cid, 0)) + (0.1 if self.held_by(tid) else 0.0), 0.03, 0.85)
        room = a["room"]
        here = [o for o in w.occupants(room) if o not in (cid, tid)]
        if self.rng.random() < refuse:
            self.log_event(tick, {"type": "frisk", "who": cid, "room": room, "vis": "public",
                                  "text": f"{name} asks to search {tname}; {tname} refuses and steps back."}, witnesses=here + [tid], actor=cid)
            self.adjust_any_aff(tid, cid, -1)
            self.adjust_any_aff(cid, tid, -2)
            self.add_tie(cid, tid, "slighted", f"{tname} would not let me search them", 0)
            w.remember(cid, f"{_hh(tick['hour'])} {tname} would not let you search them.")
            case = self.s.get("case")
            for o in here + [cid]:
                if o != cid:
                    w.remember(o, f"{_hh(tick['hour'])} (you saw) {tname} refused to be searched by {name}.")
                if case and case.get("announced"):
                    self.note_evidence(o, "clue", f"{tname} refused to be searched by {name}.")
            self.tally(cid, "frisks")
            return
        found = []
        for item, q in list(con.items()):
            if self.rng.random() < _cl(0.4 + 0.6 * self.sharpness(cid) - 0.55 * q, 0.08, 0.95):
                found.append(item)
                del con[item]
        if not con:
            t.pop("concealed", None)
        self.tally(cid, "frisks")
        if not found:
            self.log_event(tick, {"type": "frisk", "who": cid, "room": room, "vis": "public",
                                  "text": f"{name} searches {tname} and finds nothing."}, witnesses=here + [tid], actor=cid)
            w.remember(cid, f"{_hh(tick['hour'])} You searched {tname} and found nothing on them (that you could find).")
            self.adjust_any_aff(cid, tid, 1)
            return
        names = ", ".join(w.item_name(k) for k in found)
        weap = any("weapon" in w.item_spec(k).get("tags", []) for k in found)
        self.log_event(tick, {"type": "frisk", "who": cid, "room": room, "vis": "public",
                              "text": f"{name} searches {tname} and finds {names} hidden on them."}, witnesses=here + [tid], actor=cid)
        prov = "".join(self.provenance_text(k, None) for k in found[:1])
        case = self.s.get("case")
        for o in here + [cid]:
            w.remember(o, f"{_hh(tick['hour'])} {name} searched {tname} and found {names} hidden on them.{prov}")
            if case and case.get("announced"):
                self.note_evidence(o, "clue", f"{tname} was carrying {names} out of sight (found by {name}).{prov}")
            if o != cid:
                self.adjust_any_aff(o, tid, -3 if weap else -1)
        self.adjust_any_aff(tid, cid, -2)
        self.hook_found_item(tick, cid, tid, found)
        self.add_tie(cid, tid, "wronged", f"found {names} hidden on {self.nm(tid)}", -0)
        self.stat(tick, tid, "sanity", -3, "caught carrying something hidden")
        self.moment(cid, f"found {names} hidden on {tname}")

    # ------------------------------------------------------------------ prompts
    def secret_acts(self, cid):
        if not self.revealed:
            return ""
        w = self.world
        a = w.agents[cid]
        return "|frisk" if any(o != cid for o in w.occupants(a["room"]) if o in w.agents) else ""

    def secret_lines(self, cid):
        if not self.revealed:
            return []
        w, s = self.world, self.s
        a = w.agents[cid]
        self.prune_concealed(cid)
        out = []
        con = a.get("concealed", {})
        if self.lean or getattr(self, "short_docs", False):
            out.append("CONCEAL: \"conceal\": {\"item\": id, \"on\": true|false} keeps a small item out of sight on you; action 'frisk' with \"frisk\": person id searches someone in the room.")
        else:
            out.append("CONCEALED CARRY: you may keep a small item out of sight on your person (\"conceal\": {\"item\": \"<item id>\", \"on\": true}, or \"on\": false to carry it openly); people who see you "
                       "will not notice it unless they are sharp and you are twitchy. You may search someone in the room (action 'frisk' with \"frisk\": \"<person id>\"): innocent people usually "
                       "agree, those with something to hide often refuse (which looks suspicious). Concealed things can still be found.")
        if con:
            out.append("YOU ARE CONCEALING: " + ", ".join(w.item_name(k) for k in con) + ". Nobody has seen it unless they have said so.")
        held = self.held_by(cid)
        if held:
            out.append("YOU ARE KEEPING THIS BACK from the others (your choice; you have your reasons): "
                       + " | ".join(f"{e['text'][:110]} (because {e['why']})" for e in held)
                       + ". Do not volunteer it. If asked, deflect, stall or lie. You may come clean when pressed hard enough, when your reason is gone, or when it would save you "
                       "(\"disclose\": true tells everyone in the room now).")
        case = s.get("case")
        if case and case.get("announced") and len(held) < MAX_HELD:
            out.append("You may also decide to keep something you know or found back (to protect someone, to protect yourself, as leverage): "
                       "\"keep_back\": {\"what\": \"<what you know, max 20 words>\", \"why\": \"<max 12 words>\"}. Leave it null otherwise.")
        return out

    def card_secret(self, pid):
        held = self.held_by(pid)
        if not held:
            return ""
        return f" Is keeping something back from the others ({held[0]['why']}): will not volunteer it, deflects or lies if asked, unless truly pressed."

    # ------------------------------------------------------------------ withholding
    def held_by(self, cid):
        return [e for e in self.s.get("withheld", []) if e["by"] == cid and e["status"] == "held"]

    def case_tag(self):
        c = self.s.get("case")
        return f"{c['victim']}@{c['day']}:{c['hour']}" if c else None

    def clue_on_table(self, c):
        return any(x not in c.get("held", []) for x in c["found_by"])

    def clue_motive(self, cid, c):
        """(motive, protected person, reason, probability) for keeping a found clue back, or None."""
        w, s = self.world, self.s
        case = s["case"]
        a = w.agents[cid]
        if c.get("kind") == "decoy":
            return None
        killer = case.get("killer")
        if cid == killer and case.get("culprit_aware", True):
            return ("self", None, "it points at you", 0.85)
        for x in s.get("accomplices", {}).get(killer, []):
            if x["helper"] == cid and killer in w.agents:
                return ("protect", killer, f"you are shielding {self.nm(killer)}", 0.7)
        loved = [o for o in w.agents if o != cid and self.nm(o) in c["text"] and a["aff"].get(o, 0) >= 4]
        if loved:
            o = max(loved, key=lambda x: a["aff"].get(x, 0))
            return ("protect", o, f"it could hurt {self.nm(o)}, whom you care about", _cl(0.5 + 0.05 * (a["aff"][o] - 4), 0.5, 0.75))
        others = [o for o in w.agents if o != cid]
        if others and sum(a["aff"].get(o, 0) for o in others) / len(others) <= -2:
            return ("distrust", None, "you trust nobody here with it", 0.22)
        if a["drive"]["id"] in ("schemer", "saboteur"):
            return ("leverage", None, "what you know is leverage", 0.22)
        if a["sanity"] < 30:
            return ("fear", None, "you are too frightened to be seen digging", 0.2)
        return None

    def maybe_withhold_clue(self, tick, cid, c):
        w, s = self.world, self.s
        case = s.get("case")
        if not case or not self.revealed or case.get("killer") is None or len(self.held_by(cid)) >= MAX_HELD:
            return
        m = self.clue_motive(cid, c)
        if not m or self.rng.random() >= m[3]:
            return
        motive, protects, why, _ = m
        eid = max([e["id"] for e in s.setdefault("withheld", [])] + [0]) + 1
        s["withheld"].append({"id": eid, "by": cid, "kind": "clue", "text": c["text"][:170], "why": why, "motive": motive, "protects": protects,
                              "tag": self.case_tag(), "status": "held", "late": False, "day": self.day, "clue": case["clues"].index(c)})
        c.setdefault("held", []).append(cid)
        w.remember(cid, f"{_hh(tick['hour'])} (private) You decide to keep this to yourself, for now: {c['text'][:110]} ({why}).")
        self.log_event(tick, {"type": "withhold", "who": cid, "room": w.agents[cid]["room"], "vis": "gm",
                              "text": f"{self.nm(cid)} pockets a clue and tells nobody ({why}): {c['text'][:90]}"}, actor=cid)

    def keep_back(self, tick, cid, spec):
        """A character decides to sit on something they know."""
        w, s = self.world, self.s
        case = s.get("case")
        if not case or not case.get("announced") or not isinstance(spec, dict) or len(self.held_by(cid)) >= MAX_HELD:
            return
        what, why = str(spec.get("what") or "").strip()[:170], str(spec.get("why") or "").strip()[:80]
        if not what:
            return
        if any(e["by"] == cid and e["status"] == "held" and e["text"] == what for e in s.get("withheld", [])):
            return
        self.add_knowledge(tick, cid, what, why or "your own reasons", "own", None)

    def add_knowledge(self, tick, cid, text, why, motive, protects):
        w, s = self.world, self.s
        eid = max([e["id"] for e in s.setdefault("withheld", [])] + [0]) + 1
        s["withheld"].append({"id": eid, "by": cid, "kind": "knowledge", "text": text, "why": why, "motive": motive, "protects": protects,
                              "tag": self.case_tag(), "status": "held", "late": False, "day": self.day, "clue": None})
        w.remember(cid, f"{_hh(tick['hour'])} (private) You decide not to tell the others what you know: {text[:110]} ({why}).")
        self.log_event(tick, {"type": "withhold", "who": cid, "room": w.agents[cid]["room"], "vis": "gm",
                              "text": f"{self.nm(cid)} decides to say nothing about what they know ({why}): {text[:90]}"}, actor=cid)

    def review_knowledge(self, tick, hour):
        """When a body is announced, people who saw or heard something about someone they care about may decide to stay quiet."""
        w, s = self.world, self.s
        case = s.get("case")
        if not case or case.get("killer") is None or not case.get("announced"):
            return
        for cid, a in w.agents.items():
            if cid == case["killer"] or self.held_by(cid):
                continue
            lines = [m for m in a["memory"]["recent"][-30:] if "(you saw)" in m or "(overheard" in m]
            lines = [m for m in lines if any(self.nm(o) in m for o in w.agents if o != cid)]
            if not lines:
                continue
            others = [o for o in w.agents if o != cid]
            for m in reversed(lines):
                loved = [o for o in others if self.nm(o) in m and a["aff"].get(o, 0) >= 4]
                if loved and self.rng.random() < 0.45:
                    o = loved[0]
                    self.add_knowledge(tick, cid, m.split(") ", 1)[-1][:170], f"you will not drag {self.nm(o)}, whom you care about, into this", "protect", o)
                    break
            else:
                if sum(a["aff"].get(o, 0) for o in others) / len(others) <= -2 and self.rng.random() < 0.2:
                    self.add_knowledge(tick, cid, lines[-1].split(") ", 1)[-1][:170], "you trust nobody here enough to say", "distrust", None)

    # ------------------------------------------------------------------ coming clean
    def reveal_withheld(self, tick, e, why, hour, voluntary=False):
        w, s = self.world, self.s
        if e["status"] != "held":
            return
        e["status"] = "out"
        cid = e["by"]
        case = s.get("case")
        if cid not in w.agents or not case:
            return
        late = bool(case.get("announced")) and not voluntary
        e["late"] = late
        name = self.nm(cid)
        room = w.agents[cid]["room"]
        group = [o for o in w.occupants(room) if o in w.agents and o != cid]
        if e["kind"] == "clue" and e["clue"] is not None and e["clue"] < len(case["clues"]):
            c = case["clues"][e["clue"]]
            if cid in c.get("held", []):
                c["held"].remove(cid)
        else:
            ts = case.setdefault("testimonies", [])
            ts.append({"by": cid, "claim": e["text"][:170], "day": self.day, "hour": hour, "late": late})
            del ts[:-24]
        for o in group:
            w.remember(o, f"{_hh(hour)} {name} {'comes clean' if voluntary else 'finally admits'}: {e['text'][:140]}")
            self.note_evidence(o, "testimony" if e["kind"] == "knowledge" else "clue", f"{name} says: {e['text'][:140]}" if e["kind"] == "knowledge" else e["text"][:150], cid)
            if late:
                self.note_evidence(o, "contradiction", f"{name} sat on this until now: {e['text'][:80]}")
                self.adjust_any_aff(o, cid, -2)
        w.remember(cid, f"{_hh(hour)} (private) You told them: {e['text'][:100]} ({why}).")
        self.stat(tick, cid, "sanity", 2 if voluntary else -2, "came clean" if voluntary else "forced to admit it")
        self.log_event(tick, {"type": "withhold", "who": cid, "room": room, "vis": "public",
                              "text": f"{name} {'comes clean' if voluntary else 'can hold it back no longer'} ({why}): {e['text'][:110]}"}, witnesses=group, actor=cid)

    def reveal_all(self, tick, cid, why, hour, voluntary=True):
        for e in self.held_by(cid):
            self.reveal_withheld(tick, e, why, hour, voluntary)

    def press_withheld(self, tick, asker, target, hour):
        """An interrogation: the target may crack, or the asker may sense they are hiding something."""
        w = self.world
        held = self.held_by(target)
        if not held or asker not in w.agents or target not in w.agents:
            return
        t = w.agents[target]
        for e in held:
            p = 0.15 + 0.05 * max(-3, min(5, t["aff"].get(asker, 0))) + (0.25 if t["sanity"] < 40 else 0) + 0.15 * self.sharpness(asker)
            p *= {"self": 0.4, "protect": 0.55}.get(e["motive"], 1.0)
            if self.crime_on():
                p = 0.55 * p + 0.45 * self.interrogation_odds(asker, target)[1]
            if self.rng.random() < _cl(p, 0.03, 0.8):
                self.reveal_withheld(tick, e, f"pressed by {self.nm(asker)}", hour)
                return
        if self.rng.random() < 0.4 * self.sharpness(asker):
            w.remember(asker, f"{_hh(hour)} {self.nm(target)} dodged your question; you get the feeling they know more than they say.")
            self.note_evidence(asker, "clue", f"{self.nm(target)} dodged questions and seems to be holding something back.")

    def withhold_tick(self, tick, hour):
        """Reasons come and go: protectees die or turn, people crack, the vote draws near."""
        w, s = self.world, self.s
        case = s.get("case")
        if not s.get("withheld"):
            return
        tag = self.case_tag()
        if not case or not case.get("announced"):
            if not case:
                s["withheld"] = []
            return
        left = None
        if case.get("vote_day") is not None:
            left = (case["vote_day"] - self.day) * 24 + case.get("vote_hour", 12) - hour
        for e in list(s["withheld"]):
            if e["status"] != "held":
                continue
            if e["tag"] != tag or e["by"] not in w.agents:
                s["withheld"].remove(e)
                continue
            if e["kind"] == "clue" and e["clue"] is not None and e["clue"] < len(case["clues"]):
                c = case["clues"][e["clue"]]
                if any(x != e["by"] and x not in c.get("held", []) for x in c["found_by"]):
                    e["status"] = "out"            # someone else found it too: no longer a secret
                    continue
            a = w.agents[e["by"]]
            p = e.get("protects")
            if p and p not in w.agents:
                why = "nobody is left to protect"
                prob = 0.7
            elif p and a["aff"].get(p, 0) <= 0:
                why, prob = f"{self.nm(p)} is no friend of yours any more", 0.7
            elif a["sanity"] < 20:
                why, prob = "you are cracking", 0.4
            elif left is not None and left <= 4 and e["motive"] != "self":
                why, prob = "the vote is nearly here", 0.3
            else:
                continue
            if self.rng.random() < prob:
                self.reveal_withheld(tick, e, why, hour)

    def withhold_trial(self, tick, hour, subjects):
        """Before the closing arguments: with the vote minutes away, most people stop holding back; the self-serving use it to save themselves."""
        s = self.s
        for e in list(s.get("withheld", [])):
            if e["status"] != "held" or e["by"] not in self.world.agents:
                continue
            if e["motive"] in ("distrust", "leverage", "own", "fear"):
                prob = 0.8 if e["by"] in subjects else 0.6
            elif e["motive"] == "protect":
                prob = 0.25
            else:
                prob = 0.0
            if self.rng.random() < prob:
                self.reveal_withheld(tick, e, "with the vote minutes away", hour)

    def withhold_aftermath(self, tick, hour, wrongful):
        """If a wrong person is executed while someone sat on the truth, they live with it."""
        s, w = self.world.state, self.world
        for e in s.get("withheld", []):
            if e["status"] == "held" and e["by"] in w.agents and wrongful and e["motive"] != "self":
                self.stat(tick, e["by"], "sanity", -8, "their silence helped kill an innocent")
                w.remember(e["by"], f"{_hh(hour)} (private) You said nothing, and an innocent died. It may have been you who could have stopped it.")
                self.moment(e["by"], "stayed silent while an innocent was executed")
        s["withheld"] = []

    # ------------------------------------------------------------------ automatic behaviours
    def auto_secrets(self, tick, hour, decisions):
        """Models rarely think of concealed carry: killers, plotters and the paranoid tuck weapons away on their own."""
        w, s = self.world, self.s
        if not self.revealed or s.get("over"):
            return
        case = s.get("case")
        for cid, a in list(w.agents.items()):
            if a.get("hiding"):
                continue
            self.prune_concealed(cid)
            con = a.get("concealed", {})
            if len(con) >= MAX_CONCEALED:
                continue
            others = [o for o in w.agents if o != cid]
            paranoid = bool(others) and sum(a["aff"].get(o, 0) for o in others) / len(others) <= -2
            plotting = cid in s.get("plots", {}) or bool(case and case.get("killer") == cid and not case.get("announced"))
            for item in list(a["inv"]):
                if item in con or item in BIG_ITEMS:
                    continue
                tags = w.item_spec(item).get("tags", [])
                p = 0.0
                if "weapon" in tags:
                    p = 0.35 if plotting else 0.1 if paranoid else 0.0
                elif "secret" in tags:
                    p = 0.25
                if p and self.rng.random() < p:
                    self.do_conceal(tick, cid, {"item": item, "on": True})
                    self.note_use(cid, "conceal", "engine")
                    break

    # ------------------------------------------------------------------ variety
    def variety_lines(self, cid):
        """Nudge out of a rut of picking the same idle thing three turns running (experiments are encouraged, not capped)."""
        if not self.revealed:
            return []
        w, s = self.world, self.s
        a = w.agents[cid]
        ra = a.get("recent_actions", [])[-3:]
        if len(ra) < 3 or len(set(ra)) != 1 or ra[0] not in ("take", "search", "rest", "stay"):
            return []
        ideas = []
        here = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid]
        low = [o for o in here if w.agents[o]["sanity"] < 50 and a["aff"].get(o, 0) >= 2]
        if low:
            ideas.append(f"sit with {self.nm(low[0])}, who is not doing well")
        grief = a["memory"].get("lost", [])
        if grief:
            ideas.append(f"take a quiet moment for {grief[-1]['name']}")
        case = s.get("case")
        if case and case.get("announced"):
            ideas.append("investigate a room or question someone")
        if a["drive"]["id"] in ("schemer", "seeker"):
            ideas.append("quietly watch or listen in on someone")
        if here:
            ideas.append(f"have a real conversation with {self.nm(here[0])} about something other than the plan")
        ideas += ["try one of the escape ideas for real", "go back to your room and think", "search an unexplored room"]
        return [f"VARIETY: you have done the same thing ({ra[0]}) three turns running. Do something different this turn, for example: {'; '.join(ideas[:3])}."]
