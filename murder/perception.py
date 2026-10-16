"""Perception on the tile map: who can see whom (line of sight and light), who can hear what (sound spreading through doors, walls and stairs), where the cameras look,
and therefore who witnesses an event and how good a moment is for something secret.

Perception is pure geometry (no randomness, no game state) built on GridNav. PerceptionMixin hands it the game's own facts (power cuts, nominal positions) for the engine:
  * witnesses of public events are the people who could actually see or hear them, not simply everyone in the same room;
  * a plotter's window is "nobody who could see or hear this", plus camera blind spots and darkness;
  * in a very large room, people too far apart to hear each other do not hold one conversation.
The tuning dial `perception` (World group) switches the engine hooks off (0), which restores the old room-level behaviour.
"""
from .data_world import CAMERA_BLIND, ROOMS
from .gridnav import GridNav
from .scale import tiles, area, MAP_SCALE

LOUD = {"whisper": tiles(2.0, 1.5), "quiet": tiles(3.5, 2.5), "normal": tiles(8.0), "loud": tiles(14.0), "shout": tiles(18.0)}
SIGHT = {"lit": int(tiles(18)), "dim": int(tiles(7, 3)), "dark": 2}
WALL_COST, DOOR_COST, WINDOW_COST, STAIR_COST = 5.0 * MAP_SCALE, 2.0 * MAP_SCALE, 3.0 * MAP_SCALE, 4.0 * MAP_SCALE      # what blocks sound is measured in the same (scaled) tiles
FLOOR_COST = 7.0 * MAP_SCALE      # sound through a floor or a ceiling: a shout upstairs is heard below, a whisper is not
SIGHT_BLOCK = set("# +LTH")        # walls, closed doors, trees and hedges block sight (and nothing, outside a level); windows, railings and open drops do not
BIG_ROOM_AREA = area(220)         # interior tiles above which a room can hold separate conversations
TALK_RANGE = int(tiles(8, 4))             # tiles within which normal speech carries between two people in the same room
# how loud each kind of event is, for hearing it from outside its own spot
EVENT_LOUD = {"attack": "loud", "assault": "loud", "sabotage": "normal", "outburst": "shout", "punish": "loud", "island": "loud", "door": "normal", "faint": "normal",
              "friction": "normal", "reaction": "normal", "madness": "normal", "frame": "quiet", "rob": "quiet", "carry": "quiet", "lock": "quiet", "hide": "whisper",
              "conceal": "whisper", "stash": "quiet", "take": "quiet", "give": "quiet", "frisk": "quiet", "search": "quiet", "craft": "quiet", "treat": "quiet", "use": "quiet"}


