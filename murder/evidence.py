"""Evidence the cast can really have, and TereVi's Case File.

Footage: the house cameras are TereVi's. Nobody in the cast can see what they recorded, except through NeoVi, who has direct access to the archive and
may quietly show an investigator a still. Anyone else's "footage" has to come from a device of their own: a camera (GoPro, DSLR) or a tape recorder
set up and hidden in a room beforehand (it records who came and went, or what was said), then retrieved and played, or a camera in their own hands
at the moment. A line that cites footage the speaker cannot have is cut from what they say.

The Case File: when a death is announced, TereVi hands everyone a file, the first piece of evidence. It lists the victim, where and when they were
found, who found them, and (unless the show prefers to keep them hidden) the time and cause of death and the wounds. Facts start as known or
unknown; when an investigation turns one up (an autopsy-style clue, a witness, the weapon), the file is updated and everyone holding it is told.
Any piece of evidence can be updated the same way (`update_clue`). EvidenceMixin is mixed into DayRunner (engine.py).
"""
import re

CAMERA_ITEMS = ("gopro", "dslr")
FOOTAGE_RE = re.compile(r"\b(footage|cctv|surveillance|video|recordings?|on (?:the )?tape|camera archive|the cameras? (?:show|showed|shows|saw|caught|recorded|captured|prove|proves|placed)"
                        r"|(?:on|by) (?:the )?cameras?|cameras? (?:show|showed|shows|saw|caught|recorded|captured))\b", re.I)
FILE_FIELDS = ("victim", "found", "found_by", "time", "cause", "wounds", "weapon")


