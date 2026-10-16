"""Hooks: loose ends that grow out of what people actually do.

Nothing is seeded in the characters. A hook opens when something real happens that someone can notice: a person goes through another's belongings, a lock is picked or a door is
broken into, an item goes missing, a hiding place is found, someone is heard at a door at night, or two people keep noticing the same odd behaviour. Each hook has a real cause
(and usually a real culprit), clues that witnesses and traces leave behind, and a victim who may suspect the wrong person. It is solved by evidence (a witness, the stolen thing found on
someone, an admission) or it fades with a note of closure; either way it leaves a mark on how the people involved feel about each other.
HookMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS

PERSONAL_TAGS = {"notebook", "comfort", "gadget", "secret", "art", "book", "gear", "camera"}
KINDS = {"rifled": "Someone has been through your things", "forced_entry": "Someone got into your room", "stolen": "Something of yours is missing",
         "stash_found": "Your hiding place was found", "inspected": "Management went through your room", "snare": "Someone set a trap for you", "night_visitor": "Someone was at a door in the night", "suspicious": "Something is off about someone"}
SOLVE_AT = 3
FADE_DAYS = 4


def _hh(h):
    return f"{int(h):02d}:00"


class HookMixin:
    # ------------------------------------------------------------------ belongings kept in bedrooms
    def seed_belongings(self):
        """Some of each person's personal things stay in their bedroom (nothing is placed on a page: it is just what a person leaves behind when they go out)."""
        w, s = self.world, self.s
        if s.get("belongings") is not None:
            return
        out = {}
        for cid, a in w.agents.items():
            keep = {}
            for k in list(a["inv"]):
                spec = w.item_spec(k)
                tags = set(spec.get("tags", []))
                if len(keep) >= 2 or sum(a["inv"].values()) - sum(keep.values()) <= 3:
                    break
                if tags & PERSONAL_TAGS and not tags & {"weapon", "key", "poison", "medical", "secret"} and a["inv"][k] == 1:
                    keep[k] = 1
            for k in keep:
                del a["inv"][k]
            out[cid] = keep
        s["belongings"] = out

    def belongings_of(self, room):
        return {c: dict(v) for c, v in (self.s.get("belongings") or {}).items() if v and self.world.cast.get(c, {}).get("home") == room and c in self.world.agents}

    # ------------------------------------------------------------------ opening hooks
    def new_hook(self, tick, kind, victims, culprit, room, text, clues=None, seen_by=None, taken=None):
        w, s = self.world, self.s
        hid = max([h["id"] for h in s.setdefault("hooks", [])] + [0]) + 1
        victims = [v for v in dict.fromkeys(victims) if v in w.agents and v != culprit]
        if not victims:
            return None
        h = {"id": hid, "kind": kind, "victims": victims, "culprit": culprit, "room": room, "day": self.day, "hour": tick["hour"], "text": text,
             "clues": list(clues or []), "seen_by": [x for x in (seen_by or []) if x in w.agents], "taken": taken, "status": "open", "evidence": 0,
             "heat": 3, "last_new": self.day, "suspect": {}}
        s["hooks"].append(h)
        del s["hooks"][:-30]
        for v in victims:
            for ally in self.allies_of(v):
                w.remember(ally, f"{_hh(tick['hour'])} (your ally {self.nm(v)} tells you) {text}")
            w.remember(v, f"{_hh(tick['hour'])} (something is wrong) {text}" + (f" {h['clues'][0]}" if h["clues"] else ""))
            self.moment(v, KINDS[kind].lower())
            self.stat(tick, v, "sanity", -2, "something is wrong")
        self.log_event(tick, {"type": "hook", "who": victims[0], "room": room, "vis": "viewer",
                              "text": f"{KINDS[kind]}: {self.nm(victims[0])} realises. " + (f"(It was {self.nm(culprit)}.)" if culprit in w.agents else "")}, actor=victims[0])
        return h

    def record_disturbance(self, tick, kind, culprit, room, owners, neat=True, taken=None, clues=None):
        """Something happened that an owner has not noticed yet; witnesses may have seen the culprit."""
        w, s = self.world, self.s
        seen = []
        near = {room} | {n["room"] for n in w.adjacent(culprit, room)} if culprit in w.agents else {room}
        for o in w.agents:
            if o in (culprit, *owners) or w.agents[o]["room"] not in near or w.agents[o].get("asleep"):
                continue
            if self.rng.random() < 0.5 * self.notice_p(o, culprit):
                seen.append(o)
                w.remember(o, f"{_hh(tick['hour'])} (you saw) {self.nm(culprit)} leaving the {w.room_name(room)}, looking over their shoulder.")
        s.setdefault("disturbances", []).append({"kind": kind, "culprit": culprit, "room": room, "owners": [o for o in owners if o in w.agents and o != culprit], "day": self.day,
                                                 "hour": tick["hour"], "neat": neat, "taken": taken, "clues": list(clues or []), "seen_by": seen, "rolls": 0})
        del s["disturbances"][:-20]

    def hook_notice(self, tick, hour):
        """Owners who are back in a disturbed room (or have lost something) may notice that something is wrong."""
        w, s = self.world, self.s
        for dist in list(s.get("disturbances", [])):
            owners = [o for o in dist["owners"] if o in w.agents and not w.agents[o].get("asleep")]
            for o in owners:
                a = w.agents[o]
                here = a["room"] == dist["room"] or dist["kind"] == "stolen"
                if not here:
                    continue
                p = {"rifled": (0.25 if dist["neat"] else 0.7), "forced_entry": 0.5 if dist["neat"] else 1.0, "stolen": 0.55}.get(dist["kind"], 0.4)
                p = min(0.97, (p + 0.4 * self.sharpness(o) + (0.6 if dist.get("taken") else 0.0)) * self.tune("hook_notice"))
                dist["rolls"] += 1
                if self.rng.random() < p:
                    clues = list(dist["clues"])
                    if dist.get("taken"):
                        clues.append(f"Your {w.item_name(dist['taken'])} is gone.")
                    text = {"rifled": f"Someone has been through your things in the {w.room_name(dist['room'])}.", "forced_entry": f"Someone got into the {w.room_name(dist['room'])} while you were away.",
                            "stolen": f"Your {w.item_name(dist['taken'])} has been taken from you." if dist.get("taken") else "Something of yours has gone missing."}.get(dist["kind"], "Something is wrong.")
                    h = self.new_hook(tick, dist["kind"], [o], dist["culprit"], dist["room"], text, clues, dist["seen_by"], dist.get("taken"))
                    if h and dist["culprit"] in w.agents:
                        w.remember(dist["culprit"], f"{_hh(hour)} (private) {self.nm(o)} has noticed what you did in the {w.room_name(dist['room'])}.")
                    dist["owners"].remove(o)
            if not dist["owners"] or dist["rolls"] > 8 or self.day - dist["day"] > 3:
                s["disturbances"].remove(dist)

    # ------------------------------------------------------------------ going through someone's things
    def rifle_room(self, tick, cid, d):
        """Searching a room that is someone's bedroom while they are away is going through their things."""
        w, s = self.world, self.s
        a = w.agents[cid]
        room = a["room"]
        stuff = {c: v for c, v in self.belongings_of(room).items() if c != cid}
        if not stuff:
            return
        owners = [c for c in stuff if not w.agents[c].get("asleep")]
        if any(w.agents[c]["room"] == room for c in owners):
            return                                              # the owner is right there: this is not snooping
        good, _ = self.roll(cid, 0.8)
        name = self.nm(cid)
        taken = None
        looked = []
        for owner, items in stuff.items():
            looked += [w.item_name(k) for k in items]
            wants = a["drive"]["id"] in ("schemer", "saboteur", "nihilist") or a["sanity"] < 35
            if items and wants and self.rng.random() < 0.3:
                k = next(iter(items))
                s["belongings"][owner].pop(k, None)
                a["inv"][k] = a["inv"].get(k, 0) + 1
                self.note_holder(cid, k, tick["hour"])
                taken = (owner, k)
                break
        w.remember(cid, f"{_hh(tick['hour'])} (private) You went through the things in the {w.room_name(room)}: {', '.join(looked[:5]) or 'nothing much'}.")
        if self.rng.random() < 0.35 * (0.5 + self.sharpness(cid)):
            for owner in stuff:
                sec = self.world.cast[owner].get("secret", "")
                if sec and self.rng.random() < 0.2:
                    w.remember(cid, f"{_hh(tick['hour'])} (private) Among {self.nm(owner)}'s things you find a hint of something: {sec[:110]}")
        self.tally(cid, "rifles")
        self.log_event(tick, {"type": "rifle", "who": cid, "room": room, "vis": "viewer",
                              "text": f"{name} goes through the things in the {w.room_name(room)}" + (f" and takes the {w.item_name(taken[1])}" if taken else "") + ("" if good else " (clumsily)") + "."}, actor=cid)
        self.record_disturbance(tick, "rifled", cid, room, list(stuff), neat=good, taken=taken[1] if taken else None,
                                clues=[] if good else ["The drawers were left slightly open and things are out of order."])
        if taken:
            self.s["disturbances"][-1]["owners"] = [taken[0]] + [o for o in stuff if o != taken[0]]

    # ------------------------------------------------------------------ other sources of hooks
    def hook_from_door(self, tick, cid, room, how):
        """A lock was picked or a door broken: whoever sleeps there will find out."""
        owners = [c for c in self.world.agents if self.world.cast[c]["home"] == room and c != cid]
        if not owners:
            return
        clue = "Fine scratches ring the lock." if how == "picked" else "The door frame is splintered where it was forced."
        self.record_disturbance(tick, "forced_entry", cid, room, owners, neat=(how == "picked"), clues=[clue])

    def hook_from_steal(self, tick, thief, victim, item, noticed):
        if not noticed:
            self.record_disturbance(tick, "stolen", thief, self.world.agents[victim]["room"], [victim], neat=True, taken=item)

    def hook_from_stash(self, tick, finder, owner, room, spot):
        if owner in self.world.agents and owner != finder:
            self.new_hook(tick, "stash_found", [owner], finder, room, f"Your hiding place {spot} in the {self.world.room_name(room)} has been found.", [], [])

    def hook_from_night(self, tick, culprit, room, woken):
        if woken and culprit in self.world.agents:
            self.new_hook(tick, "night_visitor", woken, culprit, room, f"You were woken in the night by someone at the door of the {self.world.room_name(room)}.", ["You did not see who."], [])

    def note_odd(self, cid, observer, hour):
        """Two people noticing the same odd behaviour become a hook about that person."""
        s = self.s
        odd = s.setdefault("odd", {})
        lst = odd.setdefault(cid, [])
        if observer not in lst:
            lst.append(observer)
        if len(lst) >= 2 and not any(h["kind"] == "suspicious" and h["culprit"] == cid and h["status"] == "open" for h in s.get("hooks", [])):
            tick = {"hour": hour, "events": [], "thoughts": {}}
            h = self.new_hook(tick, "suspicious", lst[:2], cid, self.world.agents[cid]["room"], f"{self.nm(cid)} has been acting strangely.", [], lst)
            if h:
                s.setdefault("_pending_events", []).extend(tick["events"])

    # ------------------------------------------------------------------ prompts
    def hook_lines(self, cid):
        w, s = self.world, self.s
        out = []
        for h in s.get("hooks", []):
            if h["status"] != "open":
                continue
            if cid in h["victims"]:
                sus = h["suspect"].get(cid)
                line = f"ON YOUR MIND: {h['text']}" + (" " + " ".join(h["clues"][:2]) if h["clues"] else "")
                if sus in w.agents:
                    line += f" You suspect {self.nm(sus)}."
                line += (" You can look into it (search the room, ask people who were nearby, search someone you suspect) or let it go; you have no proof yet." if h["evidence"] < SOLVE_AT else "")
                out.append(line)
            elif cid == h["culprit"]:
                out.append(f"WHAT YOU DID: {self.nm(h['victims'][0])} has noticed {KINDS[h['kind']].lower()}. They do not know it was you (yet). Cover it, deflect, or own up.")
        return out[:2]

    # ------------------------------------------------------------------ progress
    def solve_hook(self, tick, h, how):
        w = self.world
        if h["status"] != "open":
            return
        h["status"] = "solved"
        c = h["culprit"]
        for v in h["victims"]:
            if v in w.agents:
                w.remember(v, f"{_hh(tick['hour'])} (you now know) It was {self.nm(c)}: {how}.")
                if c in w.agents:
                    self.adjust_any_aff(v, c, -3)
                    self.add_tie(v, c, "wronged", f"{self.nm(c)} {KINDS[h['kind']].lower().replace('someone ', '')}", -1)
        if c in w.agents:
            w.remember(c, f"{_hh(tick['hour'])} (private) {self.nm(h['victims'][0])} knows it was you.")
        self.log_event(tick, {"type": "hook", "who": h["victims"][0], "room": h["room"], "vis": "viewer", "text": f"{self.nm(h['victims'][0])} works out who: {self.nm(c)} ({how})."}, actor=h["victims"][0])

    def hook_press(self, tick, asker, target, hour):
        """An interrogation about a hook: a witness gives up what they saw; the culprit is shaken or evasive; an innocent is hurt by the suspicion."""
        w, s = self.world, self.s
        for h in s.get("hooks", []):
            if h["status"] != "open" or asker not in h["victims"] or target == asker:
                continue
            if target in h["seen_by"] and h["culprit"] in w.agents:
                h["evidence"] += 2
                h["last_new"] = self.day
                h["clues"].append(f"{self.nm(target)} saw {self.nm(h['culprit'])} near the {w.room_name(h['room'])}.")
                w.remember(asker, f"{_hh(hour)} {self.nm(target)} says they saw {self.nm(h['culprit'])} near the {w.room_name(h['room'])} around then.")
                h["suspect"][asker] = h["culprit"]
            elif target == h["culprit"]:
                t = w.agents[target]
                if self.rng.random() < 0.15 + (0.3 if t["sanity"] < 40 else 0) + 0.04 * max(0, t["aff"].get(asker, 0)):
                    h["evidence"] = SOLVE_AT
                    self.solve_hook(tick, h, "they cracked under the questions")
                else:
                    if self.rng.random() < 0.5 * self.sharpness(asker):
                        h["evidence"] += 1
                        h["last_new"] = self.day
                        w.remember(asker, f"{_hh(hour)} {self.nm(target)} answered too quickly, and would not meet your eye.")
                    h["suspect"].setdefault(asker, target) if h["evidence"] >= 1 else None
            else:
                if h["suspect"].get(asker) == target:
                    self.adjust_any_aff(target, asker, -2)
                    w.remember(target, f"{_hh(hour)} (private) {self.nm(asker)} seems to think you went through their things.")
            if h["evidence"] >= SOLVE_AT and h["status"] == "open":
                self.solve_hook(tick, h, "the evidence points one way")

    def hook_found_item(self, tick, finder, holder, items):
        """Frisking someone and finding a stolen thing solves the hook outright."""
        for h in self.s.get("hooks", []):
            if h["status"] == "open" and h.get("taken") in items and h["culprit"] == holder and finder in h["victims"]:
                h["evidence"] = SOLVE_AT
                self.solve_hook(tick, h, f"the {self.world.item_name(h['taken'])} was on them")

    def hook_tick(self, tick, hour):
        self.hook_notice(tick, hour)
        w, s = self.world, self.s
        for h in s.get("hooks", []):
            if h["status"] != "open":
                continue
            for v in h["victims"]:
                if v not in w.agents:
                    continue
                if v not in h["suspect"] and self.rng.random() < 0.15 and h["evidence"] < 1:
                    others = [o for o in w.agents if o != v]
                    if others:
                        t = min(others, key=lambda o: w.agents[v]["aff"].get(o, 0))      # without evidence, suspicion falls on whoever they already trust least
                        h["suspect"][v] = t
                        w.remember(v, f"{_hh(hour)} (suspicion) You find yourself thinking it was {self.nm(t)}.")
                        self.adjust_any_aff(v, t, -1)

    def hook_night(self, tick):
        """Each night: a hook with no news cools and eventually fades; a sharp victim may put two and two together."""
        w, s = self.world, self.s
        for h in s.get("hooks", []):
            if h["status"] != "open":
                continue
            h["heat"] = max(0, h["heat"] - 1)
            v = next((x for x in h["victims"] if x in w.agents), None)
            if v and h["culprit"] in w.agents and h["evidence"] >= 1 and self.rng.random() < 0.3 * self.sharpness(v):
                h["evidence"] += 1
                if h["evidence"] >= SOLVE_AT:
                    self.solve_hook(tick, h, "things finally add up")
                    continue
            if self.day - h["last_new"] >= FADE_DAYS:
                h["status"] = "faded"
                for x in h["victims"]:
                    if x in w.agents:
                        w.remember(x, "(private) You never found out. It still sits badly, but you stop turning it over.")
