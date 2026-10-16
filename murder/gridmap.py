"""Builds the tile map of the island from its plan files (murder/maps/, or the GM's edited copy in state/maps/) and checks it against the room graph.

The plans are drawn by hand (the first version came from `python -m murder.mapgen`): one text file per level for the tiles, one for which room each tile belongs to,
and map.json for the furniture and the secret passages. One tile is one metre, and all five levels share the island's frame, so a staircase or a hatch sits at the
same (x, y) on the two levels it joins. Everything else is worked out here:
* doors: a door tile ('+', 'L' locked) between two rooms, or a room and the grounds, is the connection between them; a window ('=') counts only where the room graph
  says the connection is a window;
* stairs: a 'U' tile with a 'D' tile at the same spot on the level above (or 'l' ladder tiles on both) joins the two;
* secret passages: the hidden tiles ('h') listed in map.json, paired across a wall or a floor;
* open ground: two outdoor zones that touch (the garden and the beach) are joined where they meet.
`verify` then checks that every room is on the map, every connection of the room graph is there with the right lock, everything can be reached, furniture stands on
floor in its own room, and no room is mostly empty.

Run `python -m murder.gridmap` to rebuild static/grid_map.json and print the levels, the room fill and any problems.

Terrain characters: '#' wall, ' ' nothing (outside a level, or solid earth in the cellars), floors w=wood k=tile c=carpet r=stone m=metal, ',' wild grass, 'g' lawn,
's' sand, 'n' dunes, 'q' rock, 'a' shallow water, '~' deep water, ':' deck, 'p' path, 'B' boardwalk, 'j' jetty, 'f' flower bed, 'T' tree, 'b' bush, 'H' hedge,
'C' cliff edge (a drop), 'K' cliff steps, 'S' roof slope, 'v' open drop (a gallery's void), 'x' railing, '+' door, 'L' locked door, '=' window,
'U'/'D' stairs up/down, 'l' ladder, 'h' hidden stair, hatch or grate (floor when not in GM view).
"""
import json
import os
import shutil
import sys
from collections import deque

from .data_world import ROOMS, CAMERA_BLIND
from .world import build_edges
from .scale import MAP_SCALE

HERE = os.path.dirname(os.path.abspath(__file__))
PLAN_DIR = os.path.join(HERE, "maps")
OPEN = {"garden", "pool", "beach"}
HUBS = {"landing", "upper_landing", "basement_hall", "foyer", "lookout", "water_tower", "voting_grounds", "lighthouse"}     # rooms people cross: exempt from the fill check
FILL_MIN = 0.45
WALK = set("wkcrmgsp,:+LUDhanqKfBjlb")
FLOORS = set("wkcrm:gsnq,pfBjK")
LEVEL_OF_ZONE = {"roof": "roof", "second": "second", "first": "first", "ground": "ground", "grounds": "ground", "basement": "basement"}
LEGEND = {"#": "wall", " ": "nothing", "w": "wood floor", "k": "tile floor", "c": "carpet", "r": "stone floor", "m": "metal floor", ",": "wild grass", "g": "lawn",
          "s": "sand", "n": "dunes", "q": "rock", "a": "shallow water", "~": "deep water", ":": "deck", "p": "path", "B": "boardwalk", "j": "jetty", "f": "flower bed",
          "T": "tree", "b": "bush", "H": "hedge", "C": "cliff edge", "K": "cliff steps", "S": "roof slope", "v": "open drop", "x": "railing", "+": "door",
          "L": "locked door", "=": "window", "U": "stairs up", "D": "stairs down", "l": "ladder", "h": "hidden stair, hatch or grate"}
ALLOWED = set(LEGEND)

with open(os.path.join(PLAN_DIR, "map.json"), encoding="utf-8") as _fh:
    _META = json.load(_fh)
W, H = _META["w"], _META["h"]
PLANES = [p["id"] for p in _META["planes"]]
PLANE_Z = {p["id"]: p["z"] for p in _META["planes"]}


def custom_dir():
    return os.path.join(os.environ.get("MC_DATA_DIR") or os.path.dirname(HERE), "state", "maps")


