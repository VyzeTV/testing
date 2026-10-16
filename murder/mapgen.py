"""Draws the first version of the island and the house as plan files (murder/maps/). Run `python -m murder.mapgen` to (re)write them.

The plan files are the map's source of truth: murder/gridmap.py reads them, works out the doors and stairs, checks them against the room graph and builds
static/grid_map.json. This module is only the drawing tool that produced the first version; once the plans are edited by hand (or in the map editor), regenerating
overwrites those edits, so it refuses to run over existing plans unless given --force.

Coordinates are metres: one tile is 1 m. All five levels share the island's frame, so a staircase, a shaft or a hatch sits at the same (x, y) on the two levels
it joins. Rooms are sized from their contents; bedrooms are the smallest at 3 x 4 or 3 x 5 m.
"""
import hashlib
import json
import math
import os
import sys

W, H = 160, 120
HERE = os.path.dirname(os.path.abspath(__file__))
MAPS = os.path.join(HERE, "maps")
PLANES = [("basement", -1), ("ground", 0), ("first", 1), ("second", 2), ("roof", 3)]
HX, HY = 60, 46                    # the house's north-west corner on the island
CODES = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
OUTDOOR = (None, "garden", "beach", "pool", "sea")


def _r(x, y, s=0):
    """A stable pseudo-random number in [0, 1) for a tile (no game randomness is used to draw the map)."""
    return int(hashlib.md5(f"{x},{y},{s}".encode()).hexdigest()[:8], 16) / 2 ** 32


def _adiff(a, b):
    d = abs(a - b) % (2 * math.pi)
    return 2 * math.pi - d if d > math.pi else d


class Level:
    def __init__(self, pid):
        self.id = pid
        self.t = [[" "] * W for _ in range(H)]
        self.z = [[None] * W for _ in range(H)]

    def get(self, x, y):
        return self.t[y][x] if 0 <= x < W and 0 <= y < H else " "

    def put(self, x, y, ch, zone="keep"):
        if 0 <= x < W and 0 <= y < H:
            self.t[y][x] = ch
            if zone != "keep":
                self.z[y][x] = zone

    def zone(self, x, y):
        return self.z[y][x] if 0 <= x < W and 0 <= y < H else None


def room(lv, rid, x0, y0, w, h, floor, ox=HX, oy=HY):
    """A walled room: interior w x h from (x0, y0) in local coordinates; its walls are shared with neighbours."""
    X0, Y0 = ox + x0, oy + y0
    for y in range(Y0 - 1, Y0 + h + 1):
        for x in range(X0 - 1, X0 + w + 1):
            if X0 <= x < X0 + w and Y0 <= y < Y0 + h:
                lv.put(x, y, floor, rid)
            elif lv.get(x, y) not in "+L=":
                if lv.zone(x, y) in OUTDOOR or lv.get(x, y) == "#":
                    lv.put(x, y, "#", None)


def marks(lv, items, ox=HX, oy=HY):
    for x, y, ch in items:
        lv.put(ox + x, oy + y, ch)


