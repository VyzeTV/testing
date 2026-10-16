"""Reliability of the optional mechanics: measure it, nudge it, and keep the prompts short.

The models mostly play the same few actions. This module (1) counts, per day, how often each optional mechanic is used by the model and how often the engine had to do it for them,
(2) offers each character one or two situational suggestions ("someone is hiding something here", "that door is locked") chosen to favour what has not been used, (3) shows the long
rule texts for the optional systems only at the start of a day (otherwise a one-line pointer), and (4) removes dialogue action lines that conjure objects nobody has.
TelemetryMixin is mixed into DayRunner (engine.py).
"""
import re

from .data_world import ITEMS, COMMON_ITEMS, ROOMS

FLAGS = ("wear", "betray", "sneak", "spy_on", "stash", "conceal", "keep_back", "disclose", "frisk", "door", "craft", "night", "sleep_in")
DOC_HOURS = (8, 10)


def _hh(h):
    return f"{int(h):02d}:00"


class TelemetryMixin:
    # ------------------------------------------------------------------ counting
    def note_use(self, cid, tag, src="model"):
        t = self.s.setdefault("telemetry", {}).setdefault(str(self.day), {}).setdefault(tag, {"model": 0, "engine": 0})
        t[src if src in ("model", "engine") else "model"] += 1
        days = self.s["telemetry"]
        if len(days) > 30:
            for k in sorted(days, key=int)[:-30]:
                del days[k]

    def note_decision(self, cid, d):
        src = d.get("_src", "model")
        self.note_use(cid, "action:" + d["action"], src)
        for f in FLAGS:
            if d.get(f):
                self.note_use(cid, f, "model")

    def usage_today(self, tag):
        t = self.s.get("telemetry", {}).get(str(self.day), {}).get(tag) or {}
        return t.get("model", 0)

    def usage_summary(self, day=None):
        return self.s.get("telemetry", {}).get(str(day or self.day), {})

    # ------------------------------------------------------------------ short docs
    def docs_full(self, cid, hour):
        """The long explanations of the optional systems appear on the first turns of a day; after that a short pointer."""
        return hour in DOC_HOURS or hour >= 23

    # ------------------------------------------------------------------ situational suggestions
    def options_hint(self, cid, hour):
        """One or two things that make sense for this person right now, favouring mechanics that have been used least today."""
        if not self.revealed:
            return []
        w, s = self.world, self.s
        a = w.agents[cid]
        room = a["room"]
        here = [o for o in w.occupants(room) if o in w.agents and o != cid]
        cands = []                                                     # (weight, text, tag)

        def add(wt, text, tag):
            cands.append((wt / (1 + self.usage_today(tag)), text, tag))
        hostile = [o for o in here if a["aff"].get(o, 0) <= -3]
        loved = [o for o in w.agents if o != cid and a["aff"].get(o, 0) >= 5]
        adj = [n for n in w.adjacent(cid, room) if n["kind"] in ("door", "window")]
        if a["drive"]["id"] in ("schemer", "seeker") and any(len([o for o in w.occupants(n["room"]) if o in w.agents]) >= 2 for n in adj):
            add(1.0, "people are talking in the next room: you could linger at the door and listen (action 'spy')", "spy_on")
        if hostile:
            add(1.2, f"{self.nm(hostile[0])} is here and you do not trust them: you could slip away quietly (\"sneak\": true) or search them (action 'frisk')", "sneak")
        if here and any("weapon" in w.item_spec(k).get("tags", []) or "secret" in w.item_spec(k).get("tags", []) for k in a["inv"]):
            add(1.0, "you carry something you would rather nobody saw: you can tuck it out of sight (\"conceal\")", "conceal")
        for n in adj:
            blk = self.door_block(cid, n["room"])
            if blk and (self.pick_tool(cid) or blk[0] == "barricade"):
                add(0.8, f"the way into the {w.room_name(n['room'])} is blocked; you could {'pick the lock' if self.pick_tool(cid) and blk[0] == 'lock' else 'break it down'}", "door")
                break
        if hour >= 18 and lockable_room(room) and room not in s.get("locks", {}):
            add(1.0 if a["sanity"] < 60 else 0.5, "night is coming: you could bolt your door (action 'lock'), or barricade it", "door")
        ready = self.craftable(cid)
        if ready:
            add(1.0, f"you have what you need to make something ({', '.join(ready[:2])}) (action 'craft')", "craft")
        owner_rooms = self.belongings_of(room)
        if any(o != cid for o in owner_rooms) and a["drive"]["id"] in ("schemer", "seeker", "saboteur"):
            add(1.2, "this is someone else's room and they are out: you could search it (action 'search')", "action:search")
        for h in s.get("hooks", []):
            if h["status"] == "open" and cid in h["victims"]:
                tgt = h["seen_by"][0] if h["seen_by"] else None
                add(1.5, f"you are still troubled by what happened ({h['text'][:60]}): ask someone who was near, or search the room" + (f" (e.g. {self.nm(tgt)})" if tgt else ""), "action:interrogate")
                break
        if self.s["npcs"]["neovi"].get("room") == room and self.s["npcs"]["neovi"].get("aff", {}).get(cid, 0) < 6 and any({"food", "comfort", "drink"} & set(w.item_spec(k).get("tags", [])) for k in a["inv"]):
            add(0.7, "NeoVi is here: a small gift (action 'give', to: neovi) might buy her blind eye for the day", "bribe")
        if self.blackout_until >= self.idx and a.get("lit"):
            add(0.8, "the power is out and you have a light: you can see who is where, and they cannot see you", "light")
        if self.has_optics(cid) and ROOMS[room][1] in ("grounds", "roof"):
            add(0.6, "you carry a lens: you could watch another part of the grounds from here (action 'spy', \"spy_on\": a room id)", "spy_on")
        if self.has(cid, "handcuffs") and (hostile or any(w.agents[o].get("asleep") for o in w.occupants(room, include_hidden=True) if o in w.agents and o != cid)):
            add(0.7, "you carry handcuffs (action 'restrain', target a person)", "restrain")
        if self.has(cid, "tape_recorder") and here:
            add(0.7, "you carry a tape recorder: hide it in a room (action 'stash') and listen to what gets said there later", "stash")
        injured = [o for o in here if w.agents[o].get("conds") or w.agents[o].get("out")]
        if injured and a["aff"].get(injured[0], 0) >= 0:
            add(1.2, f"{self.nm(injured[0])} is hurt or unconscious: you could help (action 'treat' or 'wake')", "action:treat")
        if a.get("conds") and not self.treat_options(cid) and room not in ("green_room", "bathroom") and any(c in a["conds"] for c in ("bleeding", "broken_arm", "broken_leg", "burned", "infected", "poisoned")):
            add(1.1, "you are hurt and have nothing to treat it: the green room and the bathroom keep the first-aid kit and bandages (resting there helps you heal)", "go:infirmary")
        if a.get("conds") and self.treat_options(cid):
            add(1.2, "you are hurt and you have something to treat it with (action 'treat')", "action:treat")
        if any(w.agents[o].get("out") for o in w.occupants(room, include_hidden=True) if o in w.agents and o != cid) and hostile:
            add(0.9, "someone you distrust lies helpless here: you could search them (action 'rob'), drag them away (action 'carry'), or cuff them (action 'restrain')", "action:rob")
        if self.held_by(cid):
            add(0.8, "you are holding something back: you could come clean (\"disclose\": true) or keep it hidden a little longer", "disclose")
        if hour >= 18 and self.night_allowed() and a["hp"] >= 45 and s.get("plots", {}).get(cid):
            add(1.0, "if you want the dark to yourself tonight, you could stay up (\"night\": true)", "night")
        if hour >= 16 and loved:
            add(0.4, "you could spend the night in a friend's room instead of your own (\"sleep_in\")", "sleep_in")
        if not cands:
            return []
        last = set(a.get("last_hints", []))
        pool = [c for c in cands if c[2] not in last] or cands
        pool.sort(key=lambda c: -(c[0] * self.rng.uniform(0.6, 1.4)))
        pick = pool[:2]
        a["last_hints"] = [c[2] for c in pick]
        return ["WORTH CONSIDERING NOW (only if it fits you): " + "; ".join(c[1] for c in pick) + "."]

    # ------------------------------------------------------------------ dialogue props
    def prop_names(self):
        """Phrases that point at an item in dialogue: its full name, its last two words ("frying pan"), and a distinctive single noun."""
        if not hasattr(self, "_prop_re"):
            alias = {}
            for iid, spec in ITEMS.items():
                if "special" in spec.get("tags", []):
                    continue
                n = re.sub(r"\s*\(.*?\)", "", spec["name"].lower()).replace("-", " ")
                words = n.split()
                forms = {n}
                if len(words) >= 3:
                    forms.add(" ".join(words[-2:]))
                for f in forms:
                    if len(f) >= 5:
                        alias.setdefault(f, set()).add(iid)
            singles = {}
            for iid, spec in ITEMS.items():
                if "special" in spec.get("tags", []):
                    continue
                words = re.sub(r"\s*\(.*?\)", "", spec["name"].lower()).replace("-", " ").split()
                if len(words) >= 2 and len(words[-1]) >= 6:
                    singles.setdefault(words[-1], set()).add(iid)
            for wd, ids_ in singles.items():
                if len(ids_) == 1:
                    alias.setdefault(wd, set()).update(ids_)
            self._prop_re = [(re.compile(r"\b" + re.escape(f) + r"s?\b"), ids_) for f, ids_ in sorted(alias.items(), key=lambda kv: -len(kv[0]))]
        return self._prop_re

    def filter_props(self, tick, room, group, lines):
        """Action lines that pull an object out of nowhere (nobody present carries it, it is not in the room, it is not a common supply here) are dropped."""
        w, s = self.world, self.s
        have = set(COMMON_ITEMS.get(room, [])) | set(s["room_items"].get(room, {}))
        for p in group:
            if p in w.agents:
                have |= set(w.agents[p]["inv"])
                have |= {k for k in (s.get("belongings") or {}).get(p, {})}
        out, dropped = [], 0
        for ln in lines:
            if ln["kind"] == "act":
                text_ = ln["text"].lower().replace("-", " ")
                bad = next((ids_ for rx, ids_ in self.prop_names() if rx.search(text_) and not (ids_ & have)), None)
                if bad:
                    dropped += 1
                    self.note_use(ln["speaker"], "prop_slip", "model")
                    continue
            out.append(ln)
        if dropped:
            self.log_event(tick, {"type": "system", "who": lines[0]["speaker"], "room": room, "vis": "gm",
                                  "text": f"{dropped} action line(s) in the {w.room_name(room)} named an object nobody had and were dropped."})
        return out


def lockable_room(room):
    return room in ROOMS and ROOMS[room][1] not in ("grounds", "roof") and room not in ("voting_grounds", "core_vault")
