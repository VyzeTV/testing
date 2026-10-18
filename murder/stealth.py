"""Sneaking, hiding, eavesdropping, hidden items and hidden bodies.

Everything rests on two numbers: how well someone conceals (their calm, health and luck) and how sharp the people around them are
(calm, rested, suspicious, not distracted, and in the light). StealthMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS
from .world import clamp

# room -> (a place to hide, how good the cover is). Rooms with None have nowhere to hide.
COVER = {
    "library": ("the tall stacks", 0.6), "blue_room": ("the wardrobe", 0.65), "green_room": ("the wardrobe", 0.65), "yellow_room": ("the wardrobe", 0.65),
    "red_room": ("the wardrobe", 0.65), "violet_room": ("the wardrobe", 0.65), "orange_room": ("the wardrobe", 0.65), "grey_room": ("the wardrobe", 0.65), "white_room": ("the wardrobe", 0.65), "bathroom": ("behind the shower curtain", 0.5), "kitchen": ("behind the larder door", 0.45),
    "pantry": ("behind the shelves", 0.6), "dining_hall": ("under the long table", 0.35), "lounge": ("behind the heavy curtains", 0.5),
    "games_room": ("behind the billiard table", 0.4), "laundry": ("among the hanging sheets", 0.55), "study": ("behind the desk", 0.4),
    "linen_store": ("between the shelves", 0.6), "music_room": ("behind the piano", 0.5), "art_studio": ("behind the easels", 0.5),
    "observatory": ("under a dust sheet", 0.55), "attic": ("behind the old trunks", 0.7), "master_suite": ("in the walk-in wardrobe", 0.65),
    "upper_landing": ("in the shadowed alcove", 0.3), "landing": ("in the shadowed alcove", 0.3), "foyer": ("behind the coat stand", 0.25),
    "basement_hall": ("in the dark corner", 0.45), "wine_cellar": ("between the barrels", 0.7), "boiler_room": ("behind the boiler", 0.65),
    "cold_store": ("among the hanging sides", 0.5), "garden": ("in the hedge maze", 0.6), "greenhouse": ("among the tall plants", 0.55),
    "pool": ("behind the changing screen", 0.35), "beach": ("behind the rocks", 0.35), "boathouse": ("behind the boats", 0.6),
    "generator_shed": ("behind the generator", 0.55), "lighthouse": ("up the dark stairwell", 0.6),
    "lookout": None, "water_tower": None, "voting_grounds": None, "core_vault": None,
}


def _hh(h):
    return f"{h:02d}:00"


class StealthMixin:
    # ------------------------------------------------------------------ the two numbers
    def sharpness(self, cid):
        """How likely someone is to notice what is hidden or sneaky: calm, rested, suspicious and undistracted people notice more."""
        a = self.world.agents.get(cid)
        if not a:
            return 0.3
        base = 0.38 + (0.2 if a["sanity"] >= 55 else 0) + (0.12 if a["drive"]["id"] in ("seeker", "schemer", "survivor") else 0) - 0.4 * self.slip_chance(cid)
        base -= 0.1 if cid in self.busy else 0
        base -= self.cond_mod(cid, "sharp")
        return max(0.05 if self.has_cond(cid, "blinded") else 0.1, min(1.0, base))

    def stealth(self, cid):
        return self.success_p(cid, 0.72)

    def notice_p(self, observer, subject, bonus=0.0):
        dark = self.blackout_until >= self.idx and not self.world.agents.get(observer, {}).get("lit")
        p = 0.85 + self.cond_mod(subject, "noisy") - 0.75 * self.stealth(subject) + 0.6 * (self.sharpness(observer) - 0.5) - (0.15 if dark else 0.0) + bonus
        return max(0.05, min(0.95, p))

    # ------------------------------------------------------------------ prompts
    def stealth_acts(self, cid):
        if not self.revealed:
            return ""
        w, s = self.world, self.s
        a = w.agents[cid]
        acts = ""
        if COVER.get(a["room"]):
            acts += "|hide"
        if any(True for _ in w.adjacent(cid, a["room"])):
            acts += "|spy"
        if a["inv"]:
            acts += "|stash"
        if any(st["room"] == a["room"] and (st["by"] == cid or st["id"] in a.get("known_stash", [])) for st in s.get("stash", [])):
            acts += "|retrieve"
        case = s.get("case")
        if case and case.get("killer") == cid and not case.get("announced") and not case.get("hidden") and case.get("room") == a["room"]:
            acts += "|hide_body"
        return acts

    def stealth_lines(self, cid):
        if not self.revealed:
            return []
        w, s = self.world, self.s
        a = w.agents[cid]
        out = []
        if self.lean or getattr(self, "short_docs", False):
            out.append("STEALTH: you may sneak (\"sneak\": true), hide (action 'hide'), spy on an adjacent room (action 'spy', \"spy_on\": room id) or hide an item (action 'stash', \"stash\": {\"item\": id, \"spot\": text}).")
        else:
            out.append("STEALTH: you can move quietly (\"sneak\": true; slower, and sharp people may still notice), hide in a room that has cover (action 'hide'; people who come in will not see you and "
                       "you overhear what is said), spy on an adjacent room from a doorway or window (action 'spy' with \"spy_on\": \"<room id>\"), hide an item you carry or that lies here "
                       "(action 'stash' with \"stash\": {\"item\": \"<item id>\", \"spot\": \"<where, max 8 words>\"}) and take your own stash back (action 'retrieve'). "
                       "Calm, well people conceal well; panicked or hurt people do it badly. Sharp, suspicious people who search a room properly can find what is hidden there, "
                       "and anything badly hidden can be found by luck.")
        if a.get("hiding"):
            out.append(f"YOU ARE HIDING {a['hiding']['spot']} in the {w.room_name(a['room'])}: nobody here can see you and you hear what is said. Stay (action 'hide' or 'stay') or step out.")
        mine = [st for st in s.get("stash", []) if st["by"] == cid or st["id"] in a.get("known_stash", [])]
        if mine:
            out.append("YOUR HIDDEN STASHES: " + "; ".join(f"{', '.join(f'{w.item_name(k)} x{q}' for k, q in st['items'].items())} {st['spot']} in the {w.room_name(st['room'])}" for st in mine))
        case = s.get("case")
        if case and case.get("killer") == cid and not case.get("announced") and case.get("room") == a["room"] and not case.get("hidden"):
            out.append("COVER-UP: the body has not been found yet. You can hide it here (action 'hide_body'), or stash the weapon or anything else that points at you (action 'stash'). "
                       "Dragging a body leaves marks, and hidden things can still be found.")
        return out

    # ------------------------------------------------------------------ sneaking, hiding, spying
    def do_hide(self, tick, cid, d):
        w = self.world
        a = w.agents[cid]
        cover = COVER.get(a["room"])
        name = self.nm(cid)
        if not cover:
            self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm", "text": f"{name} looked for somewhere to hide but there is no cover in the {w.room_name(a['room'])}."}, actor=cid)
            return
        if a.get("hiding"):
            return
        spot, base = cover
        good, luck = self.roll(cid, 0.75)
        q = max(0.0, min(1.0, base * 0.6 + 0.5 * self.stealth(cid) + self.rng.uniform(-0.1, 0.1)))
        if not good:
            q *= 0.4
        seen_by = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid and self.rng.random() < self.notice_p(o, cid, bonus=0.25 if not good else 0.0)]
        a["hiding"] = {"spot": spot, "q": q, "since": self.idx, "seen_by": seen_by}
        self.log_event(tick, {"type": "hide", "who": cid, "room": a["room"], "vis": "viewer",
                              "text": f"{name} slips out of sight {spot} in the {w.room_name(a['room'])}" + (" (clumsily)" if not good else "") + "."}, actor=cid)
        for o in seen_by:
            w.remember(o, f"{_hh(tick['hour'])} (you saw) {name} duck out of sight {spot}.")
        a["activity"] = "Hiding"

    def emerge(self, tick, cid, quiet=False):
        w = self.world
        a = w.agents.get(cid)
        h = a.pop("hiding", None) if a else None
        if not h:
            return
        if quiet:
            return
        seen = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid and self.rng.random() < self.notice_p(o, cid, bonus=0.3)]
        for o in seen:
            w.remember(o, f"{_hh(tick['hour'])} (you saw) {self.nm(cid)} step out from {h['spot']}, where they must have been all along.")
            self.adjust_any_aff(o, cid, -1)
        self.log_event(tick, {"type": "hide", "who": cid, "room": a["room"], "vis": "viewer",
                              "text": f"{self.nm(cid)} steps out from {h['spot']}" + (f" and is seen by {', '.join(self.nm(o) for o in seen)}" if seen else "") + "."}, actor=cid)

    def clear_hiding(self):
        for a in self.world.agents.values():
            a.pop("hiding", None)
            a["spying"] = None

    def do_spy(self, tick, cid, d):
        w = self.world
        a = w.agents[cid]
        tgt = d.get("spy_on")
        far = tgt in ROOMS and tgt not in [n["room"] for n in w.adjacent(cid, a["room"])] and self.far_spy_ok(cid, tgt)
        if far:
            a["spying"], a["spy_far"] = None, True
            self.far_look(tick, cid, tgt)
            self.log_event(tick, {"type": "hide", "who": cid, "room": a["room"], "vis": "viewer", "text": f"{self.nm(cid)} watches the {w.room_name(tgt)} through a lens."}, actor=cid)
            return
        adj = [n["room"] for n in w.adjacent(cid, a["room"])]
        if tgt == a["room"]:
            return                                  # already in the room: nothing to watch from a doorway
        if tgt not in adj:
            # a room further away cannot be watched from here: watch the door that leads towards it instead
            steps = w.path(cid, a["room"], tgt) if tgt in ROOMS else None
            nxt = steps[0][0] if steps and steps[0][0] in adj else (adj[0] if adj else None)
            if not nxt:
                return
            tgt = nxt
        a["spying"] = tgt
        self.log_event(tick, {"type": "hide", "who": cid, "room": a["room"], "vis": "viewer",
                              "text": f"{self.nm(cid)} lingers by the way into the {w.room_name(tgt)}, listening."}, actor=cid)

    def eavesdrop(self, tick, room, lines, hour):
        """Hidden people and spies at a door overhear a conversation; a spy may be caught."""
        w = self.world
        hid = [c for c, a in w.agents.items() if a.get("hiding") and a["room"] == room]
        spies = [c for c, a in w.agents.items() if a.get("spying") == room and not a.get("spy_far")]
        for c in hid + spies:
            from_hiding = c in hid
            p = (0.8 if from_hiding else 0.45) * (0.6 + 0.4 * self.stealth(c))
            got = [l for l in lines if self.rng.random() < p][:6]
            for l in got:
                who = self.nm(l["speaker"])
                w.remember(c, f"{_hh(hour)} (overheard {'from hiding' if from_hiding else 'at the door'}) " + (f"{who} {l['text'][:100]}" if l["kind"] == "act" else f"{who}: \"{l['text'][:100]}\""))
            if got:
                self.tally(c, "eavesdrops")
                self.moment(c, "overheard a conversation they were not meant to hear") if len(got) >= 3 else None
            for o in [x for x in w.occupants(room) if x in w.agents and x != c]:
                pc = self.notice_p(o, c) * (0.12 if from_hiding else 0.35)
                if self.rng.random() < pc:
                    w.remember(o, f"{_hh(hour)} You caught {self.nm(c)} " + ("hiding and listening." if from_hiding else "listening at the door."))
                    w.remember(c, f"{_hh(hour)} (private) {self.nm(o)} caught you listening.")
                    self.adjust_any_aff(o, c, -3)
                    self.stat(tick, c, "sanity", -3, "caught listening")
                    self.log_event(tick, {"type": "hide", "who": c, "room": room, "vis": "public",
                                          "text": f"{self.nm(o)} catches {self.nm(c)} " + ("hiding and listening." if from_hiding else "listening at the door.")}, witnesses=[o], actor=c)
                    if from_hiding:
                        w.agents[c].pop("hiding", None)
                    break

    # ------------------------------------------------------------------ hidden items
    def do_stash(self, tick, cid, d):
        w, s = self.world, self.s
        a = w.agents[cid]
        spec = d.get("stash") or {}
        item = spec.get("item")
        room = a["room"]
        if not item:
            return
        if a["inv"].get(item, 0) <= 0:
            if s["room_items"].get(room, {}).get(item, 0) > 0:
                w.take(cid, item, 1)
            else:
                self.log_event(tick, {"type": "system", "who": cid, "room": room, "vis": "gm", "text": f"{self.nm(cid)} tried to hide something they do not have."}, actor=cid)
                return
        qty = max(1, min(int(spec.get("qty") or 1), a["inv"].get(item, 1)))
        cover = COVER.get(room)
        base = cover[1] if cover else 0.3
        spot = (str(spec.get("spot") or "").strip()[:60]) or (cover[0] if cover else "under a loose board")
        good, luck = self.roll(cid, 0.85)
        q = max(0.0, min(1.0, 0.2 + 0.45 * self.stealth(cid) + 0.3 * base + self.rng.uniform(-0.12, 0.12)))
        if not good:
            q *= 0.5
        a["inv"][item] -= qty
        if a["inv"][item] <= 0:
            del a["inv"][item]
        sid = max([x["id"] for x in s.setdefault("stash", [])] + [0]) + 1
        s["stash"].append({"id": sid, "room": room, "items": {item: qty}, "by": cid, "q": q, "spot": spot, "day": self.day, "hour": tick["hour"]})
        a.setdefault("known_stash", []).append(sid)
        self.note_holder(cid, item, tick["hour"])
        self.log_event(tick, {"type": "stash", "who": cid, "room": room, "vis": "viewer",
                              "text": f"{self.nm(cid)} hides {w.item_name(item)} {spot} in the {w.room_name(room)}" + (" (carelessly)" if not good else "") + "."}, actor=cid)
        for o in [x for x in w.occupants(room) if x in w.agents and x != cid]:
            if self.rng.random() < self.notice_p(o, cid, bonus=0.1):
                w.remember(o, f"{_hh(tick['hour'])} (you saw) {self.nm(cid)} hiding something {spot}.")

    def do_retrieve(self, tick, cid, d):
        w, s = self.world, self.s
        a = w.agents[cid]
        got = []
        for st in list(s.get("stash", [])):
            if st["room"] == a["room"] and (st["by"] == cid or st["id"] in a.get("known_stash", [])):
                for k, q in st["items"].items():
                    n, _ = w.take_from_stash(cid, k, q)
                    if n:
                        got.append(w.item_name(k))
                        self.note_holder(cid, k, tick["hour"])
                self.play_tape(tick, cid, st)
                self.play_reel(tick, cid, st)
                s["stash"].remove(st)
        if got:
            self.log_event(tick, {"type": "stash", "who": cid, "room": a["room"], "vis": "gm", "text": f"{self.nm(cid)} retrieves what they hid: {', '.join(got)}."}, actor=cid)

    def reveal_stash(self, tick, finder, st, how):
        w, s = self.world, self.s
        s["stash"].remove(st)
        pool = s["room_items"].setdefault(st["room"], {})
        for k, q in st["items"].items():
            pool[k] = pool.get(k, 0) + q
        names = ", ".join(w.item_name(k) for k in st["items"])
        w.agents[finder].setdefault("known_stash", [])
        prov = self.provenance_text(next(iter(st["items"])), None)
        w.remember(finder, f"{_hh(tick['hour'])} You find something hidden {st['spot']} in the {w.room_name(st['room'])}: {names}.{prov}")
        self.note_evidence(finder, "clue", f"Found hidden {st['spot']} in the {w.room_name(st['room'])}: {names}.{prov}")
        self.log_event(tick, {"type": "stash", "who": finder, "room": st["room"], "vis": "public",
                              "text": f"{self.nm(finder)} {how} something hidden {st['spot']} in the {w.room_name(st['room'])}: {names}."},
                       witnesses=[o for o in w.occupants(st["room"]) if o != finder], actor=finder)
        self.found_stained(tick, finder, list(st["items"]), f"{st['spot']} in the {w.room_name(st['room'])}")
        self.play_tape(tick, finder, st)
        self.play_reel(tick, finder, st)
        self.moment(finder, f"found a hidden stash ({names})")
        if st["by"] in w.agents and st["by"] != finder:
            w.remember(st["by"], f"{_hh(tick['hour'])} (private) Your hiding place in the {w.room_name(st['room'])} has been found.")
            self.hook_from_stash(tick, finder, st["by"], st["room"], st["spot"])

    # ------------------------------------------------------------------ hiding a body
    def do_hide_body(self, tick, cid, d):
        w, s = self.world, self.s
        a = w.agents[cid]
        case = s.get("case")
        if not case or case.get("killer") != cid or case.get("announced") or case.get("hidden") or case.get("room") != a["room"] or case.get("poison_pending"):
            self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm", "text": f"{self.nm(cid)} had no body to hide here."}, actor=cid)
            return
        cover = COVER.get(a["room"])
        if not cover:
            self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm", "text": f"{self.nm(cid)} could not hide a body in the open {w.room_name(a['room'])}."}, actor=cid)
            return
        good, luck = self.roll(cid, 0.65, -0.1)
        q = max(0.0, min(1.0, 0.2 + 0.45 * self.stealth(cid) + 0.3 * cover[1] + self.rng.uniform(-0.1, 0.1)))
        if not good:
            q *= 0.4
        case["hidden"] = {"spot": cover[0], "q": q, "by": cid, "found": False}
        case["clues"].append({"room": a["room"], "scene": False, "found_by": [], "kind": "drag",
                              "text": f"Fresh drag marks scuff the floor toward {cover[0]}: something heavy was moved here."})
        self.stat(tick, cid, "sanity", -3, "hiding the body")
        self.log_event(tick, {"type": "hide", "who": cid, "room": a["room"], "vis": "viewer",
                              "text": f"{self.nm(cid)} drags {self.nm(case['victim'])}'s body {cover[0]} in the {w.room_name(a['room'])}" + ("" if good else ", clumsily") + "."}, actor=cid)
        self.moment(cid, f"hid {self.nm(case['victim'])}'s body")

    # ------------------------------------------------------------------ finding hidden things
    def hidden_things(self, room):
        """Everything findable in a room: stashes, hiders and a hidden body (each with its concealment quality)."""
        s, w = self.world.state, self.world
        out = [("stash", st, st["q"]) for st in s.get("stash", []) if st["room"] == room]
        out += [("hider", c, a["hiding"]["q"]) for c, a in w.agents.items() if a.get("hiding") and a["room"] == room]
        case = s.get("case")
        if case and case.get("hidden") and not case["hidden"].get("found") and case.get("room") == room:
            out.append(("body", case, case["hidden"]["q"]))
        return out

    def found_thing(self, tick, finder, kind, obj, how):
        w, s = self.world, self.s
        if kind == "stash":
            self.reveal_stash(tick, finder, obj, how)
        elif kind == "hider":
            h = w.agents.get(obj)
            if not h or not h.get("hiding"):
                return
            spot = h["hiding"]["spot"]
            h.pop("hiding", None)
            self.log_event(tick, {"type": "hide", "who": finder, "room": h["room"], "vis": "public",
                                  "text": f"{self.nm(finder)} {how} {self.nm(obj)} hiding {spot}."}, witnesses=[o for o in w.occupants(h["room"]) if o != finder], actor=finder)
            w.remember(obj, f"{_hh(tick['hour'])} (private) {self.nm(finder)} found you hiding.")
            self.adjust_any_aff(obj, finder, -2)
            self.stat(tick, obj, "sanity", -4, "found hiding")
            self.stat(tick, finder, "sanity", -2, "found someone hiding")
            self.moment(finder, f"found {self.nm(obj)} hiding {spot}")
        elif kind == "body":
            obj["hidden"]["found"] = True
            w.remember(finder, f"{_hh(tick['hour'])} You find where the body was hidden: {obj['hidden']['spot']}.")
            self.check_discovery(tick, tick["hour"])

    def search_for_hidden(self, tick, cid, text):
        """A deliberate search: sharp people find what is hidden; poorly hidden things are easy."""
        a = self.world.agents[cid]
        sharp = self.sharpness(cid)
        text = (text or "").lower()
        for kind, obj, q in self.hidden_things(a["room"]):
            if kind == "stash" and obj["by"] == cid:
                continue
            if kind == "hider" and obj == cid:
                continue
            spot = obj["spot"] if kind == "stash" else self.world.agents[obj]["hiding"]["spot"] if kind == "hider" else obj["hidden"]["spot"]
            hint = 0.12 if spot and any(wd in text for wd in spot.split() if len(wd) > 4) else 0.0
            p = max(0.03, min(0.95, 0.1 + 0.6 * sharp - 0.6 * q + hint + (0.15 if self.has(cid, "magnifying_glass") else 0.0)))
            if self.rng.random() < p:
                self.found_thing(tick, cid, kind, obj, "searches the room carefully and finds")
                self.tally(cid, "finds")

    def auto_stealth(self, tick, hour, decisions):
        """Behaviours the model rarely thinks of by itself: schemers and seekers listen at doors, killers try to cover their tracks."""
        w, s = self.world, self.s
        if not self.revealed or s.get("over"):
            return
        for cid, a in list(w.agents.items()):
            d = decisions.get(cid) or {}
            if a.get("hiding") or a["drive"]["id"] not in ("schemer", "seeker") or a["sanity"] < 25 or d.get("action") not in ("stay", "rest", "search", None):
                continue
            if d.get("target_room") or self.rng.random() >= 0.12:
                continue
            cands = [n["room"] for n in w.adjacent(cid, a["room"]) if n["ok"] and len([o for o in w.occupants(n["room"]) if o in w.agents]) >= 2]
            if cands:
                a["spying"] = self.rng.choice(cands)
                self.note_use(cid, "spy_on", "engine")
                self.log_event(tick, {"type": "hide", "who": cid, "room": a["room"], "vis": "viewer",
                                      "text": f"{self.nm(cid)} lingers by the way into the {w.room_name(a['spying'])}, listening."}, actor=cid)
        case = s.get("case")
        if case and case.get("killer") in w.agents and not case.get("announced") and case.get("culprit_aware", True) and not s.get("spree"):
            k = case["killer"]
            a = w.agents[k]
            helpless = [o for o in w.occupants(a["room"], include_hidden=True) if o in w.agents and o != k and w.agents[o].get("out")]
            if helpless and a["room"] == case.get("room") and not case.get("framed") and self.rng.random() < 0.6:
                self.do_stage(tick, k, {"target": helpless[0], "_src": "engine"})
                self.note_use(k, "stage", "engine")
            elif a["room"] == case.get("room") and not case.get("hidden") and COVER.get(a["room"]) and self.rng.random() < 0.3 and not case.get("poison_pending"):
                self.do_hide_body(tick, k, {"_src": "engine"})
                self.note_use(k, "hide_body", "engine")
            elif self.rng.random() < 0.25:
                weap = case.get("weapon")
                item = weap if weap and a["inv"].get(weap, 0) > 0 else next((x for x in a["inv"] if "weapon" in w.item_spec(x).get("tags", [])), None)
                if item and not a.get("hiding"):
                    self.do_stash(tick, k, {"stash": {"item": item, "spot": "", "qty": 1}, "_src": "engine"})
                    self.note_use(k, "stash", "engine")

    def stealth_passive(self, tick, hour):
        """Luck: anyone present may stumble on something badly hidden."""
        w = self.world
        rooms = {st["room"] for st in self.s.get("stash", [])} | {a["room"] for a in w.agents.values() if a.get("hiding")}
        case = self.s.get("case")
        if case and case.get("hidden") and not case["hidden"].get("found"):
            rooms.add(case["room"])
        for room in rooms:
            for o in [x for x in w.occupants(room) if x in w.agents]:
                for kind, obj, q in self.hidden_things(room):
                    if (kind == "stash" and obj["by"] == o) or (kind == "hider" and obj == o):
                        continue
                    p = (0.1 * max(0.0, 0.4 - q) / 0.4 if kind != "hider" else 0.05 * (1 - q) * self.sharpness(o)) * (0.5 + self.sharpness(o))
                    if p > 0 and self.rng.random() < p:
                        self.found_thing(tick, o, kind, obj, "stumbles on")
                        break
