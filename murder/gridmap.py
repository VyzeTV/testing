"""Builds the tile map of the house and grounds from the existing room list and connections, so the locks, the keys and the hidden entrances stay exactly what the game already uses.

Run `python -m murder.gridmap` to regenerate `static/grid_map.json`; add `--ascii` to print the map.

The whole island is ONE section (no floors to switch between): every room is a 4x4 tile room (5x5 counting one shared wall), laid out as a small blueprint:
* the upper floors, the first floor, the ground floor and the cellars are separate blocks of cells on the same plane; a hub (the landings, the foyer, the cellar hall) is a corridor with its rooms
  on either side, so every ordinary connection is simply a door through a shared wall;
* the stairs are tile pairs (U and D) that carry you to the other block, and the secret passages are hidden tile pairs (h) that look like floor until found;
* outdoors is wild grass with the garden, the pool and the beach as lawn, deck and sand; buildings in the grounds (greenhouse, shed, boathouse, lighthouse, the Voting Grounds) have a door in the
  wall that faces the zone they belong to, and "path" connections are drawn as path tiles across the grass.
* Rooms keep their ids and become zones. Furniture is placed along the walls from a short priority list (what a 4x4 room can hold).

Terrain characters: '#' wall, ' ' void, floors w=wood k=tile c=carpet r=stone m=metal, ',' wild grass, 'g' lawn, 's' sand, '~' water, ':' deck, 'p' path,
doors '+' door, 'L' locked door, '=' window, 'U'/'D' stairs up/down, 'h' hidden stair or hatch (floor when not in GM view).
"""
import json
import os
import sys
from collections import deque

from .data_world import ROOMS, CAMERA_BLIND
from .world import build_edges
from .scale import MAP_SCALE

W, H = 74, 67
PLANES = ["ground"]
PLANE = "ground"
OPEN = {"garden", "pool", "beach"}
CELL = 5                                        # a 4x4 room is 5 tiles with one shared wall
SECOND, FIRST, GROUND, BASE = (2, 2), (2, 17), (2, 40), (22, 40)


def _cell(origin, c, r, w=1, h=1):
    X, Y = origin
    return (X + CELL * c, Y + CELL * r, X + CELL * (c + w) + 1, Y + CELL * (r + h) + 1)


