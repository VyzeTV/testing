"""The live timeline: turns one engine tick (a two-hour decision turn) into minute-by-minute tile tracks, scheduled events and speech bubbles for the live viewer.

The engine still decides every two game hours; between decisions the world is played out on the tile map: people walk their real routes (A* on the tiles, through stairs and,
when the engine sent them that way, hidden hatches), settle at their own spots, wander a little, and gather for conversations. The plan is deterministic (no engine randomness is
used), so it changes no behaviour and can be recomputed for a replay. LiveMixin attaches `tick["live"]` in emit().
"""
from .gridnav import GridNav, _h
from .scale import MAP_SCALE

TILES_PER_MIN = 40.0                   # a stroll, in metres (tiles) a minute: crossing the house takes under a minute, the island a few
MAX_SPEED = 110.0                      # a hurry: someone with somewhere to be
ARRIVE_BY = 54.0
IDLE_EVERY = 22
PORTAL_MIN = 0.4                              # a flight of stairs or a hatch takes a moment


class LivePlanner:
    def __init__(self, nav=None):
        self.nav = nav or GridNav()
        self.pos = {}
        self.clock = None
        self.dead = set()

    # ------------------------------------------------------------------ helpers
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

    def walk(self, track, t_now, src, dst, hidden=frozenset(), deadline=None):
        """Append the corners of the route src -> dst to `track`, starting at minute t_now. With a deadline the walker hurries (up to a run) to arrive in time. A stair or a secret hatch is a step
        between two tiles that are not neighbours: it takes a moment, however far apart the two ends are drawn. Returns the minute of arrival (or t_now if there is no route)."""
        if src == dst:
            return t_now
        path = self.nav.route(src, dst, hidden, getattr(self, "avoid", frozenset()))
        if not path:
            track.append([round(t_now, 1), dst[0], dst[1], dst[2]])      # no route on the tiles: jump
            return t_now
        f = getattr(self, "cur_speed", 1.0)
        speed = TILES_PER_MIN * f
        steps = sum(1 for a, b in zip(path, path[1:]) if a[0] == b[0] and abs(a[1] - b[1]) + abs(a[2] - b[2]) == 1)
        portals = len(path) - 1 - steps
        if deadline is not None:
            speed = min(MAX_SPEED * f, max(TILES_PER_MIN * f, steps / max(1.0, deadline - t_now - portals * PORTAL_MIN)))
        t = t_now
        tp, last_dir, out = path[0], None, []
        for tile in path[1:]:
            if tile[0] == tp[0] and abs(tile[1] - tp[1]) + abs(tile[2] - tp[2]) == 1:
                dirv = (tile[1] - tp[1], tile[2] - tp[2])
                if last_dir is not None and dirv != last_dir:
                    out.append([round(t, 1), tp[0], tp[1], tp[2]])
                t += 1.0 / speed
                last_dir = dirv
            else:
                out.append([round(t, 1), tp[0], tp[1], tp[2]])
                t += PORTAL_MIN
                out.append([round(t, 1), tile[0], tile[1], tile[2]])
                last_dir = None
            tp = tile
        out.append([round(t, 1), tp[0], tp[1], tp[2]])
        last = None
        for pt in out:
            if last is not None and pt[1:] == last[1:]:
                continue
            track.append(pt)
            last = pt
        return t

    # ------------------------------------------------------------------ one tick
    def plan(self, tick, avoid=frozenset(), speeds=None):
        self.avoid = avoid
        self.speeds = speeds or {}
        self.cur_speed = 1.0
        nav = self.nav
        H = int(tick["hour"])
        absmin = (int(tick["day"]) - 1) * 1440 + H * 60
        start = absmin if self.clock is None else max(self.clock, absmin)
        phase = tick.get("phase")
        dur = (60 if H >= 23 else 30) if phase == "night" else 120
        agents = (tick.get("state") or {}).get("agents") or {}
        moves = tick.get("moves") or {}
        talk = tick.get("talk") or []
        free = tick.get("free") or {}
        speakers = {}
        for gi, g in enumerate(talk):
            if free and g.get("m") is not None:
                continue                                    # a chat that started during the block: they are there at its minute, and go about their business after
            for ln in g.get("lines", []):
                speakers.setdefault(ln.get("speaker"), g.get("room"))
        gtime = {}
        for gi, g in enumerate(talk):
            rm = g.get("room")
            if free and g.get("m") is not None:
                continue
            if rm in nav.rooms:
                m0 = (94 + 2 * gi) if free else 58 + 3 * gi
                gtime[rm] = (m0, min(dur - 2, m0 + 6 + len(g.get("lines", [])) * 3.5))
        occupied = set()
        for cid, p in self.pos.items():
            if cid in agents and agents[cid].get("status", "alive") == "alive":
                occupied.add(p)
        tracks, flags, arrive_at, start_at = {}, {}, {}, {}
        late_go = {}
        order = sorted(agents)
        for cid in order:
            a = agents[cid]
            room = a.get("room")
            self.cur_speed = self.speeds.get(cid, 1.0)
            if room not in nav.rooms:
                continue
            alive = a.get("status", "alive") == "alive"
            mv = moves.get(cid) or {}
            from_room = mv.get("from") if mv.get("from") in nav.rooms else None
            cur = self.pos.get(cid)
            if cur is None or (from_room and nav.room_at(*cur) != from_room and nav.room_at(*cur) is not None and mv.get("path")):
                cur = self.spot(from_room or room, cid, occupied, 1)
            track = [[0, cur[0], cur[1], cur[2]]]
            flags[cid] = {"dead": not alive, "out": bool(a.get("out")), "hiding": bool(a.get("hiding"))}
            spoke_elsewhere = speakers.get(cid) in nav.rooms and speakers.get(cid) != room and cid not in self.dead
            if not alive and not spoke_elsewhere:
                if cid not in self.dead:
                    dest = self.spot(room, cid, occupied, 2) if nav.room_at(*cur) != room else cur
                    if dest != cur:
                        track.append([1, dest[0], dest[1], dest[2]])
                    cur = dest
                    self.dead.add(cid)
                self.pos[cid] = cur
                tracks[cid] = track
                continue
            if not alive:
                self.dead.add(cid)
            hidden = nav.hidden_links_between(mv.get("path") or [])
            t = 0.0
            target_room_now = nav.room_at(*cur)
            talk_room = speakers.get(cid)
            segs = free.get(cid) if alive else None
            if segs:
                # a free-time block: walk the person from activity to activity at the minutes the engine recorded
                for si, sg in enumerate(segs):
                    rs = sg.get("room")
                    if rs not in nav.rooms:
                        continue
                    m0 = max(float(sg.get("m0", 0)), t, track[-1][0])
                    at = sg.get("at")
                    stand = nav.stand_near(at[0], at[1], at[2], occupied, rs) if at else None
                    changed_room = nav.room_at(*cur) != rs
                    if stand is not None and (changed_room or (cur != stand and sg.get("act") != "walk")):
                        dest = stand                                    # they use the thing the engine sent them to: they stand at the sofa, the stove, the chess table
                    elif changed_room:
                        dest = self.spot(rs, cid, occupied, 5 + si)
                    else:
                        dest = None
                    if dest is not None and dest != cur:
                        if m0 > track[-1][0]:
                            track.append([round(m0, 1), cur[0], cur[1], cur[2]])
                        dl = min(dur - 1.0, m0 + 14.0)
                        if cid in speakers and rs in gtime:
                            dl = min(dl, max(m0 + 2.0, gtime[rs][0] - 1.0))          # someone about to speak hurries to the room they will speak in
                        occupied.discard(cur)
                        t = self.walk(track, m0, cur, dest, hidden, dl)
                        if changed_room:
                            if cid not in start_at:
                                start_at[cid] = m0
                            arrive_at[cid] = t
                        cur = dest
                        occupied.add(cur)
                    else:
                        t = max(t, m0)
                    m1 = float(sg.get("m1", dur))
                    if not at and sg.get("act") in ("nap", "game", "read", "music", "art", "swim", "stroll", "look", "tinker", "explore") and m1 - t >= 30 and len(nav.spots(rs)) > 6:
                        nxt = self.spot(rs, cid, occupied, 20 + si)
                        if nxt != cur:
                            occupied.discard(cur)
                            tt = self.walk(track, t + (m1 - t) / 2, cur, nxt)
                            cur = nxt
                            occupied.add(cur)
                tr_room = speakers.get(cid)
                if tr_room in nav.rooms and tr_room != room and tr_room in gtime and cid not in self.dead:
                    # they spoke in one room and were then taken to another (a reaction, a punishment): they are in the talk room while it lasts
                    if nav.room_at(*cur) != tr_room:
                        d1 = self.spot(tr_room, cid, occupied, 4)
                        t0 = max(t, track[-1][0])
                        if t0 > track[-1][0]:
                            track.append([round(t0, 1), cur[0], cur[1], cur[2]])
                        t = self.walk(track, t0, cur, d1, hidden, min(dur - 1.0, max(t0 + 2.0, gtime[tr_room][0] - 1.0)))
                        cur = d1
                    late_go[cid] = (room, hidden)                      # they leave once they have said their piece
                elif nav.room_at(*cur) != room and nav.room_at(*cur) is not None:
                    # something moved them after the block (a reaction, a punishment): take them to where the engine put them
                    dest = self.spot(room, cid, occupied, 9)
                    t0 = max(t, track[-1][0])
                    if t0 > track[-1][0]:
                        track.append([round(t0, 1), cur[0], cur[1], cur[2]])
                    gs = gtime.get(room, (dur - 12,))[0] if room in gtime else dur - 8
                    dl = dur - 1.0 if (tr_room in nav.rooms and tr_room != room) else min(dur - 1.0, max(t0 + 2.0, gs - 1.0))
                    t = self.walk(track, t0, cur, dest, hidden, dl)
                    cur = dest
                occupied.add(cur)
                self.pos[cid] = cur
                tracks[cid] = track
                continue
            if talk_room in nav.rooms and talk_room != room and talk_room in gtime:
                # they spoke in one room and then left for another (a reaction, a punishment): they are in the talk room while they speak
                dest1 = self.spot(talk_room, cid, occupied, 4)
                t0 = 1 + _h(cid, tick["day"], H, "go") % 14
                start_at[cid] = t0
                if target_room_now != talk_room:
                    track.append([float(t0), cur[0], cur[1], cur[2]])
                    t = self.walk(track, t0, cur, dest1, hidden, ARRIVE_BY)
                    arrive_at[cid] = t
                    cur = dest1
                leave = gtime[talk_room][1] + 1
                if leave > track[-1][0]:
                    track.append([round(leave, 1), cur[0], cur[1], cur[2]])
                dest2 = self.spot(room, cid, occupied, 3)
                t = self.walk(track, max(leave, track[-1][0]), cur, dest2, hidden)
                cur = dest2
                occupied.add(cur)
                self.pos[cid] = cur
                tracks[cid] = track
                continue
            if room != target_room_now:
                dest = self.spot(room, cid, occupied, 3)
                t0 = 1 + _h(cid, tick["day"], H, "go") % 14
                start_at[cid] = t0
                track.append([float(t0), cur[0], cur[1], cur[2]])
                t = self.walk(track, t0, cur, dest, hidden, ARRIVE_BY)
                arrive_at[cid] = t
                cur = dest
            occupied.add(cur)
            # settle: a little wandering inside the room while nothing else is going on
            if not a.get("out") and dur >= 60 and len(nav.spots(room)) > 6 and cid not in speakers:
                k = _h(cid, tick["day"], H, "idle") % 3
                tt = max(t, 0) + IDLE_EVERY * (1 + _h(cid, H, "w") % 2)
                for i in range(k):
                    if tt > dur - 12:
                        break
                    nxt = self.spot(room, cid, occupied, 10 + i)
                    if nxt != cur:
                        occupied.discard(cur)
                        tt = self.walk(track, tt, cur, nxt)
                        cur = nxt
                        occupied.add(cur)
                    tt += IDLE_EVERY
            self.pos[cid] = cur
            tracks[cid] = track
        # conversations: speakers drift together around the middle of the room while they talk
        said = []
        groups_out = []
        for gi, g in enumerate(talk):
            room = g.get("room")
            if room not in nav.rooms:
                continue
            members = []
            for ln in g.get("lines", []):
                sp = ln.get("speaker")
                if sp in tracks and sp not in members and not flags.get(sp, {}).get("dead"):
                    members.append(sp)
            spots = nav.spots(room)
            chat = bool(free and g.get("m") is not None)
            m0 = (94 + 2 * gi) if free else 58 + 3 * gi
            if chat:
                # a chat that began during the block: they are already sitting or standing together at its minute; it starts once the last of them is in the room
                m0 = float(g["m"]) + 1.0
                for sp in members:
                    for pt in tracks.get(sp, []):
                        if pt[0] >= g["m"] - 0.5 and nav.room_at(pt[1], pt[2], pt[3]) == room:
                            m0 = max(m0, pt[0] + 0.5)
                            break
            else:
                # they start talking once the last of them has arrived (somebody slow or far away takes longer to get there)
                m0 = min(dur - 12.0, max([m0] + [tracks[sp][-1][0] + 1.0 for sp in members if tracks.get(sp) and nav.room_at(*self.pos[sp]) == room]))
            if not chat:
                anchor = None
                if free and members and tracks.get(members[0]):
                    anchor = tuple(self.pos[members[0]])
                for i, sp in enumerate(members):
                    self.cur_speed = self.speeds.get(sp, 1.0)
                    if not tracks.get(sp):
                        continue
                    cur = tuple(self.pos[sp])
                    if free and anchor is not None and nav.room_at(*anchor) == room:
                        # they talk where they met: everybody steps up to within a couple of tiles of whoever was already there, instead of walking to the middle of the room
                        near = abs(cur[1] - anchor[1]) + abs(cur[2] - anchor[2]) <= 3 and cur[0] == anchor[0]
                        dest = cur if (near or sp == members[0]) else nav.stand_near(anchor[0], anchor[1], anchor[2], {tuple(self.pos[x]) for x in members if x != sp}, room)
                        if dest is None:
                            continue
                    elif i < len(spots):
                        dest = spots[i]
                    else:
                        continue
                    if nav.room_at(*cur) == room and cur != dest:
                        tr = tracks[sp]
                        last_t = tr[-1][0]
                        tt = self.walk(tr, max(m0, last_t + 0.1), cur, dest)
                        self.pos[sp] = dest
            lines_ = g.get("lines", [])
            gap = min(2.4, 26.0 / max(1, len(lines_))) if chat else (2.4 if free else 3.5)
            for li, ln in enumerate(lines_):
                m = (m0 + 1 + li * gap) if chat else (m0 + 2 + li * gap if free else m0 + 6 + li * 3.5)
                if m > dur - 1:
                    break
                said.append({"m": round(m, 1), "who": ln.get("speaker"), "k": ln.get("kind", "say"), "text": (ln.get("text") or "")[:170], "room": room, "g": gi})
            groups_out.append({"g": gi, "m": round(m0, 1), "room": room, "chat": chat, "at": g.get("at"), "why": g.get("why", ""), "matters": g.get("matters") or [], "members": g.get("members") or members})
        for cid, (room, hid) in late_go.items():
            tr = tracks.get(cid)
            if not tr:
                continue
            last_m = max([x["m"] for x in said if x["who"] == cid] or [0])
            cur = tuple(self.pos[cid])
            dest = self.spot(room, cid, set(), 9)
            t0 = max(tr[-1][0], last_m + 0.8)
            if t0 > tr[-1][0]:
                tr.append([round(t0, 1), cur[0], cur[1], cur[2]])
            self.cur_speed = self.speeds.get(cid, 1.0)
            self.walk(tr, t0, cur, dest, hid, max(t0 + 2.0, dur - 1.0))
            self.pos[cid] = dest
        events = []
        chron = tick.get("chron") or []
        n_other = sum(1 for e in chron if e["type"] not in ("move", "arrive"))
        i_other = 0
        for e in chron:
            if e.get("m") is not None:
                m = e["m"]
            elif e["type"] == "move":
                m = start_at.get(e.get("who"), 2)
            elif e["type"] == "arrive":
                m = arrive_at.get(e.get("who"), 3)
            elif e["type"] == "talk":
                m = 96 if free else 60
            else:
                m = 4 + int(i_other * max(1, dur - 10) / max(1, n_other))
                i_other += 1
            events.append({"id": e["id"], "m": round(min(m, dur - 0.5), 1), "cls": e["cls"], "type": e["type"], "who": e.get("who"), "room": e.get("room"), "vis": e["vis"], "text": e["text"][:240]})
        events.sort(key=lambda e: (e["m"], e["id"]))
        self.clock = start + dur
        acts = {cid: [[round(sg["m0"]), round(sg["m1"]), sg.get("act"), sg.get("label"), sg.get("room")] for sg in segs] for cid, segs in free.items()} if free else {}
        return {"v": 1, "start": start, "dur": dur, "tracks": tracks, "flags": flags, "talk": said, "events": events, "acts": acts, "segment": tick.get("segment", "turn"), "groups": groups_out}


class LiveMixin:
    """Adds the live plan to every emitted tick. Failures never affect the game."""

    def live_plan(self, tick):
        pl = self.__dict__.get("_live_planner")
        if pl is None:
            pl = self._live_planner = LivePlanner(self.nav())
        speeds = {cid: round(self.move_factor(cid), 2) for cid in self.world.agents}
        tick["speeds"] = {c: v for c, v in speeds.items() if v < 0.95}
        return pl.plan(tick, self.env_avoid(), speeds)