# ---------------------------------------------------------------------------------------------- the island (ground level)
def island(g):
    for y in range(H):
        for x in range(W):
            dx, dy = (x - 80) / 68, (y - 60) / 50
            th, r = math.atan2(dy, dx), math.hypot(dx, dy)
            R = (1 + 0.07 * math.sin(3 * th + 0.6) + 0.05 * math.sin(5 * th + 2.1) + 0.03 * math.sin(11 * th + 0.3)
                 + 0.18 * math.exp(-((_adiff(th, -0.75) / 0.28) ** 2)) + 0.06 * math.exp(-((_adiff(th, 0.9) / 0.5) ** 2)))
            d = r / R
            if d > 1.1:
                g.put(x, y, "~", None)
                continue
            if d > 1.0:
                g.put(x, y, "a", "sea")
                continue
            head, beach, cove = _adiff(th, -0.75) < 0.42, _adiff(th, 0.75) < 0.5, _adiff(th, -0.15) < 0.32
            t, z = ",", "garden"
            if head:
                t = "C" if d > 0.95 else "q" if d > 0.62 else ","
            elif cove and d > 0.74:
                t, z = ("s", "beach") if d > 0.77 else ("C", "garden")
                if _adiff(th, -0.40) < 0.04 and d < 0.84:
                    t, z = "K", "garden"
            elif beach:
                t, z = ("s", "beach") if d > 0.80 else ("n", "beach") if d > 0.72 else (",", "garden")
            else:
                t, z = ("s", "beach") if d > 0.91 else (",", "garden")
            g.put(x, y, t, z)
    # shallow water belongs to the beach where it touches sand, otherwise to the garden (cliffs, rocks)
    for y in range(H):
        for x in range(W):
            if g.zone(x, y) == "sea":
                near = [g.zone(x + a, y + b) for a in (-2, -1, 0, 1, 2) for b in (-2, -1, 0, 1, 2)]
                g.z[y][x] = "beach" if "beach" in near else "garden"


def snap(lv, x, y, zone, chars):
    """The nearest tile to (x, y) in this zone with one of these terrain characters."""
    best = None
    for yy in range(y - 12, y + 13):
        for xx in range(x - 12, x + 13):
            if lv.zone(xx, yy) == zone and lv.get(xx, yy) in chars:
                d = abs(xx - x) + abs(yy - y)
                if best is None or d < best[0]:
                    best = (d, xx, yy)
    return (best[1], best[2]) if best else (x, y)


def woods(g, x0, y0, x1, y1, dens, seed):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if g.get(x, y) != ",":
                continue
            edge = min(x - x0, x1 - x, y - y0, y1 - y)
            k = dens * min(1.0, (edge + 1) / 4)
            v = _r(x, y, seed)
            if v < k:
                g.put(x, y, "T")
            elif v < k + 0.1:
                g.put(x, y, "b")


def open_clearings(g, start, walk=",gspa:fBjKqn+LUDhlkwcrm", plants="TbH"):
    """Random woods can ring a clearing with trees. Find every walkable tile that cannot be reached from `start` and clear the plants beside it until it can."""
    for _ in range(60):
        seen, stack = {start}, [start]
        while stack:
            x, y = stack.pop()
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if (nx, ny) not in seen and g.get(nx, ny) in walk:
                    seen.add((nx, ny))
                    stack.append((nx, ny))
        cut = [(x, y) for y in range(H) for x in range(W) if g.get(x, y) in walk and (x, y) not in seen]
        if not cut:
            return
        opened = False
        for x, y in cut:
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if g.get(nx, ny) in plants and any(g.get(qx, qy) in walk and (qx, qy) in seen for qx, qy in ((nx + 1, ny), (nx - 1, ny), (nx, ny + 1), (nx, ny - 1))):
                    g.put(nx, ny, ",")
                    opened = True
        if not opened:                                         # a pocket two plants deep: thin the plants next to it and try again
            for x, y in cut:
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if g.get(nx, ny) in plants:
                        g.put(nx, ny, ",")


