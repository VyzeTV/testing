"""Free time: the part of the day where people live their lives instead of taking a turn.

The day is a rhythm of TURNS (the morning announcement, the midday and evening gatherings: one decision each, as before) and FREE-TIME blocks (10, 14, 16 and 20). In a free-time block the
model is still asked for one decision (it becomes the first activity of the block), and after that the block is played out in 15-minute slices: everybody who is not busy picks what to do
next from their needs and nature (eat, drink, the bathroom, a wash, a game, a swim, music, a book, a stroll, a nap, tinkering with something, looking around), walks there, and spends real
time on it (a drink is a quarter of an hour, a meal half an hour, a game three-quarters, an experiment an hour and a half). The last half hour is the gathering: people drift together and
the conversation phase of the tick runs on whoever ended up together.

Because positions are real at every slice, the murder machinery works on time as well: a plotter who is stalking someone follows them room to room, and strikes the moment the two are
alone (or in a blind spot, or the lights are out); the longer the wait, the less patient they get, and the Director may arrange an opportunity (the target happens to need the bathroom, or a
quiet corner) without ever making the kill itself. A character with very little sanity left, or one who has been pushed past what they can bear by someone they hate, may snap and kill with
no plan at all. Nobody is shielded from being seen: perception decides who saw what.

Everything here writes into `tick["free"]` (per person: the segments with minute, room, activity), which the live planner turns into minute-by-minute tile tracks. FreeTimeMixin is mixed into
DayRunner (engine.py).
"""
from .data_world import ROOMS, RECIPES
from .world import clamp
from .gridnav import _h
from .clock import Timeline

SLICE = 15
TICK_MIN = 120
FINALE = 75
FREE_HOURS = (10, 14, 16, 20)


class _Rooms(set):
    """The rooms somebody has been in today, kept as a list inside the character so it is saved with them."""
    def __init__(self, lst):
        super().__init__(lst)
        self._l = lst

    def add(self, r):
        if r not in self._l:
            self._l.append(r)
        super().add(r)

# act: (label, minutes, rooms (where it can happen; also the fallback), furniture it is done at, short verb for the log)
ACTS = {
    "eat":      ("having a meal", 30, ["dining_hall", "kitchen", "pantry"], ["chair", "table"], "sits down to eat"),
    "drink":    ("getting a drink", 15, ["kitchen", "dining_hall", "bathroom", "pantry"], [], "gets something to drink"),
    "snack":    ("having a snack", 15, ["kitchen", "pantry"], ["fridge"], "raids the fridge"),
    "cook":     ("cooking", 45, ["kitchen"], ["stove"], "cooks something"),
    "wash":     ("washing up", 15, [], ["sink"], "washes their hands and face"),
    "bathroom": ("in the bathroom", 15, ["bathroom"], [], "uses the bathroom"),
    "shower":   ("showering", 30, ["bathroom"], [], "takes a shower"),
    "bath":     ("taking a bath", 45, [], ["tub"], "runs a bath"),
    "swim":     ("swimming", 45, ["pool"], [], "goes for a swim"),
    "game":     ("playing pool", 45, ["games_room"], ["poolTable"], "plays pool"),
    "chess":    ("playing chess", 45, [], ["chessTable"], "sets up the chess board"),
    "darts":    ("throwing darts", 30, [], ["dartboard"], "throws darts"),
    "music":    ("playing the piano", 45, ["music_room"], ["piano"], "sits at the piano"),
    "jukebox":  ("listening to music", 30, [], ["jukebox"], "puts a record on"),
    "art":      ("drawing", 45, ["art_studio"], ["easel"], "draws"),
    "read":     ("reading", 45, ["library", "study"], ["armchair", "desk"], "reads"),
    "sit":      ("relaxing", 30, [], ["sofa", "armchair", "bench", "deckChair", "hammock", "firepit", "fireplace"], "settles down"),
    "stroll":   ("walking about", 30, ["garden", "greenhouse", "beach", "lookout"], ["bench"], "takes a walk"),
    "tend":     ("tending the plants", 30, [], ["plantBed"], "tends the plants"),
    "laundry":  ("doing laundry", 30, [], ["washer"], "does some laundry"),
    "radio":    ("listening to the radio", 30, [], ["radio"], "fiddles with the radio"),
    "stargaze": ("at the telescope", 30, [], ["telescope"], "looks through the telescope"),
    "mirror":   ("at the mirror", 15, [], ["mirror"], "checks themselves in the mirror"),
    "nap":      ("napping", 60, [], ["bed"], "lies down"),
    "sleep":    ("asleep", 120, [], ["bed"], "goes back to bed"),
    "snoop":    ("snooping around", 30, [], [], "searches the room quietly"),
    "tinker":   ("making something", 45, [], ["workbench", "table"], "tinkers with something"),
    "look":     ("looking around", 30, [], [], "looks around"),
    "explore":  ("exploring", 30, [], [], "has a look around"),
    "dress":    ("getting dressed", 15, [], [], "gets dressed"),
    "gather":   ("with the others", 30, [], [], "joins the others"),
    "chat":     ("talking", 30, [], [], "starts talking"),
    "company":  ("keeping someone company", 30, [], [], "goes along"),
    "confess":  ("in the confessional booth", 15, [], ["booth"], "slips into the confessional booth"),
    "stalk":    ("keeping an eye on someone", 15, [], [], "keeps watch"),
    "flee":     ("getting away from danger", 15, [], [], "gets away from the danger"),
    "rescue":   ("dragging someone out of danger", 15, [], [], "goes in after someone"),
    "fight":    ("fighting the fire", 15, [], [], "tackles the fire"),
    "warn":     ("warning the others", 15, [], [], "shouts a warning"),
}
CAP = {"sofa": 2, "bench": 2, "table": 4, "poolTable": 2, "chessTable": 2, "firepit": 3, "fireplace": 3, "bed": 1}
SEATS = ["sofa", "armchair", "bench", "deckChair", "firepit", "fireplace", "table", "chair", "hammock"]       # where a conversation likes to happen
IDLE_ACTS = {"look", "explore", "stroll", "gather", "stay", "sit", "walk", "jukebox", "mirror"}               # an activity somebody can be talked out of
PRIVATE_ROOMS = {"blue_room", "green_room", "yellow_room", "red_room", "violet_room", "orange_room", "grey_room", "white_room", "master_suite"}
MAX_CHATS = 3
NIGHT_ACTS = {"eat", "drink", "snack", "wash", "bathroom", "read", "sit", "look", "explore", "stargaze", "radio", "tinker", "mirror", "confess", "chat", "gather", "company",
              "stalk", "flee", "rescue", "fight", "warn", "sleep", "snoop"}                                  # what people do in a sleeping house (nothing loud)
MAIN_DUR = {"experiment": 90, "craft": 45, "rest": 60, "search": 30, "spy": 45, "treat": 30, "frisk": 30, "stash": 30, "retrieve": 30, "build": 45, "hide": 45, "lock": 15,
            "unlock": 15, "barricade": 30, "give": 15, "take": 15, "use": 15, "drop": 15, "wear": 15, "stay": 15, "attack": 15, "knock": 15, "pick": 30, "break": 30}


def _tag(a, d):
    return str(d.get("activity") or "").strip()[:80] or a


