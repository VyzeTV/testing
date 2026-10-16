"""The living environment on the tile map: fire, water, smoke, light, noise, breakable doors, windows and furniture, items lying on tiles, and the marks people leave behind.

Environment is a pure simulation over sparse tile fields kept in a plain dict (`state["env"]`, saved with the game). It takes the randomness source as an argument and never touches
agents; EnvironmentMixin (bottom) connects it to the engine: hazards, the effects of fire and smoke on people, events, evidence, and a per-turn snapshot for the live viewer.
The tuning dial `environment` (World group) switches the engine side off (0).

Tile keys are "plane,x,y" strings so the state stays JSON.
"""
from .gridnav import GridNav, _h

STEP_MIN = 5
FLAMMABLE_FURN = {"bed", "wardrobe", "desk", "table", "chair", "shelf", "sofa", "piano", "easel", "chest", "crate", "barrel", "bench", "tree", "plantBed", "deckChair", "driftwood", "boat", "poolTable", "cabinet", "podium"}
HEAVY_FURN = {"wardrobe": 14, "piano": 16, "poolTable": 14, "boiler": 40, "generator": 40, "freezer": 30, "locker": 24, "terminal": 12, "boat": 20, "bed": 9, "table": 8}
NO_BREAK = {"camera", "railing", "tree", "monitor", "boiler", "generator", "freezer", "locker", "terminal", "fuseBox", "lamp"}
FLOOR_FLAMMABLE = {"w": 0.18, "c": 0.26, "g": 0.10, ",": 0.06, ":": 0.10}
OPEN_FLOOR = set("wkcrmgsp,:")
DOOR_HP, LOCKED_DOOR_HP, WINDOW_HP = 10, 14, 3


def key(p, x, y):
    return f"{p},{x},{y}"


def parse(k):
    p, x, y = k.split(",")
    return p, int(x), int(y)