LAYOUT = {
    # upper floors and the roof
    "master_suite": _cell(SECOND, 0, 0), "music_room": _cell(SECOND, 1, 0), "art_studio": _cell(SECOND, 2, 0), "lookout": _cell(SECOND, 5, 0), "water_tower": _cell(SECOND, 6, 0),
    "upper_landing": _cell(SECOND, 0, 1, 5, 1), "observatory": _cell(SECOND, 0, 2), "attic": _cell(SECOND, 1, 2),
    # first floor: the landing with the eight bedrooms on one side and the rest on the other
    "blue_room": _cell(FIRST, 0, 0), "green_room": _cell(FIRST, 1, 0), "yellow_room": _cell(FIRST, 2, 0), "red_room": _cell(FIRST, 3, 0),
    "violet_room": _cell(FIRST, 4, 0), "orange_room": _cell(FIRST, 5, 0), "grey_room": _cell(FIRST, 6, 0),
    "landing": _cell(FIRST, 0, 1, 7, 1),
    "white_room": _cell(FIRST, 0, 2), "bathroom": _cell(FIRST, 1, 2), "library": _cell(FIRST, 2, 2), "study": _cell(FIRST, 3, 2), "linen_store": _cell(FIRST, 4, 2),
    # ground floor
    "pantry": _cell(GROUND, 0, 0), "kitchen": _cell(GROUND, 1, 0), "laundry": _cell(GROUND, 2, 0),
    "foyer": _cell(GROUND, 0, 1), "dining_hall": _cell(GROUND, 1, 1), "lounge": _cell(GROUND, 0, 2), "games_room": _cell(GROUND, 1, 2),
    # the cellars
    "wine_cellar": _cell(BASE, 0, 0), "basement_hall": _cell(BASE, 0, 1), "cold_store": _cell(BASE, 0, 2), "boiler_room": _cell(BASE, 1, 1), "core_vault": _cell(BASE, 1, 0),
    # the grounds
    "garden": (2, 33, 40, 40), "pool": (6, 57, 16, 65), "beach": (50, 26, 66, 44),
    "greenhouse": (41, 34, 47, 40), "generator_shed": (41, 27, 47, 33), "lighthouse": (52, 2, 58, 8), "voting_grounds": (50, 14, 60, 22), "boathouse": (66, 34, 72, 40),
}
FLOOR = {
    "lookout": "r", "water_tower": "r", "upper_landing": "w", "master_suite": "c", "music_room": "c", "art_studio": "w", "observatory": "w", "attic": "w",
    "landing": "w", "blue_room": "c", "green_room": "c", "yellow_room": "c", "red_room": "c", "violet_room": "c", "orange_room": "c", "grey_room": "c", "white_room": "c",
    "bathroom": "k", "library": "c", "study": "c", "linen_store": "w",
    "foyer": "r", "dining_hall": "w", "kitchen": "k", "pantry": "k", "lounge": "c", "games_room": "w", "laundry": "k",
    "basement_hall": "r", "wine_cellar": "r", "boiler_room": "m", "cold_store": "k", "core_vault": "m",
    "greenhouse": "g", "boathouse": "w", "generator_shed": "m", "lighthouse": "r", "voting_grounds": "r",
}
# furniture templates in order of priority: (kind, anchor, count). Anchors: N S E W = along that wall inside, C = centre, D = on the deck. A 4x4 room takes the first few that fit.
BED = [("bed", "N", 1), ("wardrobe", "E", 1), ("desk", "W", 1), ("mirror", "S", 1)]
FURN = {
    "blue_room": BED, "green_room": BED, "yellow_room": BED, "red_room": BED, "violet_room": BED, "orange_room": BED, "grey_room": BED, "white_room": BED,
    "master_suite": [("bed", "N", 1), ("wardrobe", "E", 1), ("sofa", "S", 1), ("desk", "W", 1)],
    "music_room": [("piano", "C", 1), ("armchair", "S", 1), ("shelf", "N", 1)], "art_studio": [("easel", "C", 1), ("table", "W", 1), ("shelf", "N", 1)],
    "observatory": [("telescope", "C", 1), ("armchair", "E", 1), ("desk", "W", 1)], "attic": [("crate", "N", 2), ("chest", "E", 1), ("armchair", "S", 1)],
    "lookout": [("railing", "S", 3), ("telescope", "E", 1), ("bench", "W", 1)], "water_tower": [("barrel", "N", 2), ("railing", "S", 2), ("bench", "W", 1)],
    "upper_landing": [("plant", "E", 1), ("table", "N", 1), ("bench", "S", 2)], "landing": [("plant", "E", 1), ("table", "S", 1), ("bench", "S", 2), ("plant", "W", 1)],
    "foyer": [("bench", "W", 1), ("jukebox", "S", 1), ("plant", "N", 1)],
    "dining_hall": [("table", "C", 1), ("chair", "N", 2), ("chair", "S", 2)], "kitchen": [("stove", "N", 1), ("sink", "W", 1), ("table", "C", 1), ("fridge", "E", 1)],
    "pantry": [("shelf", "N", 2), ("barrel", "S", 1)],
    "lounge": [("sofa", "N", 1), ("fireplace", "E", 1), ("armchair", "W", 1), ("table", "C", 1)],
    "games_room": [("poolTable", "C", 1), ("dartboard", "W", 1), ("chessTable", "E", 1)],
    "laundry": [("washer", "N", 2), ("sink", "E", 1), ("shelf", "S", 1)], "bathroom": [("tub", "N", 1), ("sink", "E", 1), ("cabinet", "S", 1), ("mirror", "W", 1)],
    "library": [("shelf", "N", 2), ("desk", "C", 1), ("armchair", "W", 1), ("shelf", "E", 1)], "study": [("desk", "N", 1), ("radio", "W", 1), ("shelf", "E", 1), ("armchair", "S", 1)],
    "linen_store": [("shelf", "N", 2), ("shelf", "S", 1)],
    "basement_hall": [("crate", "E", 1), ("bench", "W", 1)], "wine_cellar": [("barrel", "N", 2), ("barrel", "S", 2), ("table", "C", 1)],
    "boiler_room": [("boiler", "C", 1), ("fuseBox", "E", 1), ("workbench", "S", 1)], "cold_store": [("freezer", "N", 2), ("shelf", "S", 1)], "core_vault": [("terminal", "N", 2), ("locker", "S", 2)],
    "lighthouse": [("lamp", "C", 1), ("crate", "S", 1)], "generator_shed": [("generator", "C", 1), ("workbench", "S", 1), ("barrel", "N", 1)],
    "greenhouse": [("plantBed", "N", 2), ("plantBed", "S", 1), ("bench", "C", 1)], "boathouse": [("boat", "C", 1), ("workbench", "S", 1), ("crate", "N", 1)],
    "voting_grounds": [("podium", "C", 8), ("monitor", "N", 1)],
    "garden": [("tree", "N", 6), ("bench", "C", 3), ("hammock", "S", 1), ("tree", "S", 3)], "pool": [("deckChair", "D", 4), ("bench", "D", 1)],
    "beach": [("driftwood", "S", 3), ("firepit", "C", 1), ("deckChair", "C", 2)],
}
STEP1 = {"bed", "shelf", "railing", "plantBed", "barrel", "crate", "armchair", "tree", "chair"}          # these may stand shoulder to shoulder
SECRET_SPOTS = ("tl", "tr", "bl", "br")