class Perception:
    def __init__(self, nav=None):
        self.nav = nav or GridNav()
        self._hear = {}
        self.cam_rooms = {rid for rid, r in self.nav.rooms.items() if not r["open"] and rid not in CAMERA_BLIND and rid != "core_vault"}

    # ------------------------------------------------------------------ sight
    def set_env(self, env):
        self.env = env

    def blocks_sight(self, plane, x, y):
        c = self.nav.char(plane, x, y)
        env = getattr(self, "env", None)
        if env is not None:
            k = f"{plane},{x},{y}"
            if c in "+L" and env.broken(k):
                return False
            if env.st["smoke"].get(k, 0) >= 4:
                return True
        return c in SIGHT_BLOCK

    def los(self, a, b):
        """Clear line between two tiles on the same level (walls and closed doors block it; windows, furniture and people do not)."""
        if a[0] != b[0]:
            return False
        pl, x0, y0, x1, y1 = a[0], a[1], a[2], b[1], b[2]
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        n = max(dx, dy)
        if n == 0:
            return True
        for i in range(1, n):
            x = x0 + round((x1 - x0) * i / n)
            y = y0 + round((y1 - y0) * i / n)
            if self.blocks_sight(pl, x, y):
                return False
        return True

    def sees(self, a, b, light="lit"):
        d = max(abs(a[1] - b[1]), abs(a[2] - b[2]))
        if d > SIGHT.get(light, SIGHT["lit"]):
            return False
        if a[0] == b[0]:
            return self.los(a, b)
        return self.sees_across(a, b)

    def sees_across(self, a, b):
        """Between neighbouring levels, only through an open drop (a gallery over a hall): someone above looks down into it, someone below looks up at its edge."""
        nav = self.nav
        za, zb = nav.z.get(a[0], 0), nav.z.get(b[0], 0)
        if abs(za - zb) != 1:
            return False
        hi, lo = (a, b) if za > zb else (b, a)
        if nav.char(hi[0], lo[1], lo[2]) == "v":                     # the one below stands under the void: look down through it
            return self.los(hi, (hi[0], lo[1], lo[2]))
        for dx in (-1, 0, 1):                                        # the one above stands at the void's edge: seen from below through it
            for dy in (-1, 0, 1):
                v = (hi[0], hi[1] + dx, hi[2] + dy)
                if nav.char(*v) == "v" and self.los(lo, (lo[0], v[1], v[2])):
                    return True
        return False

    def visible_tiles(self, a, light="lit"):
        r = SIGHT.get(light, SIGHT["lit"])
        out = []
        for y in range(a[2] - r, a[2] + r + 1):
            for x in range(a[1] - r, a[1] + r + 1):
                if 0 <= x < self.nav.w and 0 <= y < self.nav.h and self.nav.char(a[0], x, y) != " " and self.sees(a, (a[0], x, y), light):
                    out.append((x, y))
        return out

    # ------------------------------------------------------------------ sound
    def hearing_field(self, origin, loud="normal"):
        """Sound intensity (> 0) at every tile reached from `origin`: it fades by one per tile and loses more through doors, windows, walls and stairs."""
        level = LOUD[loud] if isinstance(loud, str) else float(loud)
        key = (origin, level)
        if key in self._hear:
            return self._hear[key]
        import heapq
        best = {origin: level}
        heap = [(-level, origin)]
        nav = self.nav
        while heap:
            neg, cur = heapq.heappop(heap)
            lv = -neg
            if lv < best.get(cur, 0):
                continue
            pl, x, y = cur
            nxt = []
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                t = (pl, x + dx, y + dy)
                c = nav.char(*t)
                if c == " ":
                    continue
                cost = WALL_COST if c == "#" else WINDOW_COST if c == "=" else DOOR_COST if c in "+L" else 1.0
                nxt.append((t, cost))
            if level >= tiles(10):
                for other, link in nav.links.get(cur, []):
                    if link["kind"] == "stairs":
                        nxt.append((other, STAIR_COST))
            for d in (1, -1):                                        # up through the ceiling, down through the floor (freely through an open drop)
                op = nav.level_above(pl, d)
                if op is None or nav.char(op, x, y) == " ":
                    continue
                here_c, there_c = nav.char(pl, x, y), nav.char(op, x, y)
                nxt.append(((op, x, y), 1.0 if "v" in (here_c, there_c) else FLOOR_COST))
            for t, cost in nxt:
                nl = lv - cost
                if nl > best.get(t, 0):
                    best[t] = nl
                    heapq.heappush(heap, (-nl, t))
        out = {t: v for t, v in best.items() if v > 0}
        if len(self._hear) > 400:
            self._hear.clear()
        self._hear[key] = out
        return out

    def hears(self, origin, listener, loud="normal"):
        return listener in self.hearing_field(origin, loud)

    # ------------------------------------------------------------------ cameras
    def camera_sees(self, room, power_on=True):
        return bool(power_on and room in self.cam_rooms)

    # ------------------------------------------------------------------ witnesses and chances
    def witnesses(self, origin, others, loud="normal", light="lit", visual=True):
        """Who among `others` ({id: tile}) could see or hear something happening at `origin`. Returns {id: "saw"|"heard"}."""
        out = {}
        for cid, t in others.items():
            if visual and self.sees(origin, t, light):
                out[cid] = "saw"
            elif self.hears(origin, t, loud):
                out[cid] = "heard"
        return out


