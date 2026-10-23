"""Items that actually do something.

Light (flashlight, headlamp, oil lantern, torch) lets people see in a blackout, and burns down. Binoculars and telescopes let someone watch a distant outdoor place. A magnifying glass
finds the fine clues others miss. Handcuffs restrain. A tape recorder hidden in a room records what is said there. Charts, a sextant, a radio manual or a signalling mirror help the escape
attempts they belong to. Mouse traps make a snare. Knocking at a locked door gets an answer (or a reason for being turned away).
ItemUseMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS

OPTICS = ("binoculars", "small_telescope", "brass_telescope")
FINE_KINDS = {"fibres", "hair", "door_picked", "smell", "footprints"}
NAV_ITEMS = ("old_map", "star_charts", "sextant", "binoculars", "brass_telescope")
RADIO_ITEMS = ("radio_manual", "rigged_radio", "signal_mirror", "handheld")
NAV_WORDS = ("raft", "sail", "sea", "navigat", "current", "tide", "star", "chart", "map", "boat")
RADIO_WORDS = ("radio", "transmit", "signal", "message", "broadcast", "frequency", "antenna", "lamp", "mirror")
BINDERS = ("string", "wire", "masking_tape", "duct_tape")
RESTRAIN_TURNS = 8


def _hh(h):
    return f"{int(h):02d}:00"


class ItemUseMixin:
    def has(self, cid, item):
        return self.world.agents[cid]["inv"].get(item, 0) > 0

    # ------------------------------------------------------------------ light
    def light_source(self, cid):
        a = self.world.agents[cid]
        inv = a["inv"]
        for k in ("flashlight", "headlamp"):
            if inv.get(k, 0) > 0:
                return k
        if inv.get("torch", 0) > 0:
            return "torch"
        if inv.get("oil_lantern", 0) > 0 and (a.get("lantern_ticks", 0) > 0 or inv.get("lamp_oil", 0) > 0 or inv.get("cooking_oil", 0) > 0):
            return "oil_lantern"
        return None

    def light_tick(self):
        """In a blackout everyone with a working light is lit; torches burn down and lanterns use oil."""
        w = self.world
        dark = self.blackout_until >= self.idx
        for cid, a in w.agents.items():
            a["lit"] = False
        if not dark:
            return
        for cid, a in w.agents.items():
            src = self.light_source(cid)
            if src == "torch":
                a["torch_left"] = a.get("torch_left", 6) - 1
                if a["torch_left"] <= 0:
                    a["inv"]["torch"] -= 1
                    if a["inv"]["torch"] <= 0:
                        del a["inv"]["torch"]
                    a["torch_left"] = 6
                    w.remember(cid, f"{_hh(self.s.get('_hour', 12))} Your torch gutters and goes out.")
            elif src == "oil_lantern":
                if a.get("lantern_ticks", 0) <= 0:
                    fuel = "lamp_oil" if a["inv"].get("lamp_oil", 0) > 0 else "cooking_oil"
                    a["inv"][fuel] -= 1
                    if a["inv"][fuel] <= 0:
                        del a["inv"][fuel]
                    a["lantern_ticks"] = 3
                a["lantern_ticks"] -= 1
            a["lit"] = src is not None

    def in_dark(self, cid):
        """Blind in a blackout: the power is out and this person has no light."""
        a = self.world.agents.get(cid)
        return self.blind(cid) or (self.blackout_until >= self.idx and not (a or {}).get("lit"))

    # ------------------------------------------------------------------ optics
    def has_optics(self, cid):
        return not self.blind(cid) and any(self.has(cid, k) for k in OPTICS)

    def far_spy_ok(self, cid, tgt):
        w = self.world
        here = w.agents[cid]["room"]
        return self.has_optics(cid) and ROOMS[here][1] in ("grounds", "roof") and ROOMS[tgt][1] in ("grounds", "roof") and here != tgt

    def far_look(self, tick, cid, tgt):
        if self.blind(cid):
            return
        w = self.world
        seen = [o for o in w.occupants(tgt, include_npcs=False) if o in w.agents and o != cid]
        if not seen:
            w.remember(cid, f"{_hh(tick['hour'])} (through the lens) The {w.room_name(tgt)} is empty.")
            return
        for o in seen:
            if self.rng.random() < 0.85:
                w.remember(cid, f"{_hh(tick['hour'])} (through the lens) You see {self.nm(o)} in the {w.room_name(tgt)}: {w.agents[o]['activity'][:70]}.")

    # ------------------------------------------------------------------ magnifying glass
    def fine_visible(self, cid, clue):
        if self.blind(cid):
            return False
        if clue.get("kind") not in FINE_KINDS:
            return True
        return self.has(cid, "magnifying_glass") or self.rng.random() < 0.5 * self.sharpness(cid)

    # ------------------------------------------------------------------ handcuffs
    def restrained(self, cid):
        a = self.world.agents.get(cid)
        r = (a or {}).get("restrained")
        if r and (not r.get("abs") or self.abs_now() >= r["until"]):
            a.pop("restrained", None)
            self.world.remember(cid, f"{_hh(self.s.get('_hour', 12))} (private) You work the cuffs loose at last.")
            return None
        return r

    def do_restrain(self, tick, cid, d):
        w = self.world
        a = w.agents[cid]
        t = d.get("target")
        if not self.has(cid, "handcuffs") or t not in w.agents or t == cid or w.agents[t]["room"] != a["room"] or w.agents[t].get("restrained"):
            return
        ta = w.agents[t]
        willing = ta["aff"].get(cid, 0) >= 6 and ta["sanity"] > 50
        p = 0.2 + (0.6 if ta.get("asleep") else 0) + (0.3 if ta["hp"] < 40 else 0) + (0.5 if willing else 0) + 0.2 * (self.sharpness(cid) - 0.4)
        good, _ = self.roll(cid, min(0.95, p))
        name, tname = self.nm(cid), self.nm(t)
        here = [o for o in w.occupants(a["room"]) if o not in (cid, t)]
        if good:
            a["inv"]["handcuffs"] -= 1
            if a["inv"]["handcuffs"] <= 0:
                del a["inv"]["handcuffs"]
            ta["restrained"] = {"by": cid, "abs": True, "until": self.abs_now() + RESTRAIN_TURNS * max(1, self.step)}
            ta["asleep"] = False
            self.log_event(tick, {"type": "restrain", "who": cid, "room": a["room"], "vis": "public", "text": f"{name} snaps handcuffs on {tname}."}, witnesses=here + [t], actor=cid)
            w.remember(t, f"{_hh(tick['hour'])} (private) {name} cuffed you. You cannot go anywhere until someone lets you out.")
            self.add_tie(t, cid, "wronged", f"{name} put handcuffs on them", -2)
            self.stat(tick, t, "sanity", -4, "being cuffed")
        else:
            self.log_event(tick, {"type": "restrain", "who": cid, "room": a["room"], "vis": "public", "text": f"{name} tries to cuff {tname} and {tname} twists away."}, witnesses=here + [t], actor=cid)
            self.adjust_any_aff(t, cid, -2)

    def do_free(self, tick, cid, d):
        w = self.world
        a = w.agents[cid]
        t = d.get("target") or cid
        if t not in w.agents or w.agents[t]["room"] != a["room"] or not w.agents[t].get("restrained"):
            return
        r = w.agents[t]["restrained"]
        if t == cid:
            tool = self.pick_tool(cid)
            p = (tool[0] * 0.6 if tool else 0.1)
        else:
            tool = self.pick_tool(cid)
            p = 0.9 if (r["by"] == cid or w.has_room_key(cid, a["room"]) and self.has(cid, "master_key")) else (tool[0] * 0.8 if tool else 0.0)
        if self.rng.random() < p:
            w.agents[t].pop("restrained", None)
            w.agents[t].pop("gagged", None)                         # free hands: the gag comes off too
            a["inv"]["handcuffs"] = a["inv"].get("handcuffs", 0) + 1
            self.log_event(tick, {"type": "restrain", "who": cid, "room": a["room"], "vis": "public",
                                  "text": f"{self.nm(cid)} gets {'themselves' if t == cid else self.nm(t)} out of the handcuffs."}, witnesses=[o for o in w.occupants(a["room"]) if o != cid], actor=cid)
            if t != cid:
                self.add_tie(t, cid, "helped", f"{self.nm(cid)} got them out of handcuffs", 2)

    # ------------------------------------------------------------------ tape recorder
    def tape_record(self, room, lines):
        for st in self.s.get("stash", []):
            if st["room"] == room and "tape_recorder" in st["items"]:
                tape = st.setdefault("tape", [])
                for ln in lines:
                    tape.append(f"{self.nm(ln['speaker'])}: {ln['text'][:90]}" if ln["kind"] == "say" else f"({self.nm(ln['speaker'])} {ln['text'][:60]})")
                del tape[:-12]

    def play_tape(self, tick, cid, st):
        tape = st.get("tape") or []
        w = self.world
        if "tape_recorder" not in st["items"] or not tape:
            return
        w.remember(cid, f"{_hh(tick['hour'])} You play the tape from the {w.room_name(st['room'])}: " + " | ".join(tape[-6:]))
        for ln in tape[-4:]:
            self.note_evidence(cid, "testimony", f"(tape from the {w.room_name(st['room'])}) {ln}", None)
        w.agents[cid]["footage"] = self.day
        self.tally(cid, "tapes")

    # ------------------------------------------------------------------ escape attempts
    def experiment_item_bonus(self, cid, idea):
        """Items that belong to the attempt make it likelier to work: charts for a raft, a manual for a radio."""
        w, s = self.world, self.s
        a = w.agents[cid]
        text = (idea or "").lower()
        here = set(a["inv"]) | set(s["room_items"].get(a["room"], {}))
        used, bonus = [], 0.0
        if any(k in text for k in NAV_WORDS):
            used += [k for k in NAV_ITEMS if k in here]
        if any(k in text for k in RADIO_WORDS):
            used += [k for k in RADIO_ITEMS if k in here]
        for k in used[:3]:
            bonus += 0.07
        return min(0.2, bonus), [w.item_name(k).lower() for k in used[:3]]

    # ------------------------------------------------------------------ knocking
    def do_knock(self, tick, cid, d):
        w, s = self.world, self.s
        a = w.agents[cid]
        target = d.get("door")
        blk = self.door_block(cid, target) if target else None
        if not blk or blk[0] != "lock":
            return
        inside = [o for o in w.occupants(target, include_npcs=False) if o in w.agents and not w.agents[o].get("asleep")]
        name = self.nm(cid)
        if not inside:
            w.remember(cid, f"{_hh(tick['hour'])} You knock at the {w.room_name(target)}. Nobody answers.")
            return
        opener = max(inside, key=lambda o: w.agents[o]["aff"].get(cid, 0))
        aff = w.agents[opener]["aff"].get(cid, 0)
        p = 0.25 + 0.07 * aff - (0.2 if w.agents[opener]["sanity"] < 40 else 0) - (0.25 if s.get("case") or s.get("spree") else 0)
        if self.rng.random() < max(0.02, min(0.95, p)):
            del s["locks"][target]
            self.log_event(tick, {"type": "door", "who": opener, "room": target, "vis": "public", "text": f"{self.nm(opener)} lets {name} into the {w.room_name(target)}."},
                           witnesses=[o for o in inside if o != opener], actor=opener)
            before = a["room"]
            mv = w.move(cid, target, 40 * self.step)
            if a["room"] != before:
                tick["moves"][cid] = {"from": before, "path": mv["path"], "to": a["room"]}
        else:
            reason = ("not tonight" if w.agents[opener]["sanity"] >= 40 else "they are too frightened to open up") if not (s.get("case") or s.get("spree")) else "nobody is opening doors with a killer about"
            w.remember(cid, f"{_hh(tick['hour'])} You knock at the {w.room_name(target)} and {self.nm(opener)} answers through the door: {reason}.")
            w.remember(opener, f"{_hh(tick['hour'])} {name} knocked; you did not open ({reason}).")
            self.add_tie(cid, opener, "slighted", f"{self.nm(opener)} would not open the door", 0)

    # ------------------------------------------------------------------ the snare
    def snare_ready(self, cid):
        a = self.world.agents[cid]["inv"]
        return a.get("mouse_traps", 0) > 0 and any(a.get(b, 0) > 0 for b in BINDERS)

    def itemuse_acts(self, cid):
        if not self.revealed:
            return ""
        w = self.world
        a = w.agents[cid]
        acts = ""
        here = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid]
        if self.has(cid, "handcuffs") and here:
            acts += "|restrain"
        if a.get("restrained") or any(w.agents[o].get("restrained") for o in here):
            acts += "|free"
        if any(self.door_block(cid, n["room"]) and self.door_block(cid, n["room"])[0] == "lock" for n in w.adjacent(cid, a["room"]) if n["kind"] in ("door", "window")):
            acts += "|knock"
        return acts
