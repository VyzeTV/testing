"""Live conversations: talk as a thing in the world that runs while everybody else keeps moving.

A conversation has members, a place (an anchor tile: a seat, a spot by the stove, or the people themselves when they walk and talk), a reason, and a run of exchanges a few
minutes apart on the turn's minute clock. Between exchanges the world gets a say: a member who has drifted out of earshot leaves, an event in the room (a fight, a body, a
fire) cuts it short, and somebody nearby with a reason to (a friend in it, being talked about, curiosity, a grudge) walks over and joins. Every line is heard, half heard,
or only seen by whoever is around, as perception allows at that minute; people listening on purpose (spying, hiding) hear more, and members who notice a listener get wary:
they lower their voices and drop what they should not be saying. Friends who finish talking may walk on together.

The engine resolves every move as it happens (social.py); after the turn each conversation is voiced in one call (voice.py), or by the template voice.
"""
from .social import MOVES
from .voice import voice_prompt, check_lines, spoken_line
from .data_world import ROOMS
from .llm import LLMError
from concurrent.futures import ThreadPoolExecutor

INTERRUPTS = {"attack", "body", "punish", "island", "outburst", "fall", "assault", "madness", "faint", "fire"}
LOUD_OF = {"whisper": "whisper", "quiet": "quiet", "normal": "normal", "heated": "loud"}
LOUDER = {"whisper": "quiet", "quiet": "normal", "normal": "loud", "loud": "shout", "shout": "shout"}
WARY_DROP = {"reveal", "gossip", "incite", "recruit", "confide", "threaten", "flirt"}
MAX_BEATS = 14


