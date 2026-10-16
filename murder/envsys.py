"""The engine's side of the environment: hazards (kitchen fires, lightning, burst pipes, explosions), what fire, smoke and water do to people and things, marks left as evidence,
what people are told about the room they are in, and the per-turn snapshot (`tick["env"]`) the live viewer draws. Pure simulation lives in environment.py.
Everything here is skipped when the tuning dial `environment` is 0.
"""
from .data_world import ROOMS
from .environment import Environment, STEP_MIN, key, parse
from .gridnav import GridNav

FLAMMABLE_ITEM_TAGS = {"flammable", "paper", "cloth", "clothing", "book"}
FLAMMABLE_ITEMS = {"paper", "notebook", "bread", "rags", "towels", "bed_sheets", "string", "pencil", "cardigan", "scarf", "fedora", "jacket", "apron", "maid_uniform", "cooking_oil"}


class EnvironmentMixin:
    # ------------------------------------------------------------------ plumbing
    def nav(self):
        n = self.__dict__.get("_nav")
        if n is None:
            n = self._nav = GridNav()
        return n

    def env(self):
        e = self.__dict__.get("_env")
        st = self.s.setdefault("env", {})
        if e is None or e.st is not st:
            e = self._env = Environment(self.nav(), st)
            self.perc().set_env(e)
        return e

    def env_on(self):
        return bool(self.tune("environment"))

    def env_avoid(self):
        """Tiles people walk around: anything on fire, and heavy smoke."""
        if not self.env_on():
            return frozenset()
        e = self.env()
        return frozenset({tuple(parse(k)) for k in e.st["fire"]} | {tuple(parse(k)) for k, v in e.st["smoke"].items() if v >= 5})

    def env_sync_nav(self):
        """Broken windows and wrecked furniture can be walked through: tell the navigator."""
        e = self.env()
        opened = set()
        for k, v in e.st["struct"].items():
            if v["state"] in ("broken", "destroyed", "burned"):
                p, x, y = parse(k)
                if self.nav().char(p, x, y) == "=" or k in e.furn:
                    opened.add((p, x, y))
        self.nav().set_overlay(opened)

    # ------------------------------------------------------------------ where things happen
    def env_tile_in(self, room, who="fire"):
        nav = self.nav()
        if room == "kitchen":
            st = next(((f["plane"], f["x"], f["y"]) for f in nav.gm["furniture"] if f["room"] == room and f["k"] == "stove"), None)
            if st:
                return st
        return nav.nominal(room, who, 5)

    def env_ignite_room(self, tick, room, text=None, intensity=1):
        if not self.env_on() or room not in ROOMS:
            return False
        p, x, y = self.env_tile_in(room)
        ok = self.env().ignite(p, x, y, intensity, force=True)
        if ok:
            self.env().make_noise(p, x, y, "normal", "fire", self.day, tick.get("hour", 12))
            if text:
                self.log_event(tick, {"type": "fire", "who": "terevi", "room": room, "vis": "public", "text": text}, witnesses=[o for o in self.world.occupants(room) if o in self.world.agents])
        return ok

    def env_explosion(self, tick, room, text=None):
        """A blast: fire, rubble, smoke, a wrecked door and a very loud noise."""
        if not self.env_on() or room not in ROOMS:
            return
        e, nav = self.env(), self.nav()
        p, x, y = self.env_tile_in(room, "blast")
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            e.ignite(p, x + dx, y + dy, 2, force=True)
        e.add_mark("soot", p, x, y, self.day, tick.get("hour", 12))
        for _ in range(2):
            e.smash_furniture(room, self.rng.random)
        e.make_noise(p, x, y, "shout", "explosion", self.day, tick.get("hour", 12))
        for d in nav.gm["doors"]:
            if d["a"] == room or d["b"] == room:
                if self.rng.random() < 0.5:
                    e.break_door(d["id"])
        self.env_sync_nav()

    def env_burst_pipe(self, tick, room):
        if not self.env_on():
            return
        e, nav = self.env(), self.nav()
        sink = next(((f["plane"], f["x"], f["y"]) for f in nav.gm["furniture"] if f["room"] == room and f["k"] in ("sink", "tub", "washer", "boiler")), None) or nav.nominal(room, "pipe", 6)
        e.add_water(sink[0], sink[1], sink[2], 5)
        e.add_source(sink[0], sink[1], sink[2], 10)
        e.make_noise(sink[0], sink[1], sink[2], "loud", "pipe", self.day, tick.get("hour", 12))
        self.log_event(tick, {"type": "flood", "who": "terevi", "room": room, "vis": "public", "text": f"A pipe bursts in the {nav.rooms[room]['name']}: water gushes over the floor."},
                       witnesses=[o for o in self.world.occupants(room) if o in self.world.agents])

    def env_break_door(self, edge_id, tick=None):
        if not self.env_on():
            return
        e = self.env()
        if e.break_door(edge_id):
            d = next(q for q in self.nav().gm["doors"] if q["id"] == edge_id)
            t = d["tiles"][0]
            e.add_mark("splinters", d["plane"], t[0], t[1], self.day, (tick or {}).get("hour", self.s.get("_hour", 12)))
            e.make_noise(d["plane"], t[0], t[1], "loud", "door", self.day, self.s.get("_hour", 12))
            self.env_sync_nav()

    def env_fight(self, tick, room):
        """A brawl wrecks a piece of furniture now and then, and planks end up on the floor."""
        if not self.env_on() or room not in ROOMS or self.rng.random() > 0.3:
            return
        kind = self.env().smash_furniture(room, self.rng.random)
        if kind:
            pool = self.s["room_items"].setdefault(room, {})
            if kind in ("bed", "table", "chair", "desk", "shelf", "wardrobe", "crate", "bench", "chest", "sofa", "cabinet"):
                pool["planks"] = pool.get("planks", 0) + 1
            self.env_sync_nav()
            self.log_event(tick, {"type": "wreck", "who": "terevi", "room": room, "vis": "public", "text": f"A {kind} is smashed to pieces in the {self.world.room_name(room)}."},
                           witnesses=[o for o in self.world.occupants(room) if o in self.world.agents])

    # ------------------------------------------------------------------ marks as evidence
    def env_mark(self, kind, cid, room=None, by=None, n=1):
        if not self.env_on():
            return
        a = self.world.agents.get(cid)
        room = room or (a["room"] if a else None)
        t = (self.tile_of(cid) if a else None) or (self.nav().nominal(room, kind, 7) if room in ROOMS else None)
        if t:
            self.env().add_mark(kind, t[0], t[1], t[2], self.day, self.s.get("_hour", 12), by=by or cid, n=n)

    def env_scene_marks(self, case):
        """A killing leaves blood around the victim."""
        if not self.env_on() or case["kind"] in ("suicide",) or case.get("room") not in ROOMS:
            return
        wk = case.get("weapon_kind") or case.get("method", "")
        t = self.nav().nominal(case["room"], case["victim"], 3)
        e = self.env()
        n = 4 if "sharp" in str(case.get("method", "")) or case["kind"] in ("murder", "manslaughter") else 2
        for i in range(n):
            e.add_mark("blood", t[0], t[1] + (i % 3) - 1, t[2] + (i // 3) - (1 if i else 0), self.day, case["hour"], by=case["victim"], n=2)

    def env_drag_marks(self, start_room, cid, victim):
        if not self.env_on() or start_room not in ROOMS:
            return
        nav = self.nav()
        a = self.world.agents[cid]
        src = nav.nominal(start_room, victim, 3)
        dst = self.tile_of(cid)
        path = nav.route(src, dst) if dst else None
        if path:
            for t in path[:: max(1, len(path) // 10)]:
                self.env().add_mark("drag", t[0], t[1], t[2], self.day, self.s.get("_hour", 12), by=cid)

    def env_clues(self, case):
        """Evidence the tiles kept: blood that is not the victim's, drag marks, forced doors and windows, scorching. Never names the culprit."""
        if not self.env_on():
            return []
        e, w, rn = self.env(), self.world, self.world.room_name
        room, victim, culprit = case["room"], case["victim"], case.get("killer")
        since = case["day"] * 24 + case["hour"] - 14
        out = []

        def add(kind, text):
            out.append({"room": room, "scene": True, "found_by": [], "kind": kind, "text": text})
        if culprit:
            trail = [m for m in e.marks("blood", since=since, by=culprit)]
            rooms = []
            for m in trail:
                r = self.nav().room_at(m["p"], m["x"], m["y"])
                if r and r not in rooms:
                    rooms.append(r)
            if rooms:
                add("blood_trail", f"Spots of blood that cannot be the victim's lead away through the {rn(rooms[-1] if rooms[-1] != room else rooms[0])}"
                    + (f", starting in the {rn(room)}" if room in rooms else "") + ": someone was bleeding.")
        drags = [m for m in e.marks("drag", since=since) if self.nav().room_at(m["p"], m["x"], m["y"])]
        if drags:
            rs = []
            for m in drags:
                r = self.nav().room_at(m["p"], m["x"], m["y"])
                if r and r not in rs:
                    rs.append(r)
            if len(rs) >= 2:
                add("drag_marks", f"Drag marks run from the {rn(rs[0])} to the {rn(rs[-1])}: a body, or a helpless person, was moved.")
        forced = [m for m in e.marks(since=since) if m["k"] in ("splinters", "glass") and self.nav().room_at(m["p"], m["x"], m["y"]) in (room,)]
        if forced:
            add("forced_entry", f"{'Glass' if forced[-1]['k'] == 'glass' else 'Splintered wood'} lies on the floor of the {rn(room)}: something was broken here recently.")
        if e.marks("soot", room=room):
            add("scorch", f"Soot and scorch marks in the {rn(room)}: there was a fire here.")
        return out[:3]

    # ------------------------------------------------------------------ what people are told
    def env_lines(self, cid):
        if not self.env_on():
            return []
        a = self.world.agents.get(cid)
        if not a or a["room"] not in ROOMS:
            return []
        e, nav = self.env(), self.nav()
        room = a["room"]
        lines = []
        nfire = sum(1 for k in e.st["fire"] if e.room_of(k) == room)
        smoke = max([v for k, v in e.st["smoke"].items() if e.room_of(k) == room] or [0])
        wet = max([v for k, v in e.st["water"].items() if e.room_of(k) == room] or [0])
        if nfire:
            lines.append(f"FIRE: flames are burning in this room ({nfire} tiles) and spreading over wood and carpet. Get out, or put it out (a fire extinguisher or water), or it will reach you.")
        if smoke >= 2:
            lines.append("SMOKE: the air is thick and stinging; you can barely see or breathe. Get low and get out.")
        if wet >= 2:
            lines.append("WATER: the floor is flooded here; it is slippery and spreading, and it can short the electrics.")
        near = [r for r in e.rooms_on_fire() if r != room and any(d for d in nav.gm["doors"] if {d["a"], d["b"]} == {room, r})]
        if near:
            lines.append(f"You smell smoke: the {nav.rooms[near[0]]['name']} next door is on fire.")
        return lines

    # ------------------------------------------------------------------ each turn
    def env_hazards(self, tick, hour):
        w, s = self.world, self.s
        chaos = self.chaos_factor()
        kitchen_people = [o for o in w.occupants("kitchen") if o in w.agents]
        if kitchen_people and self.rng.random() < 0.0012 * chaos:
            self.env_ignite_room(tick, "kitchen", "Grease catches on the stove in the kitchen: flames lick up the wall.")
        isl = s.get("island")
        if isl and isl.get("id") == "storm" and self.island_live(isl) and self.rng.random() < 0.025:
            room = self.rng.choice(["greenhouse", "boathouse", "generator_shed"])
            self.env_ignite_room(tick, room, f"Lightning strikes the {w.room_name(room)}: it is on fire.", 2)
        if self.rng.random() < 0.0035 * chaos:
            self.env_burst_pipe(tick, self.rng.choice(["bathroom", "laundry", "kitchen", "boiler_room"]))

    def env_reflexes(self, tick, scale=1.0):
        """People in a burning room with an extinguisher or water put the fire out, if they have their wits about them."""
        w, e = self.world, self.env()
        for room in sorted(e.rooms_on_fire()):
            for cid in [o for o in w.occupants(room) if o in w.agents]:
                a = w.agents[cid]
                if a.get("out") or a.get("sanity", 50) < 12:
                    continue
                have = a["inv"].get("fire_extinguisher", 0) > 0 or self.s["room_items"].get(room, {}).get("fire_extinguisher", 0) > 0
                water = a["inv"].get("water_bottle", 0) > 0
                if not (have or water):
                    continue
                if self.rng.random() < (0.65 if have else 0.35) * scale:
                    ft = next((parse(k) for k in e.st["fire"] if e.room_of(k) == room), None)
                    if not ft:
                        break
                    n = e.extinguish(ft[0], ft[1], ft[2], 3 if have else 1)
                    if water and not have:
                        a["inv"]["water_bottle"] -= 1
                        if a["inv"]["water_bottle"] <= 0:
                            del a["inv"]["water_bottle"]
                    if n:
                        self.log_event(tick, {"type": "fire", "who": cid, "room": room, "vis": "public",
                                              "text": f"{self.nm(cid)} {'empties the fire extinguisher over' if have else 'throws water on'} the flames in the {w.room_name(room)}."},
                                       witnesses=[o for o in w.occupants(room) if o != cid and o in w.agents], actor=cid)
                        self.special_boost(tick, cid, 2, "put out a fire", "comfort") if hasattr(self, "special_boost") else None
                    break

    def env_burn_items(self, tick):
        """Flammable things lying in a burning tile burn up."""
        e, nav = self.env(), self.nav()
        for it in e.item_tiles(self.s["room_items"]):
            k = key(it["p"], it["x"], it["y"])
            if k in e.st["fire"] and (it["i"] in FLAMMABLE_ITEMS or set(self.world.item_spec(it["i"]).get("tags", [])) & FLAMMABLE_ITEM_TAGS):
                room = nav.room_at(it["p"], it["x"], it["y"])
                pool = self.s["room_items"].get(room, {})
                if pool.get(it["i"], 0) > 0:
                    del pool[it["i"]]
                    self.log_event(tick, {"type": "wreck", "who": "terevi", "room": room, "vis": "viewer", "text": f"The {self.world.item_name(it['i']).lower()} in the {self.world.room_name(room)} burns."})

    def env_power_check(self, tick):
        """Water reaching the fuse box shorts the house."""
        e, nav = self.env(), self.nav()
        for f in nav.gm["furniture"]:
            if f["k"] == "fuseBox" and self.blackout_until < self.idx:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if e.st["water"].get(key(f["plane"], f["x"] + dx, f["y"] + dy), 0) >= 2:
                            self.blackout_until = self.idx + 2
                            self.log_event(tick, {"type": "island", "who": "terevi", "room": f["room"], "vis": "public", "text": "Water reaches the fuse box with a crack and a shower of sparks: the lights and cameras die across the house."})
                            return

    def env_light_cache(self, hour):
        c = self.__dict__.setdefault("_light_cache", {})
        e = self.env()
        sig = (hour, self.power_on(), len(e.st["fire"]), len(e.st["smoke"]))
        if c.get("sig") != sig:
            c.clear()
            c["sig"] = sig
        return c

    def env_room_light(self, room):
        c = self.env_light_cache(self.s.get("_hour", 12))
        if room not in c:
            c[room] = self.env().room_light(room, self.s.get("_hour", 12), self.power_on())
        return c[room]

    def env_frame(self, m):
        sn = self.env().snapshot(0)
        return {"m": m, "fire": sn["fire"], "smoke": sn["smoke"], "water": sn["water"]}

    def env_room_area(self, room):
        r = self.nav().rooms.get(room)
        if not r:
            return 100
        x0, y0, x1, y1 = r["rect"]
        return max(9, (x1 - x0 - 2) * (y1 - y0 - 2))

    def env_advance(self, tick, m0, m1):
        """Advance the environment from minute m0 to m1 of this turn in five-minute steps. At every step the people are where they really are: they notice, flee, burn, choke and collapse then."""
        if not self.env_on() or m1 <= m0:
            return
        e, hour = self.env(), tick["hour"]
        frames = tick.setdefault("_env_frames", [self.env_frame(0)])
        logged = tick.get("_env_logged", 0)
        for m in range(m0, m1, STEP_MIN):
            now = m + STEP_MIN
            self._slice_m = now
            try:
                evs = e.step(self.rng.random)
                for kind, text, room, tile in evs:
                    if tile and kind == "fire":
                        e.make_noise(tile[0], tile[1], tile[2], "normal", "fire", self.day, hour)
                    if logged < 14:
                        logged += 1
                        self.log_event(tick, {"type": kind, "who": "terevi", "room": room, "vis": "public", "text": text},
                                       witnesses=[o for o in self.world.occupants(room) if o in self.world.agents] if room else None)
                if e.st["fire"] or e.st["smoke"]:
                    self.env_reflexes(tick, 0.45)
                    self.env_step_effects(tick, now)
                if e.st["fire"]:
                    self.env_burn_items(tick)
            finally:
                self._slice_m = None
            if now % 30 == 0:
                frames.append(self.env_frame(now))
        tick["_env_logged"] = logged
        tick["_env_done"] = m1

    def env_step_effects(self, tick, m):
        """Five minutes of fire, heat and smoke on everyone in a burning or smoky room: they wake, run or stay; those who stay burn and choke, and may collapse."""
        w, e = self.world, self.env()
        k = self.tune("fire_lethality")
        fire_rooms, smoke_rooms = {}, {}
        for kk in e.st["fire"]:
            r = e.room_of(kk)
            fire_rooms[r] = fire_rooms.get(r, 0) + 1
        for kk, v in e.st["smoke"].items():
            r = e.room_of(kk)
            smoke_rooms[r] = max(smoke_rooms.get(r, 0), v)
        for cid in list(w.agents):
            a = w.agents.get(cid)
            if not a or a["room"] not in ROOMS:
                continue
            room = a["room"]
            nf, dens = fire_rooms.get(room, 0), smoke_rooms.get(room, 0)
            if not nf and dens < 2:
                continue
            danger = nf > 0 or dens >= 3
            if danger and not a.get("out"):
                if a.get("asleep") and self.rng.random() < 0.35:
                    a["asleep"] = False
                    self.log_event(tick, {"type": "reaction", "who": cid, "room": room, "vis": "public", "text": f"{self.nm(cid)} wakes choking on smoke."}, actor=cid)
                if not a.get("asleep"):
                    p = 0.5 * (0.6 if a["sanity"] < 25 else 1.0) * (0.45 if self.has_cond(cid, "panicking") else 1.0) * (0.5 if self.has_cond(cid, "blinded") else 1.0)
                    if self.rng.random() < p and self.fire_flee(tick, cid, m, fire_rooms, smoke_rooms):
                        continue
            area = self.env_room_area(room)
            heat = min(1.0, nf / max(6.0, area * 0.08))
            t = self.tile_of(cid)
            fire = {parse(kk): v[0] for kk, v in e.st["fire"].items()}
            near = max([i for (pl, x, y), i in fire.items() if t and pl == t[0] and max(abs(x - t[1]), abs(y - t[2])) <= 1] or [0])
            dmg = 0.0
            if nf:
                dmg += 1.0 + 2.2 * heat + 1.0 * near
            if dens >= 3:
                dmg += 0.6 + dens / 4.0
            dmg *= k
            loss = int(dmg) + (1 if self.rng.random() < dmg - int(dmg) else 0)
            if loss:
                self._slice_m = m
                try:
                    self.stat(tick, cid, "hp", -loss, "the flames" if nf else "smoke", lethal="burned to death in the fire" if nf else "overcome by smoke")
                finally:
                    self._slice_m = None
            if cid not in w.agents:
                continue
            if near and self.rng.random() < 0.5 * k:
                self.injure(tick, cid, None, set(), 5 + 4 * near, "fire")
            if dens >= 3:
                self.add_cond(tick, cid, "breathless", 1 + (1 if dens >= 6 else 0), "the smoke")
                if dens >= 6 and not a.get("out") and (a["hp"] < 55 or self.has_cond(cid, "breathless")) and self.rng.random() < 0.08 * k:
                    self.knock_out(tick, cid, "overcome", turns=1)
            if nf:
                self.maybe_panic(tick, cid, "the flames", 0.3)

    def fire_flee(self, tick, cid, m, fire_rooms, smoke_rooms):
        """Run for the nearest room that is not burning or filling with smoke. Returns True if they got out."""
        w = self.world
        a = w.agents[cid]
        reach = w.reachable_rooms(cid, max(6, int(20 * self.move_factor(cid))))
        safe = [(c, r) for r, c in reach.items() if not fire_rooms.get(r) and smoke_rooms.get(r, 0) < 3 and not self._unsafe(r)]
        if not safe:
            return False
        dest = min(safe)[1]
        start = a["room"]
        if not self._walk(tick, cid, dest, m) or a["room"] == start:
            return a["room"] != start
        self._slice_m = m
        try:
            self.log_event(tick, {"type": "reaction", "who": cid, "room": a["room"], "vis": "public", "text": f"{self.nm(cid)} runs out of the {w.room_name(start)}, away from the fire."},
                           witnesses=[o for o in w.occupants(a["room"]) if o in w.agents and o != cid], actor=cid)
            # a big fire catches some of the people who run: the doorway is burning too
            if fire_rooms.get(start, 0) >= 6 and self.rng.random() < 0.3 * self.tune("fire_lethality"):
                self.stat(tick, cid, "hp", -self.rng.randint(3, 8), "caught by the flames in the doorway", lethal="burned to death in the fire")
                if cid in w.agents:
                    self.injure(tick, cid, None, set(), 8, "fire")
        finally:
            self._slice_m = None
        if cid not in w.agents:
            return True
        a["fled"] = {"day": self.day, "m": m}
        if "free" in tick:
            self._seg(tick, cid, m, m + 15, a["room"], "flee", "getting away from danger")
            busy = getattr(self, "_free_busy", None)
            if busy is not None:
                busy[cid] = max(busy.get(cid, 0), m + 15)
        return True

    def fire_rooms(self):
        """Rooms with flames in them, with the number of burning tiles."""
        out = {}
        if not self.env_on():
            return out
        e = self.env()
        for kk in e.st["fire"]:
            r = e.room_of(kk)
            out[r] = out.get(r, 0) + 1
        return out

    def smoky_rooms(self, dens=3):
        out = {}
        if not self.env_on():
            return out
        e = self.env()
        for kk, v in e.st["smoke"].items():
            if v >= dens:
                out[e.room_of(kk)] = max(out.get(e.room_of(kk), 0), v)
        return out

    def env_tick(self, tick):
        """Advance what is left of the turn's environment (in five-minute steps), apply its effects and attach a snapshot for the viewer."""
        if not self.env_on():
            return
        e, hour = self.env(), tick["hour"]
        if not tick.pop("_hazards_done", False):
            self.env_hazards(tick, hour)
        phase = tick.get("phase")
        minutes = (60 if hour >= 23 else 30) if phase == "night" else 120
        done = tick.pop("_env_done", 0)
        self.env_advance(tick, done, minutes)
        frames = tick.pop("_env_frames", None) or [self.env_frame(0)]
        if frames[-1]["m"] != minutes:
            frames.append(self.env_frame(minutes))
        tick.pop("_env_logged", None)
        self.env_power_check(tick)
        self.env_sync_nav()
        snap = e.snapshot()
        lit = {rid: self.env_room_light(rid) for rid in ROOMS if not self.nav().rooms[rid]["open"]}
        tick["env"] = {"frames": frames, "struct": snap["struct"], "marks": snap["marks"], "noises": snap["noises"], "items": e.item_tiles(self.s["room_items"]),
                       "light": {k: v for k, v in lit.items() if v != "lit"}, "power": self.power_on(), "hour": hour}
