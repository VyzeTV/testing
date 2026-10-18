"""Story sifting: patterns over the state that spot stories forming, shown to the GM as "stories in play" and used by the auto-director.

Each pattern reads what the engine already keeps (feelings, ties, beliefs, secrets, plots, alliances, the case, the ways out) and names a
story with the people in it and a heat (how close it is to something happening). Nothing here changes the game and nothing uses chance:
sifting runs once per tick, after the turn (emit), and only records. Stories carry a stable key, so the GM sees how long one has been
building; a story that no longer matches is marked over. SiftingMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ESCAPE_ROUTES

MAX_SHOWN = 10


class SiftingMixin:
    def sift_stories(self):
        """[(key, kind, people, text, heat)] for every story forming right now."""
        w, s = self.world, self.s
        A = w.agents
        ids = sorted(A)
        nm = self.nm
        aff = lambda x, y: A[x]["aff"].get(y, 0) if x in A else 0
        out = []

        def add(kind, people, text, heat):
            out.append(("|".join([kind] + sorted(people)), kind, list(people), text, round(heat, 2)))

        # love: a triangle, or a love that is not returned
        for a in ids:
            others = [o for o in ids if o != a]
            if not others:
                continue
            b = max(others, key=lambda o: (aff(a, o), o))
            if aff(a, b) < 7:
                continue
            rest = [o for o in ids if o not in (a, b)]
            c = max(rest, key=lambda o: (aff(b, o), o)) if rest else None
            if c and aff(b, c) >= 7 and aff(b, c) > aff(b, a):
                add("triangle", [a, b, c], f"{nm(a)} loves {nm(b)}, who only has eyes for {nm(c)}.", 0.6 + 0.04 * (aff(a, b) - 7))
            elif aff(b, a) <= 0:
                add("unrequited", [a, b], f"{nm(a)} has fallen for {nm(b)}, who feels nothing of the kind.", 0.4)
        # two people who hate each other, both alone right now
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                if aff(a, b) <= -5 and aff(b, a) <= -5:
                    alone = [x for x in (a, b) if not [o for o in w.occupants(A[x]["room"]) if o in A and o != x]]
                    if len(alone) == 2:
                        add("enemies_alone", [a, b], f"{nm(a)} and {nm(b)} hate each other, and both are alone right now.", 0.7)
        # betrayal of someone who was protecting a third
        for t in s.get("ties", []):
            if t["kind"] in ("betrayed", "wronged") and t["a"] in A and t["b"] in A:
                b, a = t["a"], t["b"]
                cared = [c for c in ids if c not in (a, b) and aff(b, c) >= 6]
                if cared:
                    c = max(cared, key=lambda x: (aff(b, x), x))
                    add("betrayed_protector", [a, b, c], f"{nm(a)} betrayed {nm(b)}, who has been protecting {nm(c)}.", 0.55)
        # someone holds a proven lie against a person they fear
        for a in ids:
            for bl in self.beliefs(a):
                x = bl.get("s")
                if bl["k"] == "lied" and bl["c"] >= 0.5 and x in A and x != a and (aff(a, x) <= -3 or any(r[0] == x for r in A[a].get("harmed_by") or [])):
                    add("contradiction_fear", [a, x], f"{nm(a)} knows {nm(x)} lied, and is afraid of {nm(x)}.", 0.6)
        # a secret held by someone the owner does not like
        for a in ids:
            for k in A[a].get("known_secrets", []):
                b = k.get("of")
                if b in A and b != a and aff(b, a) <= 0:
                    add("secret_held", [a, b], f"{nm(a)} holds {nm(b)}'s secret, and {nm(b)} has no love for {nm(a)}.", 0.55)
        # an alliance wearing thin
        for al in s.get("alliances", []):
            if al.get("status") != "active":
                continue
            mem = [m for m in al["members"] if m in A]
            for m in mem:
                for o in mem:
                    if o != m and aff(m, o) <= 0:
                        add("alliance_strain", [m, o], f"{nm(m)}'s loyalty to {nm(o)} in their alliance is wearing thin.", 0.5)
        # a plotter, and a target who has started to suspect them
        for x, p in sorted((s.get("plots") or {}).items()):
            t = p.get("target")
            if x in A and t in A:
                sus = any(bl.get("s") == x and bl["k"] in ("lied", "rumor", "has") for bl in self.beliefs(t))
                if sus:
                    add("plot_suspected", [x, t], f"{nm(t)} is starting to suspect {nm(x)}, who is planning to kill them ({p.get('stage')}).", 0.9)
                else:
                    add("plot", [x, t], f"{nm(x)} is planning to kill {nm(t)} ({p.get('stage')}).", 0.5 + (0.3 if p.get("stage") in ("stalking", "striking") else 0))
        # a witness the killer does not know about
        case = s.get("case")
        if case and case.get("killer") in A and not case.get("resolved"):
            k = case["killer"]
            t = self.case_time(case)
            for h in ids:
                if h == k:
                    continue
                if any(bl["k"] == "at" and bl.get("s") == k and bl.get("r") == case.get("room") and bl.get("true", True) and bl["t0"] - 0.75 <= t <= bl.get("t1", bl["t0"]) + 0.75
                       for bl in self.beliefs(h)):
                    add("silent_witness", [h, k], f"{nm(h)} saw {nm(k)} near the scene, and {nm(k)} does not know it.", 0.85)
        # lovers at breaking point
        for b in s.get("bonds", []):
            if b.get("kind") == "romance" and b["a"] in A and b["b"] in A and A[b["a"]]["sanity"] < 35 and A[b["b"]]["sanity"] < 35:
                add("lovers_breaking", [b["a"], b["b"]], f"{nm(b['a'])} and {nm(b['b'])} are holding on to each other, barely.", 0.5)
        # a grudge for an innocent voted to death
        for rec in s.get("vote_log", [])[-3:]:
            if not rec.get("wrongful"):
                continue
            acc = rec["accused"]
            for a in ids:
                if aff(a, acc) >= 5:
                    for v in rec["voters"]:
                        if v in A and v != a:
                            add("grudge", [a, v, acc], f"{nm(a)} has not forgiven {nm(v)} for voting {nm(acc)} to death.", 0.6)
        # a way out close to done
        for rid, rt in s.get("escape", {}).get("routes", {}).items():
            pct = self.route_pct(rid)
            if pct >= 75:
                team = [c for c in rt.get("contributors", []) if c in A][:3]
                add("near_freedom", team, f"The {ESCAPE_ROUTES[rid]['title'].lower()} is {pct}% done.", 0.4 + pct / 250)
        return out

    def sift_tick(self, tick):
        """Record the stories in play this tick (in state, for the GM view and the auto-director)."""
        s = self.s
        st = s.setdefault("stories", {})
        found = self.sift_stories()
        now = set()
        for key, kind, people, text, heat in found:
            now.add(key)
            ent = st.get(key)
            if ent is None or ent.get("status") == "over":
                st[key] = {"key": key, "kind": kind, "people": people, "text": text, "heat": heat, "since": [self.day, tick.get("hour", 12)], "status": "live"}
            else:
                ent.update(text=text, heat=heat, people=people)
        for key, ent in list(st.items()):
            if key not in now and ent.get("status") == "live":
                ent["status"] = "over"
                ent["until"] = [self.day, tick.get("hour", 12)]
        if len(st) > 120:
            for key in [k for k, e in sorted(st.items(), key=lambda kv: (kv[1].get("status") == "live", kv[1]["since"]))][:len(st) - 120]:
                del st[key]

    def stories_in_play(self, limit=MAX_SHOWN):
        st = (self.s.get("stories") or {}).values()
        return sorted([e for e in st if e.get("status") == "live"], key=lambda e: (-e["heat"], e["since"], e["key"]))[:limit]
