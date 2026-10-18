"""Heights: falling, jumping and climbing as movement.

A fall takes somebody from where they lose their footing to where they land: down a staircase or a ladder, through the gallery's open floor to the foyer, from an upper
window or the roof to the lawn, over the cliff to the shore. What it does to them depends on the drop (about three metres a storey) and on what they land on (water
forgives a lot, stone nothing), and goes through the ordinary injury system: bruises and a twisted ankle from a tumble down the stairs, broken bones from a storey, death
from two or more onto something hard.

Causes handled here: a slip on stairs or a ladder while walking (darkness, a wet floor, hurrying, drink, dizziness, injuries and a frayed mind all make it likelier),
jumping from a burning room when there is no other way out, and climbing out of a window when somebody is locked in (a ground-floor window is easy; an upper one means
climbing down the wall, and failing means falling). A push from a height is `fall_from_edge` with `by` set; the murder planner (a later phase) decides when to use it.
"""
from collections import deque

from .environment import key as _ek

SURFACE = {"~": 0.15, "a": 0.25, "s": 0.55, "n": 0.5, "g": 0.6, ",": 0.6, "f": 0.55, "b": 0.5, "T": 0.7, "H": 0.6,
           "w": 0.8, "c": 0.7, ":": 0.85, "B": 0.85, "j": 0.85, "p": 0.9, "K": 1.0, "k": 1.0, "r": 1.0, "m": 1.0, "q": 1.05, "S": 0.9}
SHORE = set("sa~qn")
LANDABLE = set("wkcrmgspa~:fBjKqn,bT")
STAIR_SLIP = 0.0015                     # chance per flight of stairs for somebody steady, sober, in good light, not hurrying
LADDER_SLIP = 0.01
CLIFF_LEVELS = 2.0