class ConvoMixin:
    def convos(self):
        return self.__dict__.setdefault("_convos", [])

    def convo_reset(self):
        self._convos, self._convo_n = [], 0
        self._voice_futs, self._voice_taken = {}, set()

    def in_convo(self, cid):
        return next((c for c in self.convos() if c["state"] == "talking" and cid in c["members"]), None)

    # ------------------------------------------------------------------ starting
    def start_convo(self, tick, members, room, m0, tl, why="", matters=(), at=None, kind="chat", dur=30, nv=False):
        """Begin a conversation at minute m0 on timeline `tl`. Returns it, or None if fewer than two people can take part. `nv`: a word with NeoVi (one person is enough);
        NeoVi takes part in any conversation in the room she is working in (conv["nv"], neoviday.py)."""
        w = self.world
        members = [m for m in dict.fromkeys(members) if m in w.agents and not w.agents[m].get("out") and not w.agents[m].get("asleep") and not self.in_convo(m)]
        nv = nv and self.nv_here(room)
        if len(members) < (1 if nv else 2) or room not in ROOMS:
            return None
        self._convo_n = self.__dict__.get("_convo_n", 0) + 1
        sm = self.sim_turn(tick)
        conv = {"id": f"{room}#{self._convo_n}", "room": room, "members": members, "initiator": members[0], "why": why, "matters": sorted(set(matters or [])),
                "at": list(at) if at else None, "m0": float(m0), "end": min(sm.dur - 1.0, float(m0) + dur), "state": "talking", "beats": [], "joined": [], "left": [],
                "kind": kind, "hour": tick["hour"], "used": {}, "last_m": float(m0), "wary": False, "seen_by": set(), "exchanges": 0,
                "nv": bool(nv or self.nv_here(room)), "nv_seek": bool(nv), "nv_fed": self.s["npcs"]["neovi"].get("doing") in ("serving breakfast", "serving lunch", "serving dinner")}
        self.convos().append(conv)
        if kind == "gather":
            self.convo_gather(tick, conv, m0)
        else:
            # they may still be walking to the seat: the first exchange waits until both are there (else the earshot check parts them before a word is said)
            arrive = max([sm.end_t(c) for c in members if c in sm.tracks] + [float(m0)])
            if arrive > m0:
                conv["m0"] = min(arrive, float(m0) + 15.0, sm.dur - 3.0)
                conv["end"] = min(sm.dur - 1.0, conv["m0"] + dur)
                conv["last_m"] = conv["m0"]
        tl.at(conv["m0"] + 1.0, self.convo_step, tick, conv, tl)
        return conv

    def convo_gather(self, tick, conv, m0):
        """A gathering: whoever is not standing in the room yet walks there to join the others."""
        sm = self.sim_turn(tick)
        nav = sm.nav
        spots = nav.spots(conv["room"])
        late = m0
        for i, cid in enumerate(conv["members"]):
            if nav.room_at(*sm.pos_at(cid, m0)) == conv["room"]:
                continue
            dest = spots[i] if i < len(spots) and spots[i] not in sm.occupied(cid) else sm.spot(conv["room"], cid, sm.occupied(cid), 4)
            t = sm.walk(cid, dest, max(0.0, m0 - 10.0), deadline=m0 - 0.5, speed=self.move_factor(cid))
            late = max(late, t + 0.5)
        conv["m0"] = min(late, sm.dur - 3.0)

    def anchor_of(self, conv, m):
        sm = self.sim()
        if conv.get("at") and not conv.get("walking"):
            return tuple(conv["at"])
        p = sm.pos_at(conv["initiator"], m) if conv["initiator"] in sm.tracks else None
        return p or (tuple(conv["at"]) if conv.get("at") else None)

    # ------------------------------------------------------------------ each exchange
    def convo_step(self, tick, conv, tl):
        if conv["state"] != "talking":
            return
        w = self.world
        m = self._m
        sm = self.sim_turn(tick)
        nav = sm.nav
        perc = self.perc()
        anchor = self.anchor_of(conv, m)
        # who is still here (within earshot of the others, awake, on their feet)
        for cid in list(conv["members"]):
            a = w.agents.get(cid)
            here = sm.pos_at(cid, m) if cid in sm.tracks else None
            gone = (not a or a.get("out") or a.get("asleep") or here is None or anchor is None
                    or not (perc.hears(anchor, here, "normal") or perc.hears(here, anchor, "normal")))
            if gone:
                conv["members"].remove(cid)
                conv["left"].append([round(m, 1), cid])
        if conv.get("nv") and not self.nv_here(conv["room"]):
            conv["nv"] = False                                     # NeoVi has moved on to her next chore
        if len(conv["members"]) < (1 if conv.get("nv") and conv.get("nv_seek") else 2):
            return self.convo_end(tick, conv, "parted", m)
        # something happening in the room cuts it short
        rooms = {nav.room_at(*sm.pos_at(c, m)) for c in conv["members"]}
        for e in tick["events"]:
            em = e.get("m")
            if em is not None and conv["last_m"] < em <= m and e.get("type") in INTERRUPTS and e.get("room") in rooms:
                conv["cut_by"] = e.get("text", "")[:80]
                return self.convo_end(tick, conv, "interrupted", m)
        # the exchange itself
        beats = self.run_exchange(tick, conv) if not conv.get("wary") else self.wary_exchange(tick, conv)
        for i, b in enumerate(beats):
            b["ex"] = conv["exchanges"]
            b["m"] = round(min(sm.dur - 0.5, m + 0.7 * i), 2)
            p = sm.pos_at(b["who"], b["m"])
            b["room"] = nav.room_at(*p) if p else conv["room"]
            if conv.get("wary"):
                b["loud"] = "whisper"
        conv["beats"].extend(beats)
        conv["exchanges"] += 1
        if beats:
            for cid in conv["members"]:                     # nobody is walked off by a later catch-up before the exchange is over
                sm.hold[cid] = max(sm.hold.get(cid, 0.0), beats[-1]["m"] + 0.6)
        conv["last_m"] = m
        self.overhear(tick, conv, beats)
        # somebody nearby with a reason walks over; they speak from the next exchange, once the check above has them within earshot
        self.convo_joiners(tick, conv, m, anchor)
        # carry on, wind down, or walk on together
        nxt = m + 3.0 + self.rng.random() * 4.0
        greg = sum(self._fc(c, "gregariousness") for c in conv["members"]) / len(conv["members"])
        wind = conv["exchanges"] >= 3 and self.rng.random() < 0.12 + (60 - greg) / 300 + 0.05 * (conv["exchanges"] - 3)
        if nxt >= conv["end"] or len(conv["beats"]) >= MAX_BEATS or wind:
            if conv["kind"] == "chat" and not conv.get("walked") and self.walk_on_together(tick, conv, m + 1.5, tl):
                return
            return self.convo_end(tick, conv, "wound down", m + 1.5)
        tl.at(nxt, self.convo_step, tick, conv, tl)

    def wary_exchange(self, tick, conv):
        """Somebody is listening: they keep it to safe small talk, quietly."""
        saved = dict(conv["used"])
        for mv in WARY_DROP:
            conv["used"][mv] = conv["used"].get(mv, 0) + 50
        beats = self.run_exchange(tick, conv)
        for mv in WARY_DROP:
            conv["used"][mv] = saved.get(mv, 0)
        return beats

    def convo_joiners(self, tick, conv, m, anchor):
        w = self.world
        sm = self.sim()
        if anchor is None or len(conv["members"]) >= 5:
            return
        perc = self.perc()
        busy = getattr(self, "_free_busy", None)
        talked_about = {b.get("about") for b in conv["beats"]} | {b.get("to") for b in conv["beats"]}
        for cid in sorted(w.agents):
            a = w.agents[cid]
            if cid in conv["members"] or a.get("out") or a.get("asleep") or self.in_convo(cid) or cid not in sm.tracks:
                continue
            here = sm.pos_at(cid, m)
            if not here:
                continue
            want = a.get("want_talk") or {}
            wants = want.get("day") == self.day and any(x in conv["members"] for x in want.get("who", []))
            near = perc.hears(anchor, here, "normal") or sm.nav.room_at(*here) == sm.nav.room_at(*anchor)
            # from further off: they can see the group (and have a reason), or they have been wanting a word with one of them and are not far
            light = self.light_of(conv["room"]) if conv["room"] in ROOMS else "lit"
            far_ok = perc.sees(here, anchor, light) or (wants and here[0] == anchor[0] and abs(here[1] - anchor[1]) + abs(here[2] - anchor[2]) <= 40)
            if not (near or far_ok):
                continue
            if busy is not None and busy.get(cid, 0) > m:
                segs = (tick.get("free") or {}).get(cid) or []
                if segs and segs[-1].get("act") not in ("look", "explore", "stroll", "gather", "stay", "sit", "walk", "jukebox", "mirror", "read", "drink", "snack", "radio", "company"):
                    continue
            close = max((self._aff(cid, o) for o in conv["members"]), default=0)
            grudge = min((self._aff(cid, o) for o in conv["members"]), default=0)
            p = 0.0
            if close >= 5:
                p += 0.35
            elif close >= 3:
                p += 0.12
            if cid in talked_about:
                p += 0.45
            if self._fc(cid, "curiosity") >= 65:
                p += 0.1
            if grudge <= -4 and self._fc(cid, "anger") >= 60:
                p += 0.15
            if wants:
                p += 0.5
            if a.get("join_conv") == conv["id"]:
                p += 0.8                                           # they came over on purpose
            if not near:
                p *= 0.7                                           # walking over is a bigger step than turning round
            if p and self.rng.random() < p:
                if a["room"] != conv["room"]:
                    start = a["room"]
                    mv = w.move(cid, conv["room"], max(6, int(20 * self.move_factor(cid))))
                    if a["room"] != conv["room"]:
                        continue                                    # a locked door, or too far: they do not get there
                    pm = tick["moves"].setdefault(cid, {"from": start, "path": [start], "to": a["room"]})
                    pm["path"] = list(pm.get("path") or [start]) + mv["path"][1:]
                    pm["to"] = a["room"]
                conv["members"].append(cid)
                conv["joined"].append([round(m, 1), cid])
                sm.go_room(cid, conv["room"], m, at=anchor, salt=6, force=True, speed=self.move_factor(cid))
                if busy is not None:
                    busy[cid] = max(busy.get(cid, 0), conv["end"])
                    self._seg(tick, cid, int(m), int(conv["end"]), a["room"], "chat", f"joining {', '.join(self.nm(o) for o in conv['members'][:2] if o != cid)}", "free", anchor)
                if cid not in w.agents:
                    if cid in conv["members"]:
                        conv["members"].remove(cid)                     # a fall on the way over (walk hazards run as the walk is laid down)
                    conv["joined"] = [x for x in conv["joined"] if x[1] != cid]
                    continue
                self._fev(tick, cid, m, f"{self.nm(cid)} comes over and joins {', '.join(self.nm(o) for o in conv['members'] if o != cid)}.", "free", "viewer")
                if len(conv["members"]) >= 5:
                    return

    def convo_end(self, tick, conv, why, m):
        conv["state"] = "ended"
        conv["ended"] = [round(min(m, self.sim().dur - 0.5), 1), why]
        self.voice_submit(tick, conv)                                   # its lines are written now, while the block goes on (phase F3)
        busy = getattr(self, "_free_busy", None)
        if busy is not None:
            for cid in conv["members"]:
                if busy.get(cid, 0) > m:
                    busy[cid] = int(m)

    # ------------------------------------------------------------------ walking on together
    def walk_on_together(self, tick, conv, m, tl):
        """Two friends who have finished one thing go on to the next together, talking as they walk."""
        w = self.world
        if len(conv["members"]) != 2 or "free" not in tick or getattr(self, "_free_busy", None) is None:
            return False
        a, b = conv["members"]
        if min(self._aff(a, b), self._aff(b, a)) < 3 or self.rng.random() > 0.45:
            return False
        busy = self._free_busy
        start = w.agents[a]["room"]
        end = self.free_pick(tick, a, tick["hour"], int(m))
        if w.agents[a]["room"] == start:
            busy[a] = end
            return False
        busy[a] = end
        self.go_with(tick, b, a, m, end)
        conv["walking"], conv["walked"] = True, True
        conv["end"] = min(self.sim().dur - 1.0, m + 12.0)
        self._fev(tick, b, m, f"{self.nm(a)} and {self.nm(b)} walk on together, still talking.", "free", "viewer")
        tl.at(m + 1.5, self.convo_step, tick, conv, tl)
        return True

    def go_with(self, tick, follower, leader, m, until):
        """`follower` goes along with `leader`: same destination, side by side, the same activity nearby."""
        w = self.world
        sm = self.sim_turn(tick)
        la, fa = w.agents[leader], w.agents[follower]
        dest_room = la["room"]
        if fa["room"] != dest_room:
            mv = w.move(follower, dest_room, max(6, int(20 * self.move_factor(follower))))
            pm = tick["moves"].setdefault(follower, {"from": mv["path"][0], "path": [mv["path"][0]], "to": fa["room"]})
            pm["path"] = list(pm.get("path") or []) + mv["path"][1:]
            pm["to"] = fa["room"]
        lead_end = sm.cur.get(leader)
        if follower in sm.tracks and fa["room"] != dest_room:
            sm.go_room(follower, fa["room"], m + 0.15, salt=7, speed=self.move_factor(follower))     # they got only part of the way
            return
        if lead_end is not None and follower in sm.tracks:
            near = sm.nav.stand_near(lead_end[0], lead_end[1], lead_end[2], sm.occupied(follower), fa["room"]) or sm.spot(fa["room"], follower, sm.occupied(follower), 7)
            sm.walk(follower, near, m + 0.15, deadline=sm.end_t(leader) + 0.3, speed=self.move_factor(follower))
        segs = (tick.get("free") or {}).get(leader) or [{}]
        last = segs[-1]
        self._seg(tick, follower, int(m), int(until), fa["room"], "company", f"with {self.nm(leader)}", "free", last.get("at"))
        if getattr(self, "_free_busy", None) is not None:
            self._free_busy[follower] = until

    def companion_for(self, tick, cid, start_room, m, until):
        """When somebody sets off for something, a close friend who is idle in the same room may come along."""
        w = self.world
        busy = getattr(self, "_free_busy", None)
        if busy is None or cid not in w.agents or w.agents[cid]["room"] == start_room:
            return None
        sm = self.sim()
        pals = []
        for o in sorted(w.agents):
            oa = w.agents[o]
            if o == cid or oa.get("out") or oa.get("asleep") or busy.get(o, 0) > m or self.in_convo(o) or o in self.s.get("plots", {}):
                continue
            if oa["room"] != start_room or (o in sm.tracks and sm.nav.room_at(*sm.pos_at(o, m)) != start_room):
                continue
            if min(self._aff(cid, o), self._aff(o, cid)) >= 5 and self._fc(o, "gregariousness") >= 40:
                pals.append(o)
        if not pals or self.rng.random() > 0.35:
            return None
        pal = self.rng.choice(pals)
        self.go_with(tick, pal, cid, m, until)
        self._fev(tick, pal, m, f"{self.nm(pal)} goes along with {self.nm(cid)}.", "free", "viewer")
        return pal

    # ------------------------------------------------------------------ who hears what
    def overhear(self, tick, conv, beats, notice=True):
        """Every line is heard in full, half heard (at the edge of earshot: a fragment), or only seen being said, by whoever is around, as perception allows at that minute.
        People listening on purpose hear better; members who catch a listener get wary. Run live (so members can notice) and again when the turn is voiced, on where
        everybody finally turned out to be at each minute (a later walk can change where someone was)."""
        w = self.world
        sm = self.sim()
        perc = self.perc()
        for b in beats:
            src = sm.pos_at(b["who"], b["m"]) if b["who"] in sm.tracks else None
            if not src:
                continue
            loud = LOUD_OF.get(b.get("loud"), "normal")
            light = self.light_of(b["room"]) if b.get("room") in ROOMS else "lit"
            heard = {}
            for cid in sorted(w.agents):
                a = w.agents[cid]
                if cid in conv["members"] or a.get("out") or a.get("asleep") or cid not in sm.tracks:
                    continue
                t = sm.pos_at(cid, b["m"])
                if not t:
                    continue
                spying = a.get("spying") == conv["room"] or (a.get("hiding") and a["room"] == conv["room"])
                seen = perc.sees(src, t, light)
                if perc.hears(src, t, loud):
                    heard[cid] = "full"
                elif perc.hears(src, t, LOUDER[loud]):
                    heard[cid] = "full" if spying and self.rng.random() < 0.6 else "part"
                elif seen and cid not in conv["seen_by"]:
                    heard[cid] = "saw"
                    conv["seen_by"].add(cid)
                if heard.get(cid) in ("full", "part") and not seen:
                    b.setdefault("unseen", []).append(cid)          # heard through a wall or a floor: they have to know the voice
            b.pop("heard", None)
            b.pop("unseen", None) if not heard else None
            if heard:
                b["heard"] = heard
                for cid, lvl in heard.items():
                    if notice and lvl != "saw" and not conv.get("wary"):
                        self.maybe_notice_listener(tick, conv, cid, b["m"], spying=w.agents[cid].get("spying") == conv["room"] or bool(w.agents[cid].get("hiding")))

    def maybe_notice_listener(self, tick, conv, cid, m, spying=False):
        w = self.world
        for o in conv["members"]:
            if o not in w.agents:
                continue
            p = self.notice_p(o, cid) * (0.25 if spying else 0.6) * (0.6 + self._fc(o, "orderliness") / 125)
            if self.rng.random() < p:
                conv["wary"] = True
                conv["noticed"] = [round(m, 1), o, cid]
                if spying:
                    self._slice_m = m
                    try:
                        w.remember(o, f"{self.hh()} You caught {self.nm(cid)} listening in.")
                        self.adjust_any_aff(o, cid, -2)
                        self.log_event(tick, {"type": "hide", "who": cid, "room": conv["room"], "vis": "public",
                                              "text": f"{self.nm(o)} catches {self.nm(cid)} listening in on them."}, witnesses=[o], actor=cid)
                    finally:
                        self._slice_m = None
                return True
        return False

    def hh(self):
        return f"{int(self.s.get('_hour', 12)):02d}:{int(self.minute() or 0) % 60:02d}"

    # ------------------------------------------------------------------ voicing
    def voice_pool(self):
        pool = self.__dict__.get("_voice_pool")
        if pool is None:
            pool = self._voice_pool = ThreadPoolExecutor(max_workers=max(1, self.workers))
        return pool

    def voice_submit(self, tick, c):
        """Ask the model for a conversation's lines as soon as it ends, on a worker thread (one call, as before). Nothing about the world changes here: the answer is
        used later, in a fixed order, so a seeded run is the same whatever order the calls come back in."""
        futs = self.__dict__.setdefault("_voice_futs", {})
        if c["id"] in futs or not c["beats"]:
            return
        beats = c["beats"][:MAX_BEATS + 4]
        try:
            sysm, user = voice_prompt(self, c, beats)
        except Exception as e:
            tick["errors"].append(f"voicing {c['id']} failed: {str(e)[:80]}")
            futs[c["id"]] = None
            return
        ctx = {"beats": len(beats)}
        futs[c["id"]] = self.voice_pool().submit(self.llm.voice, sysm, user, ctx)

    def voice_convos(self, tick, hour):
        """The end of the turn: whatever is still being said ends, and the lines of every conversation not collected yet are taken in."""
        for c in self.convos():
            if c["beats"] and c["state"] == "talking":
                self.convo_end(tick, c, "turn over", self.sim().dur - 1.0)
        self.voice_collect(tick, hour)

    def voice_collect(self, tick, hour, upto=None):
        """Take in the lines of the conversations that have ended (by minute `upto`, or all), in the order they ended, then let the words do what words do: members and
        listeners remember them, the tape rolls. Waits for an answer still on its way, so the result does not depend on how fast the model is."""
        w = self.world
        taken = self.__dict__.setdefault("_voice_taken", set())
        order = {c["id"]: i for i, c in enumerate(self.convos())}
        done = sorted((c for c in self.convos() if c["beats"] and c["state"] != "talking" and c["id"] not in taken and c.get("ended")
                       and (upto is None or c["ended"][0] <= upto)), key=lambda c: (c["ended"][0], order[c["id"]]))
        if not done:
            return
        for c in done:
            taken.add(c["id"])
        got = {}
        futs = self.__dict__.setdefault("_voice_futs", {})
        for c in done:
            self.voice_submit(tick, c)
            fut = futs.get(c["id"])
            if fut is None:
                continue
            if self.should_stop():
                raise self.StopExc()
            try:
                got[c["id"]] = fut.result()
            except LLMError as e:
                if e.fatal:
                    raise
                got[c["id"]] = None
                tick["errors"].append(f"voicing {c['id']} fell back to the template voice: {str(e)[:80]}")
            except Exception as e:
                got[c["id"]] = None
                tick["errors"].append(f"voicing {c['id']} fell back to the template voice: {str(e)[:80]}")
        for c in done:
            beats = c["beats"][:MAX_BEATS + 4]
            lines, fixed = check_lines(self, beats, got.get(c["id"]), self.rng)
            for bi, (ln, b) in enumerate(zip(lines, beats)):
                ln["text"] = self.clean_line(ln["speaker"], ln["kind"], ln["text"]) or ln["text"]
                ln["m"], ln["room"], ln["move"], ln["b"], ln["ex"] = b["m"], b.get("room") or c["room"], b["move"], bi, b.get("ex", 0)
                if b.get("cont"):
                    ln["cont"] = True
                if b.get("about"):
                    ln["about"] = b["about"]
            people = list(dict.fromkeys([b["who"] for b in beats] + [x[1] for x in c["joined"]] + c["members"]))
            kept = {id(l) for l in self.filter_props(tick, c["room"], people, lines)}
            for i, ln in enumerate(lines):                          # a dropped line gets a plain one in its place, so no reply is left answering nothing
                if id(ln) not in kept:
                    sub = spoken_line(self, beats[ln["b"]], self.rng)
                    sub.update({k: ln[k] for k in ("m", "room", "move", "b", "ex", "cont") if k in ln})
                    lines[i] = sub
            if not lines:
                continue
            self.tape_record(c["room"], lines)
            self.note_scene(lines)
            for ln in lines:
                if ln["kind"] == "act":
                    self.note_acts(ln["speaker"], ln["text"])
            self.__dict__.setdefault("_heard_later", []).append((c, beats, lines, hour))
            entry = {"room": c["room"], "lines": lines, "live": True, "m": c["m0"], "members": people, "why": c.get("why", ""), "matters": c.get("matters", []),
                     "at": c.get("at"), "chat": c["kind"] == "chat", "conv": c["id"], "ended": c.get("ended"), "joined": c["joined"], "left": c["left"]}
            if c.get("noticed"):
                entry["noticed"] = c["noticed"]
            if fixed:
                entry["templated"] = fixed
            tick["talk"].append(entry)
            self.last_talk[c["room"]] = [(f"*{self.nm(l['speaker'])} {l['text']}*" if l["kind"] == "act" else f"{self.nm(l['speaker'])}: {l['text']}") for l in lines]
            self.day_notable.append(f"In the {w.room_name(c['room'])}: {self.nm(lines[0]['speaker'])} said \"{lines[0]['text'][:90]}\"")
            for p in people:
                if p in w.agents:
                    self.fix_memories(p, people, 0.4)

    def finish_hearing(self, tick):
        """Once the turn's walks are final: who heard each line (from where everybody actually was at its minute), and what they and the members remember of it.
        Booth confessions are checked the same way."""
        for c, beats, lines, hour in self.__dict__.get("_heard_later", []):
            c["seen_by"] = set()
            self.overhear(tick, c, beats, notice=False)
            for ln in lines:
                b = beats[ln["b"]] if 0 <= ln.get("b", -1) < len(beats) else {}
                ln.pop("heard", None)
                ln.pop("unseen", None)
                if b.get("heard"):
                    ln["heard"] = b["heard"]
                if b.get("unseen"):
                    ln["unseen"] = sorted(set(b["unseen"]))
            self.remember_talk(c, lines, hour)
            self.belief_from_talk(c, lines, beats)
        self._heard_later = []
        self.booth_hearing(tick)
        self.inner_hearing(tick)

    def remember_talk(self, conv, lines, hour):
        """Members remember what was said to them; listeners remember what they caught (a fragment at the edge of earshot); a passer-by remembers seeing them talk."""
        w = self.world
        hh = f"{int(hour):02d}:00"
        members = set(conv["members"]) | {x[1] for x in conv["joined"]} | {x[1] for x in conv["left"]}
        for ln in lines:
            who = self.nm(ln["speaker"])
            for cid in members:
                if cid not in w.agents:
                    continue
                if cid == ln["speaker"]:
                    w.remember(cid, f"{hh} You {'(action): ' + ln['text'][:110] if ln['kind'] == 'act' else 'said: ' + chr(34) + ln['text'][:110] + chr(34)}")
                else:
                    w.remember(cid, f"{hh} {who} {ln['text'][:110]}" if ln["kind"] == "act" else f"{hh} {who} said: \"{ln['text'][:110]}\"")
            for cid, lvl in (ln.get("heard") or {}).items():
                if cid not in w.agents:
                    continue
                topic = MOVES.get(ln.get("move"), (None, None, "something"))[2]
                if cid in (ln.get("unseen") or []):
                    # not seen, only heard: they recognise the voice if they know it well (or it is raised)
                    p = 0.45 + 0.05 * min(8, abs(self._aff(cid, ln["speaker"]))) + (0.1 if lvl == "full" else -0.15)
                    who = f"a voice, probably {self.nm(ln['speaker'])}," if self.rng.random() < p else "a voice they could not place"
                    if lvl == "full":
                        w.remember(cid, f"{hh} (heard through the wall, could not see who) {who} saying: \"{ln['text'][:100]}\"")
                    else:
                        gist = topic.replace("{x}", "someone")
                        w.remember(cid, f"{hh} (muffled, through the wall) {who}, too muffled to follow" + (f"; it sounded like {gist}" if gist not in ("something", "small talk") else ""))
                    continue
                if lvl == "full":
                    w.remember(cid, f"{hh} (overheard) {who}: \"{ln['text'][:100]}\"" if ln["kind"] == "say" else f"{hh} (overheard) {who} {ln['text'][:100]}")
                    self.tally(cid, "eavesdrops") if w.agents[cid].get("spying") or w.agents[cid].get("hiding") else None
                elif lvl == "part":
                    words = ln["text"].split()
                    frag = " ".join(words[len(words) // 3: len(words) // 3 + 4]) if len(words) >= 6 else ""
                    gist = topic.replace("{x}", "someone")
                    w.remember(cid, f"{hh} (overheard, could not make it all out) {who}" + (f" said something like \"...{frag}...\"" if frag else " was talking")
                               + (f"; it sounded like {gist}" if gist not in ("something", "small talk") else ""))
                elif lvl == "saw":
                    others = [self.nm(o) for o in conv["members"] if o != ln["speaker"]][:2]
                    w.remember(cid, f"{hh} (saw) {who} talking with {', '.join(others) or 'someone'} in the {w.room_name(conv['room'])}, too far to hear.")