def _hh(*a):
    import hashlib
    return int(hashlib.md5(repr(a).encode()).hexdigest()[:8], 16)


class Grid:
    def __init__(self):
        self.t = {PLANE: [[(",") for _ in range(W)] for _ in range(H)]}
        self.rect = dict(LAYOUT)
        self.plane = {rid: PLANE for rid in LAYOUT}
        self.used = {PLANE: set()}                  # door, stair and furniture-blocking tiles
        self.doors = []
        self.links = []
        self.furn = []
        self.zone = {PLANE: {}}                     # (x,y) -> room id

    def get(self, p, x, y):
        return self.t[p][y][x] if 0 <= x < W and 0 <= y < H else "?"

    def set(self, p, x, y, ch):
        if 0 <= x < W and 0 <= y < H:
            self.t[p][y][x] = ch


def _wall_between(R, a, b):
    """The shared wall of two touching rooms: ('H' or 'V', the wall's row or column, first and last interior position along it, which of the two is above or to the left)."""
    ax0, ay0, ax1, ay1 = R[a]
    bx0, by0, bx1, by1 = R[b]
    if ax1 - 1 == bx0:
        lo, hi = max(ay0, by0) + 1, min(ay1, by1) - 2
        if hi >= lo:
            return ("V", bx0, lo, hi, a)
    if bx1 - 1 == ax0:
        lo, hi = max(ay0, by0) + 1, min(ay1, by1) - 2
        if hi >= lo:
            return ("V", ax0, lo, hi, b)
    if ay1 - 1 == by0:
        lo, hi = max(ax0, bx0) + 1, min(ax1, bx1) - 2
        if hi >= lo:
            return ("H", by0, lo, hi, a)
    if by1 - 1 == ay0:
        lo, hi = max(ax0, bx0) + 1, min(ax1, bx1) - 2
        if hi >= lo:
            return ("H", ay0, lo, hi, b)
    return None


