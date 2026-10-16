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


LINK_TILES = "+LUDhl="                    # doors, stairs, ladders, hatches and windows: kept clear when people pick where to stand
_CACHE = {}


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
        self.links = {}
        self.link_ids = {}
        for l in self.gm["links"]:
            ends = list(l["ends"].values())
            if len(ends) != 2:
                continue
            a, b = tuple(ends[0]), tuple(ends[1])
            self.links.setdefault(a, []).append((b, l))
            self.links.setdefault(b, []).append((a, l))
        self._spots = {}
        self._furn = {}
        self._cache = {}
        self.open_tiles = set()

    # ------------------------------------------------------------------ tiles
    def char(self, plane, x, y):
        r = self.rows[plane]
        return r[y][x] if 0 <= y < len(r) and 0 <= x < len(r[y]) else " "

    def set_overlay(self, open_tiles):
        """Tiles that became passable (broken windows, wrecked furniture). Clears the route cache when the set changes."""
        open_tiles = set(open_tiles)
        if open_tiles != self.open_tiles:
            self.open_tiles = open_tiles
            self._cache.clear()
            self._spots.clear()

    def walkable(self, plane, x, y):
        if (plane, x, y) in self.open_tiles:
            return True
        return self.char(plane, x, y) in WALK and (plane, x, y) not in self.blocked

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
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                t = (pl, nx, ny)
                if t == dst or (self.walkable(pl, nx, ny) and t not in avoid):
                    nbrs.append((t, 1))
            for other, link in self.links.get(cur, []):
                if link["kind"] == "secret" and link["id"] not in hidden:
                    continue
                nbrs.append((other, 3))
            for t, c in nbrs:
                ng = g + c
                if ng < best.get(t, 1e9):
                    best[t] = ng
                    prev[t] = cur
                    hh = abs(t[1] - dst[1]) + abs(t[2] - dst[2]) if t[0] == dst[0] else 0
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