def read_plans(path=None):
    """The plan files: {"meta", "tiles": {plane: rows}, "zones": {plane: rows of room ids or None}}."""
    path = path or (custom_dir() if os.path.exists(os.path.join(custom_dir(), "map.json")) else PLAN_DIR)
    with open(os.path.join(path, "map.json"), encoding="utf-8") as fh:
        meta = json.load(fh)
    codes = meta["zone_codes"]
    tiles, zones = {}, {}
    for p in meta["planes"]:
        pid = p["id"]
        with open(os.path.join(path, f"{pid}.txt"), encoding="utf-8") as fh:
            rows = fh.read().split("\n")[:meta["h"]]
        with open(os.path.join(path, f"{pid}.zones.txt"), encoding="utf-8") as fh:
            zrows = fh.read().split("\n")[:meta["h"]]
        tiles[pid] = [r.ljust(meta["w"])[:meta["w"]] for r in rows]
        zones[pid] = [[codes.get(c) for c in r.ljust(meta["w"], ".")[:meta["w"]]] for r in zrows]
    return {"meta": meta, "tiles": tiles, "zones": zones, "path": path}


def build_grid_map(plans=None):
    P = plans or read_plans()
    meta, T, Z = P["meta"], P["tiles"], P["zones"]
    planes = [p["id"] for p in meta["planes"]]
    edges = {e["id"]: e for e in build_edges()}
    by_pair = {}
    for e in edges.values():
        by_pair.setdefault(frozenset((e["a"], e["b"])), []).append(e)

    def ch(p, x, y):
        return T[p][y][x] if 0 <= x < W and 0 <= y < H else " "

    def zone(p, x, y):
        return Z[p][y][x] if 0 <= x < W and 0 <= y < H else None

    # ---- rooms
    tiles_of = {}
    for p in planes:
        for y in range(H):
            for x in range(W):
                z = Z[p][y][x]
                if z in ROOMS:
                    tiles_of.setdefault(z, []).append((p, x, y))
    rooms = {}
    for rid in ROOMS:
        ts = tiles_of.get(rid, [])
        if not ts:
            continue
        pl = ts[0][0]
        xs, ys = [t[1] for t in ts], [t[2] for t in ts]
        pad = 0 if rid in OPEN else 1
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        lab = meta.get("labels", {}).get(rid) or list(min(((t[1], t[2]) for t in ts), key=lambda q: (q[0] - cx) ** 2 + (q[1] - cy) ** 2))
        rooms[rid] = {"name": ROOMS[rid][0], "zone": ROOMS[rid][1], "plane": pl, "rect": [min(xs) - pad, min(ys) - pad, max(xs) + 1 + pad, max(ys) + 1 + pad],
                      "open": rid in OPEN, "area": sum(1 for (p, x, y) in ts if T[p][y][x] != "v"), "label": lab,
                      "camera": rid not in OPEN and rid not in CAMERA_BLIND and rid != "core_vault"}

    # ---- doors: a door tile between two different zones
    doors, used = [], set()
    for p in planes:
        for y in range(H):
            for x in range(W):
                c = ch(p, x, y)
                if c not in "+L=":
                    continue
                for (ax, ay), (bx, by) in (((x - 1, y), (x + 1, y)), ((x, y - 1), (x, y + 1))):
                    za, zb = zone(p, ax, ay), zone(p, bx, by)
                    if not za or not zb or za == zb or za not in ROOMS or zb not in ROOMS:
                        continue
                    cands = by_pair.get(frozenset((za, zb)), [])
                    e = next((k for k in cands if k["kind"] not in ("stairs", "secret")), None)
                    if c == "=" and (not e or e["kind"] != "window"):
                        continue                                    # an ordinary window
                    if not e:
                        doors.append({"id": f"?{p}:{x},{y}", "a": za, "b": zb, "kind": "unknown", "plane": p, "tiles": [[x, y]], "problem": True})
                        continue
                    ia, ib = ((ax, ay), (bx, by)) if za == e["a"] else ((bx, by), (ax, ay))
                    via = "outdoor" if (e["a"] in OPEN or e["b"] in OPEN) else "direct"
                    doors.append({"id": e["id"], "a": e["a"], "b": e["b"], "kind": e["kind"], "hidden": e["hidden"], "locked": e["locked"], "keys": list(e.get("keys", [])),
                                  "needs": list(e.get("needs", [])), "cost": e["cost"], "discover": e.get("discover"), "via": via, "plane": p,
                                  "tiles": [[x, y]], "in_a": list(ia), "in_b": list(ib), "char": c})
                    used.add(e["id"])
    # ---- open ground: outdoor zones that touch
    for e in edges.values():
        if e["id"] in used or not (e["a"] in OPEN and e["b"] in OPEN) or e["a"] not in rooms or e["b"] not in rooms:
            continue
        pa = rooms[e["a"]]["plane"]
        best = None
        ca, cb = rooms[e["a"]]["label"], rooms[e["b"]]["label"]
        for (p, x, y) in tiles_of[e["a"]]:
            if ch(p, x, y) not in WALK:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if zone(p, x + dx, y + dy) == e["b"] and ch(p, x + dx, y + dy) in WALK:
                    d = abs(x - cb[0]) + abs(y - cb[1]) + abs(x - ca[0]) + abs(y - ca[1])
                    if best is None or d < best[0]:
                        best = (d, (x, y), (x + dx, y + dy))
        if best:
            doors.append({"id": e["id"], "a": e["a"], "b": e["b"], "kind": e["kind"], "hidden": e["hidden"], "locked": e["locked"], "keys": list(e.get("keys", [])),
                          "needs": list(e.get("needs", [])), "cost": e["cost"], "discover": e.get("discover"), "via": "open", "plane": pa,
                          "tiles": [list(best[1])], "in_a": list(best[1]), "in_b": list(best[2])})
            used.add(e["id"])

    # ---- stairs and ladders between neighbouring levels
    links = []
    order = sorted(planes, key=lambda q: PLANE_Z[q])
    for lo, hi in zip(order, order[1:]):
        for y in range(H):
            for x in range(W):
                a, b = ch(lo, x, y), ch(hi, x, y)
                if not ((a == "U" and b == "D") or (a == "l" and b == "l")):
                    continue
                za, zb = zone(lo, x, y), zone(hi, x, y)
                e = next((k for k in by_pair.get(frozenset((za, zb)), []) if k["kind"] == "stairs"), None)
                links.append({"id": e["id"] if e else f"?{lo}:{x},{y}", "a": e["a"] if e else za, "b": e["b"] if e else zb, "kind": "stairs", "hidden": False,
                              "locked": bool(e and e["locked"]), "keys": list(e.get("keys", [])) if e else [], "needs": list(e.get("needs", [])) if e else [],
                              "cost": e["cost"] if e else 8, "discover": None, "ends": {zb or "upper": [hi, x, y], za or "lower": [lo, x, y]}, "problem": not e})
                if e:
                    used.add(e["id"])
    # ---- secret passages
    for s in meta.get("secrets", []):
        e = edges.get(s["id"])
        ends = {}
        for k, (p, x, y) in enumerate(s["ends"]):
            name = zone(p, x, y) or ("tunnel" if p == "basement" else f"end{k}")
            if name in ends:
                name = f"{name}{k}"
            ends[name] = [p, x, y]
        links.append({"id": s["id"], "a": e["a"] if e else None, "b": e["b"] if e else None, "kind": "secret", "hidden": True, "locked": bool(e and e["locked"]),
                      "keys": list(e.get("keys", [])) if e else [], "needs": list(e.get("needs", [])) if e else [], "cost": e["cost"] if e else 3,
                      "discover": e.get("discover") if e else None, "note": s.get("note", ""), "ends": ends, "problem": not e})
        if e:
            used.add(e["id"])

    # ---- furniture, and TereVi's cameras
    furn = [dict(f, w=f.get("w", 1), h=f.get("h", 1)) for f in meta.get("furniture", []) if f.get("k") != "camera"]
    taken = {(f["plane"], f["x"] + i, f["y"] + j) for f in furn for i in range(f["w"]) for j in range(f["h"])}
    for rid, r in rooms.items():
        if not r["camera"]:
            continue
        spot = next(((p, x, y) for (p, x, y) in sorted(tiles_of[rid], key=lambda t: (t[2], t[1])) if ch(p, x, y) in FLOORS and (p, x, y) not in taken), None)
        if spot:
            furn.append({"k": "camera", "plane": spot[0], "x": spot[1], "y": spot[2], "w": 1, "h": 1, "room": rid})

    # ---- where each level is drawn when they are shown side by side: the island on the left, the house's levels in a column to its right, cropped to what is on them
    view, ox, oy = {}, W + 4, 0
    for p in sorted(planes, key=lambda q: (q != "ground", -PLANE_Z[q])):
        pts = [(x, y) for y in range(H) for x in range(W) if T[p][y][x] != " "]
        if not pts:
            continue
        x0, x1 = min(q[0] for q in pts), max(q[0] for q in pts) + 1
        y0, y1 = min(q[1] for q in pts), max(q[1] for q in pts) + 1
        if p == "ground":
            view[p] = {"x0": 0, "y0": 0, "x1": W, "y1": H, "ox": 0, "oy": 0}
            continue
        view[p] = {"x0": x0, "y0": y0, "x1": x1, "y1": y1, "ox": ox, "oy": oy}
        oy += (y1 - y0) + 4
    codes = meta["zone_codes"]
    rev = {v: k for k, v in codes.items()}
    out_planes = [{"id": p, "z": PLANE_Z[p], "rows": T[p], "zones": ["".join(rev.get(z, ".") if z else "." for z in row) for row in Z[p]]} for p in order]
    return {"version": 4, "scale": MAP_SCALE, "tile_m": 1, "tile_px": 10, "w": W, "h": H, "planes": out_planes, "zone_codes": codes, "view": view,
            "rooms": rooms, "doors": doors, "links": links, "furniture": furn, "legend": LEGEND}


