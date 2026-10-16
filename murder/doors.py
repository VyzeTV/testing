"""Locks, lock-picking, forced doors, barricades, and where people sleep.

Every indoor room has a lock that its people can bolt (from inside) or lock (from outside, with a key). The people who sleep in a room, whoever locked it, and anyone with
the master or skeleton keys can open it; everyone else can pick it (quiet, needs a tool) or break the door (loud, tiring, and the door stays broken until NeoVi mends it at the
start of the next week). Any ordinary door can also be blocked from the inside with props (furniture, planks, a barrel, a ladder, even a body) which others have to break down.
Loud noise wakes sleepers. Characters may sleep wherever they like, but their own room is safest and most restful.
DoorMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS, ITEMS

NO_LOCK = {"voting_grounds", "core_vault"}
PICK_TOOLS = {"skeleton_keys": 1.0, "master_key": 1.0, "bolt_cutters": 0.85, "lockpicks": 0.7, "piano_wire": 0.6, "wire": 0.5, "hair_tie": 0.3, "pen": 0.3, "craft_knife": 0.3}
BREAK_BONUS = {"sledgehammer": 0.4, "fire_axe": 0.4, "hatchet": 0.3, "crowbar": 0.3, "fire_extinguisher": 0.15, "pool_cue": 0.05, "baseball_bat": 0.15, "pipe_wrench": 0.15, "hammer": 0.1, "coal_shovel": 0.1, "fire_poker": 0.05}
PROPS = {"furniture": ("heavy furniture", 2), "planks": ("planks", 2), "barrel": ("a barrel", 2), "ladder": ("a ladder", 1), "body": ("a body", 3)}


def lockable(room):
    return room in ROOMS and ROOMS[room][1] not in ("grounds", "roof") and room not in NO_LOCK


def _hh(h):
    return f"{int(h):02d}:00"


class DoorMixin:
    # ------------------------------------------------------------------ helpers
    def door_edge(self, cid, other):
        """The ordinary door (or window) between where cid stands and an adjacent room."""
        here = self.world.agents[cid]["room"]
        for e in self.world.edges:
            if {e["a"], e["b"]} == {here, other} and e["kind"] in ("door", "window") and not e["hidden"]:
                return e
        return None

    def door_block(self, cid, other):
        """What stops cid walking into `other`: ('barricade', blk), ('lock', lk) or None."""
        w, s = self.world, self.s
        e = self.door_edge(cid, other)
        if not e:
            return None
        here_lk = s.get("locks", {}).get(w.agents[cid]["room"])
        if here_lk and here_lk.get("keyed") and not w.has_room_key(cid, w.agents[cid]["room"]):
            return ("lock_in", here_lk)                      # locked in with no key
        blk = s.get("blocks", {}).get(e["id"])
        if blk and blk["inside"] == other:
            return ("barricade", blk)
        lk = s.get("locks", {}).get(other)
        if lk and not w.has_room_key(cid, other):
            return ("lock", lk)
        return None

    def pick_tool(self, cid):
        inv = self.world.agents[cid]["inv"]
        have = [(p, k) for k, p in PICK_TOOLS.items() if inv.get(k, 0) > 0]
        return max(have) if have else None

    def break_bonus(self, cid):
        inv = self.world.agents[cid]["inv"]
        return max([b for k, b in BREAK_BONUS.items() if inv.get(k, 0) > 0] + [0.0])

    def body_here(self, room):
        s = self.s
        case = s.get("case")
        if case and case.get("room") == room and case.get("victim") not in self.world.agents and not (case.get("hidden") and not case["hidden"].get("found")):
            return case
        return next((b for b in s.get("bodies", []) if b.get("room") == room), None)

    def noise(self, tick, room, level, source=None):
        """A sound at a door: sleepers in the room and (if loud) next door may wake, and awake people nearby hear it."""
        w = self.world
        loud = level == "loud"
        woken = []
        rooms = {room: (0.9 if loud else 0.12)}
        if loud:
            for e in w.edges:
                if e["hidden"]:
                    continue
                if e["a"] == room:
                    rooms.setdefault(e["b"], 0.45)
                elif e["b"] == room:
                    rooms.setdefault(e["a"], 0.45)
        for r, p in rooms.items():
            for cid, a in w.agents.items():
                if a["room"] != r or cid == source:
                    continue
                if a.get("asleep"):
                    if self.rng.random() < p:
                        a.pop("asleep", None)
                        woken.append(cid)
                        w.remember(cid, f"{_hh(tick['hour'])} (woken) {'A crash and splintering wood' if loud else 'A faint scratching'} at the door of the {w.room_name(room)}. You are awake now, and afraid.")
                elif self.rng.random() < (0.85 if loud else 0.3) * (1.0 if r == room else 0.6):
                    w.remember(cid, f"{_hh(tick['hour'])} (heard) {'someone smashing at a door' if loud else 'a faint scratching'} at the {w.room_name(room)}.")
        return woken

    # ------------------------------------------------------------------ prompts
    def door_acts(self, cid):
        if not self.revealed:
            return ""
        w, s = self.world, self.s
        a = w.agents[cid]
        room = a["room"]
        acts = ""
        locks = s.get("locks", {})
        adj = [n for n in w.adjacent(cid, room) if n["kind"] in ("door", "window")]
        if (lockable(room) and room not in locks and room not in s.get("broken", [])) or any(
                lockable(n["room"]) and n["room"] not in locks and n["room"] not in s.get("broken", []) and w.has_room_key(cid, n["room"]) for n in adj):
            acts += "|lock"
        if room in locks or any(n["room"] in locks and w.has_room_key(cid, n["room"]) for n in adj):
            acts += "|unlock"
        blocked = [n for n in adj if self.door_block(cid, n["room"])]
        if blocked and self.pick_tool(cid) and any(self.door_block(cid, n["room"])[0] in ("lock", "lock_in") for n in blocked):
            acts += "|pick"
        if blocked:
            acts += "|break"
        if any(self.world.state.get("blocks", {}).get(n["edge"]) is None for n in adj):
            acts += "|barricade"
        return acts

    def door_lines(self, cid):
        if not self.revealed:
            return []
        w, s = self.world, self.s
        a = w.agents[cid]
        room = a["room"]
        out = []
        locks = s.get("locks", {})
        notes = []
        if room in locks:
            notes.append(f"the {w.room_name(room)} you are in is locked ({'by you' if locks[room].get('by') == cid else 'bolted'})")
        elif room in s.get("broken", []):
            notes.append(f"the door of the {w.room_name(room)} is broken and will not lock")
        for n in w.adjacent(cid, room):
            if n["kind"] not in ("door", "window"):
                continue
            other = n["room"]
            blk = s.get("blocks", {}).get(n["edge"])
            if blk and blk["inside"] == other:
                notes.append(f"the way into the {w.room_name(other)} is barricaded from inside with {blk.get('prop_name') or blk['prop']} (break it down)")
            elif blk:
                notes.append(f"you have barricaded the door to the {w.room_name(other)}")
            elif other in locks:
                notes.append(f"the {w.room_name(other)} is locked" + (" (you have a key)" if w.has_room_key(cid, other) else " (pick the lock or break the door)"))
            elif other in s.get("broken", []):
                notes.append(f"the door of the {w.room_name(other)} is broken open")
        if notes:
            out.append("DOORS NEAR YOU: " + "; ".join(notes[:6]) + ".")
        if self.lean or getattr(self, "short_docs", False):
            out.append("DOORS: actions lock/unlock/pick/break/barricade take \"door\": <room id> (and \"item\" for a barricade prop).")
        else:
            out.append("DOORS: every room has a lock. Action 'lock' bolts the room you are in (\"door\": its room id) or locks an adjacent room you hold a key for; 'unlock' undoes it. People who sleep in a room, "
                       "whoever locked it, and holders of the master or skeleton keys can open it. Others can 'pick' it (\"door\": the room beyond; quiet; needs wire, a hair tie, a pen, skeleton keys or bolt cutters) "
                       "or 'break' it (loud, tiring, wakes sleepers; a broken door stays broken until NeoVi mends it next week). 'barricade' blocks a door from your side with furniture, planks, a barrel, a ladder "
                       "or a body (\"door\": the room beyond, \"item\": the prop); whoever is on the other side must 'break' it down. Leaving a room clears your bolt or barricade.")
        return out

    # ------------------------------------------------------------------ the actions
    def do_lock(self, tick, cid, d):
        w, s = self.world, self.s
        a = w.agents[cid]
        target = d.get("door") or a["room"]
        name = self.nm(cid)
        if target != a["room"] and not (self.door_edge(cid, target) and w.has_room_key(cid, target)):
            return
        if not lockable(target) or target in s["broken"] or target in s["locks"]:
            return
        if self.scene_sealed(target):
            w.remember(cid, f"{_hh(self.s.get('_hour', 12))} (private) TereVi's tape is across the door of the {w.room_name(target)}: nobody may lock it until the trial.")
            return
        inside_ = [o for o in w.occupants(target, include_hidden=True) if o in w.agents and o != cid]
        s["locks"][target] = {"by": cid, "day": self.day, "keyed": bool(target != a["room"] and any(not w.has_room_key(o, target) for o in inside_))}
        if s["locks"][target]["keyed"]:
            for o in inside_:
                if o in w.agents and not w.has_room_key(o, target):
                    if w.agents[o].get("out"):
                        w.agents[o]["locked_by"] = cid
                    else:
                        self.add_tie(o, cid, "wronged", f"locked you in the {w.room_name(target)}", -4)
                        w.remember(o, f"{_hh(self.s.get('_hour', 12))} (private) {self.nm(cid)} locked you in the {w.room_name(target)}.")
        txt = f"{name} slides the bolt on the {w.room_name(target)}." if target == a["room"] else f"{name} locks the {w.room_name(target)}."
        self.log_event(tick, {"type": "door", "who": cid, "room": a["room"], "vis": "public", "text": txt},
                       witnesses=[o for o in w.occupants(a["room"]) if o != cid], actor=cid)

    def do_unlock(self, tick, cid, d):
        w, s = self.world, self.s
        a = w.agents[cid]
        target = d.get("door") or a["room"]
        if target not in s["locks"]:
            return
        if target != a["room"] and not (self.door_edge(cid, target) and w.has_room_key(cid, target)):
            return
        del s["locks"][target]
        self.log_event(tick, {"type": "door", "who": cid, "room": a["room"], "vis": "public", "text": f"{self.nm(cid)} unlocks the {w.room_name(target)}."},
                       witnesses=[o for o in w.occupants(a["room"]) if o != cid], actor=cid)

    def do_pick(self, tick, cid, d):
        w, s = self.world, self.s
        a = w.agents[cid]
        target = d.get("door")
        blk = self.door_block(cid, target) if target else None
        if not blk or blk[0] not in ("lock", "lock_in"):
            return
        if blk[0] == "lock_in":
            target = a["room"]
        tool = self.pick_tool(cid)
        name = self.nm(cid)
        if not tool:
            self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm", "text": f"{name} has nothing to pick the {w.room_name(target)} lock with."}, actor=cid)
            return
        p = tool[0] * (0.45 + 0.55 * self.success_p(cid, 1.0)) * self.hand_skill(cid)
        good, _ = self.roll(cid, p)
        woken = self.noise(tick, target, "quiet", cid)
        self.hook_from_night(tick, cid, target, woken)
        here = [o for o in w.occupants(a["room"]) if o != cid]
        if good:
            self.hook_from_door(tick, cid, target, "picked")
            self.log_door(target, "picked", cid, tool[1])
            del s["locks"][target]
            self.tally(cid, "picks")
            self.log_event(tick, {"type": "door", "who": cid, "room": a["room"], "vis": "public", "text": f"{name} picks the lock of the {w.room_name(target)} with the {w.item_name(tool[1])}."},
                           witnesses=here, actor=cid)
        else:
            self.log_event(tick, {"type": "door", "who": cid, "room": a["room"], "vis": "public", "text": f"{name} works at the lock of the {w.room_name(target)} and gets nowhere."},
                           witnesses=here, actor=cid)

    def do_break(self, tick, cid, d):
        w, s = self.world, self.s
        a = w.agents[cid]
        target = d.get("door")
        blk = self.door_block(cid, target) if target else None
        if not blk:
            return
        e = self.door_edge(cid, target)
        if blk[0] == "lock_in":
            target = a["room"]
        name = self.nm(cid)
        bonus = self.break_bonus(cid)
        p = max(0.1, min(0.9, 0.22 + 0.25 * (a["hp"] / 100) + bonus + (0.1 if a["sanity"] < 30 else 0)))
        good, _ = self.roll(cid, p)
        here = [o for o in w.occupants(a["room"]) if o != cid] + [o for o in w.occupants(target)]
        woken = self.noise(tick, target, "loud", cid)
        self.hook_from_night(tick, cid, target, woken)
        if a["hp"] > 12:
            self.stat(tick, cid, "hp", -2, "battering a door")
        if blk[0] == "barricade":
            b = blk[1]
            if good:
                b["hp"] -= 2 if bonus >= 0.3 else 1
            if good and b["hp"] <= 0:
                del s["blocks"][e["id"]]
                txt = f"{name} smashes through the barricade ({b.get('prop_name') or b['prop']}) at the door of the {w.room_name(target)}."
            elif good:
                txt = f"{name} drives the {b.get('prop_name') or b['prop']} back a hand's width; it is giving way."
            else:
                txt = f"{name} throws their weight against the barricaded door of the {w.room_name(target)}; it holds."
        else:
            if good:
                self.hook_from_door(tick, cid, target, "broken")
                self.log_door(target, "broken", cid)
                s["locks"].pop(target, None)
                if target not in s["broken"]:
                    s["broken"].append(target)
                if e:
                    self.env_break_door(e["id"], tick)
                txt = f"{name} breaks the door of the {w.room_name(target)} off its lock."
            else:
                txt = f"{name} slams against the locked door of the {w.room_name(target)}; it holds."
        self.tally(cid, "breakins")
        self.log_event(tick, {"type": "breakin", "who": cid, "room": target, "vis": "public", "text": txt}, witnesses=here, actor=cid)
        if woken:
            self.log_event(tick, {"type": "door", "who": woken[0], "room": target, "vis": "viewer", "text": f"{', '.join(self.nm(c) for c in woken)} jolt awake."})

    def do_barricade(self, tick, cid, d):
        w, s = self.world, self.s
        a = w.agents[cid]
        target = d.get("door")
        e = self.door_edge(cid, target) if target else None
        if not e or e["id"] in s["blocks"]:
            return
        if self.scene_sealed(a["room"]) or self.scene_sealed(target):
            return
        item = d.get("item") or ""
        prop = None
        if item == "body" and self.body_here(a["room"]):
            prop = "body"
        elif item in PROPS and item not in ("furniture", "body") and (a["inv"].get(item, 0) > 0 or s["room_items"].get(a["room"], {}).get(item, 0) > 0):
            prop = item
        elif ROOMS[a["room"]][1] not in ("grounds", "roof"):
            prop = "furniture"
        if not prop:
            return
        if prop in ITEMS and prop != "furniture":
            if a["inv"].get(prop, 0) > 0:
                a["inv"][prop] -= 1
                if a["inv"][prop] <= 0:
                    del a["inv"][prop]
            else:
                s["room_items"][a["room"]][prop] -= 1
        pname, hp = PROPS[prop]
        s["blocks"][e["id"]] = {"by": cid, "inside": a["room"], "prop": prop, "prop_name": pname, "hp": hp, "day": self.day}
        if prop == "body":
            case = self.body_here(a["room"])
            if case and "clues" in case:
                case["clues"].append({"room": a["room"], "scene": False, "found_by": [], "kind": "drag",
                                      "text": f"The body had been dragged across the floor and wedged against the door to the {w.room_name(target)}."})
            self.stat(tick, cid, "sanity", -4, "using a body as a barricade")
        self.noise(tick, a["room"], "quiet", cid)
        self.log_event(tick, {"type": "door", "who": cid, "room": a["room"], "vis": "public",
                              "text": f"{self.nm(cid)} drags {pname} against the door to the {w.room_name(target)}."},
                       witnesses=[o for o in w.occupants(a["room"]) if o != cid], actor=cid)

    def door_assault(self, cid, dest, d):
        """A plotter whose target is behind a locked or barricaded door goes through it. True if the turn was changed."""
        blk = self.door_block(cid, dest)
        if not blk:
            return False
        if blk[0] == "lock" and self.pick_tool(cid):
            d.update(action="pick", door=dest, target_room="", activity=f"Works quietly at the lock of the {self.world.room_name(dest)}")
        else:
            d.update(action="break", door=dest, target_room="", activity=f"Forces the way into the {self.world.room_name(dest)}")
        return True

    # ------------------------------------------------------------------ sleeping
    def bed_room(self, cid):
        """Where cid sleeps tonight: where they said (if they can get there), otherwise their own room."""
        w = self.world
        a = w.agents[cid]
        pref = a.get("sleep_pref")
        cand = [pref[1]] if pref and pref[0] == self.day and pref[1] in ROOMS else []
        cand.append(w.cast[cid]["home"])
        for dest in cand:
            if a["room"] == dest or w.path(cid, a["room"], dest) is not None:
                return dest
        return a["room"]

    def auto_sleep(self, hour):
        """Models rarely think about where to sleep: lovers and the frightened often end up in a friend's room, the broken sometimes just collapse in a corridor."""
        w, s = self.world, self.s
        if not self.revealed:
            return
        for cid, a in w.agents.items():
            pref = a.get("sleep_pref")
            if pref and pref[0] == self.day:
                continue
            home = w.cast[cid]["home"]
            dest = None
            partner = next((b["b"] if b["a"] == cid else b["a"] for b in s.get("bonds", []) if cid in (b["a"], b["b"]) and b["kind"] == "romance"), None)
            if partner in w.agents and w.cast[partner]["home"] != home and self.rng.random() < 0.35:
                dest = w.cast[partner]["home"]
            elif a["sanity"] < 35:
                friends = [o for o in w.agents if o != cid and a["aff"].get(o, 0) >= 5 and w.cast[o]["home"] != home]
                if friends and self.rng.random() < 0.3:
                    dest = w.cast[max(friends, key=lambda o: a["aff"].get(o, 0))]["home"]
                elif a["sanity"] < 15 and self.rng.random() < 0.1:
                    dest = "landing"
            if dest:
                a["sleep_pref"] = [self.day, dest]
                self.note_use(cid, "sleep_in", "engine")

    def sleep_where(self, cid, room):
        home = self.world.cast[cid]["home"]
        if room == home:
            return "home"
        fl = ROOMS[room][1]
        if fl in ("grounds", "roof") or room in ("cold_store", "boiler_room", "wine_cellar", "basement_hall"):
            return "rough"
        return "other"

    def send_to_bed(self, tick, cid):
        w = self.world
        a = w.agents[cid]
        dest = self.bed_room(cid)
        start = a["room"]
        if a.get("out"):
            tick["moves"][cid] = {"from": start, "path": [start], "to": start}                 # the unconscious stay where they lie
            a["slept_where"] = "rough"
            return start
        if start != dest:
            steps = w.path(cid, start, dest)
            tick["moves"][cid] = {"from": start, "path": [start] + ([r for r, _, _ in steps] if steps else [dest]), "to": dest}
            a["room"] = dest
        else:
            tick["moves"][cid] = {"from": start, "path": [start], "to": dest}
        a["slept_where"] = self.sleep_where(cid, dest)
        return dest

    def auto_night_locks(self, tick, only_asleep=False):
        """People bolt their door for the night more the more afraid they are; the very frightened pile furniture against it too."""
        w, s = self.world, self.s
        by_room = {}
        for cid, a in w.agents.items():
            if only_asleep and not a.get("asleep"):
                continue
            by_room.setdefault(a["room"], []).append(cid)
        dread = self.dread_level()
        scared_house = bool(s.get("case") or s.get("bodies") or s.get("spree"))
        troubled = {v for h in s.get("hooks", []) if h["status"] == "open" for v in h["victims"]}
        for room, who in by_room.items():
            if not lockable(room) or room in s["locks"] or room in s["broken"] or self.scene_sealed(room):
                continue
            fear = max(0.15 + 0.07 * dread + (0.25 if scared_house else 0.0) + (0.2 if min(w.agents[c]["sanity"] for c in who) < 45 else 0.0)
                       + (0.15 if any(sum(w.agents[c]["aff"].values()) < 0 for c in who) else 0.0) + (0.25 if troubled & set(who) else 0.0), 0.0)
            if self.rng.random() < min(0.9, fear * self.tune("lock_fear")):
                locker = max(who, key=lambda c: -w.agents[c]["sanity"])
                s["locks"][room] = {"by": locker, "day": self.day}
                self.note_use(locker, "lock", "engine")
                self.log_event(tick, {"type": "door", "who": locker, "room": room, "vis": "viewer", "text": f"{self.nm(locker)} bolts the door of the {w.room_name(room)} for the night."})
                if fear > 0.65 and self.rng.random() < 0.3:
                    edges = [e for e in w.edges if room in (e["a"], e["b"]) and e["kind"] in ("door", "window") and not e["hidden"] and e["id"] not in s["blocks"]]
                    if len(edges) == 1:
                        e = edges[0]
                        s["blocks"][e["id"]] = {"by": locker, "inside": room, "prop": "furniture", "prop_name": "heavy furniture", "hp": 2, "day": self.day}
                        self.log_event(tick, {"type": "door", "who": locker, "room": room, "vis": "viewer", "text": f"{self.nm(locker)} drags a wardrobe in front of the door of the {w.room_name(room)}."})

    def restock_medicine(self, tick):
        """NeoVi also restocks the medicine shelves at the turn of the week."""
        s, w = self.s, self.world
        for room, items in (("bathroom", {"bandages": 3, "paracetamol": 1}), ("green_room", {"first_aid_kit": 1})):
            stock = s["room_items"].setdefault(room, {})
            for k, q in items.items():
                stock[k] = max(stock.get(k, 0), q)
        self.log_event(tick, {"type": "system", "who": "neovi", "room": "bathroom", "vis": "public", "text": "NeoVi quietly restocks the bandages and the first-aid kit."})

    def repair_doors(self, tick):
        """NeoVi mends every broken door at the turn of the week."""
        s, w = self.s, self.world
        broken = list(s.get("broken", []))
        if not broken:
            return
        s["broken"] = []
        self.env().repair_all()
        self.env_sync_nav()
        self.log_event(tick, {"type": "door", "who": "neovi", "room": "laundry", "vis": "public",
                              "text": "NeoVi spends the night mending the broken doors: " + ", ".join(w.room_name(r) for r in broken) + ". They are as good as new."})

    def sleep_lines(self, cid, hour):
        if not self.revealed or hour < 16:
            return []
        home = self.world.cast[cid]["home"]
        return [f"SLEEP: tonight you sleep wherever you choose (\"sleep_in\": a room id; if you say nothing it is your own room, the {self.world.room_name(home)}). Your own room is the safest and most restful "
                "(a bonus to sanity and health); anywhere else is worse for your rest, and the open air or a cold cellar is worst. You have to be able to get in: people lock their doors."]