class PerceptionMixin:
    """The engine's use of perception. Every hook is skipped when the tuning dial `perception` is 0."""

    def perc(self):
        p = self.__dict__.get("_perception")
        if p is None:
            p = self._perception = Perception(self.nav())
        return p

    def perception_on(self):
        return bool(self.tune("perception"))

    def tile_of(self, cid):
        """Where someone nominally stands: the live planner's tile when it matches their room, otherwise their usual spot in the room."""
        a = self.world.agents.get(cid)
        if not a or a["room"] not in ROOMS:
            return None
        nav = self.perc().nav
        pl = self.__dict__.get("_live_planner")
        if pl is not None:
            t = pl.pos.get(cid)
            if t is not None and nav.room_at(*t) == a["room"]:
                return tuple(t)
        return nav.nominal(a["room"], cid, 3)

    def light_of(self, room):
        """lit / dim / dark for a room right now: a blackout leaves the house dark except for people carrying a light (handled by in_dark); cellars and the vault are dim."""
        if self.env_on():
            return self.env_room_light(room)
        if self.blackout_until >= self.idx:
            return "dark"
        return "dim" if room in ("wine_cellar", "boiler_room", "cold_store", "core_vault", "attic", "lighthouse") and self.s.get("_hour", 12) not in range(8, 18) else "lit"

    def power_on(self):
        return self.blackout_until < self.idx

    def event_witnesses(self, actor, room, kind, candidates):
        """Narrow a list of people who were around to those who could see or hear it."""
        if not self.perception_on() or actor not in self.world.agents or not candidates:
            return candidates
        o = self.tile_of(actor)
        if not o:
            return candidates
        loud = EVENT_LOUD.get(kind, "normal")
        light = self.light_of(room)
        others = {c: self.tile_of(c) for c in candidates if c != actor}
        others = {c: t for c, t in others.items() if t}
        got = self.perc().witnesses(o, others, loud, light)
        keep = [c for c in candidates if c == actor or c in got or c not in others]
        return keep

    def perceivers_of(self, cid, room, loud="quiet", exclude=()):
        """People in `room` who could see or hear what `cid` does there."""
        w = self.world
        people = [o for o in w.occupants(room) if o in w.agents and o != cid and o not in exclude]
        if not self.perception_on():
            return people
        o = self.tile_of(cid)
        if not o:
            return people
        light = self.light_of(room)
        got = self.perc().witnesses(o, {p: self.tile_of(p) for p in people if self.tile_of(p)}, loud, light)
        return [p for p in people if p in got]

    def hearing_cluster(self, room, members, wanting=()):
        """In a very large room, the people able to hear one another around whoever wants to talk (chained within normal talking range); everyone else is out of earshot."""
        if not self.perception_on() or room not in ROOMS or ROOMS[room][1] == "":
            return members
        nav = self.perc().nav
        if nav.area(room) < BIG_ROOM_AREA:
            return members
        humans = [m for m in members if m in self.world.agents]
        pos = {m: self.tile_of(m) for m in humans}
        pos = {m: t for m, t in pos.items() if t}
        if len(pos) < 2:
            return members
        # connected components by "can hear each other at normal volume"
        comp, seen = [], set()
        for m in pos:
            if m in seen:
                continue
            grp, stack = [], [m]
            seen.add(m)
            while stack:
                c = stack.pop()
                grp.append(c)
                for o in pos:
                    if o not in seen and max(abs(pos[c][1] - pos[o][1]), abs(pos[c][2] - pos[o][2])) <= TALK_RANGE:
                        seen.add(o)
                        stack.append(o)
            comp.append(grp)
        if len(comp) == 1:
            return members
        pick = max(comp, key=lambda g: (sum(1 for m in g if m in wanting), len(g)))
        keep = set(pick)
        return [m for m in members if m in keep or m not in pos]