class FallMixin:
    # ------------------------------------------------------------------ where a fall ends
    def drop_below(self, p, x, y):
        """Somebody goes over the edge at tile (p, x, y) (an open floor, the outside of an upper window, a roof edge, a cliff). Returns (landing tile, storeys fallen), or None
        if there is nothing to fall down here."""
        nav = self.nav()
        ch = nav.char(p, x, y)
        if ch == "C":
            seen, q = {(x, y)}, deque([(x, y, 0)])
            while q:
                cx, cy, d = q.popleft()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                    nx, ny = cx + dx, cy + dy
                    if (nx, ny) in seen or d > 14:
                        continue
                    seen.add((nx, ny))
                    c2 = nav.char(p, nx, ny)
                    if c2 in SHORE:
                        return (p, nx, ny), CLIFF_LEVELS
                    if c2 == "C":
                        q.append((nx, ny, d + 1))
            return None
        cur = p
        while True:
            below = nav.level_above(cur, -1)
            if below is None:
                break
            cur = below
            if nav.char(cur, x, y) not in "v ":
                break
        if cur == p or nav.char(cur, x, y) == " ":
            return None
        land = self._landing(cur, x, y)
        return (land, float(nav.z[p] - nav.z[cur])) if land else None

    def _landing(self, p, x, y):
        nav = self.nav()
        if nav.char(p, x, y) in LANDABLE and (nav.walkable(p, x, y) or nav.char(p, x, y) in "~aTb"):
            return (p, x, y)
        seen, q = {(x, y)}, deque([(x, y)])
        while q:
            cx, cy = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = cx + dx, cy + dy
                if (nx, ny) in seen or abs(nx - x) + abs(ny - y) > 4:
                    continue
                seen.add((nx, ny))
                if nav.walkable(p, nx, ny):
                    return (p, nx, ny)
                q.append((nx, ny))
        return None

    def _room_near(self, tile):
        """The room a tile belongs to, or the nearest one (somebody who lands in the sea is in the nearest part of the shore)."""
        nav = self.nav()
        r = nav.room_at(*tile)
        if r:
            return r
        p, x, y = tile
        for d in range(1, 12):
            for dx in range(-d, d + 1):
                for dy in (-d, d):
                    for tx, ty in ((x + dx, y + dy), (x + dy, y + dx)):
                        r = nav.room_at(p, tx, ty)
                        if r:
                            return r
        return None

    def outside_windows(self, room):
        """Windows of a room that open onto the outside: (window tile, the tile inside, the tile outside)."""
        nav = self.nav()
        out = []
        for (p, x, y) in nav.room_tiles.get(room, []):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                wx, wy = x + dx, y + dy
                if nav.char(p, wx, wy) != "=":
                    continue
                ox, oy = wx + dx, wy + dy
                if nav.room_at(p, ox, oy) != room and nav.char(p, ox, oy) not in "#=":
                    out.append(((p, wx, wy), (p, x, y), (p, ox, oy)))
        return sorted(set(out))

    # ------------------------------------------------------------------ the fall itself
    def fall(self, tick, cid, frm, to, levels, cause, by=None, m=None, text=None):
        """`cid` falls from tile `frm` and lands on tile `to`, `levels` storeys lower. Moves them there, hurts them as the drop and the ground decide, and tells everybody
        near enough to see or hear it. Returns the damage done (they may be dead)."""
        w = self.world
        a = w.agents.get(cid)
        if not a:
            return 0
        nav = self.nav()
        start_room = a["room"]
        land_room = self._room_near(to) or start_room
        surf = SURFACE.get(nav.char(*to), 0.9)
        dmg = int(self.rng.randint(3, 9) + 13 * levels * levels * surf)
        m = self.minute() if m is None else m
        sm = self.__dict__.get("_sim")
        if sm is not None and sm.tick_id is not None and cid in sm.tracks and m is not None:
            sm._cut(cid, m)
            t1 = round(min(sm.dur - 0.05, m + 0.05 + 0.05 * levels), 2)
            sm.tracks[cid].append([t1, to[0], to[1], to[2]])
            sm.cur[cid] = tuple(to)
            sm.falls.append([round(m, 2), list(frm), list(to)])
            sm.hold[cid] = max(sm.hold.get(cid, 0.0), t1 + 2.0)
        a["room"] = land_room
        name, here = self.nm(cid), w.room_name(land_room)
        if text is None:
            text = {"stairs": f"{name} loses their footing on the stairs and tumbles down into the {here}.",
                    "ladder": f"{name} slips off the ladder and drops into the {here}.",
                    "jump": f"{name} jumps from the burning {w.room_name(start_room)} and lands hard in the {here}.",
                    "climb": f"{name} loses their grip climbing down from the {w.room_name(start_room)} and falls into the {here}.",
                    "push": f"{name} goes over the edge and falls into the {here}."}.get(cause, f"{name} falls into the {here}.")
        evt = {"type": "fall", "who": cid, "room": land_room, "vis": "public", "text": text}
        if m is not None:
            evt["m"] = round(m, 1)
        seen = [o for o in sorted(set(w.occupants(start_room)) | set(w.occupants(land_room))) if o in w.agents and o != cid]
        self.log_event(tick, evt, witnesses=seen, actor=cid)
        lethal = {"stairs": "broke their neck falling down the stairs", "ladder": "fell from a ladder", "jump": "died jumping from a burning room",
                  "climb": "fell to their death climbing out of a window", "push": "was pushed to their death"}.get(cause, "died in a fall")
        self.stat(tick, cid, "hp", -dmg, "a fall", lethal=lethal)
        if cid not in w.agents:
            return dmg
        self.stat(tick, cid, "sanity", -2 - int(levels * 2), "a fall")
        if cid in w.agents:
            self.injure(tick, cid, by, set(), dmg, "fall")
        if cid in w.agents and dmg >= 22 and self.rng.random() < 0.35 * self.tune("faint_rate"):
            self.knock_out(tick, cid, "knocked out by the fall", 1, by=by)
        if cid in w.agents and not a.get("out"):
            self.maybe_panic(tick, cid, "the fall", 0.25)
        if cid in w.agents and "free" in tick:
            busy = getattr(self, "_free_busy", None)
            if busy is not None and m is not None:
                busy[cid] = max(busy.get(cid, 0), m + 15)
        return dmg

    def fall_from_edge(self, tick, cid, edge, cause="push", by=None, m=None):
        """Over the edge at tile `edge` (an open floor, a window, a roof edge, a cliff). Returns the damage, or None if there is no drop there."""
        got = self.drop_below(*edge)
        if not got:
            return None
        to, levels = got
        return self.fall(tick, cid, tuple(edge), to, levels, cause, by=by, m=m)

    # ------------------------------------------------------------------ slips while walking
    def walk_hazards(self, tick, cid):
        """Roll for a slip on each flight of stairs or ladder this person has just used. A slip ends the walk at the foot of it."""
        sm = self.__dict__.get("_sim")
        if sm is None or cid not in self.world.agents:
            return False
        steps = sm.portals.pop(cid, None)
        if not steps or self.minute() is None:
            return False
        nav = self.nav()
        a = self.world.agents[cid]
        if a.get("out"):
            return False
        for (t, top, bottom, kind, speed) in steps:
            if kind not in ("stairs", "ladder"):
                continue
            p = STAIR_SLIP if kind == "stairs" else LADDER_SLIP
            p *= 1 + 4 * self.slip_chance(cid)
            room = nav.room_at(*top)
            if room and self.light_of(room) == "dark" and not a.get("lit"):
                p *= 3
            if self.env_on() and (self.env().st["water"].get(_ek(*top), 0) >= 1 or self.env().st["water"].get(_ek(*bottom), 0) >= 1):
                p *= 4
            if speed > 1.6:
                p *= 2
            if self.rng.random() < p:
                low, high = (bottom, top) if nav.z[bottom[0]] < nav.z[top[0]] else (top, bottom)
                self.fall(tick, cid, high, low, 0.6 if kind == "stairs" else 1.0, kind, m=t)
                return True
        return False

    # ------------------------------------------------------------------ windows
    def jump_from_fire(self, tick, cid, m):
        """Trapped by a fire with no way out through the doors: out of the window (a jump from upstairs). Returns True if they got out."""
        w = self.world
        a = w.agents.get(cid)
        if not a:
            return False
        wins = self.outside_windows(a["room"])
        if not wins:
            return False
        here = self.tile_of(cid) or wins[0][1]
        win, inside, outside = min(wins, key=lambda t: abs(t[1][1] - here[1]) + abs(t[1][2] - here[2]))
        got = self.drop_below(*outside) if self.nav().char(*outside) in " S" else None
        if got is None:
            return self.climb_out(tick, cid, m, ground=True)
        to, levels = got
        self.fall(tick, cid, outside, to, levels, "jump", m=m)
        return True

    def climb_out(self, tick, cid, m=None, ground=None):
        """Out through a window: easy on the ground floor, a climb down the wall from upstairs (failing it is a fall). Returns True if they are out."""
        w = self.world
        a = w.agents.get(cid)
        if not a:
            return False
        wins = self.outside_windows(a["room"])
        if not wins:
            return False
        nav = self.nav()
        win, inside, outside = wins[0]
        m = self.minute() if m is None else m
        start = a["room"]
        drop = self.drop_below(*outside) if nav.char(*outside) in " S" else None
        if drop is None:
            land = outside if nav.walkable(*outside) else self._landing(*outside)
            if not land:
                return False
            self._climb_to(tick, cid, inside, land, m)
            self.log_event(tick, {"type": "door", "who": cid, "room": start, "vis": "public", **({"m": round(m, 1)} if m is not None else {}),
                                  "text": f"{self.nm(cid)} climbs out through a window of the {w.room_name(start)}."}, witnesses=[o for o in w.occupants(start) if o != cid], actor=cid)
            return True
        to, levels = drop
        f = self.facet(cid, "courage") if self.mind_on() else 50
        load = sum(a["inv"].values()) if a.get("inv") else 0
        ok = 0.75 - 0.12 * (levels - 1) - 0.5 * self.slip_chance(cid) + (f - 50) / 400 - (0.1 if load > 6 else 0)
        if self.rng.random() < max(0.1, ok):
            self._climb_to(tick, cid, inside, to, m, minutes=2.0 + levels)
            self.log_event(tick, {"type": "door", "who": cid, "room": start, "vis": "public", **({"m": round(m, 1)} if m is not None else {}),
                                  "text": f"{self.nm(cid)} climbs out of a window of the {w.room_name(start)} and down the wall."}, witnesses=[o for o in w.occupants(start) if o != cid], actor=cid)
            return True
        self.fall(tick, cid, outside, to, levels * 0.8, "climb", m=m)
        return True

    def _climb_to(self, tick, cid, inside, land, m, minutes=1.0):
        a = self.world.agents[cid]
        a["room"] = self._room_near(land) or a["room"]
        sm = self.__dict__.get("_sim")
        if sm is not None and sm.tick_id is not None and cid in sm.tracks and m is not None:
            sm.walk(cid, inside, m)
            t0 = max(m, sm.end_t(cid))
            sm._cut(cid, t0)
            t1 = round(min(sm.dur - 0.05, t0 + minutes), 2)
            sm.tracks[cid].append([t1, land[0], land[1], land[2]])
            sm.cur[cid] = tuple(land)
            sm.falls.append([round(t0, 2), list(inside), list(land)])
