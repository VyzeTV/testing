"""Investigation focus: while a death is investigated, free time is spent on the case.

From the announcement to the trial, people who are free examine the scene, search the rooms tied to the case (where the victim slept and was last seen, the
rooms next to the scene), and question one another about where everyone was (an unvoiced talk that swaps testimonies). Everything else is cut back to a
fraction (`FOCUS`), except real needs (food, drink, the bathroom, washing, sleep, danger) and talk. Two kinds of people still drift off: the very unstable
(sanity below 25), and a killer who knows what they did and is acting calm, which others may find odd (they remember it).
InquiryMixin is mixed into DayRunner (engine.py); free time calls `inquiry_options`, `inquiry_focus` and `inquiry_after` (freetime.py).
"""
from .data_world import ROOMS
from .gridnav import _h

FOCUS = 0.3                     # what leisure counts for while a death is investigated
NEEDS = {"eat", "drink", "snack", "bathroom", "wash", "shower", "bath", "sleep", "nap", "dress", "flee", "rescue", "fight", "warn", "stalk",
         "examine", "inquire", "question", "talk", "chat", "gather", "company", "seek_nv", "escape"}
CALM_ACTS = {"game", "chess", "darts", "music", "jukebox", "art", "read", "sit", "stroll", "swim", "radio", "stargaze", "mirror"}


class InquiryMixin:
    def inquiry_case(self):
        """The case under investigation, or None."""
        case = self.s.get("case")
        return case if case and case.get("announced") and not case.get("resolved") and case.get("victim") else None

    def case_rooms(self, case):
        """Rooms tied to the case that are worth searching: the scene, the victim's room, where the victim was seen that day, the rooms beside the scene."""
        w = self.world
        v = case["victim"]
        out = [case.get("room")]
        home = (w.cast.get(v) or {}).get("home")
        out.append(home)
        seen = [r for (d, h, r) in self.s.get("where_log", {}).get(v, []) if d == case.get("day", self.day)][-3:]
        out += seen
        out += sorted(n for e in w.edges for n in (e["a"], e["b"]) if case.get("room") in (e["a"], e["b"]) and n != case.get("room") and not e.get("hidden"))[:3]
        res = []
        for r in out:
            if r and r in ROOMS and r not in res:
                res.append(r)
        return res

    def inquiry_options(self, tick, cid, hour, m, add, f, reach):
        """What someone free can do for the case: examine the scene, search a room tied to it, question someone."""
        case = self.inquiry_case()
        if not case or tick.get("phase") == "night":
            return
        w = self.world
        a = w.agents[cid]
        here = a["room"]
        mine = a.setdefault("inquiry", {})
        if mine.get("case") != f"{case['victim']}:{case['day']}":
            mine.clear()
            mine.update({"case": f"{case['victim']}:{case['day']}", "rooms": [], "asked": []})
        drive = 0.9 + (f("curiosity") - 50) / 80 + (f("orderliness") - 50) / 160 + (0.3 if a["aff"].get(case["victim"], 0) >= 3 else 0)
        if cid == case.get("killer") and case.get("culprit_aware", True):
            drive -= 0.3                                                # a killer looks busy, without much heart in it
        far = w.reachable_rooms(cid, 40)                                # the case is worth a longer walk than a game of chess
        scene = case.get("room")
        if scene in ROOMS and scene not in mine["rooms"] and (scene in far or scene == here):
            add(drive + 0.5, "examine", room=scene, why=f"examining where {self.nm(case['victim'])} died")
        for r in self.case_rooms(case)[1:]:
            if r not in mine["rooms"] and (r in far or r == here) and not self._unsafe(r):
                add(drive + 0.1 - 0.05 * len(mine["rooms"]), "inquire", room=r, why=f"looking for clues in the {w.room_name(r)}")
                break
        ppl = [o for o in sorted(w.agents) if o != cid and o not in mine["asked"] and not w.agents[o].get("out") and not w.agents[o].get("asleep")
               and (w.agents[o]["room"] in reach or w.agents[o]["room"] == here) and self._available(tick, o, m, self._free_busy or {})]
        if ppl:
            o = min(ppl, key=lambda x: (w.agents[x]["room"] != here, -abs(a["aff"].get(x, 0)), _h(cid, x, self.day) % 97))
            add(drive + (f("assertiveness") - 50) / 100, "question", room=w.agents[o]["room"], partner=o, why=f"asking {self.nm(o)} where they were")

    def inquiry_focus(self, cid, sc):
        """Cut leisure back while a death is investigated (not for the very unstable, nor for a killer playing it cool)."""
        case = self.inquiry_case()
        if not case:
            return sc
        a = self.world.agents[cid]
        if a["sanity"] < 25:
            return sc
        if cid == case.get("killer") and case.get("culprit_aware", True) and _h(cid, self.day, "cool") % 2 == 0:
            return sc                                                   # acting as if nothing happened
        from .pastimes import PASTIME_ACTS
        return [((x[0] * FOCUS) if x[1] not in NEEDS and x[1] not in PASTIME_ACTS else x[0],) + tuple(x[1:]) for x in sc]

    def inquiry_effect(self, tick, cid, act, m):
        """Examining the scene or searching a room for the case: the clues there, and anything hidden."""
        w = self.world
        a = w.agents[cid]
        case = self.inquiry_case()
        if not case:
            return
        mine = a.setdefault("inquiry", {"rooms": [], "asked": []})
        if a["room"] not in mine.setdefault("rooms", []):
            mine["rooms"].append(a["room"])
        here = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid]
        what = "examines the scene" if act == "examine" else f"searches the {w.room_name(a['room'])} for anything to do with {self.nm(case['victim'])}'s death"
        self._slice_m = m
        try:
            self.log_event(tick, {"type": "search", "who": cid, "room": a["room"], "vis": "public", "text": f"{self.nm(cid)} {what}."}, witnesses=here, actor=cid)
            self.reveal_clues(tick, cid)
            self.search_for_hidden(tick, cid, "clue evidence " + ("body wound scene" if act == "examine" else "search drawers floor"))
        finally:
            self._slice_m = None
        self.mind_relief(cid, "purpose", 10)
        s_ = self.s.setdefault("inquiry_stats", {})
        s_[act] = s_.get(act, 0) + 1

    def inquiry_after(self, tick, cid, act, room, m):
        """A killer seen relaxing while everyone else hunts for clues may strike them as odd."""
        case = self.inquiry_case()
        if not case or cid != case.get("killer") or act not in CALM_ACTS:
            return
        w = self.world
        here = [o for o in w.occupants(room) if o in w.agents and o != cid and not w.agents[o].get("asleep")]
        for o in here:
            if self.rng.random() < 0.35:
                when = f"{(tick['hour'] * 60 + int(m)) // 60 % 24:02d}:{int(m) % 60:02d}"
                w.remember(o, f"{when} (saw) {self.nm(cid)} was {self._acts()[act][0]} as if nothing had happened, while everyone else was looking into {self.nm(case['victim'])}'s death. Strange.")
                s_ = self.s.setdefault("inquiry_stats", {})
                s_["odd_calm"] = s_.get("odd_calm", 0) + 1
