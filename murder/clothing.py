"""Clothes, wardrobes, swimsuits, disguises and bloodstains.

Everyone starts with their own clothes on them and spare copies (and a swimsuit) in the wardrobe of their bedroom. A character with no clothing in their inventory is in their underwear;
they can undress or change at will, wear a costume or clothes they find or craft, and will usually come back to their own. Clothes matter to the story: someone in another person's clothes
(or a mask or a cloak) can be mistaken for them by people who see them go by, a killer's clothes are stained and have to be changed and hidden (and are evidence if found), and a "be in your
underwear" rule can be checked in code. ClothingMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ITEMS, ROOMS
from .looks import OUTFITS, looks_of

OWN = {cid: (o[0], o[1]) for cid, o in OUTFITS.items()}
SWIM_ROOMS = {"pool", "beach", "boathouse"}


def _hh(h):
    return f"{int(h):02d}:00"


class ClothingMixin:
    # ------------------------------------------------------------------ the items
    def ensure_wardrobe(self):
        """Own clothes and a swimsuit exist as items for everyone; the clothes are on the person, spare copies and the swimsuit are in the bedroom wardrobe."""
        w, s = self.world, self.s
        for cid, c in w.cast.items():
            short = c.get("short") or c["name"].split()[0]
            clothes, swim = OWN.get(cid, ("everyday clothes", "swimwear"))
            fib, shape = (OUTFITS[cid][2], OUTFITS[cid][3]) if cid in OUTFITS else ([], [])
            s["custom_items"].setdefault(f"clothes_{cid}", {"name": f"{short}'s {clothes}", "tags": ["clothing", "own"], "owner": cid, "fibres": fib, "shape": shape})
            acc = looks_of(cid, c).get("accessory")
            if acc:
                s["custom_items"].setdefault(f"acc_{cid}", {"name": acc[0], "tags": ["accessory", "own"], "owner": cid, "fibres": [acc[1]] if acc[1] else []})
            s["custom_items"].setdefault(f"swimsuit_{cid}", {"name": f"{short}'s {swim}", "tags": ["clothing", "own", "swimwear"], "owner": cid})
        if s.get("belongings") is None:
            self.seed_belongings()
        for cid, a in w.agents.items():
            if not a.get("acc_done"):
                a["acc_done"] = True
                if f"acc_{cid}" in s["custom_items"]:
                    a["inv"].setdefault(f"acc_{cid}", 1)              # worn all the time (looks.py)
            if a.get("wardrobe_done"):
                continue
            a["wardrobe_done"] = True
            for legacy in ("outfit", "jacket"):
                a["inv"].pop(legacy, None)                         # the old catch-all 'outfit' and 'jacket' are now simply the character's own clothes
            a["inv"].setdefault(f"clothes_{cid}", 1)
            ward = s["belongings"].setdefault(cid, {})
            ward[f"clothes_{cid}"] = ward.get(f"clothes_{cid}", 0) + 2
            ward[f"swimsuit_{cid}"] = ward.get(f"swimsuit_{cid}", 0) + 1

    def tags(self, item):
        return set(self.world.item_spec(item).get("tags", []))

    def owner_of(self, item):
        return self.world.item_spec(item).get("owner")

    # ------------------------------------------------------------------ what someone is wearing
    def worn(self, cid):
        a = self.world.agents[cid]
        cl = [k for k, q in a["inv"].items() if q > 0 and "clothing" in self.tags(k)]
        if not cl:
            return None
        want = a.get("wearing", "auto")
        if want is None:
            return None                                          # undressed on purpose
        if want != "auto" and want in cl:
            return want
        own = f"clothes_{cid}"
        if own in cl:
            return own
        return ([k for k in cl if "stained" not in self.tags(k)] or cl)[0]

    def outfit_label(self, cid):
        k = self.worn(cid)
        return "their underwear" if k is None else self.world.item_name(k)

    def clothing_note(self, cid):
        """A short remark for what others see: nothing when someone is simply in their own clothes."""
        if cid not in self.world.agents:
            return ""
        k = self.worn(cid)
        if k is None:
            return " (in their underwear)"
        t = self.tags(k)
        if "swimwear" in t:
            return " (in swimwear)"
        if "stained" in t:
            return " (clothes visibly stained)"
        if "mask" in t:
            return " (wearing a mask)"
        if self.owner_of(k) not in (None, cid):
            return f" (wearing {self.nm(self.owner_of(k))}'s clothes)"
        if "costume" in t or "disguise" in t or self.owner_of(k) != cid:
            return f" (in {self.world.item_name(k).lower()})"
        return ""

    def wear(self, tick, cid, spec):
        """spec is an item id (carried, lying here, or in your own wardrobe) or 'none' for underwear."""
        w, s = self.world, self.s
        a = w.agents[cid]
        name = self.nm(cid)
        room = a["room"]
        here = [o for o in w.occupants(room) if o in w.agents and o != cid]
        if spec in ("none", "underwear", "nothing"):
            if self.worn(cid) is None:
                return False
            a["wearing"] = None
            self.log_event(tick, {"type": "clothes", "who": cid, "room": room, "vis": "public", "text": f"{name} strips down to their underwear."}, witnesses=here, actor=cid)
            return True
        if "clothing" not in self.tags(spec):
            return False
        if a["inv"].get(spec, 0) > 0 and self.worn(cid) == spec:
            return False                                       # already wearing it
        if a["inv"].get(spec, 0) <= 0:
            ward = (s.get("belongings") or {}).get(cid, {})
            if room == w.cast[cid]["home"] and ward.get(spec, 0) > 0 and w.carried(cid) < 30:
                ward[spec] -= 1
                if ward[spec] <= 0:
                    del ward[spec]
                a["inv"][spec] = a["inv"].get(spec, 0) + 1
            elif s["room_items"].get(room, {}).get(spec, 0) > 0:
                q, _ = w.take(cid, spec, 1)
                if not q:
                    return False
            else:
                return False
        a["wearing"] = spec
        t = self.tags(spec)
        own = self.owner_of(spec) == cid
        txt = (f"{name} puts on their swimsuit." if "swimwear" in t and own else f"{name} changes into their own clothes." if own
               else f"{name} changes into {w.item_name(spec).lower()}.")
        self.log_event(tick, {"type": "clothes", "who": cid, "room": room, "vis": "public", "text": txt}, witnesses=here, actor=cid)
        return True

    # ------------------------------------------------------------------ prompts
    def clothes_lines(self, cid):
        if not self.revealed:
            return []
        w, s = self.world, self.s
        a = w.agents[cid]
        k = self.worn(cid)
        ward = (s.get("belongings") or {}).get(cid, {})
        in_ward = [w.item_name(x) for x, q in ward.items() if "clothing" in self.tags(x)]
        now = ("only your underwear" if k is None else f"{w.item_name(k)}" + (" (your own)" if self.owner_of(k) == cid else " (not yours)"))
        line = f"CLOTHES: you are wearing {now}."
        if w.cast[cid]["home"] == a["room"] and in_ward:
            line += f" Your wardrobe here holds: {', '.join(in_ward)}."
        if self.lean or getattr(self, "short_docs", False):
            return [line]
        return [line + " You may change (\"wear\": an item id you carry, find here or keep in your wardrobe, or \"none\" for underwear). You feel most yourself in your own clothes; clothes you find or make "
                "are costumes. Someone else's clothes, a cloak or a mask can make people mistake you for someone else, and a killer's clothes are stained."]

    # ------------------------------------------------------------------ everyday behaviour
    def auto_clothes(self, tick, hour, decisions):
        """Morning dressing, swimsuits at the pool, a night in underwear, putting your own things back on, and a killer changing out of stained clothes."""
        w, s = self.world, self.s
        if not self.revealed:
            return
        rule = s.get("rule") if (s.get("rule") or {}).get("ai") else None
        for cid, a in list(w.agents.items()):
            if a.get("asleep"):
                continue
            home = a["room"] == w.cast[cid]["home"]
            k = self.worn(cid)
            stained = next((x for x in a["inv"] if "stained" in self.tags(x)), None)
            if stained:
                self.change_out_of_stain(tick, cid, stained)
                continue
            if rule and (rule.get("chk") or {}).get("state_check") == "underwear":
                if k is not None and self.rng.random() < 0.45:
                    self.wear(tick, cid, "none")
                continue
            if a["room"] in SWIM_ROOMS and 10 <= hour <= 18 and a["inv"].get(f"swimsuit_{cid}", 0) > 0 and (k is None or "swimwear" not in self.tags(k)) and self.rng.random() < 0.6:
                self.wear(tick, cid, f"swimsuit_{cid}")
                continue
            if k is None or (home and self.owner_of(k) != cid and self.rng.random() < 0.3) or (k and "swimwear" in self.tags(k) and a["room"] not in SWIM_ROOMS and home):
                if home or a["inv"].get(f"clothes_{cid}", 0) > 0:
                    self.wear(tick, cid, f"clothes_{cid}")
            plot = s.get("plots", {}).get(cid)
            if plot and plot.get("stage") == "striking" and self.rng.random() < 0.5:
                other = next((x for x in a["inv"] if "clothing" in self.tags(x) and self.owner_of(x) not in (None, cid)), None)
                if other and self.worn(cid) != other:
                    self.wear(tick, cid, other)

    def stain_clothes(self, cid):
        """A killer's clothes are stained by what they have done; the stained garment is a distinct item that carries its owner's label."""
        w, s = self.world, self.s
        base = self.worn(cid)
        if not base or "stained" in self.tags(base):
            return
        a = w.agents[cid]
        spec = w.item_spec(base)
        sid = f"stained_{base}"
        s["custom_items"].setdefault(sid, {"name": f"bloodstained {spec['name']}", "tags": ["clothing", "stained"], "owner": spec.get("owner")})
        a["inv"][base] -= 1
        if a["inv"][base] <= 0:
            del a["inv"][base]
        a["inv"][sid] = a["inv"].get(sid, 0) + 1
        a["wearing"] = sid

    def change_out_of_stain(self, tick, cid, stained):
        """The killer gets out of the stained clothes if they can and hides them (stash if there is cover, otherwise dropped in the laundry or the room)."""
        w, s = self.world, self.s
        a = w.agents[cid]
        if self.rng.random() > 0.6:
            return
        clean = next((x for x in a["inv"] if "clothing" in self.tags(x) and "stained" not in self.tags(x)), None)
        if not clean and a["room"] == w.cast[cid]["home"] and (s.get("belongings") or {}).get(cid, {}).get(f"clothes_{cid}", 0) > 0:
            clean = f"clothes_{cid}"
        if clean:
            self.wear(tick, cid, clean)
        else:
            a["wearing"] = None
        from .stealth import COVER
        if COVER.get(a["room"]) and self.rng.random() < 0.7:
            self.do_stash(tick, cid, {"stash": {"item": stained, "spot": "", "qty": 1}, "_src": "engine"})
        else:
            w.drop(cid, stained, 1)
        self.note_use(cid, "change_clothes", "engine")

    def label_text(self, k, owner):
        """What can still be read of the label in a garment: the whole name, only an initial (and three people on this island share the same one), or nothing at all because it was cut out.
        Each stained garment is fixed once so everybody who finds it reads the same thing. The dial `clue_clarity` shifts the odds."""
        if owner not in self.world.cast:
            return ""
        memo = self.s.setdefault("label_memo", {})
        if k not in memo:
            clar = self.tune("clue_clarity")
            r = self.rng.random()
            full = min(0.85, 0.30 * clar)
            memo[k] = "full" if r < full else "initial" if r < full + 0.45 else "cut"
            del_keys = list(memo)[:-30]
            for d in del_keys:
                memo.pop(d, None)
        how = memo[k]
        if how == "full":
            return f" The label inside reads {self.nm(owner)}."
        if how == "initial":
            return f" The laundry tag inside is faded: it shows only the initial '{self.nm(owner)[0]}'."
        return " Whoever wore it had cut the label out."

    def found_stained(self, tick, finder, items, where):
        """Stained clothes turn up: evidence, and the label inside names whose they were."""
        w, s = self.world, self.s
        case = s.get("case")
        for k in items:
            if "stained" not in self.tags(k) or not case:
                continue
            owner = self.owner_of(k)
            text = f"{w.item_name(k).capitalize()} found {where}." + self.label_text(k, owner)
            if any(c.get("kind") == "stained" and c["text"] == text for c in case["clues"]):
                continue
            case["clues"].append({"room": case.get("room"), "scene": False, "found_by": [finder], "kind": "stained", "text": text})
            self.note_evidence(finder, "clue", text)
            w.remember(finder, f"{_hh(tick['hour'])} CLUE: {text}")

    # ------------------------------------------------------------------ being seen
    def perceived_identity(self, observer, subject):
        """Who the observer thinks they saw: the person, someone else (their clothes), or nobody (a mask)."""
        w = self.world
        if subject not in w.agents:
            return subject
        k = self.worn(subject)
        if not k:
            return subject
        t = self.tags(k)
        if "mask" in t:
            return None
        if "disguise" in t and self.rng.random() < 0.6:
            return None
        owner = self.owner_of(k)
        if owner and owner != subject and owner in w.cast and self.rng.random() < max(0.15, 0.7 - 0.5 * self.sharpness(observer)):
            return owner
        return subject

    def clothes_clue(self, case):
        """What witnesses recall of how the killer looked, when it was not their own clothes."""
        w = self.world
        culprit, room = case.get("killer"), case.get("room")
        if culprit not in w.agents:
            return []
        k = self.worn(culprit)
        if not k:
            return []
        t = self.tags(k)
        owner = self.owner_of(k)
        if "mask" in t:
            return [{"room": room, "scene": True, "found_by": [], "kind": "clothes_seen", "text": f"Someone in a mask was glimpsed near the {w.room_name(room)} around the time."}]
        if owner and owner != culprit and owner in w.cast:
            return [{"room": room, "scene": True, "found_by": [], "kind": "clothes_seen", "text": f"Someone in {self.nm(owner)}'s clothes was seen near the {w.room_name(room)} around the time."}]
        return []