def line(g, pts, ch, width=2, over=",gTbnsq"):
    """A path, tunnel or jetty along the points. Diagonal steps get a corner tile, so a one-tile line can be walked end to end."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        prev = None
        for k in range(n + 1):
            x, y = round(x0 + (x1 - x0) * k / n), round(y0 + (y1 - y0) * k / n)
            cells = [(x, y)] if prev is None or (prev[0] == x or prev[1] == y) else [(x, prev[1]), (x, y)]
            prev = (x, y)
            for cx, cy in cells:
                for a in range(width):
                    for b in range(width):
                        if g.get(cx + a, cy + b) in over:
                            g.put(cx + a, cy + b, ch)


def building(g, rid, x0, y0, x1, y1, floor):
    """An outbuilding on the island, walls on its outline (island coordinates, inclusive)."""
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if x in (x0, x1) or y in (y0, y1):
                g.put(x, y, "#", None)
            else:
                g.put(x, y, floor, rid)


# ---------------------------------------------------------------------------------------------- furniture
FURN = []


def f(plane, kind, x, y, w=1, h=1, rid=None, local=True):
    FURN.append({"k": kind, "plane": plane, "x": (HX + x) if local else x, "y": (HY + y) if local else y, "w": w, "h": h, "room": rid})


def bedroom(plane, rid, x0, y0, door_side="S"):
    """3 wide x 4 or 5 deep: bed against the far wall, wardrobe, desk and mirror, the tile inside the door left clear."""
    if door_side == "S":
        f(plane, "bed", x0, y0, 1, 2, rid)
        f(plane, "wardrobe", x0 + 2, y0, 1, 1, rid)
        f(plane, "desk", x0 + 2, y0 + 2, 1, 1, rid)
        f(plane, "mirror", x0, y0 + 3, 1, 1, rid)
    else:                                                   # door on the north wall (N)
        f(plane, "bed", x0, y0 + 2, 1, 2, rid)
        f(plane, "wardrobe", x0 + 2, y0 + 3, 1, 1, rid)
        f(plane, "desk", x0 + 2, y0 + 1, 1, 1, rid)
        f(plane, "mirror", x0, y0 + 1, 1, 1, rid)


def draw():
    FURN.clear()
    L = {pid: Level(pid) for pid, _ in PLANES}
    g, b, f1, f2, rf = L["ground"], L["basement"], L["first"], L["second"], L["roof"]
    island(g)
    woods(g, 92, 10, 120, 42, 0.42, 1)
    woods(g, 14, 14, 46, 34, 0.34, 2)
    woods(g, 100, 70, 122, 84, 0.30, 3)

    # ---- the hedge maze (south-west of the house): lawn, a grid of hedges with gaps, flower beds where they cross
    MX0, MY0, MX1, MY1 = 22, 68, 52, 92
    for y in range(MY0, MY1 + 1):
        for x in range(MX0, MX1 + 1):
            if g.get(x, y) not in ",T b":
                continue
            gx, gy = (x - MX0) % 5 == 0, (y - MY0) % 5 == 0
            border = x in (MX0, MX1) or y in (MY0, MY1)
            t = "g"
            if border:
                t = "H"
            elif (gx or gy) and not (gx and gy) and _r((x - MX0) // 5 * 7 + gx, (y - MY0) // 5 * 3 + gy, 9) < 0.62:
                t = "H"
            if not border and gx and gy:
                t = "f"
            g.put(x, y, t)
    for x, y in ((37, 68), (38, 68), (52, 80), (52, 81)):          # the two ways in
        g.put(x, y, "g")
    # ---- lawns around the house and the pool deck (west of the house, outside the games room)
    for y in range(HY - 3, HY + 23):
        for x in range(HX - 3, HX + 31):
            if g.get(x, y) in ",Tb":
                g.put(x, y, "g")
    for y in range(44, 59):
        for x in range(42, 60):
            water = 45 <= x <= 55 and 47 <= y <= 55
            g.put(x, y, "~" if water else ":", "pool")

    # ---- outbuildings
    building(g, "greenhouse", 30, 50, 35, 57, "k")
    building(g, "generator_shed", 52, 34, 56, 39, "m")
    building(g, "lighthouse", 123, 25, 129, 31, "r")
    building(g, "voting_grounds", 133, 47, 141, 55, "r")
    building(g, "boathouse", 72, 94, 78, 101, "w")
    for y in range(102, 104):                                     # sand in front of the boathouse doors
        for x in range(72, 79):
            if g.get(x, y) in ",ga":
                g.put(x, y, "s", "beach")

    # ---- paths, the boardwalk over the dunes, the jetty
    paths = [
        [(HX + 12, HY + 20), (HX + 12, HY + 30), (75, 88), (75, 93)],          # front door to the boathouse
        [(73, 82), (95, 85), (110, 86)],                                     # to the beach
        [(HX + 28, HY + 6), (92, 50), (100, 40), (110, 32), (122, 28)],       # laundry door through the woods to the lighthouse
        [(128, 32), (130, 38), (131, 43)],                                   # lighthouse to the cliff steps
        [(133, 45), (136, 46)],
        [(41, 44), (41, 40), (54, 41), (54, 40)],                            # pool deck to the shed
        [(41, 44), (36, 49), (36, 53)],                                      # to the greenhouse
        [(41, 59), (40, 66), (37, 67)],                                      # to the maze
    ]
    for p in paths:
        line(g, p, "p")
    line(g, [(110, 86), (118, 90), (124, 92)], "B", 2, over="ndsg,")
    line(g, [(83, 100), (83, 114)], "j", 2, over="sna~,g")
    for y in range(100, 115):
        for x in range(83, 85):
            if g.get(x, y) == "j":
                g.z[y][x] = "beach"

    # ============================================================== the house
    # ---- ground floor: the foyer is the hub (front door, stairs up and down, dining, lounge)
    room(g, "games_room", 1, 1, 7, 8, "w")
    room(g, "pantry", 13, 4, 3, 5, "k")
    room(g, "kitchen", 17, 4, 6, 5, "k")
    room(g, "laundry", 24, 4, 3, 5, "k")
    room(g, "lounge", 1, 10, 7, 9, "c")
    room(g, "foyer", 9, 10, 7, 9, "r")
    room(g, "dining_hall", 17, 10, 8, 5, "w")
    marks(g, [(16, 12, "+"), (19, 9, "+"), (16, 6, "+"), (8, 17, "+"), (4, 9, "+"), (23, 6, "+"), (12, 19, "+"), (0, 4, "+"), (19, 3, "="), (27, 6, "+"),
              (10, 19, "="), (14, 19, "="), (0, 13, "="), (0, 16, "="), (25, 12, "="), (4, 0, "="),
              (9, 11, "U"), (9, 12, "U"), (9, 13, "U"), (9, 14, "U"), (9, 15, "U"), (15, 15, "D"), (15, 16, "D"), (15, 17, "D"),
              (14, 5, "h"), (18, 4, "h")])
    f("ground", "poolTable", 3, 4, 3, 2, "games_room"); f("ground", "dartboard", 7, 2, 1, 1, "games_room"); f("ground", "chessTable", 2, 7, 1, 1, "games_room")
    f("ground", "armchair", 6, 7, 1, 1, "games_room"); f("ground", "radio", 1, 1, 1, 1, "games_room")
    f("ground", "shelf", 13, 4, 1, 1, "pantry"); f("ground", "shelf", 15, 4, 1, 1, "pantry"); f("ground", "shelf", 13, 8, 1, 1, "pantry"); f("ground", "barrel", 15, 8, 1, 1, "pantry")
    f("ground", "stove", 20, 4, 2, 1, "kitchen"); f("ground", "fridge", 22, 4, 1, 1, "kitchen"); f("ground", "sink", 17, 8, 1, 1, "kitchen"); f("ground", "table", 18, 6, 2, 2, "kitchen")
    f("ground", "washer", 24, 4, 1, 1, "laundry"); f("ground", "washer", 25, 4, 1, 1, "laundry"); f("ground", "sink", 24, 8, 1, 1, "laundry"); f("ground", "shelf", 26, 8, 1, 1, "laundry")
    f("ground", "table", 18, 11, 6, 2, "dining_hall")
    for x in (18, 20, 21, 22, 23):
        f("ground", "chair", x, 10, 1, 1, "dining_hall")
    for x in (18, 19, 20, 21, 22, 23):
        f("ground", "chair", x, 13, 1, 1, "dining_hall")
    f("ground", "sofa", 2, 11, 3, 1, "lounge"); f("ground", "sofa", 2, 16, 3, 1, "lounge"); f("ground", "armchair", 6, 12, 1, 1, "lounge"); f("ground", "armchair", 6, 14, 1, 1, "lounge")
    f("ground", "fireplace", 1, 13, 1, 2, "lounge"); f("ground", "table", 3, 13, 2, 2, "lounge"); f("ground", "jukebox", 7, 10, 1, 1, "lounge")
    f("ground", "bench", 11, 10, 2, 1, "foyer"); f("ground", "plant", 14, 10, 1, 1, "foyer"); f("ground", "plant", 10, 18, 1, 1, "foyer"); f("ground", "mirror", 14, 18, 1, 1, "foyer")

    # ---- cellar: the stairs come down into the basement hall; the wine cellar sits under the pantry (SP-1); the smugglers' tunnel (SP-2) runs from it to the headland
    room(b, "wine_cellar", 10, 3, 6, 5, "r")
    room(b, "basement_hall", 13, 9, 3, 9, "r")
    room(b, "boiler_room", 17, 10, 5, 4, "m")
    room(b, "cold_store", 8, 11, 4, 4, "k")
    marks(b, [(14, 8, "+"), (16, 11, "+"), (12, 12, "+"), (15, 17, "U"), (14, 5, "h"), (10, 5, "h")])
    f("basement", "barrel", 11, 3, 1, 1, "wine_cellar"); f("basement", "barrel", 13, 3, 1, 1, "wine_cellar"); f("basement", "barrel", 11, 7, 1, 1, "wine_cellar")
    f("basement", "barrel", 13, 7, 1, 1, "wine_cellar"); f("basement", "table", 12, 5, 1, 1, "wine_cellar")
    f("basement", "crate", 13, 10, 1, 1, "basement_hall"); f("basement", "bench", 13, 13, 1, 2, "basement_hall")
    f("basement", "boiler", 20, 11, 2, 2, "boiler_room"); f("basement", "fuseBox", 21, 10, 1, 1, "boiler_room"); f("basement", "workbench", 17, 13, 2, 1, "boiler_room")
    f("basement", "freezer", 8, 11, 2, 1, "cold_store"); f("basement", "shelf", 8, 14, 1, 1, "cold_store")
    # the tunnel: a dark stone passage, one metre wide, under the island to the headland
    tunnel = [(HX + 8, HY + 5), (HX + 8, 40), (100, 36), (134, 36), (134, 34), (131, 34)]
    line(b, tunnel, "r", 1, over=" ")
    b.put(HX + 8, HY + 5, "h")                                   # its mouth behind the grate, and its far end under the headland
    b.put(131, 34, "h")
    # TereVi's core vault, under the lighthouse
    building(b, "core_vault", 118, 21, 129, 30, "m")
    marks(b, [(125, 29, "h")], 0, 0)
    for args in (("terminal", 121, 22, 2, 1), ("terminal", 125, 22, 2, 1), ("terminal", 119, 24, 1, 2), ("terminal", 128, 24, 1, 2), ("generator", 123, 25, 2, 2),
                 ("locker", 119, 29, 1, 1), ("locker", 121, 29, 1, 1), ("locker", 127, 29, 1, 1), ("locker", 128, 29, 1, 1)):
        f("basement", *args, "core_vault", False)

    # ---- first floor: the landing (a corridor and the gallery over the foyer) reaches every room
    room(f1, "blue_room", 1, 1, 3, 5, "c"); room(f1, "green_room", 5, 1, 3, 5, "c"); room(f1, "yellow_room", 9, 1, 3, 5, "c"); room(f1, "red_room", 13, 1, 3, 5, "c")
    room(f1, "linen_store", 17, 1, 2, 5, "w"); room(f1, "violet_room", 20, 1, 3, 5, "c"); room(f1, "white_room", 24, 1, 3, 5, "c")
    room(f1, "landing", 1, 7, 26, 2, "w")
    room(f1, "library", 1, 10, 7, 4, "c")
    room(f1, "orange_room", 17, 10, 3, 4, "c")
    room(f1, "study", 21, 10, 6, 4, "c")
    room(f1, "grey_room", 5, 15, 3, 4, "c")
    room(f1, "bathroom", 17, 15, 4, 4, "k")
    # the gallery: part of the landing, open in the middle to the foyer below
    for y in range(9, 19):
        for x in range(9, 16):
            f1.put(HX + x, HY + y, "v" if (10 <= x <= 14 and 11 <= y <= 17) else "w", "landing")
    for x in range(8, 17):                                       # its outer walls
        if f1.get(HX + x, HY + 19) != "+":
            f1.put(HX + x, HY + 19, "#", None)
    for y in range(9, 20):
        for x in (8, 16):
            if f1.zone(HX + x, HY + y) is None and f1.get(HX + x, HY + y) not in "+L":
                f1.put(HX + x, HY + y, "#", None)
    marks(f1, [(2, 6, "+"), (6, 6, "+"), (10, 6, "+"), (14, 6, "+"), (17, 6, "+"), (21, 6, "+"), (25, 6, "+"), (4, 9, "+"), (18, 9, "+"), (23, 9, "L"),
               (8, 16, "+"), (16, 16, "+"), (9, 11, "D"), (23, 7, "U"), (24, 7, "U"), (25, 7, "U"), (26, 7, "U"), (1, 12, "h"), (18, 4, "h"),
               (0, 3, "="), (0, 11, "="), (27, 3, "="), (27, 11, "="), (2, 0, "="), (10, 0, "="), (21, 0, "=")])
    for x0, rid in ((1, "blue_room"), (5, "green_room"), (9, "yellow_room"), (13, "red_room"), (20, "violet_room"), (24, "white_room")):
        bedroom("first", rid, x0, 1, "S")
    bedroom("first", "orange_room", 17, 10, "N")
    f("first", "bed", 5, 15, 1, 2, "grey_room"); f("first", "wardrobe", 5, 18, 1, 1, "grey_room"); f("first", "desk", 6, 18, 1, 1, "grey_room"); f("first", "mirror", 7, 18, 1, 1, "grey_room")
    f("first", "shelf", 17, 1, 1, 1, "linen_store"); f("first", "shelf", 18, 1, 1, 1, "linen_store"); f("first", "shelf", 17, 3, 1, 1, "linen_store")
    for x in (1, 2, 6, 7):
        f("first", "shelf", x, 10, 1, 1, "library")
    f("first", "desk", 4, 12, 1, 1, "library"); f("first", "armchair", 2, 13, 1, 1, "library"); f("first", "armchair", 6, 13, 1, 1, "library")
    f("first", "desk", 25, 11, 1, 1, "study"); f("first", "radio", 26, 10, 1, 1, "study"); f("first", "shelf", 21, 10, 1, 1, "study"); f("first", "armchair", 22, 12, 1, 1, "study")
    f("first", "terminal", 26, 13, 1, 1, "study")
    f("first", "tub", 19, 15, 2, 1, "bathroom"); f("first", "sink", 17, 18, 1, 1, "bathroom"); f("first", "cabinet", 20, 18, 1, 1, "bathroom"); f("first", "mirror", 18, 18, 1, 1, "bathroom")
    f("first", "plant", 1, 8, 1, 1, "landing"); f("first", "bench", 12, 9, 2, 1, "landing"); f("first", "plant", 15, 18, 1, 1, "landing")

    # ---- second floor: the upper landing; the attic (only through the hidden stair from the library, SP-3); the lower roof outside the window
    room(f2, "master_suite", 1, 1, 6, 5, "c"); room(f2, "music_room", 8, 1, 5, 5, "c"); room(f2, "art_studio", 14, 1, 5, 5, "w"); room(f2, "observatory", 20, 1, 5, 5, "w")
    room(f2, "upper_landing", 1, 7, 26, 2, "w")
    room(f2, "attic", 1, 10, 9, 7, "w")
    for y in range(-3, 0):                                       # the master suite's balcony, railed
        for x in range(0, 8):
            edge = y == -3 or x in (0, 7)
            f2.put(HX + x, HY + y, "x" if edge else ":", None if edge else "master_suite")
    f2.put(HX + 3, HY + 0, ":", "master_suite")                  # the balcony doorway
    for y in range(9, 20):
        for x in range(0, 28):
            if f2.get(HX + x, HY + y) == " " and f1.get(HX + x, HY + y) != " ":
                f2.put(HX + x, HY + y, "S", None)
    marks(f2, [(3, 6, "L"), (10, 6, "+"), (16, 6, "+"), (22, 6, "+"), (26, 7, "D"), (1, 7, "U"), (2, 7, "U"), (3, 7, "U"), (1, 12, "h"), (16, 9, "="),
               (0, 3, "="), (25, 3, "="), (13, 0, "="), (19, 0, "=")])
    f("second", "bed", 1, 1, 2, 2, "master_suite"); f("second", "wardrobe", 6, 1, 1, 1, "master_suite"); f("second", "sofa", 5, 5, 2, 1, "master_suite"); f("second", "desk", 6, 3, 1, 1, "master_suite")
    f("second", "piano", 9, 2, 2, 1, "music_room"); f("second", "armchair", 12, 4, 1, 1, "music_room"); f("second", "shelf", 8, 1, 1, 1, "music_room")
    f("second", "easel", 15, 2, 1, 1, "art_studio"); f("second", "easel", 17, 2, 1, 1, "art_studio"); f("second", "table", 14, 4, 1, 2, "art_studio"); f("second", "shelf", 18, 1, 1, 1, "art_studio")
    f("second", "telescope", 22, 2, 1, 1, "observatory"); f("second", "armchair", 24, 4, 1, 1, "observatory"); f("second", "desk", 20, 4, 1, 1, "observatory")
    f("second", "crate", 6, 10, 1, 1, "attic"); f("second", "crate", 8, 10, 1, 1, "attic"); f("second", "crate", 8, 12, 1, 1, "attic"); f("second", "chest", 9, 15, 1, 1, "attic")
    f("second", "armchair", 4, 15, 1, 1, "attic")
    f("second", "plant", 13, 8, 1, 1, "upper_landing"); f("second", "bench", 19, 8, 2, 1, "upper_landing")

    # ---- the roof: the lookout deck and the water tower walkway; the rest is roof slope (a fall)
    for y in range(0, 18):
        for x in range(0, 28):
            if f2.get(HX + x, HY + y) not in " x:S":
                rf.put(HX + x, HY + y, "S", None)
    room(rf, "lookout", 1, 1, 9, 7, ":")
    room(rf, "water_tower", 11, 1, 9, 7, "m")
    marks(rf, [(1, 7, "D"), (10, 4, "+")])
    f("roof", "telescope", 8, 2, 1, 1, "lookout"); f("roof", "bench", 5, 6, 2, 1, "lookout"); f("roof", "railing", 1, 1, 3, 1, "lookout")
    f("roof", "barrel", 14, 3, 2, 2, "water_tower"); f("roof", "barrel", 17, 3, 1, 1, "water_tower"); f("roof", "bench", 12, 7, 2, 1, "water_tower")

    # ---- outbuildings' furniture, doors and hatches (island coordinates)
    marks(g, [(35, 53, "+"), (54, 39, "+"), (123, 28, "+"), (133, 51, "+"), (75, 101, "L"), (125, 29, "h"), (127, 27, "h")], 0, 0)
    for args in (("plantBed", 31, 51, 2, 1, "greenhouse"), ("plantBed", 33, 51, 2, 1, "greenhouse"), ("plantBed", 31, 56, 2, 1, "greenhouse"), ("bench", 33, 54, 1, 1, "greenhouse"),
                 ("generator", 54, 36, 1, 1, "generator_shed"), ("workbench", 53, 38, 1, 1, "generator_shed"), ("barrel", 53, 35, 1, 1, "generator_shed"),
                 ("lamp", 126, 26, 1, 1, "lighthouse"), ("crate", 124, 30, 1, 1, "lighthouse"),
                 ("monitor", 137, 48, 1, 1, "voting_grounds"),
                 ("boat", 74, 96, 2, 3, "boathouse"), ("workbench", 73, 95, 1, 1, "boathouse"), ("crate", 77, 95, 1, 1, "boathouse")):
        f("ground", args[0], args[1], args[2], args[3], args[4], args[5], False)
    for i in range(8):                                             # eight podiums in a ring at the Voting Grounds
        a = 2 * math.pi * i / 8
        f("ground", "podium", round(137.5 + 2.4 * math.cos(a)), round(51 + 2.4 * math.sin(a)), 1, 1, "voting_grounds", False)
    for x, y in ((44, 45), (47, 57), (52, 57), (57, 46)):
        f("ground", "deckChair", x, y, 1, 1, "pool", False)
    f("ground", "bench", 58, 52, 1, 1, "pool", False)
    for x, y, k in ((64, 70, "bench"), (86, 44, "bench"), (37, 63, "bench"), (66, 40, "hammock"), (99, 44, "bench")):
        f("ground", k, x, y, 1, 1, "garden", False)
    for x, y, k in ((112, 95, "driftwood"), (126, 84, "driftwood"), (98, 106, "driftwood"), (116, 98, "firepit"), (114, 100, "deckChair"), (118, 100, "deckChair")):
        x, y = snap(g, x, y, "beach", "sn")
        f("ground", k, x, y, 1, 1, "beach", False)

    secrets = [
        {"id": "SP-1", "ends": [["ground", HX + 14, HY + 5], ["basement", HX + 14, HY + 5]], "note": "a sliding wall in the pantry onto a stair down"},
        {"id": "SP-2", "ends": [["basement", HX + 10, HY + 5], ["basement", HX + 8, HY + 5]], "note": "the rusted grate behind the crates into the smugglers' tunnel"},
        {"id": "SP-2", "ends": [["basement", 131, 34], ["ground", 127, 27]], "note": "the tunnel's far end, a ladder up into the lighthouse"},
        {"id": "SP-3", "ends": [["first", HX + 1, HY + 12], ["second", HX + 1, HY + 12]], "note": "the bookcase door onto a hidden stair to the attic"},
        {"id": "SP-4", "ends": [["ground", HX + 18, HY + 4], ["first", HX + 18, HY + 4]], "note": "the dumbwaiter shaft from the kitchen to the linen store"},
        {"id": "SP-5", "ends": [["ground", 125, 29], ["basement", 125, 29]], "note": "the floor hatch in the lighthouse onto the steps down to the vault"},
    ]
    labels = {"garden": [70, 36], "beach": [118, 96], "pool": [50, 60]}
    open_clearings(g, (70, 36))
    return L, secrets, labels


def write(force=False):
    L, secrets, labels = draw()
    os.makedirs(MAPS, exist_ok=True)
    if not force and os.path.exists(os.path.join(MAPS, "map.json")):
        raise SystemExit("murder/maps already holds a plan; regenerating would overwrite any edits. Run with --force to overwrite.")
    zones = sorted({z for lv in L.values() for row in lv.z for z in row if z})
    if len(zones) > len(CODES):
        raise SystemExit("too many rooms for the zone codes")
    code = {z: CODES[i] for i, z in enumerate(zones)}
    for pid, _ in PLANES:
        lv = L[pid]
        with open(os.path.join(MAPS, f"{pid}.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join("".join(r) for r in lv.t) + "\n")
        with open(os.path.join(MAPS, f"{pid}.zones.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join("".join(code[z] if z else "." for z in r) for r in lv.z) + "\n")
    meta = {"version": 4, "tile_m": 1, "w": W, "h": H, "planes": [{"id": p, "z": z} for p, z in PLANES], "zone_codes": {c: z for z, c in code.items()},
            "furniture": FURN, "secrets": secrets, "labels": labels}
    with open(os.path.join(MAPS, "map.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    print(f"wrote {len(PLANES)} levels, {len(zones)} zones, {len(FURN)} pieces of furniture to {MAPS}")


if __name__ == "__main__":
    write(force="--force" in sys.argv)
