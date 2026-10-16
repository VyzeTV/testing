"""A more active NeoVi.

Besides carrying out TereVi's punishments NeoVi now has a working day of her own: she notices what happens around her (who carries what, what is broken), inspects a bedroom for
contraband once a day and confiscates what she finds, looks after the people she has come to like (bandages, sweets), warns the ones she trusts when she has seen something worrying and
leaves them a note, reports to TereVi at night (so the host knows more than she lets on), and can be bought off with small gifts. All of it follows her feelings and her fear of TereVi.
NeoViActiveMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS


def _hh(h):
    return f"{int(h):02d}:00"


TRUST = 4
CARE_ITEMS = (("bandages", "hp", 4, "bandages a cut"), ("first_aid_kit", "hp", 8, "dresses a wound"), ("sweets", "sanity", 2, "presses a sweet into their hand"))


class NeoViActiveMixin:
    def nv(self):
        return self.s["npcs"]["neovi"]

    def neovi_here(self):
        nv = self.nv()
        return nv.get("room") not in (None, "none")

    def neovi_note_seen(self, who, what, room, kind):
        nv = self.nv()
        seen = nv.setdefault("seen", [])
        entry = {"day": self.day, "hour": self.s.get("_hour", 12), "who": who, "what": what, "room": room, "kind": kind}
        if not any(e["day"] == entry["day"] and e["who"] == who and e["what"] == what for e in seen):
            seen.append(entry)
            del seen[:-30]
            self.neovi_log.append(f"I saw {self.nm(who)} {what}.")

    # ------------------------------------------------------------------ each turn
    def neovi_active_tick(self, tick, hour):
        w, s = self.world, self.s
        if not self.revealed or not self.neovi_here():
            return
        nv = self.nv()
        room = nv["room"]
        here = [o for o in w.occupants(room, include_npcs=False) if o in w.agents]
        # she notices
        for cid in here:
            a = w.agents[cid]
            weap = next((k for k in a["inv"] if "weapon" in w.item_spec(k).get("tags", []) and "instrument" not in w.item_spec(k).get("tags", [])
                         and (k not in a.get("concealed", {}) or self.rng.random() < 0.1)), None)
            if weap and self.rng.random() < 0.6:
                self.neovi_note_seen(cid, f"carrying a {w.item_name(weap)} in the {w.room_name(room)}", room, "weapon")
            if a.get("sneaking") and self.rng.random() < 0.4:
                self.neovi_note_seen(cid, f"moving quietly through the {w.room_name(room)}", room, "sneaking")
        for dg in s.get("drags", []):
            if dg["day"] == self.day and dg["to"] == room and dg["by"] in w.agents:
                self.neovi_note_seen(dg["by"], f"dragging {self.nm(dg['victim'])} through the {w.room_name(room)}", room, "carry")
        for cid in [o for o in w.occupants(room, include_npcs=False, include_hidden=True) if o in w.agents]:
            if w.agents[cid].get("out") and self.rng.random() < 0.5 and not s.get("case"):
                self.wake_up(tick, cid, f"is brought round by NeoVi")
                self.neovi_log.append(f"I woke {self.nm(cid)} from the floor.")
        if hour in (7, 8):
            for rm, lk in list(s.get("locks", {}).items()):
                inside = [o for o in w.occupants(rm, include_hidden=True) if o in w.agents]
                if lk.get("keyed") and inside:
                    del s["locks"][rm]
                    self.log_event(tick, {"type": "door", "who": "neovi", "room": rm, "vis": "public", "text": f"NeoVi unbolts the {w.room_name(rm)} from outside: breakfast, whether anyone wants it or not."},
                                   witnesses=inside, actor="neovi")
                    self.neovi_log.append(f"I let {', '.join(self.nm(x) for x in inside)} out of the {w.room_name(rm)}.")
        if room in s.get("broken", []):
            self.neovi_log.append(f"The door of the {w.room_name(room)} is broken; it will be mended at the turn of the week.")
        # she looks after those she likes
        for cid in here:
            a = w.agents[cid]
            if nv["aff"].get(cid, 0) < 3 or self.rng.random() > 0.35:
                continue
            for item, key, amt, verb in CARE_ITEMS:
                if nv["inv"].get(item, 0) > 0 and ((key == "hp" and a["hp"] < 60) or (key == "sanity" and a["sanity"] < 40)):
                    nv["inv"][item] -= 1
                    if nv["inv"][item] <= 0:
                        del nv["inv"][item]
                    a[key] = min(100, a[key] + amt)
                    self.adjust_any_aff("neovi", cid, 1)
                    self.log_event(tick, {"type": "give", "who": "neovi", "room": room, "vis": "public", "text": f"NeoVi {verb} for {self.nm(cid)}, saying nothing."},
                                   witnesses=[o for o in here if o != cid], actor=cid)
                    self.neovi_log.append(f"I looked after {self.nm(cid)}.")
                    break
        # the daily inspection: chosen at noon, carried out at 14:00
        if hour == 12 and not s.get("_inspect") and self.tune("neovi_inspect") >= 1:
            cands = [r for r in ("blue_room", "green_room", "yellow_room", "red_room", "violet_room", "orange_room", "grey_room", "white_room") if self.belongings_of(r) or any(st["room"] == r for st in s.get("stash", []))]
            cands = [r for r in cands if not any(w.agents[o]["room"] == r for o in w.agents)]
            if cands:
                s["_inspect"] = {"day": self.day, "hour": 14, "room": self.rng.choice(cands)}
        ins = s.get("_inspect")
        if ins and ins["day"] == self.day and hour == ins["hour"] and nv["room"] == ins["room"]:
            self.neovi_inspect(tick, ins["room"], hour)
            s["_inspect"] = None
        self.neovi_notices(tick, hour)
        if hour == 18:
            self.neovi_notes(tick, hour)

    def neovi_inspect(self, tick, room, hour):
        """She goes through a bedroom while its people are out and takes what is not allowed."""
        w, s = self.world, self.s
        nv = self.nv()
        taken, owners = [], [c for c in w.agents if w.cast[c]["home"] == room]
        for st in list(s.get("stash", [])):
            if st["room"] == room and self.rng.random() < 0.5:
                for k, q in st["items"].items():
                    if {"weapon", "poison", "crafted"} & set(w.item_spec(k).get("tags", [])):
                        nv["inv"][k] = nv["inv"].get(k, 0) + q
                        taken.append(w.item_name(k))
                s["stash"].remove(st)
        for owner, items in (s.get("belongings") or {}).items():
            if owner in owners:
                for k in list(items):
                    if {"weapon", "poison", "crafted", "secret"} & set(w.item_spec(k).get("tags", [])) and self.rng.random() < 0.6:
                        nv["inv"][k] = nv["inv"].get(k, 0) + items.pop(k)
                        taken.append(w.item_name(k))
        self.log_event(tick, {"type": "inspection", "who": "neovi", "room": room, "vis": "viewer",
                              "text": f"NeoVi inspects the {w.room_name(room)} for contraband" + (f" and confiscates: {', '.join(taken)}." if taken else " and finds nothing.")})
        self.neovi_log.append(f"I inspected the {w.room_name(room)}" + (f" and took {', '.join(taken)}." if taken else "; nothing."))
        s.setdefault("notices", []).append({"room": room, "owners": owners, "text": f"A neat card on the bed: 'Room inspected by management.'" + (f" Missing: {', '.join(taken)}." if taken else ""), "day": self.day})
        del s["notices"][:-8]
        if taken:
            self.day_notable.append(f"NeoVi confiscated contraband from the {w.room_name(room)}.")

    def neovi_notices(self, tick, hour):
        w, s = self.world, self.s
        for n in list(s.get("notices", [])):
            for o in list(n["owners"]):
                if o in w.agents and w.agents[o]["room"] == n["room"] and not w.agents[o].get("asleep"):
                    w.remember(o, f"{_hh(hour)} {n['text']}")
                    self.stat(tick, o, "sanity", -1, "management went through their room")
                    n["owners"].remove(o)
            if not n["owners"] or self.day - n["day"] > 2:
                s["notices"].remove(n)

    def neovi_notes(self, tick, hour):
        """Those she trusts get a folded note when she has seen something worrying (not accusations: what she saw)."""
        w, s = self.world, self.s
        nv = self.nv()
        today = [e for e in nv.get("seen", []) if e["day"] == self.day and e["kind"] == "weapon" and e["who"] in w.agents]
        if not today:
            return
        for t in [c for c in w.agents if nv["aff"].get(c, 0) >= TRUST][:2]:
            fear_of = [e for e in today if e["who"] != t]
            if not fear_of or self.rng.random() > 0.6:
                continue
            e = self.rng.choice(fear_of)
            plotting = s.get("plots", {}).get(e["who"], {}).get("target") == t
            text = (f"Be careful around {self.nm(e['who'])}. I saw them {e['what']}." if plotting else f"I saw {self.nm(e['who'])} {e['what']}. I am only telling you what I saw.")
            w.remember(t, f"{_hh(hour)} (a folded note in NeoVi's neat hand) {text}")
            self.log_event(tick, {"type": "mercy", "who": "neovi", "room": nv["room"], "vis": "viewer", "text": f"NeoVi leaves {self.nm(t)} a note about {self.nm(e['who'])}."})
            self.neovi_log.append(f"I left {self.nm(t)} a note.")

    def neovi_report(self, tick):
        """At night she is made to tell TereVi what she saw; it comes back as a tease, not a name."""
        nv = self.nv()
        today = [e for e in nv.get("seen", []) if e["day"] == self.day]
        if not today or not self.revealed:
            return
        pick = self.rng.sample(today, min(2, len(today)))
        for e in pick:
            self.day_notable.append(f"NeoVi reported: {self.nm(e['who'])} {e['what']}.")
        self.log_event(tick, {"type": "tease", "who": "neovi", "room": nv["room"], "vis": "viewer", "text": "NeoVi tells TereVi what she saw today, because she must."})

    # ------------------------------------------------------------------ bribes and favours
    def give_to_neovi(self, tick, cid, item):
        w, s = self.world, self.s
        nv = self.nv()
        a = w.agents[cid]
        if nv.get("room") != a["room"] or a["inv"].get(item, 0) <= 0:
            return
        tags = set(w.item_spec(item).get("tags", []))
        if "weapon" in tags or "poison" in tags:
            w.remember(cid, f"{_hh(tick['hour'])} NeoVi refuses it, wide-eyed, and steps back.")
            return
        a["inv"][item] -= 1
        if a["inv"][item] <= 0:
            del a["inv"][item]
        nv["inv"][item] = nv["inv"].get(item, 0) + 1
        gain = 3 if tags & {"food", "comfort", "drink"} else 2
        nv["aff"][cid] = min(10, nv["aff"].get(cid, 0) + gain)
        nv.setdefault("favors", {})[cid] = self.day
        self.log_event(tick, {"type": "give", "who": cid, "room": a["room"], "vis": "public", "text": f"{self.nm(cid)} slips NeoVi the {w.item_name(item)}, quietly."},
                       witnesses=[o for o in w.occupants(a["room"]) if o != cid], actor=cid)
        w.remember(cid, f"{_hh(tick['hour'])} (private) NeoVi took the {w.item_name(item)} and did not meet your eye. She may look away today.")
        self.neovi_log.append(f"{self.nm(cid)} gave me the {w.item_name(item)}.")

    def neovi_favored(self, cid):
        return self.nv().get("favors", {}).get(cid) == self.day