def build_grid_map():
    g = Grid()
    edges = build_edges()
    R = g.rect
    pl = PLANE
    missing = [r for r in ROOMS if r not in R]
    if missing:
        raise ValueError(f"no place on the map for {missing}")
    # ---- rooms
    for rid, (x0, y0, x1, y1) in R.items():
        building = rid not in OPEN
        fl = FLOOR.get(rid, "w")
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                edge = xx in (x0, x1 - 1) or yy in (y0, y1 - 1)
                if building:
                    g.set(pl, xx, yy, "#" if edge else fl)
                elif rid == "garden":
                    g.set(pl, xx, yy, "g")
                elif rid == "pool":
                    g.set(pl, xx, yy, ":" if (xx < x0 + 2 or xx >= x1 - 2 or yy < y0 + 2 or yy >= y1 - 2) else "~")
                else:
                    g.set(pl, xx, yy, "~" if xx >= x1 - 3 else "s")
                if not (building and edge and g.zone[pl].get((xx, yy))):
                    g.zone[pl][(xx, yy)] = rid

    def door_char(e):
        return "L" if e["locked"] else "+"

    def add_door(e, tiles, in_a, in_b, via, ch=None):
        for (x, y) in tiles:
            g.set(pl, x, y, ch or door_char(e))
            g.used[pl].add((x, y))
        g.doors.append({"id": e["id"], "a": e["a"], "b": e["b"], "kind": e["kind"], "hidden": e["hidden"], "locked": e["locked"], "keys": list(e.get("keys", [])),
                        "needs": list(e.get("needs", [])), "cost": e["cost"], "discover": e.get("discover"), "via": via, "plane": pl,
                        "tiles": [list(t) for t in tiles], "in_a": list(in_a) if in_a else None, "in_b": list(in_b) if in_b else None})

    def free_pos(cands, keep=2):
        """First candidate tile that is not within `keep` tiles of an existing door or stair."""
        for c in cands:
            if all(abs(c[0] - u[0]) + abs(c[1] - u[1]) >= keep for u in g.used[pl]):
                return c
        return cands[0]

    def corners(rid):
        x0, y0, x1, y1 = R[rid]
        return [(x1 - 2, y1 - 2), (x0 + 1, y0 + 1), (x1 - 2, y0 + 1), (x0 + 1, y1 - 2), (x0 + 2, y1 - 2), (x1 - 3, y0 + 1)]

    def outdoor_door(e, bld, zone, ch=None):
        x0, y0, x1, y1 = R[bld]
        zx0, zy0, zx1, zy1 = R[zone]
        zc = ((zx0 + zx1) / 2, (zy0 + zy1) / 2)
        sides = []
        for side, tiles in (("N", [(xx, y0) for xx in range(x0 + 1, x1 - 1)]), ("S", [(xx, y1 - 1) for xx in range(x0 + 1, x1 - 1)]),
                            ("W", [(x0, yy) for yy in range(y0 + 1, y1 - 1)]), ("E", [(x1 - 1, yy) for yy in range(y0 + 1, y1 - 1)])):
            for (tx, ty) in tiles:
                ox, oy = {"N": (tx, ty - 1), "S": (tx, ty + 1), "W": (tx - 1, ty), "E": (tx + 1, ty)}[side]
                if g.get(pl, ox, oy) in (",", "g", "s", ":", "p") and (tx, ty) not in g.used[pl]:
                    sides.append((abs(ox - zc[0]) + abs(oy - zc[1]), side, (tx, ty), (ox, oy)))
        sides.sort()
        best = None
        for d, side, t, o in sides:
            if all(abs(t[0] - u[0]) + abs(t[1] - u[1]) >= 2 for u in g.used[pl]):
                best = (t, o, side)
                break
        if not best:
            d, side, t, o = sides[0]
            best = (t, o, side)
        t, o, side = best
        inner = {"N": (t[0], t[1] + 1), "S": (t[0], t[1] - 1), "W": (t[0] + 1, t[1]), "E": (t[0] - 1, t[1])}[side]
        add_door(e, [t], inner if e["a"] == bld else o, o if e["a"] == bld else inner, "outdoor", ch)
        return o

    def route(start, goal_zone):
        q = deque([start])
        prev = {start: None}
        goal = None
        while q:
            cur = q.popleft()
            if g.zone[pl].get(cur) == goal_zone:
                goal = cur
                break
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (cur[0] + dx, cur[1] + dy)
                if n not in prev and 0 <= n[0] < W and 0 <= n[1] < H and g.get(pl, *n) in (",", "g", "s", ":", "p"):
                    prev[n] = cur
                    q.append(n)
        path = []
        while goal and goal in prev:
            path.append(goal)
            goal = prev[goal]
        return path

    height = {"roof": 4, "second": 3, "first": 2, "ground": 1, "basement": 0}
    floor_of = {rid: ROOMS[rid][1] for rid in ROOMS}
    for e in edges:
        a, b, kind = e["a"], e["b"], e["kind"]
        if kind == "stairs":
            upper, lower = (a, b) if height[floor_of[a]] > height[floor_of[b]] else (b, a)
            tu = free_pos(corners(upper))
            g.set(pl, tu[0], tu[1], "D")
            g.used[pl].add(tu)
            tl = free_pos(corners(lower))
            g.set(pl, tl[0], tl[1], "U")
            g.used[pl].add(tl)
            g.links.append({"id": e["id"], "a": a, "b": b, "kind": "stairs", "hidden": False, "locked": e["locked"], "keys": list(e.get("keys", [])), "needs": list(e.get("needs", [])),
                            "cost": e["cost"], "discover": None, "ends": {upper: [pl, tu[0], tu[1]], lower: [pl, tl[0], tl[1]]}})
            continue
        if kind == "secret":
            ends = {}
            for rid in (a, b):
                x0, y0, x1, y1 = R[rid]
                cand = free_pos([(x0 + 2, y0 + 1), (x1 - 3, y1 - 2), (x0 + 1, y1 - 2), (x1 - 2, y0 + 1)] + corners(rid))
                g.set(pl, cand[0], cand[1], "h")
                g.used[pl].add(cand)
                ends[rid] = [pl, cand[0], cand[1]]
            g.links.append({"id": e["id"], "a": a, "b": b, "kind": "secret", "hidden": True, "locked": e["locked"], "keys": list(e.get("keys", [])), "needs": list(e.get("needs", [])),
                            "cost": e["cost"], "discover": e.get("discover"), "ends": ends})
            continue
        aopen, bopen = a in OPEN, b in OPEN
        if aopen and bopen:
            ax0, ay0, ax1, ay1 = R[a]
            bx0, by0, bx1, by1 = R[b]
            cb = ((bx0 + bx1) // 2, (by0 + by1) // 2)
            ca = ((ax0 + ax1) // 2, (ay0 + ay1) // 2)
            ta = min(((x, y) for x in range(ax0, ax1) for y in range(ay0, ay1) if g.get(pl, x, y) in "g:s"), key=lambda t: abs(t[0] - cb[0]) + abs(t[1] - cb[1]))
            tb = min(((x, y) for x in range(bx0, bx1) for y in range(by0, by1) if g.get(pl, x, y) in "g:s"), key=lambda t: abs(t[0] - ca[0]) + abs(t[1] - ca[1]))
            g.doors.append({"id": e["id"], "a": a, "b": b, "kind": kind, "hidden": e["hidden"], "locked": e["locked"], "keys": list(e.get("keys", [])), "needs": list(e.get("needs", [])),
                            "cost": e["cost"], "discover": e.get("discover"), "via": "open", "plane": pl, "tiles": [list(ta)], "in_a": list(ta), "in_b": list(tb)})
            continue
        bld, zone = (a, b) if bopen else (b, a) if aopen else (None, None)
        if bld:
            ch = "=" if kind == "window" else None
            o = outdoor_door(e, bld, zone, ch)
            if g.zone[pl].get(o) != zone:
                path = route(o, zone)
                for p in path:
                    if g.get(pl, *p) == ",":
                        g.set(pl, p[0], p[1], "p")
                g.doors[-1]["path"] = [list(p) for p in path]
            elif kind in ("path", "outside"):
                g.doors[-1]["path"] = []
            continue
        sw = _wall_between(R, a, b)
        if not sw:
            raise ValueError(f"no shared wall for connection {e['id']} ({a}-{b})")
        o, wc, lo, hi, first = sw
        mid = (lo + hi) // 2
        # keep clear of doors already in this wall
        spots = sorted(range(lo, hi + 1), key=lambda v: abs(v - mid))
        pos = next((v for v in spots if all(abs(((v, wc) if o == "H" else (wc, v))[0] - u[0]) + abs(((v, wc) if o == "H" else (wc, v))[1] - u[1]) >= 2 for u in g.used[pl])), mid)
        t = (pos, wc) if o == "H" else (wc, pos)
        before = (pos, wc - 1) if o == "H" else (wc - 1, pos)
        after = (pos, wc + 1) if o == "H" else (wc + 1, pos)
        ia, ib = (before, after) if first == a else (after, before)
        add_door(e, [t], ia, ib, "direct")

    # ---- furniture
    def interior(rid):
        x0, y0, x1, y1 = R[rid]
        return x0 + 1, y0 + 1, x1 - 1, y1 - 1

    def spread(lo, hi):
        mid = (lo + hi - 1) / 2
        return sorted(range(lo, hi), key=lambda v: abs(v - mid))

    for rid, spec in FURN.items():
        if rid not in R:
            continue
        x0, y0, x1, y1 = interior(rid) if rid not in OPEN else R[rid]
        if rid in OPEN and rid != "pool":
            x0, y0, x1, y1 = x0 + 2, y0 + 1, x1 - 2, y1 - 1
        area = (x1 - x0) * (y1 - y0)
        cap = 4 if (rid not in OPEN and area <= 16) else 999
        blocked = set(g.used[pl])
        for (dx, dy) in list(blocked):
            for ax, ay in ((1, 0), (-1, 0), (0, 1), (0, -1)):         # keep the tile in front of every door and stair clear (the diagonals are free: rooms are small)
                blocked.add((dx + ax, dy + ay))
        taken = set()
        placed_total = 0
        for kind, anchor, count in spec:
            if placed_total >= cap:
                break
            if anchor == "N":
                cells = [(xx, y0) for xx in spread(x0, x1)]
            elif anchor == "S":
                cells = [(xx, y1 - 1) for xx in spread(x0, x1)]
            elif anchor == "W":
                cells = [(x0, yy) for yy in spread(y0, y1)]
            elif anchor == "E":
                cells = [(x1 - 1, yy) for yy in spread(y0, y1)]
            elif anchor == "D":
                cells = sorted([(xx, yy) for yy in range(y0, y1) for xx in range(x0, x1) if g.get(pl, xx, yy) == ":"], key=lambda c: _hh(rid, c[0], c[1]))
            else:
                cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
                cells = sorted([(xx, yy) for yy in range(cy - 2, cy + 3) for xx in range(cx - 3, cx + 4)], key=lambda c: abs(c[0] - cx) + abs(c[1] - cy))
            placed = 0
            step = (1 if kind in STEP1 else 2) if anchor in "NSWE" else (3 if anchor == "D" else 1)
            for c in cells:
                if placed >= count or placed_total >= cap:
                    break
                if c in blocked or c in taken or not (x0 <= c[0] < x1 and y0 <= c[1] < y1):
                    continue
                if g.get(pl, *c) in ("#", " ", "~", "U", "D", "h", "+", "L", "="):
                    continue
                if any(abs(c[0] - t[0]) + abs(c[1] - t[1]) < step for t in taken):
                    continue
                taken.add(c)
                g.furn.append({"k": kind, "plane": pl, "x": c[0], "y": c[1], "room": rid})
                placed += 1
                placed_total += 1
    # cameras (TereVi): every building room outside the blind spots has one in a corner
    for rid in R:
        if rid in OPEN or rid in CAMERA_BLIND or rid in ("core_vault",):
            continue
        x0, y0, x1, y1 = R[rid]
        g.furn.append({"k": "camera", "plane": pl, "x": x0 + 1, "y": y0 + 1, "room": rid})

    # the open field only extends a few tiles around the buildings; the rest is void
    gp = g.t[pl]
    solid = [(x, y) for y in range(H) for x in range(W) if gp[y][x] not in (",", " ")]
    keep = set()
    for (x, y) in solid:
        for yy in range(max(0, y - 3), min(H, y + 4)):
            for xx in range(max(0, x - 3), min(W, x + 4)):
                keep.add((xx, yy))
    for y in range(H):
        for x in range(W):
            if gp[y][x] == "," and (x, y) not in keep:
                gp[y][x] = " "
    rooms = {rid: {"name": ROOMS[rid][0], "zone": ROOMS[rid][1], "plane": pl, "rect": list(R[rid]), "open": rid in OPEN,
                   "camera": rid not in OPEN and rid not in CAMERA_BLIND and rid != "core_vault"} for rid in ROOMS}
    planes = [{"id": PLANE, "z": 0, "rows": ["".join(row) for row in g.t[pl]]}]
    return {"version": 3, "scale": MAP_SCALE, "tile_px": 10, "w": W, "h": H, "planes": planes, "rooms": rooms, "doors": g.doors, "links": g.links, "furniture": g.furn,
            "legend": {"#": "wall", " ": "void", "w": "wood floor", "k": "tile floor", "c": "carpet", "r": "stone floor", "m": "metal floor", ",": "wild grass", "g": "lawn", "s": "sand",
                       "~": "water", ":": "deck", "p": "path", "+": "door", "L": "locked door", "=": "window", "U": "stairs up", "D": "stairs down", "h": "hidden stair or hatch"}}


def verify(gm):
    """Every room and every original connection must be present, with the same state, and reachable on the tiles. Returns a list of problems."""
    problems = []
    edges = build_edges()
    have = {d["id"]: d for d in gm["doors"]}
    have.update({d["id"]: d for d in gm["links"]})
    for e in edges:
        d = have.get(e["id"])
        if not d:
            problems.append(f"connection {e['id']} missing")
            continue
        if (d["a"], d["b"], d["kind"], bool(d["hidden"]), bool(d["locked"])) != (e["a"], e["b"], e["kind"], bool(e["hidden"]), bool(e["locked"])):
            problems.append(f"connection {e['id']} differs from the game's edge")
        if list(d.get("keys", [])) != list(e.get("keys", [])) or list(d.get("needs", [])) != list(e.get("needs", [])):
            problems.append(f"connection {e['id']} lost its keys or needs")
    for rid in ROOMS:
        if rid not in gm["rooms"]:
            problems.append(f"room {rid} missing")
    rows = {p["id"]: p["rows"] for p in gm["planes"]}
    for rid, r in gm["rooms"].items():
        x0, y0, x1, y1 = r["rect"]
        for yy in range(y0 + 1, y1 - 1):
            for xx in range(x0 + 1, x1 - 1):
                if rows[r["plane"]][yy][xx] in "# ":
                    problems.append(f"room {rid} has a wall tile inside at {xx},{yy}")
                    break
    # reachability on the tiles: a flood fill from each room's first interior tile must reach every room joined to it by a connection (hidden ones included)
    walk = set("wkcrmgsp,:+L=UDh")
    seen_links = []
    for d in gm["links"]:
        e = d["ends"]
        ks = list(e)
        seen_links.append((tuple(e[ks[0]]), tuple(e[ks[1]])))
    def flood(plane, x, y):
        out, q = {(plane, x, y)}, [(plane, x, y)]
        pair = {}
        for p1, p2 in seen_links:
            pair.setdefault(p1, []).append(p2)
            pair.setdefault(p2, []).append(p1)
        while q:
            pl, cx, cy = q.pop()
            nxt = [(pl, cx + dx, cy + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            nxt += [t for t in pair.get((pl, cx, cy), [])]
            for n in nxt:
                if n in out or not (0 <= n[1] < W and 0 <= n[2] < H):
                    continue
                if rows[n[0]][n[2]][n[1]] in walk:
                    out.add(n)
                    q.append(n)
        return out
    r0 = gm["rooms"]["foyer"]
    start = ("ground", r0["rect"][0] + 3, r0["rect"][1] + 3)
    reach = flood(*start)
    for rid, r in gm["rooms"].items():
        x0, y0, x1, y1 = r["rect"]
        if not any((r["plane"], xx, yy) in reach for yy in range(y0 + 1, y1 - 1) for xx in range(x0 + 1, x1 - 1)):
            problems.append(f"room {rid} cannot be reached from the foyer on the tile map")
    return problems


# ---------------------------------------------------------------------- the map editor's side: a saved custom map and its validation
ALLOWED = set("#wkcrm,gs~:p+L=UDh ")
FURN_KINDS = {f[0] for spec in FURN.values() for f in spec} | {"camera"}


def custom_path():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(os.environ.get("MC_DATA_DIR") or base, "state", "grid_map.json")


def load_custom():
    """The map the GM edited and saved, if there is one and it still passes validation."""
    try:
        with open(custom_path(), "r", encoding="utf-8") as f:
            gm = json.load(f)
    except (OSError, ValueError):
        return None
    return gm if not validate_edit(gm) else None


def save_custom(gm):
    problems = validate_edit(gm)
    if problems:
        return problems
    os.makedirs(os.path.dirname(custom_path()), exist_ok=True)
    with open(custom_path(), "w", encoding="utf-8") as f:
        json.dump(gm, f, separators=(",", ":"))
    return []


def reset_custom():
    try:
        os.remove(custom_path())
        return True
    except OSError:
        return False


def validate_edit(gm):
    """Checks an edited map: same shape and rooms as the generated one, only known tiles, the doors, stairs and hatches of every connection still in place, furniture standing on floor
    inside its room, and every room still reachable. Returns a list of problems (empty = fine)."""
    problems = []
    try:
        base = build_grid_map()
        if gm.get("w") != W or gm.get("h") != H or [p["id"] for p in gm["planes"]] != PLANES:
            return ["the map must keep its size and its level"]
        for p in gm["planes"]:
            if len(p["rows"]) != H or any(len(r) != W or set(r) - ALLOWED for r in p["rows"]):
                return [f"level {p['id']} has rows of the wrong length or tiles that do not exist"]
        for rid, r in base["rooms"].items():
            g = gm["rooms"].get(rid)
            if not g or g["rect"] != r["rect"] or g["plane"] != r["plane"] or g["open"] != r["open"]:
                problems.append(f"room {rid} was moved, resized or removed (rooms cannot be edited here)")
        if [ (d["id"], d["tiles"], d["plane"]) for d in gm["doors"] ] != [ (d["id"], d["tiles"], d["plane"]) for d in base["doors"] ] or [l["id"] for l in gm["links"]] != [l["id"] for l in base["links"]] or any(l["ends"] != b["ends"] for l, b in zip(gm["links"], base["links"])):
            problems.append("the doors, stairs and hidden connections cannot be moved or removed")
        rows = {p["id"]: p["rows"] for p in gm["planes"]}
        for d in gm["doors"]:
            if d["via"] != "open":
                for t in d["tiles"]:
                    if rows[d["plane"]][t[1]][t[0]] not in "+L=":
                        problems.append(f"connection {d['id']} lost its door at {t[0]},{t[1]}")
        for l in gm["links"]:
            for e in l["ends"].values():
                if rows[e[0]][e[2]][e[1]] not in "UDh":
                    problems.append(f"connection {l['id']} lost its stairs or hatch at {e[1]},{e[2]}")
        seen = set()
        for f in gm["furniture"]:
            k = (f["plane"], f["x"], f["y"], f["k"])
            if f["k"] not in FURN_KINDS or f.get("room") not in gm["rooms"]:
                problems.append(f"unknown furniture {f['k']} or room")
            elif f["k"] != "camera" and rows[f["plane"]][f["y"]][f["x"]] in "#+L=UDh ~":
                problems.append(f"{f['k']} stands on {rows[f['plane']][f['y']][f['x']]!r} at {f['x']},{f['y']}")
            if k in seen:
                problems.append(f"two {f['k']} on one tile at {f['x']},{f['y']}")
            seen.add(k)
        if not problems:
            problems += verify(gm)
    except (KeyError, TypeError, IndexError, ValueError) as e:
        problems.append(f"the map is malformed ({type(e).__name__}: {e})")
    return problems[:20]


def ascii_dump(gm):
    out = []
    for p in gm["planes"]:
        out.append(f"=== {p['id']} (z={p['z']})")
        out.extend(p["rows"])
    return "\n".join(out)


def main(argv):
    gm = build_grid_map()
    probs = verify(gm)
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "grid_map.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(gm, f, separators=(",", ":"))
    print(f"wrote {path}: {len(gm['rooms'])} rooms, {len(gm['doors'])} doors, {len(gm['links'])} stair/secret links, {len(gm['furniture'])} furniture; problems: {len(probs)}")
    for p in probs:
        print("  PROBLEM:", p)
    if "--ascii" in argv:
        print(ascii_dump(gm))
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