class FreeTimeMixin:
    def free_on(self):
        return bool(self.tune("free_time")) and self.revealed

    def free_hour(self, hour):
        return self.free_on() and hour in FREE_HOURS

    # ------------------------------------------------------------------ bodies and modesty
    def body(self, cid):
        a = self.world.agents[cid]
        b = a.setdefault("body", {})
        b.setdefault("bladder", 15 + self.rng.randint(0, 25))
        b.setdefault("hygiene", 75 + self.rng.randint(0, 20))
        return b

    def modesty(self, cid):
        """0-100: how mortified this person is to be seen in their underwear. Comes from their nature, never from the cast sheet directly."""
        if not self.mind_on():
            return 50
        f = self.facet
        v = 50 + 0.5 * (50 - f(cid, "gregariousness")) + 0.35 * (f(cid, "orderliness") - 50) - 0.45 * (f(cid, "vanity") - 50) - 0.35 * (f(cid, "romantic") - 50) \
            - 0.25 * (f(cid, "humour") - 50) - 0.2 * (f(cid, "courage") - 50) + 0.2 * (f(cid, "stress_vulnerability") - 50)
        return int(clamp(v, 0, 100))

    def body_tick(self, cid, minutes):
        b = self.body(cid)
        b["bladder"] = min(100, b["bladder"] + minutes / 60 * 11)
        b["hygiene"] = max(0, b["hygiene"] - minutes / 60 * 3.5)

    # ------------------------------------------------------------------ recording
    def _seg(self, tick, cid, m0, m1, room, act, label, kind="free", at=None):
        segs = tick["free"].setdefault(cid, [])
        while len(segs) > 1 and segs[-1]["m0"] >= m0 and segs[-1].get("kind") != "main":
            segs.pop()                                              # something planned for later was overtaken by something happening now
        if segs and segs[-1]["m1"] > m0:
            segs[-1]["m1"] = m0
        sg = {"m0": m0, "m1": min(TICK_MIN, m1), "room": room, "act": act, "label": label[:90], "kind": kind}
        if at:
            sg["at"] = list(at)
        segs.append(sg)
        if kind != "main" and room in ROOMS and cid in self.world.agents:
            self.a_visited(cid).add(room)
            self.sim_seg(tick, cid, m0, room, at, act)

    def a_visited(self, cid):
        a = self.world.agents[cid]
        v = a.setdefault("visited", {})
        if v.get("day") != self.day:
            v.clear()
            v["day"] = self.day
            v["rooms"] = []
        return _Rooms(v["rooms"])

    def _fev(self, tick, cid, m, text, etype="free", vis="viewer", room=None, witnesses=None):
        a = self.world.agents[cid]
        self._slice_m = m
        try:
            self.log_event(tick, {"type": etype, "who": cid, "room": room or a["room"], "vis": vis, "text": text}, witnesses=witnesses, actor=cid)
        finally:
            self._slice_m = None

    # ------------------------------------------------------------------ the block
    def free_slice(self, tick, hour, m, busy):
        """Every quarter of an hour of free time: the environment catches up, bodies tick, and whoever is free decides what to do next (a decision point)."""
        w = self.world
        self.env_advance(tick, m - SLICE, m)
        order = list(w.agents)
        self.rng.shuffle(order)
        for cid in order:
            a = w.agents.get(cid)
            if not a:
                continue
            self.body_tick(cid, SLICE // 3 if a.get("asleep") else SLICE)        # a sleeping body slows down
            if a.get("out") or a.get("asleep") or self.restrained(cid):
                continue
            self.modesty_check(tick, cid, m)
            if self.snap_check(tick, cid, hour, m):
                busy[cid] = m + SLICE
                continue
            if self.plot_slice(tick, cid, hour, m, busy):
                continue
            if busy.get(cid, 0) > m:
                continue
            busy[cid] = self.free_pick(tick, cid, hour, m)

    def free_time(self, tick, hour, decisions):
        """Play the block out in slices. Called from run_tick after the main decisions have been applied and resolved."""
        w, s = self.world, self.s
        tick["segment"] = "free"
        tick["free"] = {}
        tick["free_chats"] = []
        busy = self._free_busy = {}
        self._chat_n = 0
        if self.env_on():
            self.env_hazards(tick, hour)
            tick["_hazards_done"] = True
        for cid, a in w.agents.items():
            d = decisions.get(cid) or {}
            act = d.get("action", "stay")
            dur = MAIN_DUR.get(act, 30)
            if a.get("out"):
                label, dur = "unconscious", TICK_MIN
            elif a.get("asleep"):
                label, dur = "asleep", TICK_MIN
            else:
                label = _tag(act, d) or act
                if d.get("talk_to"):
                    dur = max(dur, 30)
                    want = [x for x in d["talk_to"] if x in w.agents and x != cid][:2]
                    if want:
                        a["want_talk"] = {"who": want, "day": self.day, "why": str(d.get("intent") or "")[:80]}
                if act == "experiment":
                    a["worked"] = self.day
            busy[cid] = dur
            self._seg(tick, cid, 0, dur, a["room"], act, label, "main")
        meal_ = self.__dict__.get("_meal")                     # a meal or summons in this block keeps the people at it until it ends
        if meal_:
            for cid in meal_["came"]:
                if cid in busy and cid in w.agents:
                    busy[cid] = max(busy[cid], meal_["end_m"])
                    self._seg(tick, cid, int(meal_["m"]), int(meal_["end_m"]), meal_["room"], "eat" if meal_.get("kind") == "meal" else "gather", meal_["label"].lower(), "main")
        tl = self._tl = Timeline(self)
        tl.every(SLICE, lambda m: self.free_slice(tick, hour, int(m), busy), until=TICK_MIN - SLICE)
        tl.run()
        self._tl = None
        self._free_busy = None
        # close the books: everybody's last segment runs to the end of the block
        for cid, segs in tick["free"].items():
            if segs:
                segs[-1]["m1"] = TICK_MIN
        # who is gathered in the last half hour feeds the conversation phase
        chatters = {c for ch in tick["free_chats"] for c in ch["members"]}
        for cid, d in decisions.items():
            a = w.agents.get(cid)
            if not a or a.get("out") or cid in chatters:
                continue
            last = (tick["free"].get(cid) or [{}])[-1]
            if last.get("act") == "gather":
                here = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid and not w.agents[o].get("out") and o not in chatters]
                liked = [o for o in here if a["aff"].get(o, 0) >= 0] or here
                if liked:
                    d["talk_to"] = list(dict.fromkeys(list(d.get("talk_to") or []) + liked[:2]))[:3]

    def free_chat_groups(self, tick, groups, modes, intents):
        """The conversation phase of a free-time block: one conversation for every chat that started during the block (each at its own minute and place), and the gathering for whoever
        was not in a chat. Nobody talks twice in a block."""
        w = self.world
        chats = tick.get("free_chats") or []
        chatters = {c for ch in chats for c in ch["members"]}
        for room in list(groups):
            groups[room] = [o for o in groups[room] if o not in chatters]
            if len([o for o in groups[room] if o in w.agents]) < 2:
                del groups[room]
        self.__dict__.setdefault("_talk_meta", {}).clear()
        for ch in chats:                                    # the chats themselves already ran live during the block (convo.py)
            ini = ch["members"][0]
            if ini in w.agents:
                intents[ini] = (ch.get("why") or "talk") + ("; " + intents[ini] if intents.get(ini) else "")
        return groups, modes

    def free_lines(self, cid, hour):
        """What the character is told about the free-time block, plus gentle reminders of things they could do with their hands."""
        if not self.free_hour(hour) or cid not in self.world.agents:
            return []
        w = self.world
        a = w.agents[cid]
        out = ["FREE TIME: the next two hours are yours. What you choose now is how you start them; after that you will eat, drink, wash, play, read, make things or talk as your needs "
               "and nature pull you, and people who want a word with someone will seek them out. If you have something on your mind (a plan, an experiment, a secret, someone to find), start it now."]
        ideas = []
        rid = self.tinker_option(cid)
        if rid:
            ideas.append(f"you could make a {RECIPES[rid]['name']} right now (action 'craft', \"craft\": \"{rid}\")")
        comfort = [k for k in a["inv"] if (w.item_spec(k).get("use") or {}).get("sanity", 0) > 0 or (w.item_spec(k).get("use") or {}).get("hp", 0) > 0]
        if comfort and (a["sanity"] < 70 or a["hp"] < 70):
            ideas.append(f"the {w.item_name(comfort[0])} you carry would do you good (action 'use')")
        if ideas and not any(x in ("craft", "use", "build") for x in (a.get("recent_actions") or [])[-6:]):
            out.append("IDLE HANDS: " + "; ".join(ideas) + ".")
        return out

    # ------------------------------------------------------------------ places and furniture
    def _reach(self, cid):
        w = self.world
        return w.reachable_rooms(cid, max(8, int(22 * self.move_factor(cid))))

    def _unsafe(self, room):
        if not self.env_on():
            return False
        try:
            return room in self.env().rooms_on_fire()
        except Exception:
            return False

    def _nearest(self, cid, rooms, reach):
        a = self.world.agents[cid]
        best, bc = None, 10 ** 9
        for r in rooms:
            if r not in ROOMS or self._unsafe(r):
                continue
            if r == a["room"]:
                return r
            c = reach.get(r)
            if c is not None and c < bc:
                best, bc = r, c
        return best

    def _occupied_alone(self, tick, room, m):
        """True if somebody else is using this single-person room (the bathroom) right now."""
        for oc, segs in tick["free"].items():
            for sg in segs:
                if sg["room"] == room and sg["act"] in ("bathroom", "shower", "bath") and sg["m0"] <= m < sg["m1"] and oc in self.world.agents:
                    return True
        return False

    def _furn_use(self, tick, m):
        use = {}
        for oc, segs in tick["free"].items():
            if oc not in self.world.agents:
                continue
            for sg in segs:
                if sg.get("at") and sg["m0"] <= m < sg["m1"]:
                    k = tuple(sg["at"])
                    use[k] = use.get(k, 0) + 1
        return use

    def _wrecked(self, f):
        if not self.env_on():
            return False
        try:
            st = self.env().st["struct"].get(f"{f['plane']},{f['x']},{f['y']}")
            return bool(st and st.get("state") in ("burned", "destroyed", "broken"))
        except Exception:
            return False

    def _find_furn(self, tick, cid, kinds, reach, m, rooms=None, home_only=False):
        """The nearest piece of furniture of one of these kinds that nobody is using up, in a room the person may use. Returns (room, (plane, x, y)) or None."""
        w = self.world
        a = w.agents[cid]
        home = w.cast[cid]["home"]
        use = self._furn_use(tick, m)
        order = [a["room"]] + sorted(reach, key=lambda r: reach[r])
        for r in order:
            if rooms and r not in rooms:
                continue
            if home_only and r != home:
                continue
            if r in PRIVATE_ROOMS and r != home:
                continue
            if self._unsafe(r) or r not in ROOMS:
                continue
            cands = [f for f in self.nav().furniture_in(r) if f["k"] in kinds and not self._wrecked(f) and use.get((f["plane"], f["x"], f["y"]), 0) < CAP.get(f["k"], 1)]
            if cands:
                f = self.rng.choice(cands)
                return r, (f["plane"], f["x"], f["y"])
        return None

    def _crowd(self, room, cid):
        w = self.world
        return len([o for o in w.occupants(room) if o in w.agents and o != cid])

    # ------------------------------------------------------------------ choosing what to do
    def free_pick(self, tick, cid, hour, m):
        """Choose and start the next activity for someone who is free. Returns the minute at which they are free again."""
        w, s = self.world, self.s
        a = w.agents[cid]
        b = self.body(cid)
        reach = self._reach(cid)
        here = a["room"]
        mi = self.mind(cid)["needs"] if self.mind_on() else {"social": 50, "rest": 50, "safety": 50, "purpose": 50, "privacy": 50}
        f = (lambda k: self.facet(cid, k)) if self.mind_on() else (lambda k: 50)
        imp = f("impulsiveness") / 100.0
        gr = f("gregariousness")
        home = w.cast[cid]["home"]
        recent = a.setdefault("free_recent", [])
        sc = []                                          # (score, act, room, at, why, partner)

        def add(score, act, rooms=None, kinds=None, why="", partner=None, room=None, home_only=False, far=False):
            if score <= 0:
                return
            at = None
            reach_ = w.reachable_rooms(cid, 30) if far else reach        # a real need sends people further than a whim does
            kinds = kinds if kinds is not None else ACTS[act][3]
            rooms = rooms if rooms is not None else ACTS[act][2]
            r = None
            late = m >= 90                                           # too late to set out: the conversation starts at about 95
            if room is not None:
                r = room
            elif kinds:
                got = self._find_furn(tick, cid, kinds, reach_, m, [here] if late else (rooms or None), home_only)
                if got:
                    r, at = got
                elif rooms and not (late and here not in rooms):
                    r = self._nearest(cid, [here] if late else rooms, reach_)
            elif rooms:
                r = self._nearest(cid, [here] if late else rooms, reach_) if not (late and here not in rooms) else None
            else:
                r = here
            if not r:
                return
            if r != here and act not in ("rescue", "fight", "warn", "flee") and (self._unsafe(r) or r in self.smoky_rooms()):
                return                                                   # nobody walks back into a fire for a game of chess or a plan
            score += 0.35 * imp * self.rng.random()
            score += 0.45 * (_h(cid, act) % 100 / 100.0 - 0.5)           # each person has their own tastes, so the house does not all play the same game
            score -= 0.55 * recent[-3:].count(act)                       # people do not do the same thing three times running
            if self.brain_on():
                av = self.plan_avoid(cid)
                if av and any(o in av for o in w.occupants(r)):
                    score -= 1.2                                       # they meant to keep away from somebody who is there
            crowd = self._crowd(r, cid)
            if crowd >= 3 and gr < 60 and r != here:
                score -= 0.3 * (crowd - 2)                               # the shy keep out of crowded rooms
            sc.append((score, act, r, at, why, partner))

        # danger first: flames, smoke or flood in the room you are in (a smell of smoke from next door is not a reason to run)
        if self.env_on() and any(l.startswith(("FIRE", "SMOKE", "WATER")) for l in self.env_lines(cid)):
            fled = a.get("fled") or {}
            if not (fled.get("day") == self.day and m - fled.get("m", -99) < 20) and self.rng.random() < (0.45 if self.has_cond(cid, "panicking") else 0.7):
                safe = self._nearest(cid, [x for x in reach if not self._unsafe(x) and x not in self.smoky_rooms()] or [home], reach)
                if safe and safe != here:
                    return self._start(tick, cid, "flee", safe, None, m)
        # a fire is burning somewhere else: the brave put it out, the kind pull people out, the alert wake the sleepers
        for act_, room_, why_, sc_ in self.fire_duties(tick, cid, reach, m):
            add(sc_, act_, room=room_, why=why_)
        # half-dressed
        if self.worn(cid) is None and not self.rule_is_underwear() and (a["inv"].get(f"clothes_{cid}", 0) > 0 or here == home):
            add(2.5, "dress", room=home if here != home else here)
        # the body
        hungry = max(a.get("hunger", 0) - 28, 0) / 35 + (0.3 if a.get("hunger", 0) >= 60 else 0)
        thirsty = max(a.get("thirst", 0) - 30, 0) / 35
        kind_cook = 0.35 * (f("altruism") - 40) / 60 + 0.25 * (f("orderliness") - 40) / 60
        add(hungry * 1.4, "eat", why="hungry", far=hungry > 1.0)
        add(hungry * 0.9 + kind_cook + (0.25 if hungry > 0.2 else 0), "cook", why="cooking for themselves and whoever is around")
        add(hungry * 0.7, "snack", why="hungry", far=hungry > 1.0)
        add(thirsty * 1.2, "drink", why="thirsty", far=thirsty > 1.0)
        add(max(b["bladder"] - 45, 0) / 25, "bathroom", why="needs the bathroom")
        add(max(72 - b["hygiene"], 0) / 22 + (0.6 if a.get("conds") and "burned" in a["conds"] else 0), "shower", why="needs a wash")
        add(max(72 - b["hygiene"], 0) / 40 + 0.3 * (f("vanity") - 50) / 50, "bath", why="a long soak")
        add(max(72 - b["hygiene"], 0) / 50, "wash", why="freshening up")
        add(max(70 - mi["rest"], 0) / 40 + (0.35 if hour >= 20 else 0), "nap", home_only=True, why="tired")
        # what suits them
        fun = (100 - mi["purpose"]) / 70 + (100 - mi["social"]) / 90
        cur, rom, cour, hum, ord_ = f("curiosity"), f("romantic"), f("courage"), f("humour"), f("orderliness")
        add(0.45 + fun * 0.5 + 0.3 * (gr > 55), "game", why="a game")
        add(0.5 + fun * 0.4 + (cur - 45) / 120, "chess", why="a game of chess")
        add(0.45 + fun * 0.35 + (hum - 45) / 140 + (cour - 45) / 200, "darts", why="darts")
        add(0.5 + (f("vanity") - 40) / 140 + (rom - 45) / 200, "music", why="music")
        add(0.28 + (rom - 45) / 160, "jukebox", why="some music")
        add(0.45 + (cur - 40) / 130 + (ord_ - 45) / 200, "art", why="drawing")
        add(0.34 + (cur - 40) / 90 + (100 - mi["purpose"]) / 90, "read", why="a book")
        add(0.22 + (100 - mi["privacy"]) / 70 + (100 - mi["rest"]) / 200, "sit", why="a sit-down")
        add(0.28 + (100 - mi["privacy"]) / 80, "stroll", why="fresh air")
        add(0.42 + (ord_ - 45) / 100 + (f("altruism") - 45) / 200, "tend", why="the plants")
        add(0.25 + (ord_ - 40) / 90, "laundry", why="laundry")
        add(0.42 + (cur - 40) / 110 + (100 - mi["purpose"]) / 120, "radio", why="the radio")
        add(0.28 + (cur - 45) / 110 + (rom - 45) / 200, "stargaze", why="the stars")
        add(0.2 + (f("vanity") - 40) / 110, "mirror", why="a look in the mirror")
        if 11 <= hour <= 17 and self.worn(cid) is not None:
            add(0.35 + (cour - 40) / 150, "swim", why="a swim")
        # work: whatever they were at in their last decision goes on, and things they could make
        tk = self.tinker_option(cid)
        if tk:
            add(0.75 + (100 - mi["purpose"]) / 70 + cur / 150, "tinker", why="making something")
        if a.get("worked") == self.day and self.revealed and mi["purpose"] < 75:
            add(0.9 + (100 - mi["purpose"]) / 80, "tinker", rooms=["generator_shed", "boathouse", "boiler_room", "study"], kinds=["workbench", "table", "desk", "radio"], why="back to work on a way out")
        # exploring: somewhere they have not been today
        seen = set(self.a_visited(cid))
        fresh = [r for r in reach if r not in seen and r not in PRIVATE_ROOMS and not self._unsafe(r) and r in ROOMS]
        if fresh and self.rng.random() < 0.8:
            r_ = self.rng.choice(fresh)
            add(0.35 + (cur - 40) / 100 + (100 - mi["purpose"]) / 90, "explore", room=r_, why=f"has not been in the {w.room_name(r_)} today")
        add(0.15 + (100 - mi["purpose"]) / 150, "look", why="")
        urge = self.booth_urge(cid)[0]
        if urge >= 2.0 and m < 90:
            add(0.25 + urge * 0.3, "confess", why="something to get off their chest")
        # the loose ends: something is off, someone went through their things
        for h in s.get("hooks", []):
            if cid in (h.get("victims") or []) and not h.get("closed") and h.get("room") in ROOMS and (h["room"] in reach or h["room"] == here) and self.rng.random() < 0.5:
                add(0.9 + 0.2 * (f("curiosity") - 40) / 60, "explore", room=h["room"], why="looking into who has been through their things")
                break
        # plotter still looking for a weapon
        pl = s.get("plots", {}).get(cid)
        if pl and pl.get("stage") == "preparing" and not pl.get("weapon"):
            wr = self.weapon_room(cid)
            if wr and (wr in reach or wr == here):
                add(1.1, "explore", room=wr, why="looking for something useful")
        # what they planned
        if self.brain_on():
            self.plan_options(tick, cid, hour, m, reach, add)
        # company: a conversation going on nearby with people they like
        for cv in self.convos():
            if cv["state"] != "talking" or cid in cv["members"] or len(cv["members"]) >= 5 or (cv["room"] not in reach and cv["room"] != here):
                continue
            fond = max((a["aff"].get(o, 0) for o in cv["members"]), default=0)
            if fond >= 2 and m < cv["end"] - 6:
                add(0.6 + fond / 6 + (100 - mi["social"]) / 70 + (gr - 50) / 120, "gather", room=cv["room"], why=f"joining {', '.join(self.nm(o) for o in cv['members'][:2])}")
                a["join_conv"] = cv["id"]
        self.chat_options(tick, cid, hour, m, reach, add)
        if m >= FINALE or (100 - mi["social"]) > 55:
            company = {}
            for rid in list(reach) + [here]:
                ppl = [o for o in w.occupants(rid) if o in w.agents and o != cid and not w.agents[o].get("out")]
                company[rid] = sum(1 + max(0, a["aff"].get(o, 0)) for o in ppl if a["aff"].get(o, 0) > -4)
            best = max(company, key=lambda r: company[r], default=None)
            if best and company[best] > 0 and not self._unsafe(best):
                add((1.4 if m >= FINALE else 0.2) + (100 - mi["social"]) / 60, "gather", room=best, why="company")
        # the Director's opportunities and the plotter's own errand
        self.director_arrange(tick, cid, m, sc, reach)
        if pl and pl.get("stage") in ("stalking", "striking") and pl["target"] in w.agents:
            t = pl["target"]
            tr = w.agents[t]["room"]
            if tr in reach or tr == here:
                sc.append((3.0 if pl["stage"] == "striking" else 2.0, "stalk", tr, None, "", None))
        night = tick.get("phase") == "night"
        if night:
            # the house is asleep: back to bed sooner or later, nothing loud in the meantime
            late = max(0, (int(hour) - 23)) / 2
            urgent = max(max(b["bladder"] - 45, 0) / 25, hungry * 1.4, thirsty * 1.2)          # nobody sleeps on a full bladder or an empty stomach
            self.night_options(tick, cid, hour, m, add, sc)            # secret meetings and snooping
            add(0.9 + (100 - mi["rest"]) / 45 + 0.3 * late + 0.02 * m - (0.6 if a["sanity"] < 25 else 0) - 1.5 * urgent, "sleep", room=home, why="back to bed")
            sc = [x for x in sc if x[1] in NIGHT_ACTS]
        if m >= FINALE and not night:
            # the last half hour leans towards company, but somebody with something in hand (work, a lead, a need) carries on with it
            sc = [(x[0] + (0.45 if x[1] == "gather" else 0.0),) + x[1:] for x in sc]
        if m >= 90:
            sc = [x for x in sc if x[2] == here or x[1] == "flee"] or [(0, "gather" if self._crowd(here, cid) else "look", here, None, "company" if self._crowd(here, cid) else "", None)]    # too late to set out: the conversation starts at about 95
        if not sc:
            return self._start(tick, cid, "look", here, None, m)
        best = max(sc, key=lambda x: x[0])
        _, act, room, at, why, partner = best
        recent.append(act)
        del recent[:-6]
        return self._start(tick, cid, act, room, at, m, why, partner)

    def fire_duties(self, tick, cid, reach, m):
        """What somebody who is out of the flames might do about them: (act, room, reason, score) options."""
        w = self.world
        a = w.agents[cid]
        if not self.env_on():
            return []
        fr = self.fire_rooms()
        smoky = self.smoky_rooms()
        if not fr and not smoky:
            return []
        out = []
        f = (lambda k: self.facet(cid, k)) if self.mind_on() else (lambda k: 50)
        cour, alt = f("courage"), f("altruism")
        here = a["room"]
        if here in fr or here in smoky or a["sanity"] < 20 or self.has_cond(cid, "panicking"):
            return []
        # pull somebody who has collapsed out of a burning or smoky room
        for o, oa in w.agents.items():
            if o == cid or not oa.get("out") or (oa["room"] not in fr and oa["room"] not in smoky):
                continue
            if oa["room"] not in reach and oa["room"] != here:
                continue
            aff = a["aff"].get(o, 0)
            tried = a.setdefault("rescue_tried", {})
            if tried.get(o) == self.day or not any(r not in fr and r not in smoky and not self._unsafe(r) for r in reach):
                continue                                          # they already tried (once is brave enough), or there is nowhere safe to take anybody
            if cour >= 40 and (aff >= 1 or alt >= 55) and not any(oc != cid and (self._free_busy or {}).get(oc, 0) > m and oc in w.agents and (tick["free"].get(oc) or [{}])[-1].get("act") == "rescue" and w.agents[oc]["room"] == oa["room"] for oc in w.agents):
                out.append(("rescue", oa["room"], f"goes in after {self.nm(o)}", 2.2 + alt / 100 + max(0, aff) / 20))
        # tackle a small fire with an extinguisher or a bottle of water
        have = a["inv"].get("fire_extinguisher", 0) > 0 or a["inv"].get("water_bottle", 0) > 0
        for r, n in fr.items():
            if have and cour >= 45 and n <= 10 and (r in reach or r == here):
                out.append(("fight", r, "tries to put the fire out", 1.5 + cour / 200))
        # wake the sleepers
        for o, oa in w.agents.items():
            if o != cid and oa.get("asleep") and oa["room"] not in (here,) and (oa["room"] in reach) and (fr or smoky):
                out.append(("warn", oa["room"], f"goes to wake {self.nm(o)}", 1.1 + alt / 150))
                break
        return out

    def chat_options(self, tick, cid, hour, m, reach, add):
        """Who this person would go and talk to right now, and why: somebody they were after, company, closeness, a quarrel. Adds a 'chat' choice for the best partner."""
        w, s = self.world, self.s
        a = w.agents[cid]
        if self._chat_n >= (MAX_CHATS + 1 if self.brain_on() else MAX_CHATS) or m >= 90:
            return
        mind = self.mind(cid)["needs"] if self.mind_on() else {"social": 50}
        gr = self.facet(cid, "gregariousness") if self.mind_on() else 50
        stress = self.mind(cid)["stress"] if self.mind_on() else 0
        anger = self.facet(cid, "anger") if self.mind_on() else 50
        rom = self.facet(cid, "romantic") if self.mind_on() else 50
        want = (a.get("want_talk") or {}) if (a.get("want_talk") or {}).get("day") == self.day else {}
        chatted = a.setdefault("chatted", {})
        if chatted.get("day") != self.day:
            chatted.clear()
            chatted["day"] = self.day
        busy = self._free_busy or {}
        best = None
        plan_avoid = self.plan_avoid(cid) if self.brain_on() else set()
        far = w.reachable_rooms(cid, max(14, int(48 * self.move_factor(cid)))) if self.brain_on() and self.plan_talk_targets(cid) else reach
        planned = {it["who"] for it in self.plan_talk_targets(cid)} if self.brain_on() else set()
        for o, oa in w.agents.items():
            if o == cid or oa.get("out") or oa.get("asleep"):
                continue
            if oa["room"] not in (far if o in planned else reach) and oa["room"] != a["room"]:
                continue
            if oa["room"] == "bathroom" or (oa["room"] in PRIVATE_ROOMS and oa["room"] not in (w.cast[cid]["home"], w.cast[o]["home"])):
                continue                                         # nobody follows somebody into the bathroom or into a bedroom that is not theirs for a chat
            if not self._available(tick, o, m, busy):
                continue
            aff = a["aff"].get(o, 0)
            score, why = 0.0, ""
            tags = self.chat_tags(cid, o)
            if self.brain_on() and any(it["who"] == o for it in self.plan_talk_targets(cid)):
                it = next(it for it in self.plan_talk_targets(cid) if it["who"] == o)
                score += 1.6
                why = f"means to talk to {self.nm(o)}" + (f": {it['why']}" if it.get("why") else "")
            if o in plan_avoid:
                continue
            if o in want.get("who", []):
                score += 1.0
                why = f"wants a word with {self.nm(o)}" + (f" ({want['why']})" if want.get("why") else "")
            if "secret" in tags and cid in [k.get("of") for k in w.agents[o].get("known_secrets", [])] and aff < 6:
                score += 0.55
                why = why or f"knows what {self.nm(o)} knows, and wants to talk about it"
            elif "secret" in tags:
                score += 0.7
                why = why or f"knows something about {self.nm(o)}"
            if "hook" in tags:
                score += 0.95
                why = why or f"wants to get to the bottom of what happened with {self.nm(o)}"
            if "romance" in tags:
                score += 0.5
                why = why or f"wants some time with {self.nm(o)}"
            if "purpose" in tags:
                score += 0.4
            if aff >= 3:
                score += 0.25 + aff / 25 + (100 - mind["social"]) / 130 * (0.5 + gr / 100)
                why = why or ("wants company: " + self.nm(o) if aff < 6 else f"wants to be with {self.nm(o)}")
            elif aff >= 0:
                score += (100 - mind["social"]) / 160 * (0.4 + gr / 100)
                why = why or "wants company"
            if aff <= -4:
                if stress >= 35:
                    score += 0.5 + anger / 160
                    why = why or f"has something to say to {self.nm(o)}"
                else:
                    score -= 1.0
            if rom >= 60 and aff >= 5:
                score += 0.35
            score -= 0.7 * chatted.get(o, 0)
            if best is None or score > best[0]:
                best = (score, o, why)
        if best and best[0] >= 0.7:
            score, o, why = best
            add(score + 0.2, "chat", room=w.agents[o]["room"], why=why, partner=o)

    INTENT_WORDS = ("secret", "hiding", "hide", "plan", "kill", "lie", "lying", "suspect", "suspic", "betray", "blackmail", "confront", "warn", "alliance", "ally", "trust", "evidence", "clue", "escape", "radio", "raft")

    def chat_tags(self, cid, o):
        """Why a conversation between these two matters to the story: a plot, bad blood, something one of them knows about the other, a loose end, a spark, a purpose."""
        w, s = self.world, self.s
        a, oa = w.agents[cid], w.agents[o]
        tags = []
        plots = s.get("plots", {})
        if plots.get(cid, {}).get("target") == o or plots.get(o, {}).get("target") == cid or (plots.get(cid) and plots.get(o)):
            tags.append("plot")
        if a["aff"].get(o, 0) <= -4 or oa["aff"].get(cid, 0) <= -4:
            tags.append("feud")
        if any(k.get("of") == o for k in a.get("known_secrets", [])) or any(k.get("of") == cid for k in oa.get("known_secrets", [])):
            tags.append("secret")
        for h in s.get("hooks", []):
            if not h.get("closed") and ((cid in (h.get("victims") or []) and h.get("culprit") == o) or (o in (h.get("victims") or []) and h.get("culprit") == cid)):
                tags.append("hook")
                break
        rom = self.facet(cid, "romantic") if self.mind_on() else 50
        if a["aff"].get(o, 0) >= 6 and oa["aff"].get(cid, 0) >= 6 and rom >= 55:
            tags.append("romance")
        want = a.get("want_talk") or {}
        if want.get("day") == self.day and o in want.get("who", []) and any(k in (want.get("why") or "").lower() for k in self.INTENT_WORDS):
            tags.append("purpose")
        return sorted(set(tags))

    def _available(self, tick, o, m, busy):
        """Somebody who is not already in a chat and is only idling (or free this very slice) can be approached."""
        if any(o in ch["members"] for ch in tick.get("free_chats", [])):
            return False
        if busy.get(o, 0) <= m:
            return True
        segs = tick["free"].get(o) or []
        cur = next((sg for sg in reversed(segs) if sg["m0"] <= m < sg["m1"]), None)
        return bool(cur and cur["act"] in IDLE_ACTS and cur["kind"] != "main")

    def rule_is_underwear(self):
        rule = self.s.get("rule")
        return bool(rule and (rule.get("chk") or {}).get("state_check") == "underwear")

    def tinker_option(self, cid):
        """A recipe the character could make right now from what they carry and what lies about, preferring useful ones."""
        a = self.world.agents[cid]
        if self.world.carried(cid) >= 28:
            return None
        ok = []
        for rid, r in RECIPES.items():
            try:
                plan, _ = self.recipe_plan(cid, rid)
            except Exception:
                continue
            if plan is not None:
                tags = set(self.world.item_spec(r["out"]).get("tags", []))
                if ("weapon" in tags or "poison" in tags) and cid not in self.s.get("plots", {}):
                    continue
                ok.append(rid)
        return self.rng.choice(ok) if ok else None

    def director_arrange(self, tick, cid, m, sc, reach):
        """Opportunity, never a kill: when a plotter has been waiting a long time, their target is more likely to want somewhere quiet. The strike itself is still the plotter's to make."""
        s, w = self.s, self.world
        k = self.tune("director_nudge")
        if not k:
            return
        for pc, p in s.get("plots", {}).items():
            if p.get("target") != cid or p.get("stage") != "striking" or pc not in w.agents:
                continue
            wait = p.get("wait", 0)
            if wait < 4 or self.rng.random() > min(0.5, 0.08 * wait * k):
                continue
            quiet = self._nearest(cid, ["bathroom"], reach) if self.body(cid)["bladder"] > 25 else None
            if quiet and not self._occupied_alone(tick, quiet, m):
                sc.append((2.6, "bathroom", quiet, None, "needs the bathroom", None))
            else:
                home = w.cast[cid]["home"]
                if home in reach or home == w.agents[cid]["room"]:
                    sc.append((2.2, "nap" if w.agents[cid]["sanity"] < 90 else "read", home, None, "", None))
            self.note_nudge(tick, pc, cid, m)
            return

    def note_nudge(self, tick, plotter, target, m):
        n = self.s.setdefault("nudges", [])
        if len(n) < 200:
            n.append({"day": self.day, "m": m, "plotter": plotter, "target": target})
        self._fev(tick, plotter, m, f"Director: {self.nm(target)} is steered towards a quiet corner (the plan against them has stalled).", "system", "gm")

    # ------------------------------------------------------------------ doing it
    def _walk(self, tick, cid, room, m):
        """Walk towards `room` for up to a slice or two. Returns True if they are there."""
        w = self.world
        a = w.agents[cid]
        start = a["room"]
        if start == room:
            return True
        mv = w.move(cid, room, max(6, int(20 * self.move_factor(cid))))
        before = [o for o in w.occupants(start) if o != cid]
        pm = tick["moves"].setdefault(cid, {"from": start, "path": [start], "to": start})
        pm["path"] = list(pm.get("path") or [start]) + [r for r in mv["path"][1:]]
        pm["to"] = a["room"]
        self._slice_m = m
        try:
            for ev in mv["events"]:
                self.log_event(tick, ev, witnesses=before, actor=cid)
            if a["room"] != start:
                name = self.nm(cid)
                self.log_event(tick, {"type": "move", "who": cid, "room": start, "vis": "public",
                                      "text": f"{name} {'slips out of' if a.get('sneaking') else 'leaves'} {w.room_name(start)} for {w.room_name(a['room'])}."}, actor=cid)
                for o in before:
                    self.witness(o, {"type": "leave", "who": cid, "room": start, "to": a["room"], "hour": tick["hour"]})
                arrivals = [o for o in w.occupants(a["room"]) if o != cid]
                self.log_event(tick, {"type": "arrive", "who": cid, "room": a["room"], "vis": "public",
                                      "text": f"{name} arrives in {w.room_name(a['room'])}."}, actor=cid)
                for o in arrivals:
                    self.witness(o, {"type": "arrive", "who": cid, "room": a["room"], "frm": start, "hour": tick["hour"]})
        finally:
            self._slice_m = None
        return a["room"] == room

    def _start(self, tick, cid, act, room, at, m, why="", partner=None):
        w = self.world
        a = w.agents[cid]
        label, dur, _rooms, _kinds, verb = ACTS[act]
        walked = a["room"] != room
        start_room, m_go = a["room"], m
        arrived = self._walk(tick, cid, room, m)
        if not arrived:
            self._seg(tick, cid, m, m + SLICE, a["room"], "walk", f"heading for {w.room_name(room)}")
            return m + SLICE
        if walked:
            m += SLICE // 2 if dur > SLICE else 0
        if act in ("bathroom", "shower", "bath") and self._occupied_alone(tick, a["room"], m):
            act, label, dur, verb, at = "look", "waiting for the bathroom", 15, "waits for the bathroom", None
        if act == "chat":
            return self._start_chat(tick, cid, partner, m, why)
        if act == "explore":
            label = "exploring the " + w.room_name(room)
        end = m + dur
        self._seg(tick, cid, m, end, a["room"], act, label, "free", at)
        if walked and act not in ("bathroom", "shower", "bath", "nap", "dress", "flee", "rescue", "stalk"):
            self.companion_for(tick, cid, start_room, m_go, end)         # a close friend may come along
        if cid not in w.agents:
            return end                                                   # the way there killed them (a fall, a trap)
        self._effect(tick, cid, act, m, at)
        self.plan_done_by_act(cid, act, a["room"])
        return end

    def _start_chat(self, tick, cid, partner, m, why):
        """Two people sit or stand together and talk for half an hour. The partner stops what they were idling at; the conversation itself is written when the block ends."""
        w = self.world
        a, pa = w.agents[cid], w.agents.get(partner)
        if not pa or a["room"] != pa["room"] or self._chat_n >= (MAX_CHATS + 1 if self.brain_on() else MAX_CHATS) or not self._available(tick, partner, m, self._free_busy or {}):
            return self._start(tick, cid, "look", a["room"], None, m)
        room = a["room"]
        seat, seated = None, False
        got = self._find_furn(tick, cid, SEATS, {}, m, [room])
        if got:
            seat, seated = got[1], True
        else:
            t = self.nav().nominal(room, partner, 3)
            seat = (t[0], t[1], t[2])
        dur = 30
        self._chat_n += 1
        gid = f"{room}#{self._chat_n}"
        matters = self.chat_tags(cid, partner)
        tick["free_chats"].append({"gid": gid, "room": room, "m": m, "dur": dur, "members": [cid, partner], "at": list(seat), "why": why, "matters": sorted(set(matters))})
        for c, other in ((cid, partner), (partner, cid)):
            if self.brain_on():
                self.plan_mark(c, "talk", who=other)
            self._seg(tick, c, m, m + dur, room, "chat", f"talking with {self.nm(other)}", "free", seat)
            if self._free_busy is not None:
                self._free_busy[c] = m + dur
            ch = w.agents[c].setdefault("chatted", {})
            ch[other] = ch.get(other, 0) + 1
        text = f"{self.nm(cid)} and {self.nm(partner)} sit down to talk." if seated else f"{self.nm(cid)} goes over to {self.nm(partner)} for a word."
        self._fev(tick, cid, m, text, "free", "viewer", witnesses=[o for o in w.occupants(room) if o in w.agents and o not in (cid, partner)])
        if getattr(self, "_tl", None) is not None:
            self.start_convo(tick, [cid, partner], room, m, self._tl, why=why, matters=matters, at=seat, kind="chat", dur=dur)
        return m + dur

    def _effect(self, tick, cid, act, m, at=None):
        w, s = self.world, self.s
        a = w.agents[cid]
        b = self.body(cid)
        room = a["room"]
        here = [o for o in w.occupants(room) if o in w.agents and o != cid]
        name = self.nm(cid)
        verb = ACTS[act][4]
        note = lambda text, vis="viewer": self._fev(tick, cid, m, text, "free", vis, witnesses=here)
        if act == "eat":
            from .data_world import COMMON_ITEMS
            item = next((k for k in list(a["inv"]) + list(s["room_items"].get(room, {})) + ["bread", "tinned_food"] if "food" in w.item_spec(k).get("tags", []) or k in ("bread", "tinned_food", "loaf_bread")), None)
            if item and (a["inv"].get(item, 0) > 0 or s["room_items"].get(room, {}).get(item, 0) > 0 or item in COMMON_ITEMS.get(room, [])):
                self._slice_m = m
                try:
                    self.consume(tick, cid, item)
                finally:
                    self._slice_m = None
            else:
                a["hunger"] = max(0, a.get("hunger", 0) - 25)
                note(f"{name} {verb}.")
            a["thirst"] = max(0, a.get("thirst", 0) - 15)
        elif act == "confess":
            self.booth_visit(tick, cid, m)
        elif act == "snoop":
            self.do_snoop(tick, cid, m)
        elif act == "sleep":
            a["asleep"], a["activity"], a["slept_at"] = True, "Asleep", m
        elif act == "drink":
            a["thirst"] = max(0, a.get("thirst", 0) - 55)
            note(f"{name} {verb}.")
        elif act == "snack":
            a["hunger"] = max(0, a.get("hunger", 0) - 20)
            a["thirst"] = max(0, a.get("thirst", 0) - 15)
            note(f"{name} {verb}.")
        elif act == "cook":
            a["hunger"] = max(0, a.get("hunger", 0) - 35)
            fed = [o for o in here if w.agents[o].get("hunger", 0) >= 30]
            for o in fed:
                w.agents[o]["hunger"] = max(0, w.agents[o]["hunger"] - 15)
                self.stat(tick, o, "sanity", 1, "a cooked meal")
                self.adjust_any_aff(o, cid, 1) if self.rng.random() < 0.3 else None
            self.mind_relief(cid, "purpose", 8)
            note(f"{name} {verb}" + (f" and feeds {', '.join(self.nm(o) for o in fed[:3])}." if fed else "."))
        elif act == "wash":
            b["hygiene"] = min(100, b["hygiene"] + 25)
            a["thirst"] = max(0, a.get("thirst", 0) - 10)
            note(f"{name} {verb}.", "gm")
        elif act == "bathroom":
            b["bladder"] = 0
            note(f"{name} {verb}.", "gm")
            self.mind_relief(cid, "privacy", 10)
        elif act in ("shower", "bath"):
            b["hygiene"] = 100 if act == "bath" else 95
            note(f"{name} {verb}.")
            self.stat(tick, cid, "sanity", 2 if act == "bath" else 1, "a wash")
            self.mind_relief(cid, "privacy", 20 if act == "bath" else 15)
        elif act == "swim":
            self.stat(tick, cid, "sanity", 2, "a swim")
            note(f"{name} {verb}.")
        elif act in ("game", "chess", "darts"):
            partner = [o for o in here if a["aff"].get(o, 0) > -4]
            self.stat(tick, cid, "sanity", 2, "a game")
            if partner:
                o = self.rng.choice(partner)
                self.adjust_any_aff(cid, o, 1) if self.rng.random() < 0.4 else None
                note(f"{name} {verb} with {self.nm(o)}.")
            else:
                note(f"{name} {verb} alone.")
            self.mind_relief(cid, "social", 8 if partner else 2)
            self.mind_relief(cid, "purpose", 4)
        elif act in ("music", "jukebox", "art", "read", "stroll", "sit", "tend", "laundry", "radio", "stargaze", "mirror"):
            cause = {"music": "music", "jukebox": "music", "art": "drawing", "read": "a quiet read", "stroll": "fresh air", "sit": "a rest", "tend": "the garden", "laundry": "something useful",
                     "radio": "the radio", "stargaze": "the stars", "mirror": "looking presentable"}[act]
            if act not in ("laundry", "mirror") or self.rng.random() < 0.5:
                self.stat(tick, cid, "sanity", 1, cause)
            note(f"{name} {verb}.")
            self.mind_relief(cid, "purpose", {"art": 12, "read": 10, "tend": 12, "laundry": 10, "radio": 10, "stargaze": 6, "music": 8}.get(act, 3))
            self.mind_relief(cid, "privacy", 6)
            if act == "sit":
                self.mind_relief(cid, "rest", 8)
            if act == "tend" and self.rng.random() < 0.25:
                self.scratch(tick, cid, "thorns in the garden")
            if act == "radio" and self.revealed and self.rng.random() < 0.25:
                w.remember(cid, f"{(tick['hour'] * 60 + m) // 60:02d}:{(tick['hour'] * 60 + m) % 60:02d} (heard) a burst of static on the radio, and under it something that might have been a voice.")
        elif act == "nap":
            a["hp"] = clamp(a["hp"] + 2)
            self.mind_relief(cid, "rest", 14)
            note(f"{name} {verb}.", "gm")
        elif act == "tinker":
            rid = self.tinker_option(cid)
            if rid:
                self._slice_m = m
                try:
                    self.do_craft(tick, cid, {"craft": rid})
                finally:
                    self._slice_m = None
            self.mind_relief(cid, "purpose", 14)
            self.stat(tick, cid, "sanity", 1, "making something")
        elif act in ("look", "explore"):
            self._slice_m = m
            try:
                for ev in w.search(cid, "looks around", 0.7):
                    self.log_event(tick, ev, actor=cid)
            finally:
                self._slice_m = None
            if act == "explore":
                self.mind_relief(cid, "purpose", 6)
        elif act == "dress":
            self._slice_m = m
            try:
                self.wear(tick, cid, f"clothes_{cid}")
            finally:
                self._slice_m = None
        elif act == "rescue":
            victims = [o for o, oa in w.agents.items() if o != cid and oa["room"] == room and oa.get("out")]
            for v_ in victims:
                a.setdefault("rescue_tried", {})[v_] = self.day
            safe = next((r for r, _c in sorted(self._reach(cid).items(), key=lambda kv: kv[1]) if r not in self.fire_rooms() and r not in self.smoky_rooms() and not self._unsafe(r)), None)
            if victims and safe:
                v = victims[0]
                start = room
                self.stat(tick, cid, "hp", -1, "dragging someone out of the smoke")
                if cid in w.agents:
                    w.agents[v]["room"] = safe
                    w.agents[cid]["room"] = safe
                    for c_ in (v, cid):
                        pm = tick["moves"].setdefault(c_, {"from": start, "path": [start], "to": start})
                        pm["path"] = list(pm.get("path") or [start]) + [safe]
                        pm["to"] = safe
                    self._slice_m = m
                    try:
                        self.log_event(tick, {"type": "carry", "who": cid, "room": safe, "vis": "public", "text": f"{name} drags {self.nm(v)} out of the {w.room_name(start)} and away from the smoke."},
                                       witnesses=[o for o in w.occupants(safe) if o in w.agents and o != cid], actor=cid)
                    finally:
                        self._slice_m = None
                    self._seg(tick, v, m, TICK_MIN, safe, "unconscious", "carried to safety")
                    self.adjust_any_aff(v, cid, 2)
                    self.moment(cid, f"pulled {self.nm(v)} out of a burning room")
        elif act == "fight":
            note(f"{name} {verb}.")
            self.stat(tick, cid, "sanity", 1, "doing something about it")
        elif act == "warn":
            woke = [o for o in here if w.agents[o].get("asleep")]
            for o in woke:
                w.agents[o]["asleep"] = False
                w.remember(o, f"{tick['hour']:02d}:{m % 60:02d} {name} shook you awake: there is a fire in the house.")
            note(f"{name} {verb}" + (f" and wakes {', '.join(self.nm(o) for o in woke)}." if woke else "."))

    def mind_relief(self, cid, need, amount):
        if self.mind_on():
            n = self.mind(cid)["needs"]
            n[need] = min(100, n[need] + amount)


    # ------------------------------------------------------------------ embarrassment
    def modesty_check(self, tick, cid, m):
        """Somebody in their underwear in front of other people is mortified in proportion to their modesty. Shy people cover up and leave; the rest shrug."""
        k = self.tune("modesty")
        if not k:
            return
        w = self.world
        a = w.agents[cid]
        if self.worn(cid) is not None or a.get("asleep") or a["room"] in ("bathroom",):
            return
        watchers = [o for o in self.perceivers_of(cid, a["room"], "quiet") if o in w.agents]
        if not watchers:
            return
        mod = self.modesty(cid)
        if mod < 40:
            return
        key = f"_embarrassed_{self.day}_{tick['hour']}"
        if a.get(key):
            return
        a[key] = True
        self._slice_m = m
        try:
            sev = (mod - 30) / 70 * k
            if self.mind_on():
                self._thought(self.mind(cid), -(1.5 + 4.0 * sev), "seen in their underwear")
            self.stat(tick, cid, "sanity", -int(round(1 + 3 * sev)), "mortified to be seen undressed")
            w_ = self.rng.choice(watchers)
            self.log_event(tick, {"type": "embarrassed", "who": cid, "room": a["room"], "vis": "public",
                                  "text": f"{self.nm(cid)} goes red and tries to cover up when {self.nm(w_)} looks over."}, witnesses=watchers, actor=cid)
            if self.rng.random() < 0.4 * (100 - w_and_mod(self, w_)) / 100:
                self.adjust_any_aff(w_, cid, -1)
            self.moment(cid, "was seen in their underwear in front of other people")
        finally:
            self._slice_m = None

    # ------------------------------------------------------------------ the plot, minute by minute
    def plot_slice(self, tick, cid, hour, m, busy):
        """Called each slice for every free person. A plotter in the striking stage who shares a room with the target and has a window strikes with growing urgency."""
        s, w = self.s, self.world
        p = s.get("plots", {}).get(cid)
        if not p or p.get("stage") not in ("stalking", "striking") or not self.murders:
            return False
        t = p["target"]
        if t not in w.agents or s.get("case"):
            return False
        a, ta = w.agents[cid], w.agents[t]
        self.plot_defaults(p)
        if a["room"] != ta["room"]:
            p["wait"] = p.get("wait", 0) + (0.25 if p["stage"] == "striking" else 0)
            return False
        alone = len(self.perceivers_of(cid, a["room"], "quiet", exclude=(t,))) == 0 if self.perception_on() else len([o for o in w.occupants(a["room"]) if o in w.agents]) <= 2
        from .data_world import CAMERA_BLIND
        window = alone or a["room"] in CAMERA_BLIND or self.blackout_until >= self.idx or bool(ta.get("asleep"))
        if not window:
            p["wait"] = p.get("wait", 0) + 0.25
            return False
        if p["stage"] == "stalking":
            p["seen"] = p.get("seen", 0) + 1
            return False
        if not self.scheme_allows(cid, p, self.days_left() <= 0):
            p["wait"] = p.get("wait", 0) + 0.1                   # not the planned place or time: they wait for it
            return False
        # the longer they have waited, the less patience they have; nerves hold some people back
        wait = p.get("wait", 0)
        prob = 0.55 + 0.06 * wait + 0.12 * (self.facet(cid, "impulsiveness") - 50) / 50 + 0.1 * (self.facet(cid, "cruelty") - 50) / 50 - 0.1 * (a["sanity"] > 85)
        prob = min(0.97, max(0.2, prob)) * (1.0 if self.perception_on() else 0.9)
        if self.rng.random() >= prob:
            p["wait"] = wait + 0.5
            return False
        p["window"] = "alone" if alone else "blind spot" if a["room"] in CAMERA_BLIND else "dark" if self.blackout_until >= self.idx else "asleep"
        self.plan_note(p, f"struck at {self.nm(t)} ({p['window']})")
        self._slice_m = m
        try:
            self.resolve_attacks(tick, [(cid, {"target": t, "method": self.scheme_method(cid, p) or self.plot_method(p), "frame": None, "staged": self.scheme_staging(p)})], hour)
        finally:
            self._slice_m = None
        busy[cid] = m + SLICE
        self._seg(tick, cid, m, m + SLICE, a["room"], "attack", "attacking")
        p["wait"] = 0
        return True

    # ------------------------------------------------------------------ snapping
    def snap_odds(self, cid, here):
        """(probability for one slice, the person they'd turn on). Needs very little sanity left, or real hatred plus a lot of stress; calm people are almost never at risk."""
        a = self.world.agents[cid]
        k = self.tune("snap_rate")
        if not k or not self.murders:
            return 0.0, None
        stress = self.mind(cid)["stress"] if self.mind_on() else max(0, 60 - a["sanity"])
        anger = self.facet(cid, "anger") / 100 if self.mind_on() else 0.5
        imp = self.facet(cid, "impulsiveness") / 100 if self.mind_on() else 0.5
        hated = [o for o in here if a["aff"].get(o, 0) <= -4]
        tgt = min(hated, key=lambda o: a["aff"].get(o, 0)) if hated else None
        p = 0.0
        low = max(0, 30 - a["sanity"]) / 30
        if low > 0:
            p += 0.04 * low * (0.5 + imp)
            if tgt is None and here:
                tgt = min(here, key=lambda o: a["aff"].get(o, 0))
        if tgt and stress >= 45:
            p += 0.02 + 0.05 * min(1.0, (stress - 45) / 40) * (0.4 + 0.6 * anger) * (0.5 + imp)
        if a["drive"]["id"] in ("avenger", "nihilist") and tgt:
            p *= 1.4
        if self.has_cond(cid, "deranged") and tgt:
            p *= 1.6
        return min(0.35, p * k), tgt

    def snap_check(self, tick, cid, hour, m):
        w, s = self.world, self.s
        if cid not in w.agents:
            return False
        a = w.agents[cid]
        here = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid and not w.agents[o].get("out")]
        if not here:
            return False
        p, tgt = self.snap_odds(cid, here)
        if p <= 0 or tgt is None or self.rng.random() >= p:
            return False
        name, tname = self.nm(cid), self.nm(tgt)
        w.remember(cid, f"{hour:02d}:00 (private) Something in you gave way. You went for {tname}.")
        self._slice_m = m
        try:
            self.log_event(tick, {"type": "snap", "who": cid, "room": a["room"], "vis": "public", "text": f"{name} snaps and goes for {tname}!"},
                           witnesses=[o for o in here], actor=cid)
            self.moment(cid, f"snapped and attacked {tname}")
            if s.get("case"):
                self.do_assault(tick, cid, tgt, None, hour)
            else:
                weapon = next((k for k in list(a["inv"]) + list(s["room_items"].get(a["room"], {})) if "weapon" in w.item_spec(k).get("tags", []) and "instrument" not in w.item_spec(k).get("tags", [])), None)
                self.s["snapped"] = {"killer": cid, "target": tgt, "day": self.day, "m": m}
                self.resolve_attacks(tick, [(cid, {"target": tgt, "method": weapon or "hands", "frame": None, "snap": True})], hour)
        finally:
            self._slice_m = None
        case = s.get("case")
        if case and case.get("killer") == cid:
            case["snap"] = True
            case["note"] = ((case.get("note") or "") + " It looked unplanned: a sudden fit of violence.").strip()
        self._seg(tick, cid, m, m + SLICE, a["room"], "attack", "snapped")
        return True


def w_and_mod(runner, cid):
    try:
        return runner.modesty(cid)
    except Exception:
        return 50