def _walkable(gm):
    rows = {p["id"]: p["rows"] for p in gm["planes"]}
    blocked = {(f["plane"], f["x"] + i, f["y"] + j) for f in gm["furniture"] if f["k"] != "camera" for i in range(f.get("w", 1)) for j in range(f.get("h", 1))}

    def ok(p, x, y):
        r = rows.get(p)
        return r is not None and 0 <= y < len(r) and 0 <= x < len(r[y]) and r[y][x] in WALK and (p, x, y) not in blocked
    return rows, ok


def room_fill(gm):
    """For each building room: the share of its floor that is furniture, the tiles beside furniture and the tiles in front of its doors and stairs."""
    rows, _ = _walkable(gm)
    zones = {p["id"]: p["zones"] for p in gm["planes"]}
    codes = gm["zone_codes"]
    feat = set()
    for f in gm["furniture"]:
        if f["k"] == "camera":
            continue
        for i in range(-1, f.get("w", 1) + 1):
            for j in range(-1, f.get("h", 1) + 1):
                feat.add((f["plane"], f["x"] + i, f["y"] + j))
    for d in gm["doors"]:
        for t in (d.get("in_a"), d.get("in_b")):
            if t:
                feat.add((d["plane"], t[0], t[1]))
    for l in gm["links"]:
        for e in l["ends"].values():
            for i in (-1, 0, 1):
                for j in (-1, 0, 1):
                    feat.add((e[0], e[1] + i, e[2] + j))
    out = {}
    for rid, r in gm["rooms"].items():
        if r["open"]:
            continue
        p = r["plane"]
        x0, y0, x1, y1 = r["rect"]
        floor = [(p, x, y) for y in range(y0, y1) for x in range(x0, x1) if codes.get(zones[p][y][x]) == rid and rows[p][y][x] not in " #"]
        if floor:
            out[rid] = round(sum(1 for t in floor if t in feat) / len(floor), 2)
    return out


