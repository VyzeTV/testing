"""One-time edit of the plan files (phase E): the hedge maze becomes the Garden Maze (joined only to Outdoors), the north of the island becomes the Woods
(dense trees, a path to a clearing with an old camp and the hammock), and a hatch under the leaves drops into a new branch of the smugglers' tunnel.
Run once:  python -m murder.maps.split_outdoors   (it refuses to run twice)."""
import hashlib
import json
import os
from collections import deque

HERE = os.path.dirname(os.path.abspath(__file__))
MAZE, WOODS = "p", "q"
HATCH = (53, 9)
CLEAR = (49, 10)
WALKABLE = set("gsp,f")


def _r(x, y, s=0):
    return int(hashlib.md5(f"woods:{x},{y},{s}".encode()).hexdigest()[:8], 16) / 2 ** 32


def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return [list(row) for row in fh.read().split("\n")]


def save(name, rows):
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as fh:
        fh.write("\n".join("".join(r) for r in rows))


def main():
    meta = json.load(open(os.path.join(HERE, "map.json"), encoding="utf-8"))
    if "maze" in meta["zone_codes"].values():
        print("already split")
        return
    T, Z = load("ground.txt"), load("ground.zones.txt")
    B = load("basement.txt")
    # ---- the Garden Maze: a closed hedge ring with its entrance on the north path
    for y in range(48, 64):
        for x in range(12, 33):
            edge = y in (48, 63) or x in (12, 32)
            if edge and not (y == 48 and x in (22, 23)):
                T[y][x] = "H"
            elif T[y][x] in WALKABLE:
                Z[y][x] = MAZE
                if T[y][x] == "s":
                    T[y][x] = "g"
    # ---- the Woods: dense trees north of the house, a path to a clearing
    keep = {(CLEAR[0], y) for y in range(CLEAR[1], 17)} | {(CLEAR[0] + dx, CLEAR[1] + dy) for dx in range(-3, 4) for dy in range(-2, 2)}
    keep |= {(x, HATCH[1]) for x in range(CLEAR[0], HATCH[0] + 1)} | {HATCH}
    woods = []
    for y in range(5, 16):
        for x in range(34, 63):
            if Z[y][x] == "N" and T[y][x] in ",gTb":
                Z[y][x] = WOODS
                woods.append((x, y))
                if (x, y) in keep:
                    T[y][x] = ","
                else:
                    r = _r(x, y)
                    T[y][x] = "T" if r < 0.5 else "b" if r < 0.58 else ","
    # whatever the path cannot reach becomes trees, so the Woods are one piece
    seen, q = {(CLEAR[0], 15)}, deque([(CLEAR[0], 15)])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in seen or n not in set(woods) or T[n[1]][n[0]] in "T":
                continue
            seen.add(n)
            q.append(n)
    for x, y in woods:
        if T[y][x] not in "T" and (x, y) not in seen:
            T[y][x] = "T"
    T[HATCH[1]][HATCH[0]] = "h"
    # ---- the tunnel branch under the Woods, down to the smugglers' tunnel on row 25
    for y in range(HATCH[1], 25):
        if B[y][HATCH[0]] == " ":
            B[y][HATCH[0]] = "r"
    B[HATCH[1]][HATCH[0]] = "h"
    save("ground.txt", T)
    save("ground.zones.txt", Z)
    save("basement.txt", B)
    meta["zone_codes"][MAZE], meta["zone_codes"][WOODS] = "maze", "woods"
    meta.setdefault("labels", {}).update({"maze": [22, 56], "woods": [46, 8]})
    for f in meta["furniture"]:
        if f.get("k") == "hammock":
            f.update({"x": CLEAR[0] - 3, "y": CLEAR[1], "room": "woods"})
    meta["furniture"] += [{"k": "firepit", "plane": "ground", "x": CLEAR[0] + 1, "y": CLEAR[1] - 1, "w": 1, "h": 1, "room": "woods"},
                          {"k": "crate", "plane": "ground", "x": CLEAR[0] - 1, "y": CLEAR[1] - 1, "w": 1, "h": 1, "room": "woods"}]
    meta["secrets"].append({"id": "SP-6", "ends": [["ground", HATCH[0], HATCH[1]], ["basement", HATCH[0], HATCH[1]]],
                            "note": "a trapdoor under the leaves by the old camp, onto a ladder down into a branch of the smugglers' tunnel"})
    with open(os.path.join(HERE, "map.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=1)
    print(f"maze and woods drawn: {len(woods)} woods tiles, {len(seen)} reachable")


if __name__ == "__main__":
    main()
