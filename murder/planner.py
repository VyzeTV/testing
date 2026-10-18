"""The murder planner: how a plotter means to do it, from what the world offers and what they believe.

When a plot reaches the preparing stage the plotter settles on a scheme, scored from the affordances around them and their own beliefs:
  asleep   strike the target asleep in their own bedroom at night (better if they sleep alone)
  alone    a place the plotter has seen the target alone, more than once
  height   a place with a drop (a gallery over a hall, a roof, the lighthouse, a cliff) where the target goes: a push looks like a fall
  poison   a poison they hold or know where to find

The scheme decides where (and for `asleep`, when) the plotter strikes: they wait for the target in that place rather than striking anywhere, unless
the deadline is on them or they have waited too long. A push sends the target over the edge (falls.py) and opens a murder case with the pusher as
culprit; anyone who saw it is a witness. MurderPlanMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS

PATIENCE = 10            # plot turns in the striking stage before the plotter takes any chance, scheme or not


class MurderPlanMixin:
    # ------------------------------------------------------------------ what the world offers
    def drop_edges(self, room):
        """Tiles in `room` someone could go over (with where they would land)."""
        cache = self.__dict__.setdefault("_edge_cache", {})
        if room not in cache:
            nav = self.nav()
            out = []
            for t in nav.room_tiles.get(room, []):
                if nav.char(*t) in ("v", "C") and self.drop_below(*t):
                    out.append(t)
            cache[room] = out
        return cache[room]

    def seen_alone_in(self, cid, t):
        """{room: times} where `cid` saw `t` with nobody else around (from their own sightings)."""
        out = {}
        bs = self.beliefs(cid)
        for b in bs:
            if b["k"] != "at" or b["s"] != t or b["src"] != "seen":
                continue
            mid = (b["t0"] + b.get("t1", b["t0"])) / 2
            crowd = [o for o in bs if o["k"] == "at" and o["s"] not in (t, cid) and o["src"] == "seen" and o["r"] == b["r"] and o["t0"] - 0.1 <= mid <= o.get("t1", o["t0"]) + 0.1]
            if not crowd:
                out[b["r"]] = out.get(b["r"], 0) + 1
        return out

    def poison_source(self, cid):
        w, s = self.world, self.s
        mine = next((k for k in sorted(w.agents[cid]["inv"]) if "poison" in w.item_spec(k).get("tags", [])), None)
        if mine:
            return mine, None
        for room in sorted(s["room_items"]):
            for k, q in sorted(s["room_items"][room].items()):
                if q > 0 and "poison" in w.item_spec(k).get("tags", []):
                    return k, room
        return None, None

    # ------------------------------------------------------------------ choosing
    def plan_schemes(self, cid, t):
        """Every scheme open to `cid` against `t`, scored: [(score, scheme)]."""
        w = self.world
        out = []
        cr = (self.facet(cid, "cruelty") - 50) / 100
        home = w.cast[t].get("home")
        if home in ROOMS:
            mates = [o for o in w.agents if o != t and w.cast[o].get("home") == home]
            out.append((0.9 + (0.5 if not mates else -0.3) + 0.3 * cr, {"kind": "asleep", "room": home, "when": "night",
                                                                       "why": f"{self.nm(t)} asleep in their room" + ("" if not mates else ", if the roommate sleeps through it")}))
        alone = self.seen_alone_in(cid, t)
        for room, n in sorted(alone.items(), key=lambda kv: (-kv[1], kv[0]))[:2]:
            out.append((0.7 + 0.25 * min(4, n), {"kind": "alone", "room": room, "when": "day", "why": f"{self.nm(t)} is often alone in the {w.room_name(room)}"}))
        for room in sorted({b["r"] for b in self.beliefs(cid) if b["k"] == "at" and b["s"] == t}):
            if self.drop_edges(room):
                out.append((1.45 + 0.2 * cr, {"kind": "height", "room": room, "when": "day",
                            "why": f"a fall from the {w.room_name(room)} would look like an accident"}))
        item, where = self.poison_source(cid)
        if item:
            out.append((1.1 if not where else 0.8, {"kind": "poison", "item": item, "room": where, "when": "any",
                                                    "why": f"the {w.item_name(item)}" + (f" from the {w.room_name(where)}" if where else " they already have")}))
        return sorted(out, key=lambda x: -x[0])

    def choose_scheme(self, tick, cid, p):
        """Settle on how to do it (once, when the plot starts preparing); a scheme that stops being possible is dropped and chosen again."""
        t = p.get("target")
        if t not in self.world.agents:
            return None
        opts = self.plan_schemes(cid, t)
        if not opts:
            return None
        best = max(opts, key=lambda x: x[0] + 0.3 * self.rng.random())[1]
        p["scheme"] = best
        self.plan_note(p, {"asleep": "will come for them in the night", "alone": f"will catch them alone in the {self.world.room_name(best['room'])}",
                           "height": f"will push them from the {self.world.room_name(best['room'])}", "poison": "will poison them"}[best["kind"]])
        self.log_event(tick, {"type": "plot", "who": cid, "room": self.world.agents[cid]["room"], "vis": "gm",
                              "text": f"{self.nm(cid)} plans the murder of {self.nm(t)}: {best['why']}."}, actor=cid)
        return best

    def scheme_allows(self, cid, p, urgent=False):
        """May the plotter strike here and now, given the scheme? (Any chance will do once the deadline is on them or they have waited too long.)"""
        sc = p.get("scheme")
        if not sc or urgent or p.get("stage_ticks", 0) >= PATIENCE:
            return True
        a = self.world.agents[cid]
        night = self.s.get("_hour", 12) >= 22
        if sc["kind"] == "asleep":
            return night and a["room"] == sc["room"]
        if sc["kind"] in ("alone", "height"):
            return a["room"] == sc["room"]
        return True

    def scheme_method(self, cid, p):
        """The attack method the scheme calls for, or None to use the plot's own."""
        sc = p.get("scheme") or {}
        if sc.get("kind") == "poison":
            item = sc.get("item")
            if item and self.world.agents[cid]["inv"].get(item, 0) > 0:
                return f"poison:{item}"
        if sc.get("kind") == "height" and self.world.agents[cid]["room"] == sc.get("room") and self.drop_edges(sc["room"]):
            return "push"
        return None

    # ------------------------------------------------------------------ the push
    def push_kill(self, tick, cid, t, m=None):
        """`cid` shoves `t` over the nearest edge in the room. A fatal fall is a murder with `cid` as the culprit. Returns the damage, or None."""
        w = self.world
        a, ta = w.agents[cid], w.agents.get(t)
        if not ta or ta["room"] != a["room"]:
            return None
        edges = self.drop_edges(a["room"])
        if not edges:
            return None
        sm = self.__dict__.get("_sim")
        m = self.minute() if m is None else m
        pos = sm.pos_at(t, m) if sm is not None and t in sm.tracks and m is not None else None
        edge = min(edges, key=lambda e: (e[0] != pos[0], abs(e[1] - pos[1]) + abs(e[2] - pos[2])) if pos else (0, 0)) if pos else edges[0]
        here = [o for o in w.occupants(a["room"]) if o in w.agents and o not in (cid, t)]
        self.log_event(tick, {"type": "attack", "who": cid, "room": a["room"], "vis": "public",
                              "text": f"{self.nm(cid)} shoves {self.nm(t)} toward the edge of the {w.room_name(a['room'])}."}, witnesses=here, actor=cid)
        self.__dict__["_pushed_by"] = (t, cid, list(here))
        try:
            return self.fall_from_edge(tick, t, edge, "push", by=cid, m=m)
        finally:
            self.__dict__.pop("_pushed_by", None)