def verify(gm):
    """Everything the game needs from the map. Returns a list of problems (empty when the map is good)."""
    problems = []
    rows, ok = _walkable(gm)
    for p in gm["planes"]:
        bad = {c for row in p["rows"] for c in row if c not in ALLOWED}
        if bad:
            problems.append(f"level {p['id']} has unknown tiles: {''.join(sorted(bad))}")
    for rid in ROOMS:
        r = gm["rooms"].get(rid)
        if not r:
            problems.append(f"room {rid} is not on the map")
            continue
        want = LEVEL_OF_ZONE.get(ROOMS[rid][1])
        if want and r["plane"] != want:
            problems.append(f"room {rid} is on the {r['plane']} level, but the game puts it on the {want} level")
    for d in gm["doors"]:
        if d.get("problem"):
            problems.append(f"a door at {d['plane']} {d['tiles'][0]} joins {d['a']} and {d['b']}, which the room graph does not connect")
        elif d.get("char") in ("+", "L") and (d["char"] == "L") != bool(d["locked"]):
            problems.append(f"the door of {d['id']} ({d['a']}-{d['b']}) should be {'locked (L)' if d['locked'] else 'an ordinary door (+)'}")
    for l in gm["links"]:
        if l.get("problem"):
            problems.append(f"link {l['id']} at {list(l['ends'].values())} matches no stairs or secret passage of the room graph")
        for e in l["ends"].values():
            if rows[e[0]][e[2]][e[1]] not in "UDlh" and not (l["kind"] == "secret" and rows[e[0]][e[2]][e[1]] in WALK):
                problems.append(f"link {l['id']} ends on '{rows[e[0]][e[2]][e[1]]}' at {e}")
    present = {d["id"] for d in gm["doors"]} | {l["id"] for l in gm["links"]}
    for e in build_edges():
        if e["id"] not in present:
            problems.append(f"connection {e['id']} ({e['a']}-{e['b']}, {e['kind']}) is missing from the map")
    zones = {p["id"]: p["zones"] for p in gm["planes"]}
    codes = gm["zone_codes"]
    for f in gm["furniture"]:
        for i in range(f.get("w", 1)):
            for j in range(f.get("h", 1)):
                x, y = f["x"] + i, f["y"] + j
                c = rows[f["plane"]][y][x]
                if c not in FLOORS:
                    problems.append(f"{f['k']} in {f['room']} stands on '{c}' at {f['plane']} {x},{y}")
                elif f["room"] and codes.get(zones[f["plane"]][y][x]) != f["room"]:
                    problems.append(f"{f['k']} of {f['room']} stands in {codes.get(zones[f['plane']][y][x])} at {f['plane']} {x},{y}")
    # everything can be reached from the front door, through every door, stair and (known) secret passage
    start = None
    for d in gm["doors"]:
        if d["id"] == next((e["id"] for e in build_edges() if {e["a"], e["b"]} == {"foyer", "garden"}), None):
            start = (d["plane"], *d["in_a"]) if d["a"] == "foyer" else (d["plane"], *d["in_b"])
    if start:
        links = {}
        for l in gm["links"]:
            ends = [tuple(v) for v in l["ends"].values()]
            if len(ends) == 2:
                links.setdefault(ends[0], []).append(ends[1])
                links.setdefault(ends[1], []).append(ends[0])
        seen, q = {start}, deque([start])
        while q:
            cur = q.popleft()
            p, x, y = cur
            nxt = [(p, x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))] + links.get(cur, [])
            for t in nxt:
                if t not in seen and (ok(*t) or t in links):
                    seen.add(t)
                    q.append(t)
        reached = {codes.get(zones[p][y][x]) for (p, x, y) in seen}
        for rid in ROOMS:
            if rid in gm["rooms"] and rid not in reached:
                problems.append(f"{rid} cannot be reached on foot from the front door")
        # no floor is walled off by furniture: every free tile of a room can be walked to
        cut = {}
        for p in zones:
            for y, row in enumerate(zones[p]):
                for x, c in enumerate(row):
                    rid = codes.get(c)
                    if rid is not None and rid in reached and ok(p, x, y) and (p, x, y) not in seen:
                        cut.setdefault(rid, []).append((x, y))
        for rid, ts in sorted(cut.items()):
            problems.append(f"{len(ts)} floor tile(s) of {rid} cannot be walked to (walled off by furniture or plants, e.g. {ts[0][0]},{ts[0][1]})")
    else:
        problems.append("the foyer has no front door")
    # every secret passage leads from one of its rooms to the other by itself (through its own tunnel, if it has one)
    for sid in sorted({l["id"] for l in gm["links"] if l["kind"] == "secret" and l.get("a")}):
        segs = [l for l in gm["links"] if l["id"] == sid]
        a, b = segs[0]["a"], segs[0]["b"]
        lk = {}
        for l in segs:
            ends = [tuple(v) for v in l["ends"].values()]
            if len(ends) == 2:
                lk.setdefault(ends[0], []).append(ends[1])
                lk.setdefault(ends[1], []).append(ends[0])
        src = [(p, x, y) for p in zones for y, row in enumerate(zones[p]) for x, c in enumerate(row) if codes.get(c) == a]
        seen, q, done = set(src), deque(src), False
        while q and not done:
            p, x, y = q.popleft()
            for t in [(p, x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))] + lk.get((p, x, y), []):
                if t in seen or not (ok(*t) or t in lk):
                    continue
                z = codes.get(zones[t[0]][t[2]][t[1]])
                if z == b:
                    done = True
                    break
                if z in (a, None):
                    seen.add(t)
                    q.append(t)
        if not done:
            problems.append(f"secret passage {sid} does not lead from {a} to {b}")
    for rid, v in room_fill(gm).items():
        if rid not in HUBS and v < FILL_MIN:
            problems.append(f"{rid} is mostly empty ({int(v * 100)}% of its floor is used; at least {int(FILL_MIN * 100)}%)")
    return problems


