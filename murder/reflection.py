"""Structured reflection: the nightly diary also makes choices the engine applies.

The diary stays free prose, but each night's reflection may also pick up to three choices from a fixed menu:
* trust: "I no longer trust Ayden" (feelings drop and they are less open to what Ayden says) or "I trust Seul again";
* protect: "I'll protect Seul" (for three days: more likely to step in when Seul is attacked, and they keep an eye on Seul);
* reread: "Noah's joke was a threat" (a belief that Noah is dangerous, and a fear thought);
* resolve: "Tomorrow I confront Chloe" (confront, apologise, ask or thank: someone they want to talk to tomorrow).
The drive change the reflection already makes stays as it was. A model answer's choices are checked against the menu and the living cast;
without a model (or when it gives none), the engine makes the same kinds of choices from thresholds: trust drops after a proven lie or a
betrayal, rises after being helped; someone dear in danger is protected; a low mind rereads a slight as a threat; a hurt is confronted
or a wrong apologised for. ReflectionMixin is mixed into DayRunner (engine.py).
"""

MENU = ("trust", "protect", "reread", "resolve")
RESOLVE = ("confront", "apologise", "ask", "thank")
MAX_CHOICES = 3


class ReflectionMixin:
    def reflect_menu(self, cid):
        """The instruction the reflection prompt carries (chaos.reflect_prompt)."""
        w = self.world
        ids = ", ".join(f"{o}={self.nm(o)}" for o in sorted(w.agents) if o != cid)
        return (' Also pick 0 to 3 "choices" that today really changed, from this menu only: {"kind": "trust", "about": id, "dir": "down" or "up"}, '
                '{"kind": "protect", "about": id}, {"kind": "reread", "about": id} (something they did now reads as a threat), '
                '{"kind": "resolve", "about": id, "act": "confront" or "apologise" or "ask" or "thank"} (what they will do tomorrow). '
                'Existing commitments persist. Add a concrete "reason" to replace a protection vow or unfinished intention; omission keeps it. '
                f"People: {ids}.")

    def valid_choices(self, cid, raw):
        w = self.world
        out = []
        for c in raw if isinstance(raw, list) else []:
            if not isinstance(c, dict) or c.get("kind") not in MENU or c.get("about") not in w.agents or c.get("about") == cid:
                continue
            if c["kind"] == "trust" and c.get("dir") not in ("up", "down"):
                continue
            if c["kind"] == "resolve" and c.get("act") not in RESOLVE:
                continue
            if any(o["kind"] == c["kind"] and o["about"] == c["about"] for o in out):
                continue
            out.append({k: c[k] for k in ("kind", "about", "dir", "act", "reason") if k in c})
        return out[:MAX_CHOICES]

    def threshold_choices(self, cid):
        """The engine's own choices for the night, from what happened today."""
        w, s = self.world, self.s
        a = w.agents[cid]
        today = self.day * 24
        out = []
        liars = [b["s"] for b in self.beliefs(cid) if b["k"] == "lied" and b.get("t0", 0) >= today - 1 and b["s"] in w.agents]
        betrayers = [t["b"] for t in s.get("ties", []) if t["a"] == cid and t["kind"] in ("betrayed", "wronged") and t.get("day") == self.day and t["b"] in w.agents]
        for x in (liars + betrayers)[:1]:
            out.append({"kind": "trust", "about": x, "dir": "down"})
        helpers = [t["b"] for t in s.get("ties", []) if t["a"] == cid and t["kind"] == "helped" and t.get("day") == self.day and t["b"] in w.agents]
        if helpers and not any(o["about"] == helpers[0] for o in out):
            out.append({"kind": "trust", "about": helpers[0], "dir": "up"})
            out.append({"kind": "resolve", "about": helpers[0], "act": "thank"})
        dear = [o for o in sorted(w.agents) if o != cid and a["aff"].get(o, 0) >= 8]
        for o in dear:
            b = w.agents[o]
            if b["hp"] < 60 or b["sanity"] < 30 or any(r[1] == self.day for r in b.get("harmed_by") or []):
                out.append({"kind": "protect", "about": o})
                break
        hurt_by = [r[0] for r in (a.get("harmed_by") or []) if r[1] == self.day and r[0] in w.agents]
        if hurt_by and a["sanity"] < 35:
            out.append({"kind": "reread", "about": hurt_by[-1]})
        if hurt_by and self.facet(cid, "courage") >= 60 and self.facet(cid, "anger") >= 50:
            out.append({"kind": "resolve", "about": hurt_by[-1], "act": "confront"})
        else:
            wronged = [t["a"] for t in s.get("ties", []) if t["b"] == cid and t["kind"] == "wronged" and t.get("day") == self.day and t["a"] in w.agents]
            if wronged and self.facet(cid, "altruism") >= 45:
                out.append({"kind": "resolve", "about": wronged[-1], "act": "apologise"})
        return self.valid_choices(cid, out)

    def apply_choices(self, cid, tick, choices):
        w, s = self.world, self.s
        a = w.agents[cid]
        nm = self.nm
        done = []
        for c in choices:
            x, k = c["about"], c["kind"]
            if k == "trust" and c["dir"] == "down":
                w.adjust_aff(cid, x, -1)
                a.setdefault("distrust", {})[x] = self.day
                txt = f"{nm(cid)} no longer trusts {nm(x)}."
            elif k == "trust":
                from .relationships import earn_trust, trust, wary
                w.adjust_aff(cid, x, 1)
                now = self.commitments.now(tick)
                earn_trust(s, cid, x, now)
                if wary(s, cid, x, now) or trust(s, cid, x) < 2:
                    txt = f"{nm(cid)} trusts {nm(x)} a little more, but remains cautious."
                else:
                    again = a.get("distrust", {}).pop(x, None) is not None
                    txt = f"{nm(cid)} decides to trust {nm(x)} again." if again else f"{nm(cid)} trusts {nm(x)} a little more."
            elif k == "protect":
                previous = {o["id"] for o in self.commitments.active(cid)}
                vow = self.commitments.request(tick, cid, {"kind": "protect", "target": x, "hours": 72, "reason": c.get("reason")})
                if not vow or vow["id"] in previous:
                    continue
                a["want_talk"] = {"who": [x], "day": self.day + 1, "why": f"keep an eye on {nm(x)}"}
                txt = f"{nm(cid)} resolves to protect {nm(x)}."
            elif k == "reread":
                self.believe(cid, {"k": "rumor", "s": x, "n": f"{nm(x)} is dangerous; what they did today was a threat", "src": "inferred", "c": 0.6,
                                   "t0": self.abs_now(), "true": self.dangerous(x), "reread": True})
                if self.mind_on():
                    self._thought(self.mind(cid), -3, f"afraid of {nm(x)}")
                txt = f"{nm(cid)} now reads {nm(x)} as a threat."
            else:
                why = {"confront": f"confront {nm(x)}", "apologise": f"apologise to {nm(x)}", "ask": f"ask {nm(x)} what is really going on",
                       "thank": f"thank {nm(x)}"}[c["act"]]
                previous = {o["id"] for o in self.commitments.active(cid)}
                intention = self.commitments.request(tick, cid, {"kind": c["act"], "target": x, "hours": 24, "reason": c.get("reason")})
                if not intention or intention["id"] in previous:
                    continue
                intention.setdefault("not_before", (self.day + 1) * 24 + 8)
                a["want_talk"] = {"who": [x], "day": self.day + 1, "why": why, "commitment_id": intention["id"]}
                txt = f"{nm(cid)} plans to {why} tomorrow."
            done.append(txt)
            st = s.setdefault("reflect_stats", {})
            st[k] = st.get(k, 0) + 1
        if done:
            tick["events"].append({"type": "drive", "who": cid, "room": a["room"], "vis": "gm", "text": "Reflection: " + " ".join(done)})
        return done

    def reflect_choices(self, cid, tick, r):
        """The night's choices: the model's, checked, or the engine's own when the model gives none."""
        if cid not in self.world.agents:
            return []
        got = self.valid_choices(cid, (r or {}).get("choices")) if isinstance(r, dict) else []
        if not got:
            got = self.threshold_choices(cid)
        return self.apply_choices(cid, tick, got)

    def dangerous(self, x):
        """Is the reread right? Someone who has killed or is plotting a death."""
        return x in (self.s.get("plots") or {}) or self.s.get("stats", {}).get(x, {}).get("kills", 0) > 0

    def committed_to(self, cid, x):
        for c in self.commitments.active(cid):
            if c["kind"] in ("protect", "pact") and c.get("target") == x and (c["due"] is None or self.commitments.now() < c["due"]):
                return True
        c = (self.world.agents.get(cid) or {}).get("commit") or {}
        return not c.get("commitment_id") and c.get("protect") == x and self.day <= c.get("until", 0)
