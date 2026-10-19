"""Marks on bodies and weapons that anyone can read by eye: no lab, no print matching.

The show gives the cast no forensic tools, so evidence on a body or a weapon is only what a person can see and compare. Each character has a
few visible traits (hand size, the hand they use, height; from looks.py, or the cast field `body`). The fight records which side each
blow landed on and whether it came from above, so the body can be read: blows on the victim's left mean a right-handed attacker facing them,
blows from above mean someone taller, finger bruises on the throat show the size of the hand, defensive cuts on the forearms mean they fought,
and skin under the nails means the attacker carries fresh scratches. A bare hand on a bloody handle leaves a handprint of a size (no
fingerprints that anyone could match); gloves leave a fabric weave instead, and the gloves themselves are stained. At the trial people
compare by looking: hands on the table, who uses which hand, who stands taller, whose hands are scratched (and whether anyone saw them in the
garden, where thorns would explain it). MarksMixin is mixed into DayRunner (engine.py).
"""

HEIGHTS = ("short", "medium", "tall")
SIDED = {"head", "face", "chest", "torso", "back", "arm", "shoulder", "neck", "throat"}


class MarksMixin:
    def build_of(self, cid):
        """{"hand", "handed", "height"}: what anyone can see of someone's build (looks.py, or the cast field `body`)."""
        c = self.world.cast.get(cid) or {}
        if c.get("body"):
            return c["body"]
        lk = self.looks(cid)
        return {"hand": lk["hand"], "handed": lk["handed"], "height": lk["height"]}

    def taller(self, a, b):
        return HEIGHTS.index(self.build_of(a)["height"]) > HEIGHTS.index(self.build_of(b)["height"])

    def blow_marks(self, cid, t, part):
        """Where a landed blow shows on the body: the side (facing, a right hand lands on the victim's left) and whether it came from above."""
        side = "left" if self.build_of(cid)["handed"] == "right" else "right"
        if self.rng.random() < 0.2:
            side = "right" if side == "left" else "left"
        return {"side": side if part in SIDED else None, "above": part in ("head", "face") and self.taller(cid, t)}

    def read_wounds(self, case):
        """What looking at the body tells: (sentences, {"handed", "taller", "hand", "scratched"})."""
        w = self.world
        wounds = case.get("wounds") or []
        v = self.nm(case["victim"])
        out, inf = [], {}
        kind = wounds[0]["kind"] if wounds else None
        sides = [wd.get("side") for wd in wounds if wd.get("side")]
        if kind in ("sharp", "blunt") and len(sides) >= 2:
            left = sides.count("left")
            if left / len(sides) >= 0.7 or left / len(sides) <= 0.3:
                side = "left" if left * 2 > len(sides) else "right"
                inf["handed"] = "right" if side == "left" else "left"
                out.append(f"Most of the {'wounds' if kind == 'sharp' else 'blows'} are on {v}'s {side} side: whoever did it was facing them and used their {inf['handed']} hand.")
        heads = [wd for wd in wounds if wd["part"] in ("head", "face")]
        if heads:
            inf["taller"] = any(wd.get("above") for wd in heads)
            out.append(f"The blows to the head came down from above: someone taller than {v}." if inf["taller"] else f"The blows to the head came level or from below: not someone much taller than {v}.")
        if kind == "hands" and case.get("killer"):
            inf["hand"] = self.build_of(case["killer"])["hand"]
            out.append(f"Finger-shaped bruises around the throat: a {inf['hand']} hand.")
        if kind == "water":
            out.append("Bruises on the shoulders where someone held them under.")
        if any(wd["part"] == "arm" for wd in wounds):
            out.append(f"Cuts and bruises on the forearms: {v} tried to shield themselves.")
        if case.get("killer_scratched"):
            inf["scratched"] = True
            out.append(f"Skin and a little blood under {v}'s fingernails: they scratched whoever did it, and those scratches will still show.")
        case["marks"] = inf
        return out, inf

    def hand_mark_text(self, culprit, weapon):
        """What the handle of the weapon shows to the naked eye: a bloody handprint of some size, a glove's weave, or just a smear."""
        if not culprit or not weapon:
            return ""
        if self.gloves_of(culprit):
            return " The blood on the handle is smeared in a fine weave, like fabric: whoever held it wore gloves."
        if {"cut", "bludgeon"} & set(self.item_caps(weapon)["does"]) and self.rng.random() < 0.35 + 0.4 * min(1.0, self.tune("clue_clarity")):
            size = self.build_of(culprit)["hand"]
            return f" A bloody handprint on the handle: a {size} hand."
        return " Blood smeared on the handle, too messy to show a hand."

    def gloves_take_blood(self, cid):
        """The gloves that kept a hand off the handle are stained now, and are evidence until got rid of."""
        g = self.gloves_of(cid)
        if not g:
            return None
        w, s = self.world, self.s
        a = w.agents[cid]
        sid = f"stained_{g}"
        s["custom_items"].setdefault(sid, {"name": f"bloodstained {w.item_name(g)}", "tags": ["clothing", "stained"], "owner": cid})
        a["inv"][g] -= 1
        if a["inv"][g] <= 0:
            del a["inv"][g]
        a["inv"][sid] = a["inv"].get(sid, 0) + 1
        return sid

    def scratch(self, tick, cid, why):
        """Fresh scratches on the hands and face, visible to anyone for a day or so."""
        return self.add_cond(tick, cid, "scratched", 1, why=why, body="hands")

    def mark_facts(self, case, ids):
        """Trial facts from what the body and the weapon show, compared by eye against everyone present. `by` is whoever examined the body."""
        clues = case.get("clues", [])
        by = next((f for c in clues if c.get("kind") == "scene" for f in c.get("found_by") or [] if f in ids), None)
        wby = next((f for c in clues if c.get("kind") == "weapon" for f in c.get("found_by") or [] if f in ids), None)
        inf = dict(case.get("marks") or {})
        if case.get("handmark") and wby:
            inf.setdefault("hand", case["handmark"])
        out = []
        victim = case.get("victim")
        people = [p for p in ids if p != victim]
        for key, holder in (("handed", by), ("taller", by), ("hand", wby if case.get("handmark") else by), ("scratched", by)):
            if key not in inf or not holder:
                continue
            for p in people:
                b = self.build_of(p)
                if key == "handed":
                    fits, w_, txt = b["handed"] == inf["handed"], (0.6, -1.2), f"{self.nm(p)} uses their {b['handed']} hand."
                elif key == "taller":
                    fits, w_, txt = self.taller(p, victim) == inf["taller"], (0.5, -0.8), f"{self.nm(p)} is {'taller' if self.taller(p, victim) else 'not taller'} than {self.nm(victim)}."
                elif key == "hand":
                    fits, w_, txt = b["hand"] == inf["hand"], (1.0, -1.2), f"{self.nm(p)} has a {b['hand']} hand."
                else:
                    if not self.has_cond(p, "scratched"):
                        continue
                    fits, w_, txt = True, (2.5, 0), f"{self.nm(p)} has fresh scratches on their hands."
                out.append({"by": holder, "about": p, "kind": "mark", "mark": key, "fits": fits, "w": w_[0] if fits else w_[1], "text": txt, "true": True})
        return out

    def thorn_alibi(self, p, ids):
        """Someone with scratches says it was the garden's thorns; it holds if somebody else saw them in the garden that day."""
        rec = self.conds(p).get("scratched") or {}
        seen = any(b["k"] == "at" and b["s"] == p and b.get("r") in ("garden", "greenhouse", "woods", "maze") and b["t0"] >= self.abs_now() - 24
                   for o in ids if o != p for b in self.beliefs(o))
        return ("thorn" in (rec.get("why") or "")), seen