# ------------------------------------------------------------------ the GM's edited map
def load_custom():
    """The map built from the GM's edited plans, if there are any and they still check out; otherwise None."""
    if not os.path.exists(os.path.join(custom_dir(), "map.json")):
        return None
    try:
        gm = build_grid_map(read_plans(custom_dir()))
    except Exception:
        return None
    if verify(gm):
        return None
    gm["custom"] = True
    return gm


def validate_edit(gm):
    """Problems with an edited map sent by the viewer (its levels' tiles and furniture), checked by rebuilding it from plans."""
    try:
        return verify(build_grid_map(_plans_from(gm)))
    except Exception as e:  # malformed upload
        return [f"the edited map could not be read: {type(e).__name__}: {e}"]


def _plans_from(gm):
    base = read_plans(PLAN_DIR)
    tiles = {}
    for p in gm["planes"]:
        if p["id"] not in base["tiles"] or len(p["rows"]) != H or any(len(r) != W for r in p["rows"]):
            raise ValueError(f"level {p['id']} has the wrong size")
        tiles[p["id"]] = list(p["rows"])
    meta = dict(base["meta"], furniture=[{k: f[k] for k in ("k", "plane", "x", "y", "w", "h", "room") if k in f} for f in gm["furniture"] if f.get("k") != "camera"])
    return {"meta": meta, "tiles": tiles, "zones": base["zones"], "path": None}


