"""Deciding ahead (phase F4): the next block's decisions are asked for near the end of this one, so the next block can start at once.

At minute 107 of a day block the engine builds everyone's decision prompt for the next block and sends the model calls off on worker threads. Building a prompt
early leaves no trace (`decide_prepare_dry` puts back the dice, the hints shown and the counters it touched). When the next block starts, everyone is decided
as usual (same prompts, same side effects); for a person whose situation is unchanged since the early ask (`ahead_sig`: out cold or asleep, badly hurt, a death
announced or tried, the rule, who is still alive), the early answer is used instead of a new call. Not their room, a plot starting, a new condition or an island
event: a decision says where to go, and the engine overrides it for plots, care and danger anyway. Anyone whose situation changed is asked again, and the early
call is wasted.
Only when someone is watching live and has caught up with the engine (`viewer_close`; otherwise the next block is ready before it is needed and early calls would buy
nothing), and only with the dial `decide_ahead` on. Nothing is asked ahead when the next turn will not be an ordinary block (a trial, the last call, a vigil, a finale, the endgame, the evening, the leader rule).
Counts in `s["ahead"]`: used, stale, wasted. AheadMixin is mixed into DayRunner (engine.py).
"""
import copy
import random


class AheadMixin:
    def ahead_ok(self, nh):
        """Will the turn at hour `nh` be an ordinary block that asks everyone? (These checks only read the world.)"""
        s = self.s
        if nh > 20 or not self.revealed or s.get("over") or not self.free_hour(nh):
            return False
        if (s.get("rule") or {}).get("id") == "leader":
            return False
        case = s.get("case")
        if case and case.get("announced") and not case.get("resolved") and (self.day > case["vote_day"] or (self.day == case["vote_day"] and nh >= case["vote_hour"])):
            return False
        if self.endgame_due() or self.season_over_due(nh) or self.rescue_due(nh) or self.last_call_due(nh) or self.vigil_due(nh) or self.ready_route():
            return False
        return True

    def ahead_sig(self, cid):
        """What would make an early decision stale (see the module's docstring for what does not)."""
        s, a = self.s, self.world.agents.get(cid) or {}
        case = s.get("case") or {}
        return (bool(a.get("out")), bool(a.get("asleep")), a.get("hp", 0) < 50, case.get("victim"), bool(case.get("announced")), bool(case.get("resolved")),
                (s.get("rule") or {}).get("id"), len(s.get("graveyard") or []), len(self.world.agents))

    def decide_prepare_dry(self, cid, hour):
        """decide_prepare without leaving a trace: the dice, the hints shown and the counters it touches are put back."""
        rngs = {k: v.getstate() for k, v in self.__dict__.items() if isinstance(v, random.Random)}
        hints = {c: copy.deepcopy(a.get("last_hints")) for c, a in self.world.agents.items()}
        tele = copy.deepcopy(self.s.get("telemetry"))
        why = copy.deepcopy(self.__dict__.get("_why_model"))
        try:
            return self.decide_prepare(cid, hour)
        finally:
            for k, st in rngs.items():
                self.__dict__[k].setstate(st)
            for c, h in hints.items():
                if h is None:
                    self.world.agents[c].pop("last_hints", None)
                else:
                    self.world.agents[c]["last_hints"] = h
            self.s["telemetry"] = tele
            if why is None:
                self.__dict__.pop("_why_model", None)
            else:
                self._why_model = why

    def decide_ahead(self, bk):
        """Near the end of a day block: ask for the next block's decisions now, on worker threads."""
        nh = int(bk["hour"]) + self.step
        self._ahead = {}
        if not self.tune("decide_ahead") or not self.viewer_close() or not self.ahead_ok(nh):
            return
        for cid in sorted(self.world.agents):
            got = self.decide_prepare_dry(cid, nh)
            if got[0] != "ask":
                continue
            sysm, user, ctx = got[1]
            self._ahead[cid] = {"day": self.day, "hour": nh, "sig": self.ahead_sig(cid), "fut": self.voice_pool().submit(self.llm.decide, sysm, user, ctx)}

    def viewer_close(self):
        """Is someone watching live and close behind the engine (so a faster start of the next block would actually be seen)? The session sets `viewer_pos`."""
        pos = self.__dict__.get("viewer_pos")
        return pos is not None and pos() >= self.idx - 1

    def ahead_answer(self, cid, hour):
        """The early answer for `cid` at this hour if their situation has not changed since it was asked, else None (the early call is then wasted)."""
        st = self.s.setdefault("ahead", {"used": 0, "stale": 0, "wasted": 0})
        e = (self.__dict__.get("_ahead") or {}).pop(cid, None)
        if not e:
            return None
        if e["day"] != self.day or e["hour"] != hour or e["sig"] != self.ahead_sig(cid):
            st["stale"] += 1
            st["wasted"] += 1
            return None
        st["used"] += 1
        return e["fut"]

    def ahead_drop(self):
        """Early answers nobody used (someone died, the turn turned out to be something else): wasted calls."""
        left = self.__dict__.get("_ahead") or {}
        if left:
            st = self.s.setdefault("ahead", {"used": 0, "stale": 0, "wasted": 0})
            st["wasted"] += len(left)
        self._ahead = {}
