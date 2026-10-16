"""Where items come from, and crafting.

Nothing appears from nowhere. A character has what they carry; they can take what lies in the room they are in, and the room's common supplies (unlimited, but only the
sorts of thing that would plausibly be found there: rags and string in the laundry, nails in the shed, oleander in the garden). Anything else has to be CRAFTED (action 'craft'):
the ingredients come from the inventory, from what lies in the room, or from the room's common supplies, a few recipes need a tool and a fitting room, and a botched attempt wastes
materials and can hurt. Crafted items are special items: they exist only because someone made them, and a homemade weapon at a crime scene says where its parts came from.
CraftMixin is mixed into DayRunner (engine.py).
"""
import math

from .data_world import RECIPES, COMMON_ITEMS

WEAPON_RECIPES = ("garrote", "bottle_shiv", "spear", "nail_board", "sock_cosh", "molotov", "torch")


def _hh(h):
    return f"{int(h):02d}:00"


class CraftMixin:
    # ------------------------------------------------------------------ where things can be found
    def item_sources(self, item, limit=2):
        """Rooms where an item can be had: common supplies first, then wherever one lies."""
        w, s = self.world, self.s
        rooms = [r for r, lst in COMMON_ITEMS.items() if item in lst]
        if not rooms:
            rooms = [r for r, pool in s["room_items"].items() if pool.get(item, 0) > 0]
        return [w.room_name(r) for r in rooms[:limit]]

    def recipe_plan(self, cid, rid):
        """(plan, reason). plan is a list of (item, qty, source) to use up, or None."""
        w, s = self.world, self.s
        r = RECIPES[rid]
        a = w.agents[cid]
        room = a["room"]
        if r["where"] and room not in r["where"]:
            return None, f"it has to be made in the {' or '.join(w.room_name(x) for x in r['where'][:3])}"
        inv, stock, common = a["inv"], s["room_items"].get(room, {}), set(COMMON_ITEMS.get(room, []))
        used_inv, used_stock = {}, {}
        plan = []
        for options, qty in r["needs"]:
            need = qty
            for src in ("inv", "stock", "common"):
                for it in options:
                    if need <= 0:
                        break
                    if src == "inv":
                        n = min(need, inv.get(it, 0) - used_inv.get(it, 0))
                        used_inv[it] = used_inv.get(it, 0) + max(0, n)
                    elif src == "stock":
                        n = min(need, stock.get(it, 0) - used_stock.get(it, 0))
                        used_stock[it] = used_stock.get(it, 0) + max(0, n)
                    else:
                        n = need if it in common else 0
                    if n > 0:
                        plan.append((it, n, src))
                        need -= n
            if need > 0:
                return None, f"missing {w.item_name(options[0])}" + (f" ({qty} needed)" if qty > 1 else "")
        for group in r["tools"]:
            if not any(inv.get(t, 0) > 0 or stock.get(t, 0) > 0 for t in group):
                return None, f"needs a tool: {w.item_name(group[0])}"
        return plan, ""

    def craftable(self, cid):
        return [rid for rid in RECIPES if self.recipe_plan(cid, rid)[0] is not None]

    # ------------------------------------------------------------------ prompts
    def craft_acts(self, cid):
        return "|craft" if self.revealed and self.craftable(cid) else ""

    def craft_lines(self, cid):
        if not self.revealed:
            return []
        w, s = self.world, self.s
        a = w.agents[cid]
        room = a["room"]
        out = []
        com = COMMON_ITEMS.get(room, [])
        if self.lean or getattr(self, "short_docs", False):
            out.append("ITEMS: you only have what you carry; you may take what lies here or the room's unlimited common supplies; anything else must be crafted (action 'craft', \"craft\": recipe id).")
        else:
            out.append("ITEMS: you only have what is listed under Carrying. You may take what you SEE lying here, and the COMMON SUPPLIES of this room (unlimited, free). Nothing else exists: "
                       "you cannot use, give or produce an item you do not have. To make something else you must CRAFT it (action 'craft' with \"craft\": a recipe id) from ingredients you carry, "
                       "that lie here or are common supplies here; if the parts are elsewhere, go and get them first. Crafted things are special and traceable.")
        if com:
            out.append("COMMON SUPPLIES HERE (unlimited, take freely): " + ", ".join(w.item_name(k) for k in com) + ".")
        ready = self.craftable(cid)
        if ready:
            out.append("YOU COULD CRAFT RIGHT NOW: " + "; ".join(f"{rid} = {RECIPES[rid]['name']}" for rid in ready[:5]) + ".")
        if not self.lean and not getattr(self, "short_docs", False):
            hints = []
            for rid, r in RECIPES.items():
                if rid in ready:
                    continue
                have = sum(1 for options, _ in r["needs"] if any(a["inv"].get(it, 0) > 0 for it in options))
                if have >= 1 and len(r["needs"]) - have <= 2:
                    missing = [(opts, q) for opts, q in r["needs"] if not any(a["inv"].get(it, 0) > 0 for it in opts)]
                    bits = []
                    for opts, q in missing[:2]:
                        src = self.item_sources(opts[0], 1)
                        bits.append(f"{q} x {w.item_name(opts[0])}" + (f" (in the {src[0]})" if src else ""))
                    where = f"; make it in the {w.room_name(r['where'][0])}" if r["where"] else ""
                    hints.append(f"{rid} = {r['name']}: still needs {', '.join(bits)}{where}")
            if hints:
                out.append("PARTLY READY TO CRAFT: " + " | ".join(hints[:3]) + ".")
        return out

    # ------------------------------------------------------------------ crafting
    def do_craft(self, tick, cid, d):
        w, s = self.world, self.s
        a = w.agents[cid]
        rid = d.get("craft")
        name = self.nm(cid)
        if rid not in RECIPES:
            return
        plan, why = self.recipe_plan(cid, rid)
        if plan is None:
            self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm", "text": f"{name} tried to make a {RECIPES[rid]['name']} but {why}."}, actor=cid)
            w.remember(cid, f"{_hh(tick['hour'])} You could not make the {RECIPES[rid]['name']}: {why}.")
            return
        r = RECIPES[rid]
        p = r["p"] * (0.55 + 0.45 * self.success_p(cid, 1.0)) * (0.5 + 0.5 * self.hand_skill(cid))
        good, _ = self.roll(cid, p)
        room = a["room"]
        for it, n, src in plan:
            k = n if good else int(math.ceil(n / 2))
            if src == "inv":
                a["inv"][it] -= k
                if a["inv"][it] <= 0:
                    del a["inv"][it]
            elif src == "stock":
                s["room_items"][room][it] -= k
                if s["room_items"][room][it] <= 0:
                    del s["room_items"][room][it]
        used = ", ".join(w.item_name(it) for it, _, _ in plan)
        if not good:
            if r["risk"] == "cut":
                self.stat(tick, cid, "hp", -2, "cut while crafting")
            elif r["risk"] == "burn":
                self.stat(tick, cid, "hp", -3, "burned while crafting")
            self.log_event(tick, {"type": "craft", "who": cid, "room": room, "vis": "viewer", "text": f"{name} tries to make a {r['name']} from {used} and ruins it."}, actor=cid)
            return
        out = r["out"]
        if w.carried(cid) < 30:
            a["inv"][out] = a["inv"].get(out, 0) + 1
        else:
            pool = s["room_items"].setdefault(room, {})
            pool[out] = pool.get(out, 0) + 1
        self.note_holder(cid, out, tick["hour"])
        s.setdefault("crafted", []).append({"item": out, "by": cid, "day": self.day, "hour": tick["hour"], "room": room})
        del s["crafted"][:-40]
        self.tally(cid, "crafts")
        self.log_event(tick, {"type": "craft", "who": cid, "room": room, "vis": "viewer", "text": f"{name} makes a {r['name']} from {used}."}, actor=cid)
        for o in [x for x in w.occupants(room) if x in w.agents and x != cid]:
            pn = self.notice_p(o, cid, bonus=0.1)
            if self.rng.random() < pn:
                w.remember(o, f"{_hh(tick['hour'])} (you saw) {name} making a {r['name']} out of {used}.")
            elif self.rng.random() < 0.4:
                w.remember(o, f"{_hh(tick['hour'])} (odd) {name} was busy making something with their hands and put it away when you looked.")

    def craft_weapon_option(self, cid):
        """A weapon this person could make right now (used by plotters who have none)."""
        opts = [rid for rid in WEAPON_RECIPES if self.recipe_plan(cid, rid)[0] is not None]
        return self.rng.choice(opts) if opts else None

    # ------------------------------------------------------------------ evidence
    def crafted_hint(self, item):
        """A homemade weapon says something about where it was made: its parts come from particular rooms."""
        rec = next((r for r in RECIPES.values() if r["out"] == item), None)
        if not rec:
            return ""
        rooms = []
        for options, _ in rec["needs"]:
            src = self.item_sources(options[0], 1)
            if src and src[0] not in rooms:
                rooms.append(src[0])
        where = f" and the parts come from places like the {' and the '.join(rooms[:3])}" if rooms else ""
        return f" It is homemade ({rec['name']}), so someone made it{where}."
