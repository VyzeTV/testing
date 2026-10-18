"""Hurting without killing, and what can be done to someone who cannot fight back.

Blows, cuts, falls and fire now leave injuries (broken bones, bleeding, concussion, burns, lost fingers or limbs); a blow can knock someone out. There is a deliberate non-lethal attack
(knockout: a blow, a choke or a spiked drink) with a small risk that it kills. A helpless person (knocked out, fainted, drugged, restrained) can be carried to another room, searched, robbed,
stripped, locked in a room, or placed beside a body with the murder weapon in their hand so that they take the blame. NonlethalMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS

SEVERE_TAGS = {"sharp"}
CHOPPERS = {"hatchet", "fire_axe", "cleaver", "pruning_saw", "rusty_saw", "hacksaw", "meat_hook"}


def _hh(h):
    return f"{int(h):02d}:00"


class NonlethalMixin:
    def sevmul(self):
        return self.tune("injury_severity")

    # ------------------------------------------------------------------ injuries
    def injure(self, tick, cid, by, tags, dmg, kind="blow", weapon=None):
        """What a blow, a fall or a flame does to a body besides taking health."""
        w = self.world
        if cid not in w.agents:
            return []
        m = self.sevmul()
        r = self.rng.random
        got = []
        hard = dmg >= 14
        why = f"hit by {self.nm(by)}" if by in w.agents else kind

        def give(cond, sev=1, body=None, p=1.0):
            if r() < p * m:
                if self.add_cond(tick, cid, cond, sev, why, body, by=by if by in w.agents else None):
                    got.append(cond)
        if kind == "fall":
            give("broken_leg", 1, "leg", 0.18 if hard else 0.05)
            give("broken_arm", 1, "arm", 0.15 if hard else 0.04)
            give("concussion", 1, None, 0.15 if hard else 0.05)
            give("whiplash", 1, None, 0.12)
            give("bleeding", 1 + dmg // 15, None, 0.15)
        elif kind == "fire":
            give("burned", 1 + dmg // 12, None, 0.8)
            give("breathless", 1, None, 0.35)
            give("blinded", 1, None, 0.15)
        elif kind == "blade":
            give("bleeding", 1 + dmg // 12, None, 0.7)
            give("lost_fingers", 1, None, 0.03)
        elif "sharp" in tags:
            give("bleeding", 1 + (dmg // 12), None, 0.8 if hard else 0.5)
            if weapon in CHOPPERS:
                give("lost_hand", 1, "hand", 0.04)
                give("lost_fingers", 1, None, 0.06)
                give("lost_eye", 1, None, 0.015)
            else:
                give("lost_eye", 1, None, 0.01)
        elif "blunt" in tags:
            give("concussion", 1 + (1 if dmg >= 18 else 0), None, 0.3 if hard else 0.12)
            give("broken_arm", 1, "arm", 0.1 if hard else 0.03)
            give("broken_leg", 1, "leg", 0.07 if hard else 0.02)
            give("whiplash", 1, None, 0.15)
            give("bleeding", 1, None, 0.2 if hard else 0.05)
        else:
            give("whiplash", 1, None, 0.12)
            give("weak", 1, None, 0.08)
            give("concussion", 1, None, 0.08 if hard else 0.03)
            give("broken_arm", 1, "arm", 0.04)
            give("bleeding", 1, None, 0.05)
        return got

    def maybe_ko(self, tick, attacker, target, tags, dmg):
        """A heavy blow, or a beating on someone already hurt, can knock them out."""
        w = self.world
        if target not in w.agents or w.agents[target].get("out"):
            return False
        v = w.agents[target]
        p = 0.04 + (0.2 if "blunt" in tags else 0.0) + (0.25 if v["hp"] < 35 else 0.0) + (0.06 if dmg >= 18 else 0.0)
        if self.rng.random() < p * self.sevmul() * self.tune("faint_rate"):
            return self.knock_out(tick, target, "knocked out", 2, by=attacker)
        return False

    # ------------------------------------------------------------------ the deliberate non-lethal attack
    def do_knockout(self, tick, cid, d):
        w, s = self.world, self.s
        a = w.agents[cid]
        t = d.get("target")
        if t not in w.agents or t == cid or w.agents[t]["room"] != a["room"] or w.agents[t].get("out"):
            return
        ta = w.agents[t]
        method = (d.get("method") or "hands").lower()
        name, tname = self.nm(cid), self.nm(t)
        room = a["room"]
        here = [o for o in w.occupants(room) if o not in (cid, t)]
        unaware = bool(ta.get("asleep") or ta.get("hiding") or ta["aff"].get(cid, 0) >= 3 or ta.get("restrained"))
        sed = method if a["inv"].get(method, 0) > 0 and method in ("sleeping_pills", "drugged_drink") else None
        weapon = method if a["inv"].get(method, 0) > 0 and "weapon" in w.item_spec(method).get("tags", []) and "blunt" in w.item_spec(method).get("tags", []) else None
        if sed:
            p = 0.75 if unaware else 0.3
            a["inv"][sed] -= 1
            if a["inv"][sed] <= 0:
                del a["inv"][sed]
            if self.rng.random() < p:
                self.knock_out(tick, t, "drugged", 3, by=cid, quiet=True)
                self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "viewer", "text": f"{name} slips {tname} something in a drink and {tname} slumps, out cold."}, actor=cid)
                self.hook_note_knockout(tick, cid, t)
            else:
                w.remember(t, f"{_hh(tick['hour'])} Your drink tasted wrong, and you left it. {name} was watching.")
                self.add_tie(t, cid, "wronged", f"{name} tried to give them something in a drink", -3)
            return
        if method == "choke":
            base, risk, how = 0.5, 0.1, "chokes"
        elif weapon:
            base, risk, how = 0.55, 0.05, f"cracks {tname} over the head with the {w.item_name(weapon)}"
        else:
            base, risk, how = 0.35, 0.02, "strikes"
        p = base + (0.3 if unaware else 0.0) + (0.2 if ta["hp"] < 40 else 0.0) - 0.25 * self.sharpness(t) * (0 if unaware else 1) - self.attack_penalty(cid)
        good, _ = self.roll(cid, max(0.1, min(0.95, p)))
        if good:
            self.knock_out(tick, t, "choked out" if method == "choke" else "knocked out", 2, by=cid, quiet=True)
            self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "public",
                                  "text": f"{name} {how if method != 'hands' else 'knocks ' + tname + ' out cold'}{'' if method != 'choke' else ' ' + tname + ' until they go limp'}."}, witnesses=here, actor=cid)
            tags = set(w.item_spec(weapon).get("tags", [])) if weapon else {"hands"}
            self.injure(tick, t, cid, tags, 12, "blow", weapon)
            gag = self.gag_item(cid)
            if gag:                                                       # gagged while out: they will not be calling for help (combat.py)
                ta["gagged"] = {"with": gag, "day": self.day, "by": cid}
                w.agents[cid]["inv"][gag] -= 1
                if w.agents[cid]["inv"][gag] <= 0:
                    del w.agents[cid]["inv"][gag]
                self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "public", "text": f"{name} gags {tname} with the {w.item_name(gag)}."}, witnesses=here, actor=cid)
            if self.rng.random() < risk * self.sevmul() and not s.get("case") and self.lethal_blow(tick, cid, t, weapon, tick["hour"]):
                return
            self.hook_note_knockout(tick, cid, t)
        else:
            self.log_event(tick, {"type": "assault", "who": cid, "room": room, "vis": "public", "text": f"{name} lunges at {tname} to knock them out, and {tname} fights them off."}, witnesses=here + [t], actor=cid)
            self.adjust_any_aff(t, cid, -4)
            self.stat(tick, t, "hp", -self.rng.randint(4, 9), f"a failed attack by {name}")
            w.remember(t, f"{_hh(tick['hour'])} (private) {name} tried to knock you out.")
        self.tally(cid, "knockouts")

    def hook_note_knockout(self, tick, culprit, victim):
        """Whoever was knocked out knows something happened to them; the culprit's name is not given."""
        w = self.world
        w.remember(culprit, f"{_hh(tick['hour'])} (private) {self.nm(victim)} is out cold at your feet.")
        self.s.setdefault("knockouts", []).append({"by": culprit, "victim": victim, "room": w.agents[victim]["room"], "day": self.day, "hour": tick["hour"]})
        del self.s["knockouts"][:-12]

    # ------------------------------------------------------------------ moving the helpless
    def can_carry(self, cid, t):
        w = self.world
        a, ta = w.agents[cid], w.agents[t]
        return (ta.get("out") or ta.get("restrained") or ta["hp"] < 25) and a["hp"] > 25 and w.carried(cid) <= self.carry_cap(cid)

    def do_carry(self, tick, cid, d):
        """Handled with the carrier's own movement (see apply_decision); this logs it."""
        w = self.world
        a = w.agents[cid]
        t = d.get("target")
        start = d.get("_carry_start")
        if t not in w.agents or not start or a["room"] == start or w.agents[t]["room"] != start or not self.can_carry(cid, t):
            return
        if self.hands_free(cid) < 2:
            for k in self.held_items(cid):
                w.drop(cid, k, 1, )                                  # both hands are needed to drag someone (carry.py)
        ta = w.agents[t]
        ta["room"] = a["room"]
        self.s.setdefault("drags", []).append({"from": start, "to": a["room"], "by": cid, "victim": t, "day": self.day, "hour": tick["hour"]})
        del self.s["drags"][:-12]
        self.stat(tick, cid, "hp", -1, "dragging someone")
        self.env_drag_marks(start, cid, t)
        tick["moves"][t] = {"from": start, "path": [start, a["room"]], "to": a["room"]}
        here = [o for o in w.occupants(start) if o not in (cid, t)] + [o for o in w.occupants(a["room"]) if o not in (cid, t)]
        self.log_event(tick, {"type": "carry", "who": cid, "room": a["room"], "vis": "public", "text": f"{self.nm(cid)} drags {self.nm(t)} into the {w.room_name(a['room'])}."}, witnesses=here, actor=cid)

    def do_rob(self, tick, cid, d):
        """Go through the pockets of someone who cannot stop you: take what they carry, or strip them of their clothes."""
        w = self.world
        a = w.agents[cid]
        t = d.get("target")
        if t not in w.agents or t == cid or w.agents[t]["room"] != a["room"]:
            return
        ta = w.agents[t]
        if not (ta.get("out") or ta.get("restrained") or ta.get("asleep")):
            return
        want = d.get("item") or ""
        took = []
        if want == "clothes":
            pool = [k for k in ta["inv"] if "clothing" in self.tags(k)]
        elif want and ta["inv"].get(want, 0) > 0:
            pool = [want]
        else:
            pool = [k for k in ta["inv"] if not self.tags(k) & {"clothing", "accessory"}]
        for k in pool[:6]:
            if w.carried(cid) >= self.carry_cap(cid):
                break
            q = ta["inv"].pop(k, 0)
            if q:
                a["inv"][k] = a["inv"].get(k, 0) + q
                self.note_holder(cid, k, tick["hour"])
                took.append(w.item_name(k))
                self.record_disturbance(tick, "stolen", cid, a["room"], [t], neat=True, taken=k)
        if want == "clothes":
            ta["wearing"] = "auto"
        if took and ta.get("out"):
            ta["robbed_by"] = cid
        if took:
            self.log_event(tick, {"type": "rob", "who": cid, "room": a["room"], "vis": "viewer", "text": f"{self.nm(cid)} takes {', '.join(took[:4])} from {self.nm(t)}, who does not stir."}, actor=cid)
            w.remember(cid, f"{_hh(tick['hour'])} (private) You took {', '.join(took[:4])} from {self.nm(t)}.")
            self.tally(cid, "robberies")

    def condition_death(self, tick, cid, cond, rec):
        """A wound or illness finishes someone. If another person made the wound, they are the culprit; otherwise it is an accident. Either way the body tells a story."""
        w, s = self.world, self.s
        a = w.agents[cid]
        by = rec.get("by")
        cause = {"bleeding": "bled to death", "infected": "died of an infected wound", "burned": "died of their burns"}.get(cond, "died of their injuries")
        hour = tick.get("hour", 12)
        since = (self.day - rec["day"]) * 24 + hour - rec.get("hour", hour)
        origin = rec.get("room")
        if by in w.agents and by != cid:
            case = self.open_case(tick, "manslaughter", cid, culprit=by, wkind="sharp" if cond != "burned" else "fire", weapon=None, room=a["room"], hour=hour, witnesses=[],
                                  cause=cause, detail=f"{self.nm(cid)} {cause}, from a wound {self.nm(by)} had given them")
        else:
            self.accident_death(tick, cid, cause, detail=f"{self.nm(cid)} {cause}")
            case = s.get("case")
        if not case:
            return
        case["clues"].append({"room": a["room"], "scene": True, "found_by": [], "kind": "wound_age", "text":
                              f"{self.nm(cid)} {cause}. The wound was about {max(1, since)} hours old; they did not die at once, so whoever hurt them need not have been here when they died."})
        trail = [b for b in s.get("blood", []) if b["by"] == cid]
        if trail:
            first = trail[0]["room"]
            case["clues"].append({"room": first, "scene": True, "found_by": [], "kind": "blood_trail", "text":
                                  f"A trail of blood runs from the {w.room_name(first)} to where {self.nm(cid)} lay: they were hurt there and made it this far."})
        if origin and origin != a["room"]:
            case["clues"].append({"room": origin, "scene": True, "found_by": [], "kind": "wound_place", "text": f"The wound was made in the {w.room_name(origin)}."})

    def blackout_alibis(self, case):
        """Anyone who was found unconscious around the time of the death cannot have done it: lay those facts on the table."""
        w, s = self.world, self.s
        out = []
        for b in s.get("blackouts", []):
            if b["who"] == case.get("victim") or b["who"] not in w.agents:
                continue
            start, end = b["day"] * 24 + b["hour"], b["woke_day"] * 24 + b["woke_hour"]
            when = case["day"] * 24 + case["hour"] if "day" in case else self.day * 24 + case["hour"]
            if not (start - 1 <= when <= end + 1):
                continue
            seers = [x for x in b["seen_by"] if x in w.agents and x != case.get("killer")]
            if seers:
                out.append(f"ALIBI: {', '.join(self.nm(x) for x in seers[:3])} found {self.nm(b['who'])} unconscious in the {w.room_name(b['room'])} around {b['hour']:02d}:00, "
                           f"and they stayed that way. {self.nm(b['who'])} cannot have killed {self.nm(case['victim'])}.")
        return out

    def do_stage(self, tick, cid, d):
        """Put an unconscious person beside the body with the murder weapon in their hand, so that they take the blame."""
        w, s = self.world, self.s
        a = w.agents[cid]
        t = d.get("target")
        case = s.get("case")
        if (not case or case.get("killer") != cid or case.get("announced") or t not in w.agents or t == cid or w.agents[t]["room"] != a["room"] or not w.agents[t].get("out")
                or case.get("room") != a["room"] or case.get("framed")):
            return
        ta = w.agents[t]
        weapon = case.get("weapon")
        given = None
        if weapon and (a["inv"].get(weapon, 0) > 0 or s["room_items"].get(a["room"], {}).get(weapon, 0) > 0):
            if a["inv"].get(weapon, 0) > 0:
                a["inv"][weapon] -= 1
                if a["inv"][weapon] <= 0:
                    del a["inv"][weapon]
            else:
                s["room_items"][a["room"]][weapon] -= 1
            ta["inv"][weapon] = ta["inv"].get(weapon, 0) + 1
            given = weapon
        self.stain_clothes(t)
        case["framed"] = t
        for c in case["clues"]:
            if c.get("kind") == "weapon" and given:
                c["text"] = f"A {w.item_name(given)}, freshly stained, is in the hand of {self.nm(t)}, who lies unconscious beside the body."
        case["clues"].append({"room": a["room"], "scene": True, "found_by": [], "kind": "framed_unconscious", "by": cid,
                              "text": f"{self.nm(t)} lies unconscious beside the body" + (f" with the {w.item_name(given)} in their hand" if given else "") + ", clothes stained."})
        marks = {"knocked out": f"a fresh lump at the back of {self.nm(t)}'s head, the kind a blow from behind leaves",
                 "choked out": f"red marks on {self.nm(t)}'s throat: someone choked them out",
                 "drugged": f"{self.nm(t)} will not wake as they should and their pupils are tiny: they were drugged, not struck down by a fight",
                 "tased": f"burn marks on {self.nm(t)}'s skin from a taser"}.get(ta["out"]["cause"])
        if marks:
            case["clues"].append({"room": a["room"], "scene": True, "found_by": [], "kind": "frame_flaw", "by": cid, "text": f"A closer look: {marks}. {self.nm(t)} was put out of action, which sits badly with them being the killer."})
        dr = [x for x in s.get("drags", []) if x["victim"] == t and x["day"] == self.day]
        if dr:
            case["clues"].append({"room": a["room"], "scene": True, "found_by": [], "kind": "drag_marks", "by": cid,
                                  "text": f"Scuff marks in the dust lead from the {w.room_name(dr[-1]['from'])} to where {self.nm(t)} lies: they were dragged here, they did not walk."})
        ta["staged_beside"] = case["victim"]
        w.remember(cid, f"{_hh(tick['hour'])} (private) You arranged {self.nm(t)} beside {self.nm(case['victim'])}'s body, the {w.item_name(given) if given else 'scene'} in their hand.")
        self.log_event(tick, {"type": "frame", "who": cid, "room": a["room"], "vis": "viewer", "text": f"{self.nm(cid)} sets {self.nm(t)} beside the body to take the blame."}, actor=cid)
        self.tally(cid, "framings")
