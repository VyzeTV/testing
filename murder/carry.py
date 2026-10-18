"""Hands, pockets and what items can do.

Every item gets a short capability record (`item_caps`): what it can do (cut, bludgeon, poison, bind, light, open, climb with, burn), its size
(small things fit a pocket; medium things are held or hidden under clothes; large things need both hands and cannot be hidden), the traces it
leaves (blood, marks, noise) and whether it burns or breaks. It is derived from the item's tags, with sizes set by name, so the planner and the
fight can reason about any of the house's items without a hand-written entry for each.

What someone holds is visible: a person seen with a large or unhidden weapon is believed to have it (a `has` belief, "seen with a crowbar").
Small things ride in a pocket and stay hidden until a search. A large item takes both hands: carrying a person means putting it down first.
Drawing a weapon that was hidden (pocketed or under clothes) costs the first moment of a fight, so the target sees it coming. Whoever is knocked
out or falls drops what they were holding. CarryMixin is mixed into DayRunner (engine.py).
"""

SMALL = {"letter_opener", "pen_knife", "scissors", "razor_blades", "palette_knife", "darts", "corkscrew", "skewers", "sewing_needles", "craft_knife",
         "ice_pick", "steak_knife", "key", "matches", "lighter", "pills", "sleeping_pills", "vial", "syringe", "rope_short", "whistle", "flashlight", "candle"}
LARGE = {"sledgehammer", "harpoon", "coal_shovel", "baseball_bat", "guitar", "rapier", "pruning_saw", "diving_weight", "driftwood", "candelabra", "crowbar",
         "fire_poker", "pipe_wrench", "brass_telescope", "reading_lamp", "meat_hook", "ladder", "fire_extinguisher", "axe", "oar"}
DOES = {"sharp": "cut", "blunt": "bludgeon", "poison": "poison", "drug": "poison", "restraint": "bind", "light": "light", "fire": "burn", "flammable": "burn",
        "key": "open", "tool": "open"}


class CarryMixin:
    def item_caps(self, item):
        """{"does": [...], "size": small|medium|large, "traces": [...], "breaks": bool, "burns": bool} for any item."""
        cache = self.__dict__.setdefault("_caps", {})
        if item in cache:
            return cache[item]
        tags = set(self.world.item_spec(item).get("tags", []))
        does = sorted({v for k, v in DOES.items() if k in tags} | ({"climb"} if "rope" in item or "ladder" in item else set()))
        if item in LARGE or "large" in tags:
            size = "large"
        elif item in SMALL or tags & {"poison", "drug", "key", "medical", "document", "notebook"} or ("sharp" in tags and "knife" in item and "kitchen" not in item and item != "cleaver"):
            size = "small"
        elif tags & {"weapon", "tool", "gear", "instrument", "gadget"}:
            size = "medium"
        else:
            size = "small"
        traces = sorted(({"blood"} if tags & {"sharp", "blunt"} else set()) | ({"marks"} if "blunt" in tags or "tool" in tags else set())
                        | ({"noise"} if size == "large" and "blunt" in tags else set()))
        cache[item] = {"does": does, "size": size, "traces": traces, "breaks": bool(tags & {"glass"}), "burns": bool(tags & {"flammable", "paper", "document", "clothing"})}
        return cache[item]

    def held_items(self, cid):
        """What anyone looking can see in `cid`'s hands: large items, and weapons they are not hiding."""
        a = self.world.agents.get(cid) or {}
        hidden = a.get("concealed") or {}
        out = []
        for k, q in sorted(a.get("inv", {}).items()):
            if q <= 0:
                continue
            caps = self.item_caps(k)
            if caps["size"] == "large" or (caps["size"] == "medium" and k not in hidden and {"cut", "bludgeon"} & set(caps["does"])):
                out.append(k)
        return out

    def pocketed(self, cid):
        a = self.world.agents.get(cid) or {}
        return [k for k, q in sorted(a.get("inv", {}).items()) if q > 0 and self.item_caps(k)["size"] == "small"]

    def hands_free(self, cid):
        """Hands left free: a large item takes both, anything else in the hands one."""
        held = self.held_items(cid)
        if any(self.item_caps(k)["size"] == "large" for k in held):
            return 0
        return max(0, 2 - len(held))

    def must_draw(self, cid, weapon):
        """A weapon that is not in the hand (pocketed or hidden) has to be drawn first."""
        return bool(weapon) and weapon not in self.held_items(cid)

    def drop_held(self, tick, cid, why):
        """Knocked out or falling: whatever was in their hands falls to the floor."""
        w = self.world
        a = w.agents.get(cid)
        if not a:
            return []
        out = []
        for k in self.held_items(cid):
            q, _ = w.drop(cid, k, 1)
            if q:
                out.append(k)
        if out:
            self.log_event(tick, {"type": "drop", "who": cid, "room": a["room"], "vis": "public",
                                  "text": f"{self.nm(cid)} drops the {', '.join(w.item_name(k) for k in out)} ({why})."}, witnesses=[o for o in w.occupants(a["room"]) if o != cid], actor=cid)
        return out

    def seen_holding(self, observer, subject, t):
        """`observer` saw `subject` holding something worth remembering: a weapon in the hand becomes a belief."""
        for k in self.held_items(subject):
            if {"cut", "bludgeon"} & set(self.item_caps(k)["does"]):
                self.believe(observer, {"k": "has", "s": subject, "o": k, "n": f"{self.nm(subject)} was carrying a {self.world.item_name(k)}", "src": "seen", "c": 0.85, "t0": t, "true": True})