class Environment:
    def __init__(self, nav=None, state=None):
        self.nav = nav or GridNav()
        self.st = state if state is not None else {}
        for k, v in (("fire", {}), ("water", {}), ("smoke", {}), ("struct", {}), ("marks", []), ("noises", []), ("seq", 0), ("sources", [])):
            self.st.setdefault(k, v)
        self.furn = {}
        for f in self.nav.gm["furniture"]:
            self.furn[key(f["plane"], f["x"], f["y"])] = f["k"]
        self.door_tiles = {}
        for d in self.nav.gm["doors"]:
            for t in d["tiles"]:
                self.door_tiles[key(d["plane"], t[0], t[1])] = d

    # ------------------------------------------------------------------ what is where
    def furniture_at(self, k):
        f = self.furn.get(k)
        return f if f and self.st["struct"].get(k, {}).get("state") not in ("destroyed", "burned") else None

    def hp_of(self, k):
        p, x, y = parse(k)
        c = self.nav.char(p, x, y)
        if c in "+L":
            return LOCKED_DOOR_HP if c == "L" else DOOR_HP
        if c == "=":
            return WINDOW_HP
        f = self.furn.get(k)
        return HEAVY_FURN.get(f, 6) if f else 0

    def flammability(self, k):
        """How readily this tile burns (0 = not at all)."""
        p, x, y = parse(k)
        c = self.nav.char(p, x, y)
        if c == "#" or c == " ":
            return 0.0
        if self.st["struct"].get(k, {}).get("state") == "burned":
            return 0.0                                    # already burnt: nothing left to burn, and nothing more to report
        base = FLOOR_FLAMMABLE.get(c, 0.0)
        if c in "+L":
            base = 0.30
        f = self.furniture_at(k)
        if f in FLAMMABLE_FURN:
            base = max(base, 0.50)
        if self.st["struct"].get(k, {}).get("state") in ("burned", "destroyed") and not f:
            base *= 0.3
        return base

    def room_of(self, k):
        p, x, y = parse(k)
        return self.nav.room_at(p, x, y)

    def broken(self, k):
        return self.st["struct"].get(k, {}).get("state") in ("broken", "burned", "destroyed")

    # ------------------------------------------------------------------ marks and noise
    def add_mark(self, kind, plane, x, y, day, hour, by=None, n=1):
        self.st["seq"] += 1
        self.st["marks"].append({"id": self.st["seq"], "k": kind, "p": plane, "x": x, "y": y, "day": day, "hour": hour, "by": by, "n": n})
        del self.st["marks"][:-500]

    def marks(self, kind=None, room=None, since=None, by=None):
        out = []
        for m in self.st["marks"]:
            if kind and m["k"] != kind:
                continue
            if by and m.get("by") != by:
                continue
            if since is not None and m["day"] * 24 + m["hour"] < since:
                continue
            if room and self.nav.room_at(m["p"], m["x"], m["y"]) != room:
                continue
            out.append(m)
        return out

    def make_noise(self, plane, x, y, loud, kind, day, hour):
        self.st["noises"].append({"p": plane, "x": x, "y": y, "loud": loud, "kind": kind, "day": day, "hour": hour})
        del self.st["noises"][:-30]

    # ------------------------------------------------------------------ fire, water, smoke
    def ignite(self, plane, x, y, intensity=1, force=False):
        k = key(plane, x, y)
        if k in self.st["fire"] or self.st["water"].get(k, 0) >= 1:
            return False
        if not force and self.flammability(k) <= 0:
            return False
        self.st["fire"][k] = [intensity, 0]
        return True

    def add_water(self, plane, x, y, depth):
        k = key(plane, x, y)
        self.st["water"][k] = min(6, self.st["water"].get(k, 0) + depth)

    def add_source(self, plane, x, y, steps=10):
        self.st["sources"].append({"p": plane, "x": x, "y": y, "left": steps})

    def extinguish(self, plane, x, y, radius=2):
        n = 0
        for k in list(self.st["fire"]):
            p, fx, fy = parse(k)
            if p == plane and max(abs(fx - x), abs(fy - y)) <= radius:
                del self.st["fire"][k]
                n += 1
        return n

    def fire_tiles(self):
        return [(parse(k), v[0]) for k, v in self.st["fire"].items()]

    def rooms_on_fire(self):
        return {self.room_of(k) for k in self.st["fire"]} - {None}

    def step(self, rng):
        """One step of STEP_MIN minutes. `rng()` returns a float in [0, 1). Returns a list of (kind, text, room, tile) events."""
        st, nav = self.st, self.nav
        ev = []
        before_rooms = self.rooms_on_fire()
        # --- water first: it puts fires out. Burst pipes keep gushing for a while, water runs to lower neighbours and slowly dries
        for src in list(st["sources"]):
            self.add_water(src["p"], src["x"], src["y"], 2)
            src["left"] -= 1
            if src["left"] <= 0:
                st["sources"].remove(src)
        water = st["water"]
        nw = dict(water)
        for k, d in sorted(water.items()):
            if d >= 2:
                p, x, y = parse(k)
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = key(p, x + dx, y + dy)
                    c = nav.char(p, x + dx, y + dy)
                    if c != " " and (c in OPEN_FLOOR or c in "+L") and nw.get(n, 0) < nw.get(k, 0) - 1 and rng() < 0.7:
                        nw[n] = nw.get(n, 0) + 1
                        nw[k] = nw.get(k, 0) - 1
        for k in list(nw):
            if nw[k] == 1 and rng() < 0.06:
                nw[k] = 0
            if nw[k] <= 0:
                del nw[k]
        st["water"] = water = nw
        # --- fire
        fire = st["fire"]
        add = {}
        for k in list(fire):
            if water.get(k, 0) >= 1:
                del fire[k]
                continue
            i, age = fire[k]
            age += 1
            fuel = self.flammability(k) > 0.2
            if age in (2, 4) and fuel and i < 3:
                i += 1
            life = 6 + (4 if self.furniture_at(k) else 0) if fuel else 2
            p, x, y = parse(k)
            if age >= life:
                del fire[k]
                self.add_mark("soot", p, x, y, 0, 0)
                f = self.furniture_at(k)
                if not (f and f in FLAMMABLE_FURN) and nav.char(p, x, y) not in "+L=":
                    st["struct"][k] = {"hp": 0, "max": 0, "state": "burned"}        # a scorched floor tile will not catch again
                if f and f in FLAMMABLE_FURN:
                    st["struct"][k] = {"hp": 0, "max": self.hp_of(k), "state": "burned"}
                    ev.append(("wreck", f"The {f} in the {nav.rooms[self.room_of(k)]['name']} burns to ash.", self.room_of(k), (p, x, y)))
                elif nav.char(p, x, y) in "+L=":
                    st["struct"][k] = {"hp": 0, "max": self.hp_of(k), "state": "burned"}
                    ev.append(("wreck", f"A burning {'window frame' if nav.char(p, x, y) == '=' else 'door'} collapses in the {nav.rooms[self.room_of(k)]['name'] if self.room_of(k) else 'house'}.", self.room_of(k), (p, x, y)))
                continue
            fire[k] = [i, age]
            st["smoke"][k] = min(9.0, st["smoke"].get(k, 0) + 1.5 * i)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = key(p, x + dx, y + dy)
                if n in fire or n in add:
                    continue
                fl = self.flammability(n)
                if fl > 0 and water.get(n, 0) < 1 and rng() < min(0.9, fl * (1.0 + 0.6 * i)):
                    add[n] = [1, 0]
        for k, v in add.items():
            fire[k] = v
        # --- smoke: spreads through open tiles (doors and windows pass less), thins outdoors
        smoke = st["smoke"]
        ns = {}
        for k, c in smoke.items():
            if c < 0.3:
                continue
            p, x, y = parse(k)
            nbrs = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ch = nav.char(p, x + dx, y + dy)
                if ch == "#" or ch == " ":
                    continue
                w = 0.5 if ch in "+L" else 0.3 if ch == "=" else 1.0
                if ch == "=" and self.broken(key(p, x + dx, y + dy)):
                    w = 1.0
                nbrs.append((key(p, x + dx, y + dy), w))
            out_share = c * 0.16
            for n, w in nbrs:
                ns[n] = ns.get(n, 0) + out_share * w
            keep = c - out_share * sum(w for _, w in nbrs)
            outdoors = nav.char(p, x, y) in ",gs:p"
            ns[k] = ns.get(k, 0) + keep * (0.6 if outdoors else 0.92)
        st["smoke"] = {k: min(9.0, round(v, 2)) for k, v in ns.items() if v >= 0.3}
        # --- reports
        after = self.rooms_on_fire()
        for rid in sorted(after - before_rooms):
            tile = next((parse(k) for k in fire if self.room_of(k) == rid), None)
            ev.append(("fire", f"Fire spreads into the {nav.rooms[rid]['name']}.", rid, tile))
        for rid in sorted(before_rooms - after):
            ev.append(("fire", f"The fire in the {nav.rooms[rid]['name']} has burned itself out.", rid, None))
        return ev

    # ------------------------------------------------------------------ breaking things
    def damage(self, k, amount):
        """Hit a door, window or piece of furniture. Returns the new state ('ok', 'broken' or 'destroyed')."""
        s = self.st["struct"].setdefault(k, {"hp": self.hp_of(k), "max": self.hp_of(k), "state": "ok"})
        if s["state"] != "ok" or s["max"] <= 0:
            return s["state"]
        s["hp"] -= amount
        if s["hp"] <= 0:
            p, x, y = parse(k)
            s["state"] = "broken" if self.nav.char(p, x, y) in "+L=" else "destroyed"
        return s["state"]

    def break_door(self, edge_id):
        """Mark every tile of a connection broken (the old edge keeps its own state; this is what the tile map shows)."""
        d = next((q for q in self.nav.gm["doors"] if q["id"] == edge_id), None)
        if not d:
            return False
        for t in d["tiles"]:
            k = key(d["plane"], t[0], t[1])
            self.st["struct"][k] = {"hp": 0, "max": self.hp_of(k), "state": "broken"}
        return True

    def repair_all(self):
        for k in list(self.st["struct"]):
            if self.st["struct"][k]["state"] == "broken":
                del self.st["struct"][k]

    def smash_furniture(self, room, rng):
        """A brawl or a blast wrecks one breakable piece of furniture in a room. Returns its kind or None."""
        r = self.nav.rooms[room]
        cands = [(f["k"], key(f["plane"], f["x"], f["y"])) for f in self.nav.gm["furniture"] if f["room"] == room and f["k"] not in NO_BREAK]
        cands = [c for c in cands if self.furniture_at(c[1])]
        if not cands:
            return None
        kind, k = cands[int(rng() * len(cands)) % len(cands)]
        self.st["struct"][k] = {"hp": 0, "max": self.hp_of(k), "state": "destroyed"}
        p, x, y = parse(k)
        self.add_mark("glass" if kind in ("shelf", "cabinet") else "splinters", p, x, y, 0, 0)
        return kind

    # ------------------------------------------------------------------ light
    @staticmethod
    def daylight(hour):
        if hour < 6 or hour >= 20:
            return 0.0
        if hour < 8:
            return (hour - 6) / 2 * 0.8 + 0.1
        if hour >= 18:
            return (20 - hour) / 2 * 0.8 + 0.1 if hour < 20 else 0.0
        return 1.0

    def light_rows(self, plane, hour, power=True):
        """Light level 0-15 for every tile of a level, as strings of hex digits (one char per tile; ' ' where there is nothing)."""
        nav, day = self.nav, self.daylight(hour)
        w, h = nav.w, nav.h
        lv = [[0.0] * w for _ in range(h)]
        rows = nav.rows[plane]
        for y in range(h):
            for x in range(w):
                c = rows[y][x]
                if c == " ":
                    continue
                if c in ",gsp:~":
                    lv[y][x] = 15 * day
                elif c != "#":
                    lv[y][x] = 11.0 if power else 0.0
        for y in range(h):
            for x in range(w):
                if rows[y][x] == "=":
                    for yy in range(max(0, y - 4), min(h, y + 5)):
                        for xx in range(max(0, x - 4), min(w, x + 5)):
                            if rows[yy][xx] not in "# " and max(abs(xx - x), abs(yy - y)) <= 4:
                                lv[yy][xx] = max(lv[yy][xx], day * 8 * (1 - max(abs(xx - x), abs(yy - y)) / 5))
        srcs = [(f["x"], f["y"], 7, 10) for f in nav.gm["furniture"] if f["plane"] == plane and f["k"] == "lamp"]
        for k, (i, age) in self.st["fire"].items():
            p, fx, fy = parse(k)
            if p == plane:
                srcs.append((fx, fy, 5, 5 + 3 * i))
        for (sx, sy, rad, lev) in srcs:
            for yy in range(max(0, sy - rad), min(h, sy + rad + 1)):
                for xx in range(max(0, sx - rad), min(w, sx + rad + 1)):
                    if rows[yy][xx] != " ":
                        lv[yy][xx] = max(lv[yy][xx], lev * (1 - max(abs(xx - sx), abs(yy - sy)) / (rad + 1)))
        smoke = self.st["smoke"]
        for k, c in smoke.items():
            p, sx, sy = parse(k)
            if p == plane:
                lv[sy][sx] *= max(0.25, 1 - c / 12)
        return ["".join(" " if rows[y][x] == " " else "0123456789abcdef"[min(15, int(lv[y][x]))] for x in range(w)) for y in range(h)]

    def room_light(self, room, hour, power=True):
        """lit / dim / dark: the average light over a room's floor."""
        r = self.nav.rooms[room]
        rows = self.light_rows(r["plane"], hour, power)
        x0, y0, x1, y1 = r["rect"]
        vals = [int(rows[y][x], 16) for y in range(y0 + 1, y1 - 1) for x in range(x0 + 1, x1 - 1) if rows[y][x] != " "]
        avg = sum(vals) / len(vals) if vals else 0
        return "lit" if avg >= 8 else "dim" if avg >= 3 else "dark"

    # ------------------------------------------------------------------ items lying about
    def item_tiles(self, room_items):
        """Where each item stack in each room lies: a fixed pick among the room's free tiles, so a stack stays where it is until someone takes it."""
        out = []
        for room, stack in room_items.items():
            if room not in self.nav.rooms:
                continue
            spots = self.nav.spots(room)
            if not spots:
                continue
            used = set()
            for item in sorted(stack):
                q = stack[item]
                if q <= 0:
                    continue
                i = _h(item, room, "tile") % len(spots)
                for j in range(len(spots)):
                    t = spots[(i + j) % len(spots)]
                    if t not in used:
                        used.add(t)
                        out.append({"i": item, "q": q, "p": t[0], "x": t[1], "y": t[2]})
                        break
                else:
                    t = spots[i]                                # a small room with more kinds of thing than free tiles: they lie in a heap
                    out.append({"i": item, "q": q, "p": t[0], "x": t[1], "y": t[2]})
        return out

    # ------------------------------------------------------------------ for the viewer
    def snapshot(self, marks_limit=160):
        st = self.st
        return {"fire": [[*parse(k), v[0]] for k, v in st["fire"].items()],
                "smoke": [[*parse(k), round(v, 1)] for k, v in st["smoke"].items()],
                "water": [[*parse(k), v] for k, v in st["water"].items()],
                "struct": [[*parse(k), v["state"]] for k, v in st["struct"].items() if v["state"] != "ok"],
                "marks": st["marks"][-marks_limit:], "noises": st["noises"][-12:]}
