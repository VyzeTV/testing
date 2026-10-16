"""Walking on the tile map: which tiles can be stood on, where people stand in a room, and A* routes between tiles (across levels through stairs and, when allowed, hidden hatches).

GridNav is built from the generated grid map (murder/gridmap.py) and is pure: it holds no game state. The live planner (livetimeline.py) uses it to turn the engine's room-level moves
into tile paths. Furniture blocks tiles; doors, stairs and open floor do not; windows and walls do.
"""
import hashlib
import heapq

from .gridmap import build_grid_map, load_custom, PLANES, WALK
from .data_world import ROOMS


def _h(*a):
    return int(hashlib.md5(repr(a).encode()).hexdigest()[:8], 16)


LINK_COST = 3                             # steps a stair, ladder or hatch costs
LINK_TILES = "+LUDhl="                    # doors, stairs, ladders, hatches and windows: kept clear when people pick where to stand
_CACHE = {}
_SHARED = {}                              # id(map) -> (map, {room: spots}, {route key: path}): spots and routes depend only on the map, so every GridNav on it shares them


def default_map():
    """The saved custom map if the GM edited one, otherwise the generated map."""
    if "gm" not in _CACHE:
        _CACHE["gm"] = load_custom() or build_grid_map()
    return _CACHE["gm"]


