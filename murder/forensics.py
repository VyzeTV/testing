"""More kinds of evidence at a crime scene, drawn from what actually happened: where the culprit came from, how doors were opened, who could have had a key, whether the victim was
asleep, what they carried that left a trace, and whether the victim had been troubled before the death. None of it names the killer; together it narrows the field.
ForensicsMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS

FIBRE_ITEMS = {"scarf", "jacket", "fedora", "outfit", "apron", "maid_uniform", "towels", "rags", "bed_sheets", "cardigan", "tote_bag", "sunglasses"}
SOLVENT_TAGS = {"flammable", "poison"}


def _hh(h):
    return f"{int(h):02d}:00"


class ForensicsMixin:
    def log_door(self, room, kind, by, tool=None):
        s = self.s
        s.setdefault("door_log", []).append({"room": room, "kind": kind, "by": by, "tool": tool, "day": self.day, "hour": s.get("_hour", 12)})
        del s["door_log"][:-40]

    def key_holders(self, room):
        """Everyone who could open a locked room: whoever sleeps there, whoever locked it, and holders of a master, skeleton or spare key."""
        w, s = self.world, self.s
        out = []
        for c, a in w.agents.items():
            if (w.cast.get(c, {}).get("home") == room or a["inv"].get(f"key_{room}", 0) > 0 or a["inv"].get("master_key", 0) > 0 or a["inv"].get("skeleton_keys", 0) > 0
                    or (s.get("locks", {}).get(room) or {}).get("by") == c):
                out.append(c)
        return out

    def forensic_clues(self, case, tick):
        w, s = self.world, self.s
        culprit, victim, room, hour = case["killer"], case["victim"], case["room"], case["hour"]
        if not culprit or case["kind"] in ("suicide", "accident"):
            return []
        out = []
        rn = w.room_name

        def add(kind, text):
            out.append({"room": room, "scene": True, "found_by": [], "kind": kind, "text": text})

        mv = (tick.get("moves") or {}).get(culprit) or {}
        came = mv.get("from")
        if came and came != room and came in ROOMS and ROOMS[came][1] == "grounds" and ROOMS[room][1] != "grounds" and self.rng.random() < 0.7:
            add("footprints", f"Damp, gritty footprints lead in from outside: whoever did this came in from the grounds, not from the corridor.")
        if s.get("locks", {}).get(room) and self.rng.random() < 0.9:
            add("door_lock", f"The door of the {rn(room)} was locked and was not forced.")
            names = ", ".join(self.nm(c) for c in self.key_holders(room)[:5])
            add("keyholders", f"Who could open the {rn(room)} without breaking in: {names or 'nobody'}, and anyone with the master or skeleton keys.")
        recent = [d for d in s.get("door_log", []) if d["room"] == room and (self.day - d["day"]) * 24 + hour - d["hour"] <= 12]
        for d in recent[-2:]:
            if d["kind"] == "picked":
                add("door_picked", f"Fine scratches ring the lock of the {rn(room)}: it was picked, by someone with the right tool" + (f" (something thin, such as wire)" if d.get("tool") in ("wire", "lockpicks", "piano_wire") else "") + ".")
            elif d["kind"] == "broken":
                add("door_forced", f"The door of the {rn(room)} was forced: the frame is splintered. It would have been loud.")
        if (w.all_agents.get(victim, {}).get("asleep") or w.all_agents.get(victim, {}).get("out")) and self.rng.random() < 0.9:
            add("unwoken", f"There are no defensive wounds: {self.nm(victim)} never woke up.")
        inv = w.agents[culprit]["inv"] if culprit in w.agents else {}
        fib = [k for k in inv if k in FIBRE_ITEMS]
        if fib and self.rng.random() < 0.4:
            it = self.rng.choice(fib)
            add("fibres", f"A few fibres, the kind that come from a {w.item_name(it).lower()}, are caught on the doorframe.")
        solv = [k for k in inv if set(w.item_spec(k).get("tags", [])) & SOLVENT_TAGS]
        if solv and self.rng.random() < 0.3:
            add("smell", f"A faint chemical smell hangs in the air, like {w.item_name(self.rng.choice(solv)).lower()}.")
        missing = [k for k in (f"key_{room}",) if any(a["inv"].get(k, 0) > 0 for c, a in w.agents.items() if c != victim)]
        if missing and self.rng.random() < 0.6:
            add("missing_key", f"The spare key for the {rn(room)} is not where it is kept: someone has taken it.")
        for h in s.get("hooks", []):
            if victim in h["victims"] and h["status"] in ("open", "faded") and self.rng.random() < 0.9:
                add("prior_hook", f"{self.nm(victim)} had been uneasy in the days before: \"{h['text']}\" It may or may not be connected.")
                break
        out = out[:5] + self.env_clues(case)
        return out[:7]
