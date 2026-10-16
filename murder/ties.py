"""Relationship ties: why people feel the way they do about each other, taken from what actually happened.

Feelings (affinity) are numbers; ties are the reasons. Every real event between two people (a rescue, a slight, a gift, a search, an accusation, a betrayal, a night spent together) adds a
short tie that both shapes how they treat each other and gives the dialogue something true to refer to. In a new game nobody starts with ties; people are strangers who become something.
TiesMixin is mixed into DayRunner (engine.py).
"""

MAX_PER_PAIR = 6


def _hh(h):
    return f"{int(h):02d}:00"


class TiesMixin:
    def add_tie(self, a, b, kind, text, delta=0):
        """a feels this way about b because of what happened (text). Optionally moves a's affinity toward b."""
        w, s = self.world, self.s
        if a == b or a not in w.agents:
            return
        ties = s.setdefault("ties", [])
        if any(t["a"] == a and t["b"] == b and t["kind"] == kind and t["text"] == text for t in ties):
            return
        ties.append({"a": a, "b": b, "kind": kind, "text": text[:110], "day": self.day})
        mine = [t for t in ties if t["a"] == a and t["b"] == b]
        for old in mine[:-MAX_PER_PAIR]:
            ties.remove(old)
        if len(ties) > 160:
            del ties[:len(ties) - 160]
        if delta and b in w.agents:
            self.adjust_any_aff(a, b, delta)

    def ties_about(self, a, b):
        return [t for t in self.s.get("ties", []) if t["a"] == a and t["b"] == b]

    def relationship_label(self, a, b):
        kinds = [t["kind"] for t in self.ties_about(a, b)]
        if "wronged" in kinds or "betrayed" in kinds:
            return "someone who wronged you"
        if "allied" in kinds and "betrayed" not in kinds:
            return "an ally"
        if "helped" in kinds:
            return "someone who helped you"
        if "slighted" in kinds and kinds.count("slighted") >= 2:
            return "someone who keeps wearing you down"
        if "close" in kinds:
            return "someone you have grown close to"
        return ""

    def tie_lines(self, cid):
        """The reasons behind your feelings about the people who matter right now."""
        w = self.world
        if cid not in w.agents:
            return []
        here = [o for o in w.occupants(w.agents[cid]["room"]) if o in w.agents and o != cid]
        pairs = {}
        for t in self.s.get("ties", []):
            if t["a"] == cid and t["b"] in w.agents:
                pairs.setdefault(t["b"], []).append(t)
        if not pairs:
            return []
        order = sorted(pairs, key=lambda o: (o not in here, -len(pairs[o])))
        bits = []
        for o in order[:3]:
            texts = "; ".join(t["text"] for t in pairs[o][-2:])
            lab = self.relationship_label(cid, o)
            bits.append(f"{self.nm(o)}{' (' + lab + ')' if lab else ''}: {texts}")
        return ["WHY YOU FEEL AS YOU DO (what actually happened between you): " + " | ".join(bits) + ". Let it colour how you treat them and refer to it naturally."]

    def card_ties(self, pid, group):
        """A short note for the conversation card: the one tie that matters most with someone in the room."""
        w = self.world
        bits = []
        for o in group:
            if o == pid or o not in w.agents:
                continue
            ts = self.ties_about(pid, o)
            if ts:
                bits.append(f"toward {self.nm(o)}: {ts[-1]['text']}")
        return (" History: " + "; ".join(bits[:3]) + ".") if bits else ""
