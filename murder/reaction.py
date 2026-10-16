"""The reaction pass, and explicit conflict resolution.

Decisions are still made in parallel from one snapshot (cheap), but:
  - the order in which they are applied is by initiative (calm, healthy, quick people go first), not a coin toss, and a person whose action was pre-empted is told so;
  - when something dramatic happens in a room during a turn, the people there get one quick reaction before the turn ends (flee, help, comfort, confront, hide, shout).
ReactMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS
from .stealth import COVER

SHOCKS = {"attack", "assault", "madness", "outburst", "sabotage", "body", "punish", "frisk", "breakin"}
REACTIONS = {"stay", "flee", "help", "comfort", "confront", "hide", "alert"}
MAX_REACTORS = 4


def _hh(h):
    return f"{int(h):02d}:00"


class ReactMixin:
    # ------------------------------------------------------------------ conflict resolution
    def initiative(self, cid):
        a = self.world.agents[cid]
        base = 0.5 * self.success_p(cid, 1.0) + 0.25 * (a["sanity"] / 100) + 0.25 * (a["hp"] / 100)
        return base + (0.1 if a["drive"]["id"] in ("survivor", "schemer") else 0.0)

    def apply_order(self, ids):
        """Who acts first when two people want the same thing: the quick and level-headed, with some luck."""
        return sorted(ids, key=lambda c: -(self.initiative(c) + self.rng.uniform(0, 0.35)))

    def stale_notices(self, decisions):
        """Someone who set out to talk to a person who has since gone elsewhere is told so (instead of a silent mismatch)."""
        w = self.world
        for cid, d in decisions.items():
            if cid not in w.agents:
                continue
            for t in d.get("talk_to", []):
                if t in w.agents and w.agents[t]["room"] != w.agents[cid]["room"] and self.rng.random() < 0.6:
                    w.remember(cid, f"{_hh(self.s.get('_hour', 12))} You went looking for {self.nm(t)} but they were not there.")

    # ------------------------------------------------------------------ the reaction pass
    def reaction_pass(self, tick, hour):
        w = self.world
        if self.lean or self.should_stop():
            return
        rooms = {}
        for e in tick["events"]:
            if e.get("type") in SHOCKS and e.get("room") in ROOMS:
                rooms.setdefault(e["room"], []).append((e.get("who"), e["text"][:150]))
        if not rooms:
            return
        said = {}
        for g in tick["talk"]:
            for l in g["lines"]:
                said.setdefault(g.get("room"), []).append(f"{self.nm(l['speaker'])}: {l['text'][:80]}")
        reactors = []
        for room, evs in rooms.items():
            actors = {x for x, _ in evs}
            for o in w.occupants(room):
                if o in w.agents and o not in actors and not w.agents[o].get("asleep"):
                    reactors.append((o, room, evs))
        self.rng.shuffle(reactors)
        done = 0
        for cid, room, evs in reactors[:MAX_REACTORS]:
            if cid not in w.agents or w.agents[cid]["room"] != room:
                continue
            self.react_one(tick, cid, room, evs, said.get(room, [])[-3:], hour)
            done += 1
        return done

    def react_one(self, tick, cid, room, evs, talk, hour):
        w = self.world
        a = w.agents[cid]
        humans = [o for o in w.occupants(room) if o in w.agents and o != cid]
        reach = list(w.reachable_rooms(cid, 40 * self.step).keys())
        ctx = {"cid": cid, "room": room, "humans": humans, "reachable": [r for r in reach if r != room], "hour": hour}
        user = (f"A MOMENT, not a full turn. Day {self.day}, {_hh(hour)}, {w.room_name(room)}.\n"
                f"JUST NOW: {' | '.join(t for _, t in evs)}\n"
                + (f"JUST SAID: {' / '.join(talk)}\n" if talk else "")
                + f"YOU: health {a['hp']}/100, sanity {a['sanity']}/100 (you feel {self.mood_text(a)}). "
                  f"Others here: {', '.join(f'{o}={self.nm(o)} ({a['aff'].get(o, 0):+d})' for o in humans) or 'nobody'}. "
                  f"Rooms you could run to: {', '.join(f'{r}={w.room_name(r)}' for r in ctx['reachable'][:8]) or 'none'}.\n"
                "React in the next few seconds, in character, as this person would. Options: stay (freeze or watch), flee (to_room), help (target: someone hurt), "
                "comfort (target), confront (target: say it to their face), hide (if there is cover), alert (shout for the others).\n"
                'Reply as JSON: {"reaction": "stay|flee|help|comfort|confront|hide|alert", "target": "<person id or empty>", "to_room": "<room id or empty>", '
                '"line": "<what you say aloud, max 18 words, plain and human, or empty>", "act": "<a short verb phrase for what you physically do, or empty>", "thought": "<private, max 15 words>"}')
        try:
            r = self.llm.react(self.system_prompt(cid), user, ctx)
        except Exception as e:
            if getattr(e, "fatal", False):
                raise
            return
        kind = r.get("reaction") if r.get("reaction") in REACTIONS else "stay"
        tgt = r.get("target") if r.get("target") in w.agents and r.get("target") != cid else None
        line = str(r.get("line") or "").strip()[:140]
        act = str(r.get("act") or "").strip()[:80]
        name = self.nm(cid)
        witnesses = humans
        parts = []
        if kind == "flee":
            to = r.get("to_room") if r.get("to_room") in ctx["reachable"] else (ctx["reachable"][0] if ctx["reachable"] else None)
            if to:
                before = a["room"]
                mv = w.move(cid, to, 40 * self.step)
                if a["room"] != before:
                    tick["moves"].setdefault(cid, {"from": before, "path": [before], "to": before})
                    tick["moves"][cid]["path"] = tick["moves"][cid].get("path", [before]) + mv["path"][1:]
                    tick["moves"][cid]["to"] = a["room"]
                    parts.append(f"bolts for the {w.room_name(a['room'])}")
                    for o in humans:
                        self.witness(o, {"type": "leave", "who": cid, "room": before, "to": a["room"], "hour": hour})
        elif kind == "hide" and COVER.get(room) and not a.get("hiding"):
            self.do_hide(tick, cid, {})
            parts.append("ducks out of sight")
        elif kind == "help" and tgt and w.agents[tgt]["room"] == room:
            kit = next((k for k in ("first_aid_kit", "bandages") if a["inv"].get(k, 0) > 0), None)
            gain = 10 if kit else 4
            if kit:
                a["inv"][kit] -= 1
                if a["inv"][kit] <= 0:
                    del a["inv"][kit]
            w.agents[tgt]["hp"] = min(100, w.agents[tgt]["hp"] + gain)
            w.adjust_aff(tgt, cid, 1)
            self.add_tie(tgt, cid, "helped", f"{name} came to their aid when it counted", 1)
            parts.append(f"drops beside {self.nm(tgt)} to help" + (f" with the {w.item_name(kit)}" if kit else ""))
        elif kind == "comfort" and tgt and w.agents[tgt]["room"] == room:
            self.special_boost(tick, tgt, 2, "was held together by someone", "comfort")
            w.adjust_aff(tgt, cid, 1)
            self.add_tie(tgt, cid, "helped", f"{name} steadied them when they were shaking", 1)
            parts.append(f"goes to {self.nm(tgt)} and steadies them")
        elif kind == "confront" and tgt and w.agents[tgt]["room"] == room:
            self.adjust_any_aff(tgt, cid, -1)
            self.adjust_any_aff(cid, tgt, -1)
            self.add_tie(tgt, cid, "slighted", f"{name} rounded on them in front of everyone", 0)
            parts.append(f"rounds on {self.nm(tgt)}")
        elif kind == "alert":
            for n in w.adjacent(cid, room):
                for o in w.occupants(n["room"]):
                    if o in w.agents and o != cid and not w.agents[o].get("asleep"):
                        w.remember(o, f"{_hh(hour)} (heard) {name} shouting from the {w.room_name(room)}.")
            parts.append("shouts for help")
        if act and not parts:
            parts.append(act.rstrip("."))
        text = (f"{name} {', '.join(parts)}" if parts else f"{name} freezes") + (f': "{line}"' if line else ".")
        self.log_event(tick, {"type": "reaction", "who": cid, "room": a["room"], "vis": "public", "text": text}, witnesses=witnesses, actor=cid)
        th = str(r.get("thought") or "")[:120]
        if th:
            tick["thoughts"][cid] = (tick["thoughts"].get(cid, "") + " | " + th).strip(" |")