class EvidenceMixin:
    # ------------------------------------------------------------------ footage
    def has_footage(self, cid):
        """Can `cid` honestly cite a recording? A still from NeoVi, a tape or camera of their own they played, or a camera in their hands."""
        a = self.world.agents.get(cid) or {}
        if cid in ("terevi", "neovi"):
            return True
        if a.get("footage"):
            return True
        return any(a.get("inv", {}).get(k, 0) > 0 for k in CAMERA_ITEMS + ("tape_recorder",))

    def scrub_footage(self, cid, text):
        """Cut the sentences of `text` that cite footage `cid` cannot have. Returns the text (possibly shortened) or a plain fallback."""
        if not text or self.has_footage(cid) or not FOOTAGE_RE.search(text):
            return text
        parts = re.split(r"(?<=[.!?])\s+", text)
        keep = [p for p in parts if not FOOTAGE_RE.search(p)]
        self.s["footage_cut"] = self.s.get("footage_cut", 0) + 1
        return " ".join(keep).strip() or "I can't prove it. Not yet."

    def camera_record(self, room, entries):
        """A camera of someone's own, hidden in `room`, records who it sees (stash entries holding a camera)."""
        for st in self.s.get("stash", []):
            if st["room"] == room and any(k in st["items"] for k in CAMERA_ITEMS):
                reel = st.setdefault("reel", [])
                reel.extend(entries)
                del reel[:-16]

    def play_reel(self, tick, cid, st):
        reel = st.get("reel") or []
        if not reel:
            return
        w = self.world
        w.remember(cid, f"You watch what the hidden camera in the {w.room_name(st['room'])} recorded: " + " | ".join(reel[-6:]))
        for ln in reel[-4:]:
            self.note_evidence(cid, "clue", f"(camera in the {w.room_name(st['room'])}) {ln}", None)
        w.agents[cid]["footage"] = self.day

    def neovi_shares_footage(self, tick, hour):
        """During an announced case NeoVi may quietly show someone near her a still from TereVi's archive (the only way the cast sees it)."""
        w, s = self.world, self.s
        case = s.get("case")
        if not case or not case.get("announced") or case.get("resolved"):
            return None
        clue = next((c for c in case["clues"] if c.get("kind") == "ledger"), None)
        nroom = s["npcs"]["neovi"].get("room")
        if not clue or nroom in (None, "none") or self.rng.random() > 0.25:
            return None
        near = [c for c in sorted(w.occupants(nroom)) if c in w.agents and c not in clue["found_by"] and c != case.get("killer") and not w.agents[c].get("asleep")]
        if not near:
            return None
        cid = self.rng.choice(near)
        clue["found_by"].append(cid)
        w.agents[cid]["footage"] = self.day
        w.remember(cid, f"{hour % 24:02d}:00 CLUE (from NeoVi, in secret): {clue['text']}")
        self.note_evidence(cid, "clue", f"(NeoVi's still from the cameras) {clue['text']}")
        self.log_event(tick, {"type": "clue", "who": "neovi", "room": nroom, "vis": "viewer",
                              "text": f"NeoVi glances at the monitor, then quietly shows {self.nm(cid)} a still from TereVi's camera archive."})
        return cid

    # ------------------------------------------------------------------ the Case File
    def make_case_file(self, case, victim_name, room, shown, hour, time_text=None, found_by=None):
        """TereVi's Case File: the first piece of evidence. Facts start known, or hidden when the show prefers them hidden."""
        w = self.world
        staged = bool(case.get("staged"))
        f = {
            "victim": {"label": "Victim", "value": victim_name, "known": True},
            "found": {"label": "Found in", "value": f"the {w.room_name(room)}", "known": True},
            "found_by": {"label": "Found by", "value": ", ".join(self.nm(c) for c in (found_by or [])) or None, "known": bool(found_by)},
            "time": {"label": "Time of death", "value": time_text or f"around {hour % 24:02d}:00 on Day {self.day}, give or take two hours", "known": self.rng.random() >= 0.3},
            "cause": {"label": "Cause of death", "value": shown, "known": not staged and self.rng.random() >= 0.2},
            "wounds": {"label": "Wounds", "value": None, "known": False},
            "weapon": {"label": "Weapon", "value": None, "known": False},
        }
        case["cf"] = f
        case.setdefault("file_extra", [])
        case["file"] = self.render_case_file(case)
        return f

    def render_case_file(self, case):
        out = []
        for k in FILE_FIELDS:
            fact = (case.get("cf") or {}).get(k)
            if not fact:
                continue
            if fact["known"] and fact["value"]:
                out.append(f"{fact['label']}: {fact['value']}.")
            elif k in ("time", "cause"):
                out.append(f"{fact['label']}: withheld by TereVi.")
            else:
                out.append(f"{fact['label']}: unknown.")
        return out + list(case.get("file_extra") or [])

    def file_add(self, case, line):
        """An extra line in the Case File (a second victim, the blackout alibis...)."""
        ex = case.setdefault("file_extra", [])
        if line not in ex:
            ex.append(line)
        case["file"] = self.render_case_file(case) if case.get("cf") else list(case.get("file", [])) + ([line] if line not in case.get("file", []) else [])

    def file_set(self, case, field, value, known=False):
        cf = case.get("cf")
        if cf and field in cf:
            cf[field]["value"] = value
            cf[field]["known"] = cf[field]["known"] or known
            case["file"] = self.render_case_file(case)

    def file_learn(self, tick, field, value=None, why=""):
        """A fact in the Case File comes to light: the file is updated and everyone holding it is told."""
        case = self.s.get("case")
        cf = (case or {}).get("cf")
        if not cf or field not in cf or (cf[field]["known"] and (value is None or cf[field]["value"] == value)):
            return False
        if value is not None:
            cf[field]["value"] = value
        if not cf[field]["value"]:
            return False
        cf[field]["known"] = True
        case["file"] = self.render_case_file(case)
        line = f"{cf[field]['label']}: {cf[field]['value']}"
        case.setdefault("file_updates", []).append({"field": field, "day": self.day, "hour": tick["hour"], "why": why})
        if case.get("announced"):
            for c in self.world.agents:
                self.world.remember(c, f"TereVi's Case File was updated ({why}): {line}.")
                self.note_evidence(c, "file", "Case File update: " + line)
            self.log_event(tick, {"type": "clue", "who": "terevi", "room": "foyer", "vis": "viewer", "text": f"The Case File is updated: {line} ({why})."})
        return True

    def update_clue(self, tick, clue, new_text, why):
        """New facts about a piece of evidence: its description changes, and whoever found it is told."""
        if not clue or clue.get("text") == new_text:
            return False
        clue.setdefault("history", []).append(clue["text"])
        clue["text"] = new_text
        for c in clue.get("found_by") or []:
            if c in self.world.agents:
                self.world.remember(c, f"CLUE UPDATED ({why}): {new_text}")
                self.note_evidence(c, "clue", f"(updated: {why}) {new_text}")
        return True

    def learn_from_clue(self, tick, clue):
        """What a found clue tells the Case File: the scene gives the time and the wounds, the weapon names the weapon."""
        case = self.s.get("case")
        if not case or not case.get("cf"):
            return
        kind = clue.get("kind")
        if kind == "scene":
            self.file_learn(tick, "time", why="the body was examined")
            if case.get("wound_text"):
                self.file_learn(tick, "wounds", case["wound_text"], why="the body was examined")
        elif kind == "weapon" and case.get("weapon"):
            self.file_learn(tick, "weapon", f"a {self.world.item_name(case['weapon'])}", why="the weapon was found")
            if not case["cf"]["cause"]["known"]:
                self.file_learn(tick, "cause", why="the weapon was found")