def save_custom(gm):
    """Write an edited map as the GM's plans (state/maps/). Returns the problems; nothing is written unless there are none."""
    problems = validate_edit(gm)
    if problems:
        return problems
    plans = _plans_from(gm)
    d = custom_dir()
    os.makedirs(d, exist_ok=True)
    codes = plans["meta"]["zone_codes"]
    rev = {v: k for k, v in codes.items()}
    for pid, rows in plans["tiles"].items():
        with open(os.path.join(d, f"{pid}.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(rows) + "\n")
        with open(os.path.join(d, f"{pid}.zones.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join("".join(rev.get(z, ".") if z else "." for z in row) for row in plans["zones"][pid]) + "\n")
    with open(os.path.join(d, "map.json"), "w", encoding="utf-8") as fh:
        json.dump(plans["meta"], fh, indent=1)
    return []


def reset_custom():
    if os.path.isdir(custom_dir()):
        shutil.rmtree(custom_dir())
    return True


def ascii_dump(gm, planes=None):
    out = []
    for p in gm["planes"]:
        if planes and p["id"] not in planes:
            continue
        v = gm["view"].get(p["id"], {"x0": 0, "y0": 0, "x1": W, "y1": H})
        out.append(f"=== {p['id']} (z={p['z']})")
        out += [row[v["x0"]:v["x1"]] for row in p["rows"][v["y0"]:v["y1"]]]
    return "\n".join(out)


def main(argv):
    gm = build_grid_map()
    probs = verify(gm)
    path = os.path.join(os.path.dirname(HERE), "static", "grid_map.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(gm, fh, separators=(",", ":"))
    if "--ascii" in argv:
        print(ascii_dump(gm))
    fill = room_fill(gm)
    print("room fill: " + ", ".join(f"{k} {int(v * 100)}%" for k, v in sorted(fill.items(), key=lambda kv: kv[1])))
    print(f"wrote {path}: {len(gm['rooms'])} rooms, {len(gm['doors'])} doors, {len(gm['links'])} stairs and secret passages, {len(gm['furniture'])} furniture; problems: {len(probs)}")
    for pr in probs:
        print("  -", pr)
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
