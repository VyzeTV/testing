"""Where everybody stands: the engine's own tile positions, minute by minute.

Positions used to be reconstructed after each turn by a planner that only guessed where people had been. Now the engine walks people on the tiles as it moves them: every
move is a route on the map (A* through doors, stairs and, when the engine sent someone that way, hidden passages), started at the engine's minute within the turn. Whatever the
engine asks about positions during the turn (who saw it, who heard it, who can talk to whom) is answered from here, and each emitted turn carries the walks as `tick["live"]` in the
shape the viewer plays. Positions are saved with the game (`state["sim"]`).

A conversation is staged before its lines get their minutes: its members walk to it and stay until their last line, so nobody ever speaks from somewhere else.

Forward mode (phase F2, a day block): the Sim keeps a frontier, the engine's current minute. Nothing is laid before it: a walk or a stop asked for an earlier minute starts at
the frontier instead (counted in `late`), so once the clock has passed a minute, every track up to it is final and a piece of the block can be shown while the rest is made.

Turns still exist (rebuild phase 2b replaces them with a minute clock); within a turn, minute 0 is its start and `dur` its length.
"""
from .gridnav import GridNav, _h

TILES_PER_MIN = 40.0                   # a stroll, in metres (tiles) a minute: crossing the house takes under a minute, the island a few
MAX_SPEED = 110.0                      # a hurry: someone with somewhere to be
PORTAL_MIN = 0.4                       # a flight of stairs or a hatch takes a moment
LADDER_MIN = 1.0                       # a ladder takes longer
IDLE_EVERY = 22                        # minutes between little wanders inside a room when nothing else is going on
LINE_GAP_MIN = 0.3                     # the shortest gap between two lines of a conversation


def _key(t):
    return (t[0], t[1], t[2])


def turn_window(tick):
    """(absolute start minute, length) of a turn."""
    H = int(tick["hour"])
    start = (int(tick["day"]) - 1) * 1440 + H * 60
    dur = (120 if 23 <= H < 31 else 30) if tick.get("phase") == "night" else 120         # the night blocks are two hours; bedtime (22) and dawn are short
    return start, dur


def pos_on(track, m):
    """Where a track is at minute m: on the tile it has reached along a straight stretch, or still at the top of a stair until it is through."""
    if not track:
        return None
    if m <= track[0][0]:
        return _key(track[0][1:])
    for i in range(len(track) - 1):
        a, b = track[i], track[i + 1]
        if a[0] <= m < b[0]:
            if a[1] != b[1] or (a[2] != b[2] and a[3] != b[3]) or b[0] - a[0] <= 0:
                return _key(a[1:])
            if abs(b[2] - a[2]) + abs(b[3] - a[3]) == 1 and b[0] - a[0] <= PORTAL_MIN + 1e-6 and a[1] == b[1]:
                return _key(a[1:])
            f = (m - a[0]) / (b[0] - a[0])
            return (a[1], int(round(a[2] + (b[2] - a[2]) * f)), int(round(a[3] + (b[3] - a[3]) * f)))
    return _key(track[-1][1:])