class GridNav:
    def __init__(self, gm=None):
        self.gm = gm or default_map()
        self.w, self.h = self.gm["w"], self.gm["h"]
        self.rows = {p["id"]: p["rows"] for p in self.gm["planes"]}
        self.z = {p["id"]: p.get("z", 0) for p in self.gm["planes"]}
        self.blocked = {(f["plane"], f["x"] + i, f["y"] + j) for f in self.gm["furniture"] if f["k"] != "camera" for i in range(f.get("w", 1)) for j in range(f.get("h", 1))}
        self.rooms = self.gm["rooms"]
        codes = self.gm.get("zone_codes") or {}
        self.zones = {p["id"]: p.get("zones") for p in self.gm["planes"]}
        self.codes = {c: r for c, r in codes.items() if r in ROOMS}
        self.room_tiles = {}
        for p in self.gm["planes"]:
            for y, row in enumerate(p.get("zones") or []):
                for x, c in enumerate(row):
                    rid = self.codes.get(c)
                    if rid:
                        self.room_tiles.setdefault(rid, []).append((p["id"], x, y))
        self.walk = {p: [bytearray(1 if c in WALK else 0 for c in row) for row in rows] for p, rows in self.rows.items()}
        for (p, x, y) in self.blocked:
            g = self.walk.get(p)
            if g is not None and 0 <= y < len(g) and 0 <= x < len(g[y]):
                g[y][x] = 0
        self.links = {}
        self.link_ids = {}
        for l in self.gm["links"]:
            ends = list(l["ends"].values())
            if len(ends) != 2:
                continue
            a, b = tuple(ends[0]), tuple(ends[1])
            self.links.setdefault(a, []).append((b, l))
            self.links.setdefault(b, []).append((a, l))
        # a link can carry you further than it costs to take (a hidden passage's far end); across levels the distance estimate is lowered by that surplus so it never overestimates
        seen = {}
        for a, outs in self.links.items():
            for b, l in outs:
                seen[(l["id"], frozenset((a, b)))] = max(0, abs(a[1] - b[1]) + abs(a[2] - b[2]) - LINK_COST)
        self.link_surplus = sum(seen.values())
        self._spots, self._cache = self._shared()
        self._furn = {}
        self.open_tiles = set()

    def _shared(self):
        hit = _SHARED.get(id(self.gm))
        if hit is None or hit[0] is not self.gm:
            if len(_SHARED) > 8:
                _SHARED.clear()
            hit = _SHARED[id(self.gm)] = (self.gm, {}, {})
        if len(hit[2]) > 50000:
            hit[2].clear()
        return hit[1], hit[2]

    # ------------------------------------------------------------------ tiles
    def char(self, plane, x, y):
        r = self.rows[plane]
        return r[y][x] if 0 <= y < len(r) and 0 <= x < len(r[y]) else " "

    def set_overlay(self, open_tiles):
        """Tiles that became passable (broken windows, wrecked furniture). Clears the route cache when the set changes."""
        open_tiles = set(open_tiles)
        if open_tiles != self.open_tiles:
            self.open_tiles = open_tiles
            self._spots, self._cache = ({}, {}) if open_tiles else self._shared()

    def walkable(self, plane, x, y):
        if self.open_tiles and (plane, x, y) in self.open_tiles:
            return True
        g = self.walk.get(plane)
        return g is not None and 0 <= y < len(g) and 0 <= x < len(g[y]) and g[y][x] == 1

    def room_at(self, plane, x, y):
        zr = self.zones.get(plane)
        if zr is None or not (0 <= y < len(zr) and 0 <= x < len(zr[y])):
            return None
        return self.codes.get(zr[y][x])

    def area(self, room):
        """Floor area of a room in tiles (square metres)."""
        r = self.rooms.get(room)
        return r["area"] if r and "area" in r else len(self.room_tiles.get(room, ()))

    def level_above(self, plane, d=1):
        """The level d storeys above (or below, for negative d), or None."""
        z = self.z.get(plane, 0) + d
        return next((p for p, zz in self.z.items() if zz == z), None)

    # ------------------------------------------------------------------ where people stand
    def spots(self, room):
        """Free floor tiles inside a room, nearest the middle first, keeping the tiles in front of doors and stairs clear."""
        if room in self._spots:
            return self._spots[room]
        tiles = self.room_tiles.get(room, [])
        if not tiles:
            self._spots[room] = []
            return []
        plane = tiles[0][0]
        keep_clear = set()
        for (p, x, y) in tiles:
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                if self.char(p, x + dx, y + dy) in LINK_TILES:
                    keep_clear.add((x, y))
        lab = (self.rooms.get(room) or {}).get("label")
        cx, cy = lab if lab else (sum(t[1] for t in tiles) / len(tiles), sum(t[2] for t in tiles) / len(tiles))
        out = [t for t in tiles if self.walkable(*t) and (t[1], t[2]) not in keep_clear and self.char(*t) not in LINK_TILES]
        if not out:
            out = [t for t in tiles if self.walkable(*t)]
        out.sort(key=lambda t: (abs(t[1] - cx) + abs(t[2] - cy), t[2], t[1]))
        self._spots[room] = out
        return out

    def furniture_in(self, room):
        """The furniture of a room as dicts (k, plane, x, y), cameras left out. Wrecked pieces (burnt, smashed) are still listed: the environment decides whether they can be used."""
        f = self._furn.get(room)
        if f is None:
            f = self._furn[room] = [x for x in self.gm["furniture"] if x["room"] == room and x["k"] != "camera"]
        return f

    def stand_near(self, plane, x, y, taken=frozenset(), room=None):
        """A free floor tile next to (x, y): the nearest walkable one that nobody else stands on, preferring the side the room is open on."""
        best = None
        for r in (1, 2):
            cands = []
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if max(abs(dx), abs(dy)) != r:
                        continue
                    t = (plane, x + dx, y + dy)
                    if t in taken or not self.walkable(plane, x + dx, y + dy) or self.char(plane, x + dx, y + dy) in LINK_TILES:
                        continue
                    if room is not None and self.room_at(*t) != room:
                        continue
                    cands.append((abs(dx) + abs(dy), _h(x, y, dx, dy), t))
            if cands:
                cands.sort()
                return cands[0][2]
        return None

    def nominal(self, room, cid, salt=3):
        """Where this person usually stands in this room (a fixed pick among its free tiles, spread over the whole room). The live planner starts from the same pick."""
        spots = self.spots(room)
        if not spots:
            r = self.rooms[room]
            x0, y0, x1, y1 = r["rect"]
            return (r["plane"], (x0 + x1) // 2, (y0 + y1) // 2)
        return spots[_h(cid, room, salt) % len(spots)]

    # ------------------------------------------------------------------ routes
    def route(self, src, dst, hidden=frozenset(), avoid=frozenset()):
        """Shortest walk from tile src to tile dst, both (plane, x, y). Hidden hatch links are usable only if their id is in `hidden`. Returns a list of tiles or None."""
        key = (src, dst, hidden, avoid)
        if key in self._cache:
            return self._cache[key]
        if src == dst:
            return [src]
        best = {src: 0}
        prev = {}
        walk, opened, surplus = self.walk, self.open_tiles, self.link_surplus
        dp_, dx_, dy_ = dst
        heap = [(0, 0, 0, src)]
        n = 0
        while heap:
            _, _, g, cur = heapq.heappop(heap)
            if cur == dst:
                path = [cur]
                while cur in prev:
                    cur = prev[cur]
                    path.append(cur)
                path.reverse()
                self._cache[key] = path
                return path
            if g > best.get(cur, 1e9):
                continue
            pl, x, y = cur
            nbrs = []
            g_ = walk.get(pl)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                t = (pl, nx, ny)
                if t == dst or (((g_ is not None and 0 <= ny < len(g_) and 0 <= nx < len(g_[ny]) and g_[ny][nx]) or (opened and t in opened)) and t not in avoid):
                    nbrs.append((t, 1))
            for other, link in self.links.get(cur, ()):
                if link["kind"] == "secret" and link["id"] not in hidden:
                    continue
                nbrs.append((other, LINK_COST))
            for t, c in nbrs:
                ng = g + c
                if ng < best.get(t, 1e9):
                    best[t] = ng
                    prev[t] = cur
                    md = abs(t[1] - dx_) + abs(t[2] - dy_)
                    hh = md if t[0] == dp_ else max(0, md - surplus)
                    n += 1
                    heapq.heappush(heap, (ng + hh, n, ng, t))
        self._cache[key] = None
        return None

    @staticmethod
    def corners(path):
        """Compress a tile path to its turning points (keeps the first, last and every plane change)."""
        if not path or len(path) < 3:
            return list(path or [])
        out = [path[0]]
        for i in range(1, len(path) - 1):
            a, b, c = path[i - 1], path[i], path[i + 1]
            if a[0] != b[0] or b[0] != c[0] or (b[1] - a[1], b[2] - a[2]) != (c[1] - b[1], c[2] - b[2]):
                out.append(b)
        out.append(path[-1])
        return out

    def hidden_links_between(self, rooms):
        """Ids of hidden connections joining consecutive rooms of a room path (the engine only sends people through them once they are known)."""
        ids = set()
        for a, b in zip(rooms, rooms[1:]):
            for l in self.gm["links"]:
                if l["kind"] == "secret" and {l["a"], l["b"]} == {a, b}:
                    ids.add(l["id"])
        return frozenset(ids)
