"""The day's schedule: fixed draws that pull people to one place at one time.

TereVi wakes the house at 08:00, serves breakfast (08:30-09:30), lunch (12:30-13:30) and dinner (18:30-19:30) in the Dining Hall, speaks again at 20:00
and calls curfew at 22:00. Meals are optional: each person weighs hunger, loneliness, friends and enemies at the table. A calm meal (no accusation, fight,
outburst, punishment or hostile exchange) lifts everyone at it: a little sanity (more with a friend there), company, warmth between people who talked, less
stress, and the day's news passes around the table. A tense meal gives nothing. Skipping costs quietly: no company, no news, and someone who keeps skipping
gets noticed. The daily rule, the director or the GM can cancel, move or add a draw (s["schedule_mods"]).
"""

DEFAULT_DRAWS = [
    {"id": "wake", "kind": "announce", "at": 8 * 60, "label": "Wake-up announcement", "room": "foyer"},
    {"id": "breakfast", "kind": "meal", "at": 8 * 60 + 30, "end": 9 * 60 + 30, "label": "Breakfast", "room": "dining_hall"},
    {"id": "lunch", "kind": "meal", "at": 12 * 60 + 30, "end": 13 * 60 + 30, "label": "Lunch", "room": "dining_hall"},
    {"id": "dinner", "kind": "meal", "at": 18 * 60 + 30, "end": 19 * 60 + 30, "label": "Dinner", "room": "dining_hall"},
    {"id": "evening", "kind": "announce", "at": 20 * 60, "label": "Evening announcement", "room": "foyer"},
    {"id": "curfew", "kind": "curfew", "at": 22 * 60, "label": "Curfew", "room": None},
]
TENSE_MOVES = {"putdown", "accuse", "threaten", "confront", "snap", "stand_up", "counter"}
TENSE_EVENTS = {"attack", "assault", "punish", "outburst", "madness", "body", "fight", "fire", "betrayal"}
NEWS_TYPES = {"attack", "assault", "body", "fire", "punish", "outburst", "madness", "betrayal", "discover", "leak", "fall", "island", "experiment", "arrival", "occasion"}
from .data_world import ROOMS

SKIP_NOTICED = 3                      # meals in a row before the others remark on it
FETCH_COST = 28                       # further than this from a mandatory scene and NeoVi comes to get you