class Sim:
    """Tile positions for one game, and the walks of the current turn."""

    def __init__(self, nav=None, state=None):
        self.nav = nav or GridNav()
        self.st = state if state is not None else {}
        self.st.setdefault("pos", {})
        self.st.setdefault("clock", None)
        self.tick_id = None
        self.tracks, self.cur, self.hold = {}, {}, {}
        self.start_at, self.arrive_at = {}, {}
        self.jumps = 0
        self.portals, self.falls = {}, []
        self.avoid = frozenset()
        self.dur = 120
        self.start = 0
        self.forward, self.frontier, self.late = False, 0.0, 0

    # ------------------------------------------------------------------ a turn
    def begin(self, start, dur, rooms):
        """Start a turn at absolute minute `start`. `rooms` maps each person to the room the engine has them in; whoever has no saved position (or a position from another day)
        starts at a spot in that room; everybody else starts where they stood and walks if the engine has moved them since."""
        self.start = start if self.st["clock"] is None else max(self.st["clock"], start)
        self.dur = dur
        self.tracks, self.cur, self.hold, self.start_at, self.arrive_at = {}, {}, {}, {}, {}
        self.portals, self.falls = {}, []
        self.forward, self.frontier, self.late = False, 0.0, 0
        new_day = self.st["clock"] is None or self.st["clock"] // 1440 != self.start // 1440 or self.start - self.st["clock"] > 180
        taken = set()
        for cid in sorted(rooms):
            room = rooms[cid]
            p = self.st["pos"].get(cid)
            p = _key(p) if p else None
            if p is None or (new_day and self.nav.room_at(*p) != room) or self.nav.room_at(*p) is None and room in self.nav.rooms:
                if room not in self.nav.rooms:
                    continue
                p = self.spot(room, cid, taken, 1)
            taken.add(p)
            self.cur[cid] = p
            self.tracks[cid] = [[0, p[0], p[1], p[2]]]

    def _fwd(self, m):
        """In forward mode nothing is laid before the frontier."""
        if self.forward and m < self.frontier:
            if self.frontier - m > 0.05:
                self.late += 1
            return self.frontier
        return m

    def end(self):
        self.forward = False
        for cid, p in self.cur.items():
            self.st["pos"][cid] = list(p)
        self.st["clock"] = self.start + self.dur

    def room_of(self, cid, m=None):
        p = self.cur.get(cid) if m is None else self.pos_at(cid, m)
        return self.nav.room_at(*p) if p else None

    def pos_at(self, cid, m):
        return pos_on(self.tracks.get(cid), m)

    def end_t(self, cid):
        tr = self.tracks.get(cid)
        return tr[-1][0] if tr else 0.0

    def occupied(self, but=None):
        return {p for c, p in self.cur.items() if c != but}

    # ------------------------------------------------------------------ places
    def spot(self, room, cid, occupied, salt=0):
        spots = self.nav.spots(room)
        if not spots:
            r = self.nav.rooms[room]
            x0, y0, x1, y1 = r["rect"]
            return (r["plane"], (x0 + x1) // 2, (y0 + y1) // 2)
        off = _h(cid, room, salt) % len(spots)
        for i in range(len(spots)):
            t = spots[(off + i * 3) % len(spots)]
            if t not in occupied:
                return t
        return spots[off]

    # ------------------------------------------------------------------ walking
    def _cut(self, cid, m):
        """Stop whatever this person was doing after minute m (a later plan overrides it): keep their track up to m and stand them where they are at m."""
        tr = self.tracks[cid]
        m = self._fwd(m)
        here = pos_on(tr, m)
        while len(tr) > 1 and tr[-1][0] > m:
            tr.pop()
        if tr[-1][0] < m and _key(tr[-1][1:]) != here:
            tr.append([round(m, 2), here[0], here[1], here[2]])
        elif _key(tr[-1][1:]) != here:
            tr[-1] = [tr[-1][0], here[0], here[1], here[2]]
        self.cur[cid] = here
        return here

    def walk(self, cid, dest, m0, deadline=None, hidden=frozenset(), speed=1.0):
        """Walk `cid` to tile `dest` starting at minute m0 (cutting short anything they had planned after it). With a deadline they hurry, up to a run, to be there in time.
        Returns the minute they arrive."""
        if cid not in self.tracks:
            return m0
        m0 = self._fwd(max(float(m0), self.hold.get(cid, 0.0)))
        here = self._cut(cid, m0)
        tr = self.tracks[cid]
        dest = _key(dest)
        if here == dest:
            return m0
        nav = self.nav
        path = nav.route(here, dest, hidden, self.avoid) or nav.route(here, dest, hidden)
        if not path:
            path = nav.route(here, dest, frozenset(l["id"] for l in nav.gm["links"] if l["kind"] == "secret"))
        if not path:
            # the tile itself cannot be stood on (a seat on the furniture, a blocked spot): stand beside it, and step off it first if that is where they are
            alt = nav.stand_near(dest[0], dest[1], dest[2], set(), nav.room_at(*dest))
            src = here if nav.route(here, alt or dest) else (nav.stand_near(here[0], here[1], here[2], set(), nav.room_at(*here)) or here)
            if alt:
                path = nav.route(src, alt, hidden) or nav.route(src, alt)
                if path:
                    dest = _key(alt)
                    if src != here:
                        path = [here] + path
        if tr[-1][0] < m0:
            tr.append([round(m0, 2), here[0], here[1], here[2]])
        if not path:
            self.jumps += 1                                    # no route on the tiles: they are simply there (should never happen on a valid map)
            tr.append([round(m0, 2), dest[0], dest[1], dest[2]])
            self.cur[cid] = dest
            return m0
        f = speed or 1.0
        v = TILES_PER_MIN * f
        steps = sum(1 for a, b in zip(path, path[1:]) if a[0] == b[0] and abs(a[1] - b[1]) + abs(a[2] - b[2]) == 1)
        portals = len(path) - 1 - steps
        if deadline is not None:
            v = min(MAX_SPEED * f, max(TILES_PER_MIN * f, steps / max(0.5, deadline - m0 - portals * PORTAL_MIN)))
        t, tp, last_dir, out = m0, path[0], None, []
        for tile in path[1:]:
            if tile[0] == tp[0] and abs(tile[1] - tp[1]) + abs(tile[2] - tp[2]) == 1:
                dirv = (tile[1] - tp[1], tile[2] - tp[2])
                if last_dir is not None and dirv != last_dir:
                    out.append([round(t, 2), tp[0], tp[1], tp[2]])
                t += 1.0 / v
                last_dir = dirv
            else:
                out.append([round(t, 2), tp[0], tp[1], tp[2]])
                ladder = nav.char(*tp) == "l" or nav.char(*tile) == "l"
                kind = "ladder" if ladder else next((l["kind"] for o, l in nav.links.get(tp, []) if o == tile), "jump")
                self.portals.setdefault(cid, []).append((round(t, 2), tp, tile, kind, v / TILES_PER_MIN))
                t += LADDER_MIN if ladder else PORTAL_MIN
                out.append([round(t, 2), tile[0], tile[1], tile[2]])
                last_dir = None
            tp = tile
        out.append([round(t, 2), tp[0], tp[1], tp[2]])
        for pt in out:
            if pt[1:] == tr[-1][1:]:
                continue
            tr.append(pt)
        a, b = nav.room_at(*here), nav.room_at(*dest)
        if a != b:
            self.start_at.setdefault(cid, m0)
            self.arrive_at[cid] = t
        self.cur[cid] = dest
        return t

    def go_room(self, cid, room, m0, at=None, salt=3, deadline=None, hidden=frozenset(), speed=1.0, force=False):
        """Send someone to `room` at minute m0: to a free tile next to `at` (the sofa, the stove) when given, else to their own spot in the room. Someone already in the room only moves
        when sent to a particular thing (or when `force` is set). Returns the minute they are there."""
        if cid not in self.tracks or room not in self.nav.rooms:
            return m0
        m0 = self._fwd(max(float(m0), self.hold.get(cid, 0.0)))
        here = self.pos_at(cid, m0) if m0 < self.end_t(cid) else self.cur[cid]
        inside = self.nav.room_at(*here) == room
        dest = None
        if at:
            dest = self.nav.stand_near(at[0], at[1], at[2], self.occupied(cid), room) or self.nav.stand_near(at[0], at[1], at[2], frozenset(), room)
        if dest is None and (not inside or force):
            dest = self.spot(room, cid, self.occupied(cid), salt)
        if dest is None or (inside and not at and not force):
            if m0 < self.end_t(cid) and self.nav.room_at(*self.cur[cid]) != room:
                self._cut(cid, m0)                              # they were on their way out: they stay
            return m0
        return self.walk(cid, dest, m0, deadline, hidden, speed)

    def idle(self, cid, room, salt, every=IDLE_EVERY):
        """A couple of little wanders inside the room in the quiet part of the turn, so a room of people does not look frozen."""
        if cid not in self.tracks or room not in self.nav.rooms or len(self.nav.spots(room)) <= 6 or self.dur < 60:
            return
        k = _h(cid, salt, "idle") % 3
        tt = max(self.end_t(cid), self.hold.get(cid, 0.0)) + every * (1 + _h(cid, salt, "w") % 2)
        for i in range(k):
            if tt > self.dur - 12:
                break
            nxt = self.spot(room, cid, self.occupied(cid), 10 + i)
            if nxt != self.cur[cid] and self.nav.room_at(*self.cur[cid]) == room:
                tt = self.walk(cid, nxt, tt)
            tt += every

    def idle_step(self, cid, room, m, salt):
        """Forward mode: now and then, someone with nothing on wanders to another spot in the room, from minute m."""
        if cid not in self.tracks or room not in self.nav.rooms or len(self.nav.spots(room)) <= 6 or self.dur < 60 or m > self.dur - 12:
            return
        if self.end_t(cid) > m or self.hold.get(cid, 0.0) > m or _h(cid, salt, int(m), "idle") % 3:
            return
        nxt = self.spot(room, cid, self.occupied(cid), 10 + int(m) // IDLE_EVERY)
        if nxt != self.cur[cid] and self.nav.room_at(*self.cur[cid]) == room:
            self.walk(cid, nxt, m)

    def tracks_ok(self):
        """Every point of every track stands on a walkable tile (or one opened up by damage)."""
        return all(self.nav.walkable(p[1], p[2], p[3]) for tr in self.tracks.values() for p in tr)


class SimMixin:
    """The engine's side: one Sim per game, a turn opened on first use, and the live record of the turn attached when it is emitted."""

    def sim(self):
        sm = self.__dict__.get("_sim")
        if sm is None:
            sm = self._sim = Sim(self.nav(), self.s.setdefault("sim", {}))
        return sm

    def sim_turn(self, tick):
        """The Sim with this tick's turn open (opening it the first time the turn moves anybody)."""
        sm = self.sim()
        if sm.tick_id != id(tick):
            start, dur = turn_window(tick)
            sm.begin(start, dur, {cid: a["room"] for cid, a in self.world.agents.items()})
            sm.tick_id = id(tick)
            sm.avoid = self.env_avoid()
            self._sim_tick, self._sim_m = tick, 0.0
            self._sim_said, self._sim_groups, self._sim_talk_seen = [], [], set()
        return sm

    def sim_forward(self, tick):
        """Put this block's Sim in forward mode (phase F2): from now on nothing is laid before the engine's minute. NeoVi gets her track at once."""
        sm = self.sim_turn(tick)
        sm.forward, sm.frontier = True, float(self._m or 0.0)
        self.nv_track_start(tick, sm)
        return sm

    def sim_idle(self, tick, m):
        """Forward mode: the idle wander a little, as the block runs (not those in free time, out cold, asleep or in a conversation)."""
        sm = self.__dict__.get("_sim")
        if sm is None or not sm.forward:
            return
        free = tick.get("free") or {}
        for cid in sorted(self.world.agents):
            a = self.world.agents[cid]
            if cid in free or a.get("out") or a.get("asleep") or self.in_convo(cid):
                continue
            sm.idle_step(cid, a["room"], float(m), (tick["day"], int(tick["hour"])))

    def nv_track_start(self, tick, sm):
        """Forward mode: NeoVi stands on the map from the start of the block; her chores and her punishments walk her there as they happen."""
        nv = (self.s.get("npcs") or {}).get("neovi") or {}
        nav = sm.nav
        if not self.neovi_maid() or "neovi" in sm.tracks or "neovi" in self.world.agents:
            return
        mv = (tick.get("moves") or {}).get("neovi") or {}
        path = [r for r in (mv.get("path") or []) if r in nav.rooms] or ([nv["room"]] if nv.get("room") in nav.rooms else [])
        if not path:
            return
        p = sm.st["pos"].get("neovi")
        p = _key(p) if p else None
        if p is None or nav.room_at(*p) != path[0]:
            p = sm.spot(path[0], "neovi", sm.occupied(), 1)
        sm.cur["neovi"], sm.tracks["neovi"] = p, [[0, p[0], p[1], p[2]]]
        if not tick.get("nv_plan") and len(path) > 1:
            t = float(self._stagger("neovi", tick))
            for room in dict.fromkeys(path[1:]):
                t = sm.go_room("neovi", room, max(t, sm.end_t("neovi")))

    def nv_walk(self, room, deadline=None, final=False):
        """Forward mode: walk NeoVi to `room` from now. Returns when she gets there (or None without her on the map). `final`: she stays there for the rest of the block."""
        sm = self.__dict__.get("_sim")
        if sm is None or not sm.forward or "neovi" not in sm.tracks or room not in sm.nav.rooms:
            return None
        if sm.hold.get("neovi", 0.0) >= sm.dur:
            return sm.end_t("neovi")
        now = float(self._m or 0.0)
        t = sm.go_room("neovi", room, now, deadline=deadline)
        if final:
            sm.hold["neovi"] = sm.dur
        return t

    def sim_now(self):
        """The minute within the current turn the engine is at."""
        m = self.minute()
        return m if m is not None else float(self.__dict__.get("_sim_m") or 0.0)

    def sim_pos(self, cid):
        """Where `cid` stands right now in the current turn, or None outside a turn."""
        sm = self.__dict__.get("_sim")
        if sm is None or sm.tick_id is None or cid not in sm.tracks:
            return None
        return sm.pos_at(cid, self.sim_now())

    def sim_go(self, tick, cid, m0):
        """Walk `cid` to the room the engine has just put them in, setting off at minute m0. Returns the minute they arrive."""
        sm = self.sim_turn(tick)
        a = self.world.agents.get(cid)
        if not a or cid not in sm.tracks or a["room"] not in sm.nav.rooms or sm.room_of(cid) == a["room"]:
            return float(m0)
        path = ((tick.get("moves") or {}).get(cid) or {}).get("path") or []
        sm.avoid = self.env_avoid()
        t = sm.go_room(cid, a["room"], m0, deadline=min(sm.dur - 1.0, float(m0) + 40.0), hidden=sm.nav.hidden_links_between(path), speed=self.move_factor(cid))
        if self.walk_hazards(tick, cid):
            t = sm.end_t(cid)
        return round(float(t), 2)

    def first_in(self, cid, room):
        """The first minute of the current turn, up to now, at which `cid` stood in `room` (None if they have not been there, or outside a turn)."""
        sm = self.__dict__.get("_sim")
        now = self.minute()
        if sm is None or sm.tick_id is None or cid not in sm.tracks or now is None:
            return None
        tr, nav = sm.tracks[cid], sm.nav
        for i, p in enumerate(tr):
            if p[0] > now:
                break
            if nav.room_at(p[1], p[2], p[3]) == room:
                return float(p[0])
        return None

    def present(self, cid, room):
        """Is `cid` in `room` at the engine's current minute? (Somebody the engine has sent there may still be on the way.) Without positions, the room is all there is."""
        p = self.sim_pos(cid)
        return p is None or self.nav().room_at(*p) == room

    def _stagger(self, cid, tick):
        return 1 + _h(cid, tick["day"], int(tick["hour"]), "go") % 14

    def sim_sync(self, tick, m, stagger=False):
        """Walk everybody whose room the engine has changed to it, starting at minute m (spread over the first quarter hour when `stagger`)."""
        sm = self.sim_turn(tick)
        sm.avoid = self.env_avoid()
        self._sim_m = float(m)
        for cid in sorted(self.world.agents):
            a = self.world.agents[cid]
            if cid not in sm.tracks or a["room"] not in sm.nav.rooms:
                continue
            if sm.room_of(cid) != a["room"]:
                m0 = max(float(m), sm.end_t(cid) if not stagger else 0.0) + (self._stagger(cid, tick) if stagger else 0)
                path = ((tick.get("moves") or {}).get(cid) or {}).get("path") or []
                sm.go_room(cid, a["room"], m0, deadline=min(sm.dur - 1.0, m0 + 40.0), hidden=sm.nav.hidden_links_between(path), speed=self.move_factor(cid))
                self.walk_hazards(tick, cid)

    def sim_seg(self, tick, cid, m0, room, at, act):
        """A free-time activity starts: walk them to it (to the piece of furniture it is done at, if any)."""
        sm = self.sim_turn(tick)
        if cid not in sm.tracks or room not in sm.nav.rooms:
            return
        self._sim_m = float(m0)
        inside = sm.room_of(cid, m0) == room
        if not at and inside:
            return
        if act == "walk" and inside:
            return
        path = ((tick.get("moves") or {}).get(cid) or {}).get("path") or []
        sm.go_room(cid, room, m0, at=at if act != "walk" else None, salt=5, deadline=min(sm.dur - 1.0, float(m0) + 14.0),
                   hidden=sm.nav.hidden_links_between(path), speed=self.move_factor(cid))
        self.walk_hazards(tick, cid)

    # ------------------------------------------------------------------ conversations
    def sim_talk(self, tick, part=None):
        """Give every conversation of the turn its minutes, after walking its members to it. Lines only ever fall while their speaker is in the room.
        `part` "staged": only the conversations written whole (staged as soon as they are written, in forward mode); None: all not done yet."""
        sm = self.sim_turn(tick)
        nav, dur = sm.nav, sm.dur
        free = bool(tick.get("free"))
        said, groups = self._sim_said, self._sim_groups
        seen = self._sim_talk_seen
        for gi, g in enumerate(tick.get("talk") or []):
            if gi in seen or (part == "staged" and g.get("live")):
                continue
            seen.add(gi)
            room = g.get("room")
            if room not in nav.rooms:
                continue
            lines = g.get("lines") or []
            if g.get("live"):
                # a live conversation (convo.py): its members were really there, and every line already has its minute and the room it was said in
                for ln in lines:
                    said.append({"m": round(min(dur - 0.5, float(ln.get("m", 0))), 1), "who": ln.get("speaker"), "k": ln.get("kind", "say"), "text": (ln.get("text") or "")[:170],
                                 "room": ln.get("room") or room, "g": gi})
                groups.append({"g": gi, "m": round(float(g.get("m", 0)), 1), "room": room, "chat": bool(g.get("chat")), "at": g.get("at"), "why": g.get("why", ""),
                               "matters": g.get("matters") or [], "members": g.get("members") or [], "live": True})
                continue
            members = []
            for ln in lines:
                sp = ln.get("speaker")
                if sp in sm.tracks and sp not in members and (self.world.all_agents.get(sp) or {}).get("status", "alive") == "alive":
                    members.append(sp)
            chat = free and g.get("m") is not None
            m0 = float(g["m"]) + 1.0 if chat else min((94.0 + 2 * gi) if free else (58.0 + 3 * gi), max(dur * 0.5, dur - 26.0) + gi)    # (short night turns talk earlier)
            anchor = tuple(g["at"]) if chat and g.get("at") else None
            # whoever is not in the room at the start walks there (cutting short what they were doing) and arrives in time, or the talk waits for them
            for i, sp in enumerate(members):
                if nav.room_at(*sm.pos_at(sp, m0)) == room:
                    continue
                go = max(0.0, sm.hold.get(sp, 0.0), m0 - 12.0)
                dl = m0 - 0.5 if m0 - 0.5 > go + 0.5 else None
                spots = nav.spots(room)
                if anchor is None and not free and i < len(spots) and spots[i] not in sm.occupied(sp):
                    t = sm.walk(sp, spots[i], go, dl, speed=self.move_factor(sp))
                else:
                    t = sm.go_room(sp, room, go, at=anchor, salt=4, deadline=dl, speed=self.move_factor(sp), force=True)
                m0 = max(m0, t + 0.5)
            m0 = min(m0, dur - 2.0)
            for sp in members:                                  # anyone still not there by the end of the turn (no route) is fetched at once
                if nav.room_at(*sm.pos_at(sp, m0)) != room:
                    sm.go_room(sp, room, m0, salt=4, force=True)
                    m0 = max(m0, min(dur - 2.0, sm.end_t(sp) + 0.2))
            # how long they are all together: until the first of them sets off somewhere else
            leave = {}
            for sp in members:
                tr, prev = sm.tracks[sp], None
                for p in tr:
                    if p[0] > m0 and nav.room_at(p[1], p[2], p[3]) != room:
                        leave[sp] = prev[0] if prev and prev[0] > m0 else m0
                        break
                    prev = p
            n = len(lines)
            gap = min(2.4, 26.0 / max(1, n)) if chat else (2.4 if free else 3.5)
            lead = 1.0 if chat else (2.0 if free else 6.0)
            need = lead + n * gap
            wend = min([dur - 1.0] + list(leave.values()))
            if wend - m0 < need and wend - m0 < 0.5 + n * 0.8:
                for sp in list(leave):                        # not enough time before somebody leaves: they stay for the conversation
                    sm._cut(sp, max(m0, leave[sp]))
                    del leave[sp]
                wend = dur - 1.0
            if wend - m0 < need:
                lead = min(lead, 0.5)
                gap = max(LINE_GAP_MIN, (wend - m0 - lead) / max(1, n))
            last = {}
            for li, ln in enumerate(lines):
                m = min(dur - 0.5, m0 + lead + li * gap)
                sp = ln.get("speaker")
                said.append({"m": round(m, 1), "who": sp, "k": ln.get("kind", "say"), "text": (ln.get("text") or "")[:170], "room": room, "g": gi})
                last[sp] = m
            for sp in members:
                sm.hold[sp] = max(sm.hold.get(sp, 0.0), last.get(sp, m0) + 0.6)
            groups.append({"g": gi, "m": round(m0, 1), "room": room, "chat": chat, "at": g.get("at"), "why": g.get("why", ""), "matters": g.get("matters") or [], "members": g.get("members") or members})

    # ------------------------------------------------------------------ the end of a turn
    def sim_finish(self, tick):
        """Close the turn: walk whoever the engine moved since, stage conversations not staged yet, let the idle wander, and return the live record of the turn."""
        sm = self.sim_turn(tick)
        self.sim_talk(tick)
        nav, dur = sm.nav, sm.dur
        agents = (tick.get("state") or {}).get("agents") or {}
        flags = {}
        free = tick.get("free") or {}
        speakers = {s_["who"] for s_ in self._sim_said}
        for cid in sorted(sm.tracks):
            a = agents.get(cid) or (self.world.all_agents.get(cid) or {})
            alive = a.get("status", "alive") == "alive"
            flags[cid] = {"dead": not alive, "out": bool(a.get("out")), "hiding": bool(a.get("hiding"))}
            room = a.get("room")
            if room not in nav.rooms:
                continue
            if sm.room_of(cid) != room:
                m0 = max(sm.end_t(cid), sm.hold.get(cid, 0.0), self.minute() or 0.0)
                if m0 <= 0.0:
                    m0 = float(self._stagger(cid, tick))      # nobody moved them yet this turn: they set off in the first quarter hour
                path = ((tick.get("moves") or {}).get(cid) or {}).get("path") or []
                sm.go_room(cid, room, max(m0, 1.0 if not alive else m0), deadline=dur - 1.0, hidden=nav.hidden_links_between(path), speed=self.move_factor(cid) if cid in self.world.agents else 1.0)
            elif alive and not a.get("out") and cid not in speakers and cid not in free and not sm.forward:
                sm.idle(cid, room, (tick["day"], int(tick["hour"])))           # (in forward mode the idle wandered as the block ran: sim_idle)
        for tr in sm.tracks.values():                           # a walk squeezed against the end of the turn still finishes inside it
            for p in tr:
                p[0] = round(min(p[0], dur - 0.05), 2)
        events = []
        chron = tick.get("chron") or []
        n_other = sum(1 for e in chron if e["type"] not in ("move", "arrive"))
        i_other = 0
        for e in chron:
            if e.get("m") is not None:
                m = e["m"]
            elif e["type"] == "move":
                m = sm.start_at.get(e.get("who"), 2)
            elif e["type"] == "arrive":
                m = sm.arrive_at.get(e.get("who"), 3)
            elif e["type"] == "talk":
                m = min([s_["m"] for s_ in self._sim_said] or [96 if free else 60])
            else:
                m = 4 + int(i_other * max(1, dur - 10) / max(1, n_other))
                i_other += 1
            events.append({"id": e["id"], "m": round(min(m, dur - 0.5), 1), "cls": e["cls"], "type": e["type"], "who": e.get("who"), "room": e.get("room"), "vis": e["vis"], "text": e["text"][:240]})
        events.sort(key=lambda e: (e["m"], e["id"]))
        self.sim_neovi(tick, sm, events, flags)
        for s_ in self._sim_said:                               # a walk re-laid later in the turn wins: a line comes from where its speaker really is
            if s_["who"] in sm.tracks:
                r_ = nav.room_at(*sm.pos_at(s_["who"], s_["m"]))
                if r_ and r_ != s_["room"]:
                    s_["room"] = r_
        acts ={cid: [[round(sg["m0"]), round(sg["m1"]), sg.get("act"), sg.get("label"), sg.get("room")] for sg in segs] for cid, segs in free.items()} if free else {}
        if tick.get("nv_plan") and acts:
            acts["neovi"] = [[c[0], c[1], "chore", c[3], c[2]] for c in tick["nv_plan"]]          # her chores for Who's where
        live = {"v": 2, "start": sm.start, "dur": dur, "tracks": sm.tracks, "flags": flags, "talk": sorted(self._sim_said, key=lambda s_: (s_["m"], s_["g"])), "events": events, "acts": acts,
                "segment": tick.get("segment", "turn"), "groups": self._sim_groups}
        if sm.late:
            live["late"] = sm.late                                     # walks asked for a minute already past, started at the frontier instead
        if sm.jumps:
            live["jumps"] = sm.jumps
            sm.jumps = 0
        if sm.falls:
            live["falls"] = sm.falls
        sm.end()
        sm.tick_id = None
        self._sim_m = 0.0
        return live

    def sim_neovi(self, tick, sm, events, flags):
        """NeoVi on the map. She is not a participant, so the engine only keeps her room; her walk is laid down when the turn closes, after everybody else's, so it never
        changes what the cast saw or heard. She walks the turn's route and reaches each person she punishes just before she does it."""
        nv = (self.s.get("npcs") or {}).get("neovi") or {}
        nav, dur = sm.nav, sm.dur
        if "neovi" in sm.tracks and "neovi" not in self.world.agents:
            for q in sm.tracks["neovi"]:                              # forward mode: she walked as the block ran
                q[0] = round(min(q[0], dur - 0.05), 2)
            flags["neovi"] = {"dead": False, "out": False, "hiding": False}
            return
        if nv.get("room") not in nav.rooms or "neovi" in sm.tracks or "neovi" in self.world.agents:
            return
        mv = (tick.get("moves") or {}).get("neovi") or {}
        path = [r for r in (mv.get("path") or []) if r in nav.rooms] or [nv["room"]]
        p = sm.st["pos"].get("neovi")
        p = _key(p) if p else None
        if p is None or nav.room_at(*p) != path[0]:
            p = sm.spot(path[0], "neovi", sm.occupied(), 1)
        sm.cur["neovi"], sm.tracks["neovi"] = p, [[0, p[0], p[1], p[2]]]
        due = {}
        for e in events:
            if e["type"] == "punish" and e.get("room") in nav.rooms:
                due.setdefault(e["room"], e["m"])
        plan = [(float(c[0]), c[2]) for c in tick.get("nv_plan") or [] if c[2] in nav.rooms]
        if plan:
            # a block of chores: she walks from chore to chore at their minutes, and to anyone she punishes on the way
            cut = max(due.values()) - 12.0 if due else None              # a punishment comes last: the rule is enforced after the chores, and she stays there
            stops = sorted([x for x in plan[1:] if cut is None or x[0] < cut] + [(max(0.0, due[r] - 12.0), r) for r in due], key=lambda x: x[0])
            last = plan[-1][1]
            for at, room in stops:
                if room in due and abs(at - (due[room] - 12.0)) < 0.01:
                    at = max(sm.end_t("neovi"), at)
                    sm.go_room("neovi", room, at, deadline=max(at + 0.5, due[room] - 0.3))
                else:
                    sm.go_room("neovi", room, max(at, sm.end_t("neovi")))
                    last = room
            if nav.room_at(*sm.cur["neovi"]) == last:
                sm.idle("neovi", last, (tick["day"], int(tick["hour"])))
        else:
            stops = [r for r in dict.fromkeys(path[1:]) if r in due]
            if path[-1] not in stops:
                stops.append(path[-1])
            t = float(self._stagger("neovi", tick))
            for room in stops:
                if room in due:
                    at = max(sm.end_t("neovi"), due[room] - 12.0)
                    t = sm.go_room("neovi", room, at, deadline=max(at + 0.5, due[room] - 0.3))
                else:
                    t = sm.go_room("neovi", room, max(t, sm.end_t("neovi")))
            if nav.room_at(*sm.cur["neovi"]) == path[-1]:
                sm.idle("neovi", path[-1], (tick["day"], int(tick["hour"])))
        for q in sm.tracks["neovi"]:
            q[0] = round(min(q[0], dur - 0.05), 2)
        flags["neovi"] = {"dead": False, "out": False, "hiding": False}
