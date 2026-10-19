"""The chronicle: one typed, persistent record of everything that happens, built from the events each tick already produces.

Every entry is {id, day, hour, type, who, room, vis, cls, text, with?, seen?, ...}. It is only a record: nothing in the simulation reads it back yet, so
recording changes no behaviour (it uses no randomness). The viewer's Chronicle panel and, later, clues, hooks and trial evidence are views over it.
`cls` is the importance class used by the pause settings planned for the live edition: critical, important, notable, background.
ChronicleMixin is mixed into DayRunner (engine.py).
"""
import re

from .data_world import ROOMS

CRITICAL = {"body", "discover", "death", "verdict", "execution", "attack", "arrival", "reveal", "deadline", "case", "trial", "newcomer"}
IMPORTANT = {"fire", "flood", "wreck", "plot", "madness", "faint", "punish", "frame", "carry", "rob", "assault", "sabotage", "outburst", "island", "drive", "system_notable", "inspection", "condition", "snap", "raft", "flare"}
NOTABLE = {"interrogation", "friction", "hook", "alliance", "betrayal", "treat", "experiment", "occasion", "rumor", "secret", "lock", "give", "director", "tease", "hide", "frisk", "conceal", "stash", "craft", "reaction", "door", "embarrassed", "intrude", "snoop_caught"}
CHRON_MAX = 4000
BROADCAST_CRITICAL = {"verdict", "trial", "trial_open", "reveal", "deadline", "finale", "last_call", "endgame", "execution", "spree_death", "arrival"}


def chron_class(kind, vis, text=""):
    if kind in CRITICAL:
        return "critical"
    if kind == "broadcast":
        return "critical" if any(k in (text or "").lower() for k in ("dead", "trial", "verdict", "deadline", "reckoning")) else "notable"
    if kind in IMPORTANT:
        return "important"
    if kind in NOTABLE:
        return "notable"
    return "background"


def query_chronicle(log, day=None, who=None, kind=None, cls=None, q=None, gm=True, limit=300, after=0):
    out = []
    for e in log:
        if e["id"] <= after:
            continue
        if day is not None and e["day"] != day:
            continue
        if who and e.get("who") != who and who not in e.get("with", []) and who not in e.get("people", []):
            continue
        if kind and e["type"] != kind:
            continue
        if cls and e["cls"] != cls:
            continue
        if not gm and e["vis"] == "gm":
            continue
        if q and q.lower() not in e["text"].lower():
            continue
        out.append(e)
    return out[-limit:]


class ChronicleMixin:
    def chron_names(self):
        return {cid: re.compile(r"\b" + re.escape(self.nm(cid).split()[0]) + r"\b") for cid in self.world.cast}

    def chron_add(self, tick, kind, who, room, vis, text, witnesses=None, extra=None):
        """Append one entry to the persistent chronicle and to this tick's `chron` list."""
        s = self.s
        s["chron_seq"] = s.get("chron_seq", 0) + 1
        ent = {"id": s["chron_seq"], "day": self.day, "hour": tick.get("hour", 12), "type": kind, "who": who, "room": room, "vis": vis,
               "cls": chron_class(kind, vis, text), "text": text}
        names = getattr(self, "_chron_names", None)
        if names is None:
            names = self._chron_names = self.chron_names()
        with_ = [cid for cid, rx in names.items() if cid != who and rx.search(text or "")]
        if with_:
            ent["with"] = with_
        if witnesses:
            ent["seen"] = [c for c in witnesses if c != who][:8]
        if extra:
            ent.update(extra)
        log = s.setdefault("chronicle", [])
        log.append(ent)
        del log[:-CHRON_MAX]
        tick.setdefault("chron", []).append(ent)
        return ent

    def chron_flush(self, tick):
        """Turn everything this tick produced (events, announcements, conversations) into chronicle entries. Called from emit()."""
        side = getattr(self, "_chron_w", {})
        for evt in tick.get("events", []):
            wit, _actor = side.get(id(evt), (None, None))
            self.chron_add(tick, evt.get("type", "event"), evt.get("who"), evt.get("room"), evt.get("vis", "viewer"), evt.get("text", ""), witnesses=wit,
                           extra={k: evt[k] for k in ("cause", "m") if evt.get(k) is not None} or None)
        side.clear()
        for b in tick.get("broadcasts", []):
            bk = b.get("kind")
            self.chron_add(tick, "broadcast", b.get("speaker"), None, "public", b.get("text", "")[:400],
                           extra={"kind": bk, "cls": "critical" if bk in BROADCAST_CRITICAL else "important" if bk in ("tease", "occasion", "meddle") else "notable"})
        for g in tick.get("talk", []):
            lines = g.get("lines") or []
            speakers = []
            for ln in lines:
                if ln.get("speaker") not in speakers:
                    speakers.append(ln.get("speaker"))
            said = next((ln for ln in lines if ln.get("kind") == "say"), None)
            if not speakers:
                continue
            who = ", ".join(self.nm(c) if c in self.world.cast else str(c) for c in speakers)
            first = f' "{said["text"][:90]}"' if said else ""
            self.chron_add(tick, "talk", speakers[0], g.get("room"), "viewer", f"{who} talk in the {ROOMS[g['room']][0] if g.get('room') in ROOMS else g.get('room')}:{first}",
                           extra={"people": speakers, "lines": len(lines)})

    def chron_death(self, tick, case, desc, shown):
        """A plain statement of every death: what the cast can see, and (GM view) what actually happened."""
        w = self.world
        victim, culprit = case["victim"], case.get("killer")
        vname = self.nm(victim)
        room = case["room"]
        rn = w.room_name(room)
        kind = case["kind"]
        self.chron_add(tick, "death", victim, room, "public", f"{vname} is dead, found in the {rn}." if kind != "suicide" else f"{vname} took their own life in the {rn}.",
                       extra={"victim": victim, "kind": kind})
        if culprit and culprit in w.agents:
            how = {"murder": "murdered", "manslaughter": "killed"}.get(kind, "killed")
            self.chron_add(tick, "death", victim, room, "gm", f"TRUTH: {vname} was {how} by {self.nm(culprit)} ({desc}) in the {rn} around {int(case['hour']):02d}:00."
                           + (" The killer did not know it." if not case.get("culprit_aware", True) else "") + (" Staged: " + str(case.get("staged")) + "." if case.get("staged") else ""),
                           extra={"victim": victim, "killer": culprit, "kind": kind})
        else:
            self.chron_add(tick, "death", victim, room, "gm", f"TRUTH: {vname}'s death was {shown} (no culprit: {kind}).", extra={"victim": victim, "kind": kind})
