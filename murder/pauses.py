"""GM pause hooks: at a high-stakes roll the engine can stop and ask the GM to encourage, discourage, or let the dice decide.

The rolls that can pause: a plotter deciding whether to strike now, a witness deciding whether to speak at the trial (only for strong
facts), and someone deciding whether to betray an ally. Which ones pause is a viewer setting (Director panel); a live session passes the
question to the viewer and waits, up to a timeout, for an answer. Encourage and discourage move the chance by the `gm_nudge` dial
(default 0.25); they never force the outcome, which is clamped short of certain either way. With no GM listening (tests, mock seasons,
replays) nothing pauses and the chance is unchanged. A test or a batch run can set `roll_policy` to answer every question itself.
PauseMixin is mixed into DayRunner (engine.py).
"""

ROLL_KINDS = {"strike": "a plotter deciding whether to strike", "witness": "a witness deciding whether to speak at the trial",
              "betray": "someone deciding whether to betray an ally"}


class PauseMixin:
    def gm_roll(self, kind, p, who=None, about=None, text=""):
        """Ask the GM about a deciding roll. Returns the (possibly shifted) chance; the caller rolls it."""
        ask = self.__dict__.get("roll_policy") or self.__dict__.get("_ask_gm")
        if not ask or kind not in ROLL_KINDS:
            return p
        q = {"kind": kind, "who": who, "about": about, "text": text, "p": round(float(p), 2), "day": self.day, "hour": self.s.get("_hour", 12)}
        try:
            ans = ask(q)
        except Exception:  # a GM that does not answer never stalls the game
            ans = None
        if ans not in ("encourage", "discourage"):
            return p
        shift = float(self.tune("gm_nudge"))
        newp = max(0.03, min(0.97, p + shift if ans == "encourage" else p - shift))
        log = self.s.setdefault("gm_rolls", [])
        log.append({**q, "answer": ans, "to": round(newp, 2)})
        del log[:-40]
        self.__dict__.setdefault("_roll_notes", []).append(f"GM {ans}d {text or kind}: {int(p * 100)}% → {int(newp * 100)}%")
        return newp

    def flush_roll_notes(self, tick):
        for n in self.__dict__.pop("_roll_notes", []):
            self.log_event(tick, {"type": "director", "who": "terevi", "room": "foyer", "vis": "gm", "text": n})
