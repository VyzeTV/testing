"""Gear a careful killer uses: gloves, a coat, a bag, a holster.

Gloves (work, oven or rubber gloves) leave no fingerprints on a weapon; without them, the weapon at the scene carries prints (smudged, or
clear enough to match, as the clue-clarity dial decides). A coat (raincoat, trench coat, jacket, a bedsheet cloak) takes the blood instead of
the clothes underneath: the stained coat is the evidence, to be got rid of. A bag (tote or duffel bag) hides up to three medium things that
would otherwise be seen in the hand, though drawing from it takes a moment. A holster hides one medium weapon and it comes out at once.
GearMixin is mixed into DayRunner (engine.py); `carry.py` asks it what is stowed.
"""

GLOVES = ("rubber_gloves", "work_gloves", "oven_gloves")
COATS = ("raincoat", "trench_coat", "jacket", "sheet_cloak")
BAGS = ("duffel_bag", "tote_bag")
BAG_HOLDS = 3


class GearMixin:
    def _first(self, cid, items):
        a = self.world.agents.get(cid) or {}
        return next((k for k in items if a.get("inv", {}).get(k, 0) > 0), None)

    def gloves_of(self, cid):
        return self._first(cid, GLOVES)

    def coat_of(self, cid):
        return self._first(cid, COATS)

    def stowed(self, cid):
        """{item: "holster" | "bag"} for the medium weapons someone carries out of sight in a holster or a bag."""
        a = self.world.agents.get(cid) or {}
        meds = [k for k, q in sorted(a.get("inv", {}).items()) if q > 0 and self.item_caps(k)["size"] == "medium" and {"cut", "bludgeon"} & set(self.item_caps(k)["does"])]
        out = {}
        if a.get("inv", {}).get("holster", 0) > 0 and meds:
            out[meds.pop(0)] = "holster"
        if self._first(cid, BAGS):
            for k in meds[:BAG_HOLDS]:
                out[k] = "bag"
        return out

    def prints_text(self, culprit, weapon):
        """What the weapon at the scene shows: no prints if they wore gloves; otherwise prints, matched to them or not yet."""
        w = self.world
        if not culprit or not weapon:
            return ""
        gl = self.gloves_of(culprit)
        if gl:
            return " No fingerprints anywhere on it, only faint smudges of fabric: whoever used it wore gloves."
        if self.rng.random() < 0.35 + 0.4 * min(1.0, self.tune("clue_clarity")):
            return f" Clear fingerprints on the handle: {self.nm(culprit)}'s."
        return " Fingerprints on the handle, too smudged to match yet."

    def coat_takes_blood(self, cid):
        """The killer's coat takes the blood instead of their clothes: the coat becomes the stained evidence. Returns the stained coat id, or None."""
        coat = self.coat_of(cid)
        if not coat:
            return None
        w, s = self.world, self.s
        a = w.agents[cid]
        sid = f"stained_{coat}"
        s["custom_items"].setdefault(sid, {"name": f"bloodstained {w.item_name(coat)}", "tags": ["clothing", "stained"], "owner": cid})
        a["inv"][coat] -= 1
        if a["inv"][coat] <= 0:
            del a["inv"][coat]
        a["inv"][sid] = a["inv"].get(sid, 0) + 1
        return sid