class ScheduleMixin:
    # ------------------------------------------------------------------ the plan of the day
    def day_schedule(self):
        """Today's draws: the defaults with the rule's, director's and GM's changes applied (cancel / move / add)."""
        draws = [dict(d) for d in DEFAULT_DRAWS]
        for mod in self.s.get("schedule_mods") or []:
            if mod.get("day") not in (None, self.day):
                continue
            op = mod.get("op")
            if op == "cancel":
                draws = [d for d in draws if d["id"] != mod.get("id")]
            elif op == "move":
                for d in draws:
                    if d["id"] == mod.get("id"):
                        span = d.get("end", d["at"]) - d["at"]
                        d["at"] = int(mod["at"])
                        if "end" in d:
                            d["end"] = d["at"] + span
                        d["room"] = mod.get("room") or d["room"]
            elif op == "add" and mod.get("draw"):
                draws.append(dict(mod["draw"]))
        return sorted(draws, key=lambda d: d["at"])

    def schedule_view(self):
        return [{"id": d["id"], "label": d["label"], "kind": d["kind"], "at": d["at"], "end": d.get("end"), "room": d.get("room")} for d in self.day_schedule()]

    def gm_schedule(self, tick, it, hour):
        """The GM (or the director) cancels, moves or adds a draw. A change to a time already past applies tomorrow."""
        op = it.get("op")
        try:
            at = int(it.get("at")) if it.get("at") not in (None, "") else None
        except (TypeError, ValueError):
            at = None
        if op not in ("cancel", "move", "add") or (op != "cancel" and (at is None or not 8 * 60 <= at <= 21 * 60 + 30)):
            return None
        room = it.get("room") if it.get("room") in ROOMS else None
        ref = at if at is not None else next((d["at"] for d in self.day_schedule() if d["id"] == it.get("id")), 0)
        day = self.day if ref > hour * 60 else self.day + 1
        mod = {"op": op, "day": day}
        if op == "add":
            n = len(self.s.get("schedule_mods") or []) + 1
            mod["draw"] = {"id": f"gm{n}", "kind": "summons", "at": at, "end": at + 60, "label": (str(it.get("text") or "").strip()[:40] or "A summons"), "room": room or "dining_hall"}
        else:
            mod["id"] = str(it.get("id") or "")
            if op == "move":
                mod["at"], mod["room"] = at, room
        self.s.setdefault("schedule_mods", []).append(mod)
        del self.s["schedule_mods"][:-20]
        what = {"cancel": f"cancels {mod.get('id')}", "move": f"moves {mod.get('id')} to {at // 60:02d}:{at % 60:02d}" if at is not None else "",
                "add": f"calls everyone to the {self.world.room_name(mod['draw']['room'])} at {at // 60:02d}:{at % 60:02d}" if op == "add" else ""}[op]
        self.log_event(tick, {"type": "system", "who": "terevi", "room": "foyer", "vis": "gm", "text": f"Director: TereVi {what} (day {day})."})
        return mod

    def meal_in_turn(self, hour):
        """The meal (or summons) that starts during the turn beginning at `hour`, with its start minute inside the turn, or (None, None)."""
        span = 60 * max(1, self.step)
        for d in self.day_schedule():
            if d["kind"] in ("meal", "summons") and hour * 60 <= d["at"] < hour * 60 + span:
                return d, float(min(d["at"] - hour * 60, 60))
        return None, None

    # ------------------------------------------------------------------ mandatory scenes
    def fetch_stragglers(self, tick, ids, room, label):
        """A mandatory scene (the trial, a vigil, the last call...): whoever will not make it on their own (asleep, hiding, locked away, too far, dragging their feet)
        is fetched by NeoVi. Returns who was fetched."""
        w = self.world
        got = []
        for cid in ids:
            a = w.agents.get(cid)
            if not a or a["room"] == room:
                continue
            steps = w.path(cid, a["room"], room)
            cost = sum(c for _, _, c in steps) if steps else 0
            why = ("asleep" if a.get("asleep") else "hiding" if a.get("hiding") else "cannot get there" if steps is None else "too far" if cost > FETCH_COST
                   else "dragging their feet" if a["sanity"] < 25 or (self.s.get("meal_skips") or {}).get(cid, 0) >= SKIP_NOTICED else None)
            if not why:
                continue
            got.append(cid)
            a.pop("asleep", None)
            by = "NeoVi" if self.neovi_maid() else "TereVi's drones"
            self.log_event(tick, {"type": "fetch", "who": "neovi" if self.neovi_maid() else "terevi", "room": a["room"], "vis": "viewer", "why": why,
                                  "text": f"{by} fetch{'es' if by == 'NeoVi' else ''} {self.nm(cid)} from the {w.room_name(a['room'])} for {label}."})
            w.remember(cid, f"{by} came to fetch you for {label}.")
        if got:
            tick["fetched"] = got
        return got

    # ------------------------------------------------------------------ the news ledger
    def note_news(self, evt, witnesses, actor):
        if evt.get("type") not in NEWS_TYPES or evt.get("vis") == "gm":
            return
        knows = [c for c in list(witnesses or []) + [actor] if c in self.world.agents]
        if not knows:
            return
        news = self.s.setdefault("news", [])
        news.append({"day": self.day, "text": str(evt.get("text", ""))[:160], "knows": sorted(set(knows))})
        del news[:-40]

    def spread_news(self, tick, people, label):
        """Whatever one of them saw today, the others hear over the meal (at most three stories)."""
        w = self.world
        told = 0
        for n in reversed(self.s.get("news") or []):
            if told >= 3 or n["day"] < self.day - 1:
                break
            knew = [p for p in people if p in n["knows"]]
            new = [p for p in people if p not in n["knows"]]
            if not knew or not new:
                continue
            for p in new:
                w.remember(p, f"Over {label.lower()}, {self.nm(knew[0])} told everyone: {n['text'][:120]}")
                self.belief_news(p, knew[0], n["text"][:140])
            n["knows"] = sorted(set(n["knows"]) | set(new))
            told += 1
        return told

    # ------------------------------------------------------------------ going to the meal
    def meal_pull(self, cid, others):
        """How much `cid` wants to come to the table, given who else is there (0..1)."""
        w = self.world
        a = w.agents[cid]
        need = self.mind(cid)["needs"]
        p = 0.55 + a.get("hunger", 0) / 160 + a.get("thirst", 0) / 300 + (100 - need["social"]) / 300
        p += 0.15 * (self.facet(cid, "gregariousness") - 50) / 50
        aff = [a["aff"].get(o, 0) for o in others if o != cid]
        p += 0.05 * sum(1 for x in aff if x >= 2) - 0.08 * sum(1 for x in aff if x <= -4)
        if a["sanity"] < 20:
            p -= 0.2                                          # the badly shaken hide away
        p -= self.mind(cid)["stress"] / 400
        pl = (self.s.get("plots") or {}).get(cid)
        if pl and pl.get("stage") in ("stalking", "striking"):
            p -= 0.35                                         # busy with something else
        if cid in (self.__dict__.get("busy") or ()):
            p -= 0.25
        return max(0.05, min(0.95, p))

    def meal_call(self, tick, hour, draw, m):
        """At the meal's start minute: everyone weighs coming, the ones who come walk to the table and eat."""
        w = self.world
        room = draw["room"]
        can = [c for c in sorted(w.agents) if not w.agents[c].get("out") and not w.agents[c].get("asleep") and not self.restrained(c)]
        if not can or room not in ROOMS:
            return None
        at_table = [c for c in can if w.agents[c]["room"] == room]
        rule = self.s.get("rule") or {}
        must = (rule.get("id") == "mealtime" and draw["id"] in ("lunch", "dinner")) or draw["kind"] == "summons"     # the daily rule (or a summons) makes it mandatory
        if must:
            self.fetch_stragglers(tick, can, room, draw["label"].lower())
        come = []
        for cid in can:
            if must or self.rng.random() < self.meal_pull(cid, at_table + come):
                come.append(cid)
        sm = self.sim_turn(tick)
        came = []
        for cid in come:
            if w.agents[cid]["room"] != room:
                mv = w.move(cid, room, 400)
                if w.agents[cid]["room"] != room:
                    continue                                  # locked out, or too far
                pm = tick["moves"].setdefault(cid, {"from": mv["path"][0], "path": [mv["path"][0]], "to": room})
                pm["path"] = list(pm.get("path") or []) + mv["path"][1:]
                pm["to"] = room
                dest = sm.spot(room, cid, sm.occupied(cid), 7)
                if dest:
                    sm.walk(cid, dest, m, deadline=min(sm.dur - 5.0, m + 25.0), speed=self.move_factor(cid))
            came.append(cid)
        skipped = [c for c in can if c not in came]
        if draw["kind"] == "meal":
            self.meal_for(tick, came)
        meal = {"id": draw["id"], "label": draw["label"], "room": room, "m": m, "end_m": m + (draw.get("end", draw["at"] + 60) - draw["at"]),
                "came": came, "skipped": skipped, "hour": hour, "kind": draw["kind"]}
        self.__dict__["_meal"] = meal
        names = ", ".join(self.nm(c) for c in came) or "nobody"
        self.log_event(tick, {"type": "meal", "who": "terevi", "room": room, "vis": "viewer",
                              "text": (f"{draw['label']} is served in the {w.room_name(room)}. At the table: {names}." if draw["kind"] == "meal"
                                       else f"TereVi summons everyone to the {w.room_name(room)} ({draw['label']}). There: {names}.")})
        return meal

    # ------------------------------------------------------------------ after the meal
    def meal_tension(self, tick, meal):
        """What soured the meal, or None if it stayed calm."""
        room, lo, hi = meal["room"], meal["m"] - 5, meal["end_m"] + 30
        for e in tick["events"]:
            if e.get("room") == room and e.get("type") in TENSE_EVENTS and lo <= e.get("m", lo) <= hi:
                return e.get("type")
        for c in self.convos():
            if c["room"] != room:
                continue
            for b in c["beats"]:
                if b.get("move") in TENSE_MOVES and lo <= b.get("m", lo) <= hi:
                    return b["move"]
        return None

    def meal_settle(self, tick, hour):
        meal = self.__dict__.pop("_meal", None)
        if not meal:
            return None
        w, s = self.world, self.s
        came = [c for c in meal["came"] if c in w.agents and not w.agents[c].get("out")]
        why = self.meal_tension(tick, meal)
        meal["calm"] = why is None and len(came) >= 2
        meal["sour"] = why
        if meal["calm"]:
            talked = {}
            for c in self.convos():
                if c["room"] == meal["room"]:
                    for b in c["beats"]:
                        if b.get("who") in came and b.get("to") in came and b["who"] != b["to"]:
                            talked.setdefault(frozenset((b["who"], b["to"])), True)
            for cid in came:
                friends = sum(1 for o in came if o != cid and w.agents[cid]["aff"].get(o, 0) >= 2)
                self.special_boost(tick, cid, 3 + min(2, friends), f"a calm {meal['label'].lower()}", "meal")
                m_ = self.mind(cid)
                m_["needs"]["social"] = min(100.0, m_["needs"]["social"] + 20)
                m_["stress"] = max(0.0, m_["stress"] - 8)
            for pair in talked:
                a_, b_ = tuple(pair)
                w.adjust_aff(a_, b_, 1)
                w.adjust_aff(b_, a_, 1)
            meal["news"] = self.spread_news(tick, came, meal["label"])
            meal["pairs"] = len(talked)
        elif why:
            for cid in came:
                self.mind(cid)["stress"] = min(100.0, self.mind(cid)["stress"] + 4)
            self.log_event(tick, {"type": "meal", "who": "terevi", "room": meal["room"], "vis": "viewer",
                                  "text": f"{meal['label']} turns sour ({why.replace('_', ' ')}). Nobody enjoys it."})
        # skipping: a streak the others notice
        streak = s.setdefault("meal_skips", {})
        for cid in came:
            streak.pop(cid, None)
        for cid in meal["skipped"]:
            if cid not in w.agents:
                continue
            streak[cid] = streak.get(cid, 0) + 1
            if streak[cid] == SKIP_NOTICED and came:
                for o in came:
                    w.remember(o, f"{self.nm(cid)} has skipped {SKIP_NOTICED} meals in a row now. Where do they go?")
                self.log_event(tick, {"type": "meal", "who": cid, "room": meal["room"], "vis": "viewer",
                                      "text": f"The others notice {self.nm(cid)} has missed {SKIP_NOTICED} meals in a row."})
        tick["meal"] = {k: meal[k] for k in ("id", "label", "room", "came", "skipped", "calm", "sour") if k in meal}
        s.setdefault("meals", []).append({"day": self.day, **tick["meal"]})
        del s["meals"][:-30]
        return meal
