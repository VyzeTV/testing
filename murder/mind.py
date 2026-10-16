"""The mind of a character: personality facets, values, needs, and the thoughts that turn what happens into stress.

* Facets (0-100, 16 of them) and values (12) are derived once from each character's own description (persona, speech, candor, role, secret) with a small fixed per-character spread,
  so nothing is pre-set beyond what the cast sheets already say.
* Needs (social, rest, safety, purpose, privacy; 0-100, 100 = fully met) change with what actually happens each turn: company, sleep, danger, meaningful activity, time alone.
* Thoughts are the memory of events with weight: every change of sanity made anywhere in the engine is absorbed as a thought (bad ones weigh on the mind, good ones lift it) that
  fades over hours or days, bigger shocks lasting longer. Stress = weighted thoughts (scaled by stress vulnerability) + unmet needs. Sanity is the projection of the set point minus
  stress, so it recovers by itself when nothing new hurts and when needs are met, instead of only drifting down.
* `routine_decision` lets the engine decide quiet, routine turns from needs and relationships, so the model is asked only when something is at stake.
The tuning dials `mind` and `engine_decisions` (World group) switch these off (0). MindMixin is mixed into DayRunner (engine.py).
"""
import hashlib

from .data_world import ROOMS

FACETS = ["anger", "vengefulness", "trust", "gregariousness", "altruism", "assertiveness", "courage", "cruelty", "impulsiveness", "stress_vulnerability", "vanity", "ambition",
          "curiosity", "orderliness", "humour", "romantic"]
VALUES = ["loyalty", "law", "truth", "cooperation", "cunning", "friendship", "independence", "self_control", "competition", "romance", "knowledge", "tranquility"]
NEEDS = ["social", "rest", "safety", "purpose", "privacy"]
KW = {
    "anger": (("temper", "angry", "explosive", "hot-headed", "aggressive", "snap", "furious", "rage"), ("calm", "gentle", "patient", "serene")),
    "vengefulness": (("grudge", "revenge", "vengeful", "payback", "never forgives"), ("forgiving", "easygoing")),
    "trust": (("trusting", "naive", "sweet", "open", "friendly", "warm"), ("paranoid", "cynical", "suspicious", "guarded", "distrust", "secretive")),
    "gregariousness": (("loud", "social", "popular", "charming", "chatty", "idol", "talkative", "life of the party", "extrovert"), ("loner", "quiet", "shy", "introvert", "reclusive", "withdrawn", "private")),
    "altruism": (("kind", "caring", "protective", "helpful", "gentle", "generous", "selfless", "nurturing"), ("selfish", "manipulative", "cold", "callous", "exploit")),
    "assertiveness": (("bossy", "commanding", "leader", "blunt", "overbearing", "domineering", "confident"), ("timid", "soft-spoken", "meek", "submissive")),
    "courage": (("daring", "fearless", "brave", "reckless", "bold", "stunt"), ("anxious", "fearful", "timid", "claustrophobic", "cowardly", "afraid")),
    "cruelty": (("cruel", "sadistic", "ruthless", "cutting", "sharp-tongued", "vicious", "cold-blooded", "mean"), ("gentle", "kind", "tender")),
    "impulsiveness": (("impulsive", "reckless", "hothead", "dramatic", "chaotic", "spontaneous", "wild"), ("methodical", "careful", "calculating", "analytical", "deliberate", "cautious")),
    "stress_vulnerability": (("anxious", "fragile", "sensitive", "dramatic", "nervous", "panic", "insecure", "fear"), ("stoic", "composed", "unflappable", "resilient", "steady", "tough")),
    "vanity": (("idol", "vain", "fashion", "attention", "popular", "photogenic", "influencer", "image"), ("humble", "modest")),
    "ambition": (("ambitious", "driven", "prodigy", "competitive", "gamer", "champion", "star", "rising"), ("lazy", "aimless", "content")),
    "curiosity": (("curious", "explorer", "hacker", "inventor", "scientist", "tinker", "investigat"), ("incurious", "dull")),
    "orderliness": (("organized", "meticulous", "perfectionist", "tidy", "precise", "disciplined"), ("messy", "chaotic", "sloppy", "disorganized")),
    "humour": (("joker", "funny", "witty", "banter", "teasing", "jokes", "comedian", "playful"), ("humourless", "grim", "serious")),
    "romantic": (("flirt", "romantic", "charming", "babe", "seduc", "lover", "heartthrob"), ("aloof", "prude", "asexual")),
}
VKW = {
    "loyalty": ("loyal", "devoted", "protective", "faithful"), "law": ("rules", "law", "order", "disciplin", "duty"), "truth": ("honest", "truth", "blunt", "journalist", "documentary", "broadcast"),
    "cooperation": ("team", "cooperat", "together", "helpful", "choir", "band"), "cunning": ("manipul", "schem", "cunning", "trick", "hacker", "strateg", "secret"),
    "friendship": ("friend", "kind", "warm", "loyal", "social"), "independence": ("loner", "independent", "free", "private", "solo", "rebel"),
    "self_control": ("disciplin", "composed", "calm", "methodical", "stoic"), "competition": ("compet", "gamer", "champion", "rival", "prodigy", "win"),
    "romance": ("romantic", "flirt", "lover", "charming", "babe"), "knowledge": ("curious", "scien", "study", "hacker", "student", "explor", "learn"), "tranquility": ("calm", "peace", "quiet", "serene", "gentle"),
}
_cache = {}


def _h(*a):
    return int(hashlib.md5(repr(a).encode()).hexdigest()[:8], 16)


def derive_mind(cid, cast):
    """Facets and values from the character sheet. Deterministic: the same sheet always gives the same numbers."""
    text = " ".join(str(cast.get(k, "")) for k in ("persona", "speech", "candor", "role", "secret", "origin")).lower()
    facets = {}
    for f in FACETS:
        v = 50 + (_h(cid, f) % 21) - 10
        plus, minus = KW[f]
        v += 12 * min(2, sum(1 for k in plus if k in text)) - 12 * min(2, sum(1 for k in minus if k in text))
        facets[f] = max(5, min(95, v))
    values = {}
    for k in VALUES:
        v = 45 + (_h(cid, "v", k) % 21) - 10
        v += 14 * min(2, sum(1 for w in VKW[k] if w in text))
        values[k] = max(5, min(95, v))
    return facets, values


DESC = {"anger": ("quick to anger", "slow to anger"), "vengefulness": ("holds grudges", "forgives easily"), "trust": ("trusting", "distrustful"), "gregariousness": ("craves company", "a loner"),
        "altruism": ("looks after others", "looks after number one"), "assertiveness": ("pushes to be in charge", "keeps their head down"), "courage": ("bold", "easily frightened"),
        "cruelty": ("enjoys cutting people down", "dislikes hurting anyone"), "impulsiveness": ("acts on impulse", "thinks before acting"), "stress_vulnerability": ("cracks under pressure", "hard to rattle"),
        "vanity": ("cares how they look", "does not care about image"), "ambition": ("driven to win", "unambitious"), "curiosity": ("endlessly curious", "incurious"),
        "orderliness": ("orderly", "messy"), "humour": ("jokes constantly", "humourless"), "romantic": ("romantic and flirtatious", "cold toward romance")}
VDESC = {"loyalty": "loyalty", "law": "rules and order", "truth": "the truth", "cooperation": "working together", "cunning": "cleverness", "friendship": "friendship", "independence": "independence",
         "self_control": "self-control", "competition": "winning", "romance": "romance", "knowledge": "knowledge", "tranquility": "peace and quiet"}


class MindMixin:
    def mind_on(self):
        return bool(self.tune("mind"))

    def mind(self, cid):
        a = self.world.agents[cid]
        m = a.get("mind")
        if m is None:
            facets, values = derive_mind(cid, self.world.cast.get(cid, {}))
            m = a["mind"] = {"facets": facets, "values": values, "needs": {n: 70.0 for n in NEEDS}, "thoughts": [], "set": float(a["sanity"]), "proj": float(a["sanity"]), "pending": [], "stress": 0.0}
        return m

    def facet(self, cid, name):
        if cid not in self.world.agents:
            return 50
        return self.mind(cid)["facets"].get(name, 50)

    # ------------------------------------------------------------------ thoughts and stress
    def mind_note(self, cid, delta, why=""):
        """Called by stat() for every change of sanity: it becomes a thought at the next update."""
        a = self.world.agents.get(cid)
        if a is not None and delta and self.mind_on():
            self.mind(cid)["pending"].append((float(delta), why or "events"))

    def _thought(self, m, w, cause):
        mag = abs(w)
        if w < 0:
            ttl = 3 + int(mag / 1.6)
            ttl = min(30, ttl + (6 if mag >= 10 else 0))
        else:
            ttl = min(8, 2 + int(mag / 2))
        m["thoughts"].append({"c": cause[:60], "w": w, "t0": ttl, "t": ttl})
        if len(m["thoughts"]) > 60:
            m["thoughts"].sort(key=lambda t: -abs(t["w"]) * t["t"] / t["t0"])
            del m["thoughts"][40:]

    def stress_of(self, cid):
        m = self.mind(cid)
        sv = 0.55 + self.facet(cid, "stress_vulnerability") / 100.0          # 0.6 .. 1.5
        g = self.facet(cid, "gregariousness") / 50.0
        neg = sum(-t["w"] * t["t"] / t["t0"] for t in m["thoughts"] if t["w"] < 0)
        pos = sum(t["w"] * t["t"] / t["t0"] for t in m["thoughts"] if t["w"] > 0)
        needs = 0.0
        wts = {"social": 0.9 * g, "rest": 1.0, "safety": 1.3, "purpose": 0.8, "privacy": 0.8 * (2 - g)}
        for n, v in m["needs"].items():
            if v < 35:
                needs += (35 - v) * 0.22 * wts[n]
            elif v >= 85:
                needs -= (v - 85) * 0.12
        press = self.pressure() * 20 if self.revealed else 0.0          # the deadline looming over everyone
        total = (neg * sv + needs - pos * 0.8 + press * sv) * self.tune("stress_scale")
        return max(0.0, total), neg, pos, needs

    def mind_project(self, cid):
        """Set sanity from the mind. Anything that changed sanity since the last projection (stat() or a direct assignment) is first absorbed as thoughts."""
        a, m = self.world.agents[cid], self.mind(cid)
        pend, m["pending"] = m["pending"], []
        seen = 0.0
        for w, why in pend:
            self._thought(m, w, why)
            seen += w
        resid = (a["sanity"] - m["proj"]) - seen
        if abs(resid) >= 0.5:
            self._thought(m, resid, "events")
        stress = self.stress_of(cid)[0]
        m["stress"] = round(stress, 1)
        new = max(0.0, min(100.0, min(m["set"] + 6, 100.0) - stress))
        a["sanity"] = int(round(new))
        m["proj"] = float(a["sanity"])

    # ------------------------------------------------------------------ every turn
    def mind_tick(self, tick):
        if not self.mind_on():
            return
        w = self.world
        night = tick.get("phase") == "night"
        scale = 0.5 if night else 1.0
        talkers = {}
        for g in tick.get("talk", []):
            ppl = {ln.get("speaker") for ln in g.get("lines", [])} & set(w.agents)
            for c in ppl:
                talkers[c] = ppl - {c}
        danger = {}
        did = {}
        for e in tick.get("events", []):
            r, t = e.get("room"), e.get("type")
            if t in ("attack", "assault", "fire", "madness", "faint", "body", "punish", "flood", "island") and r:
                danger[r] = danger.get(r, 0) + (2 if t in ("attack", "fire", "body") else 1)
            if t in ("experiment", "craft", "build", "discover") and e.get("who"):
                did[e["who"]] = did.get(e["who"], 0) + 1
        for cid, a in list(w.agents.items()):
            m = self.mind(cid)
            n = m["needs"]
            g = self.facet(cid, "gregariousness")
            others = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid]
            # social
            if cid in talkers:
                liked = sum(1 for o in talkers[cid] if a["aff"].get(o, 0) >= 1)
                n["social"] = min(100, n["social"] + (18 + 6 * min(2, liked)) * scale)
                if liked:
                    self._thought(m, 2.0 + min(2, liked), "good company")
            else:
                n["social"] = max(0, n["social"] - (4 + 5 * g / 100) * scale)
            # rest
            if a.get("asleep") or night and a["room"] == w.cast[cid]["home"]:
                n["rest"] = min(100, n["rest"] + 25 * scale)
            else:
                n["rest"] = max(0, n["rest"] - (5 if not night else 3) * scale)
            if tick.get("hour", 12) >= 22 and not a.get("night_owl"):
                n["rest"] = min(100, n["rest"] + 35)
            # safety
            d = danger.get(a["room"], 0)
            if d:
                n["safety"] = max(0, n["safety"] - 14 * min(3, d))
            else:
                n["safety"] = min(100, n["safety"] + 7 * scale)
            if self.blackout_until >= self.idx and not others:
                n["safety"] = max(0, n["safety"] - 8)
            # purpose
            if did.get(cid):
                n["purpose"] = min(100, n["purpose"] + 28)
            else:
                n["purpose"] = max(0, n["purpose"] - 4 * scale)
            # privacy
            if not others:
                n["privacy"] = min(100, n["privacy"] + (10 + (100 - g) / 12) * scale)
            else:
                n["privacy"] = max(0, n["privacy"] - (2 + len(others) * 2 + (g < 40) * 3) * scale)
            for t in m["thoughts"]:
                t["t"] -= scale
            m["thoughts"] = [t for t in m["thoughts"] if t["t"] > 0]
            self.mind_project(cid)
            a["mind_view"] = self.mind_view(cid)

    def mind_view(self, cid):
        m = self.mind(cid)
        top = sorted(m["thoughts"], key=lambda t: -abs(t["w"]) * t["t"] / t["t0"])[:3]
        return {"stress": m["stress"], "needs": {k: int(v) for k, v in m["needs"].items()}, "thoughts": [[t["c"], round(t["w"] * t["t"] / t["t0"], 1)] for t in top]}

    # ------------------------------------------------------------------ what the character is told about themselves
    def mind_lines(self, cid):
        if not self.mind_on() or cid not in self.world.agents:
            return []
        m = self.mind(cid)
        out = []
        traits = [DESC[f][0] for f in FACETS if m["facets"][f] >= 72] + [DESC[f][1] for f in FACETS if m["facets"][f] <= 28]
        if traits:
            out.append("YOUR NATURE: " + ", ".join(traits[:6]) + ".")
        vals = sorted(m["values"], key=lambda k: -m["values"][k])[:2]
        out.append("YOU VALUE: " + " and ".join(VDESC[v] for v in vals) + ".")
        n = m["needs"]
        feel = []
        if n["social"] < 30:
            feel.append("lonely: you need company")
        if n["rest"] < 25:
            feel.append("exhausted: you need sleep")
        if n["safety"] < 30:
            feel.append("unsafe: you want walls, locks or allies around you")
        if n["purpose"] < 25:
            feel.append("useless: you need to get something done (a plan, an experiment, a search)")
        if n["privacy"] < 25:
            feel.append("crowded: you need time alone")
        mod = self.modesty(cid) if hasattr(self, "modesty") else 50
        if mod >= 70:
            out.append("YOU ARE MODEST: being seen in your underwear mortifies you; you cover up, dress, or stay out of sight.")
        elif mod <= 25:
            out.append("YOU ARE UNSELF-CONSCIOUS about your body: being seen in your underwear does not bother you.")
        if feel:
            out.append("YOU FEEL: " + "; ".join(feel) + ".")
        if m["stress"] >= 55:
            out.append("YOU ARE UNDER HEAVY STRESS: small things set you off.")
        return out

    # ------------------------------------------------------------------ engine-made decisions for quiet turns
    def engine_decisions_on(self):
        return bool(self.tune("engine_decisions")) and self.mind_on()

    def model_reason(self, cid, hour):
        """Why this turn needs the model, or None if the engine can decide it."""
        a, s, w = self.world.agents[cid], self.s, self.world
        if s.get("case") and _h(cid, self.day, hour, "case") % 2 == 0:
            return "case"
        if s.get("spree") or self.occasion_now:
            return "event"
        if self.env_lines(cid):
            return "hazard"
        rule = s.get("rule")
        if rule and rule.get("id") not in (None, "none"):
            return "rule"
        plots = s.get("plots", {})
        if plots.get(cid, {}).get("stage") in ("stalking", "striking") or any(p.get("target") == cid and p.get("stage") in ("stalking", "striking") for p in plots.values()):
            return "plot"
        brain = self.brain_on()
        if brain and self.revealed and self.plan_needed(cid, hour):
            return "plan"
        if (hour == 8 if brain else hour in (8, 20)) or not self.revealed:
            return "daystart"
        m = self.mind(cid)
        if m["stress"] >= 50 or min(m["needs"].values()) < 8:
            return "crisis"
        if m["needs"]["purpose"] < 20 and not (brain and self.plan_items(cid)):
            return "purpose"
        if a.get("conds") and any(c in a["conds"] for c in ("bleeding", "poisoned", "broken_leg", "broken_arm", "burned", "deranged", "panicking")):
            return "hurt"
        others = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid]
        if any(a["aff"].get(o, 0) <= -3 or w.agents[o]["aff"].get(cid, 0) <= -3 for o in others):
            return "conflict"
        if any(b for b in s.get("bonds", []) if cid in (b.get("a"), b.get("b"))) and others:
            return "bond"
        if not brain and _h(cid, self.day, hour) % 5 == 0:
            return "heartbeat"
        return None

    def needs_model(self, cid, hour):
        """Whether this turn is one the model should decide: anything at stake, a crisis, a plot, a rule, a case, the start and end of the day, and a regular heartbeat for variety."""
        if not self.engine_decisions_on():
            return True
        why = self.model_reason(cid, hour)
        if why:
            c = self.__dict__.setdefault("_why_model", {})
            c[why] = c.get(why, 0) + 1
        return why is not None

    def routine_decision(self, cid, hour):
        """A quiet turn decided from needs, time of day and relationships (no model call). Returns a cleaned decision."""
        w, a = self.world, self.world.agents[cid]
        m = self.mind(cid)
        n = m["needs"]
        g = self.facet(cid, "gregariousness") / 50.0
        imp = self.facet(cid, "impulsiveness") / 100.0
        home = w.cast[cid]["home"]
        here = a["room"]
        others = [o for o in w.occupants(here) if o in w.agents and o != cid]
        liked_here = [o for o in others if a["aff"].get(o, 0) >= 0]
        reach = set(w.reachable_rooms(cid, 40 * self.step).keys()) | {here}
        hungry = a.get("hunger", 0) >= 60 or a.get("thirst", 0) >= 50
        cands = []                                   # (score, kind, room, why)
        night = hour >= 21 or hour < 7
        cands.append((0.5 + 0.4 * (here == home), "idle", here, "Spends the time quietly"))
        cands.append(((100 - n["rest"]) / 45 + (1.6 if night else 0), "rest", home, "Heads to bed" if here != home else "Rests"))
        if hungry:
            kit = "kitchen" if "kitchen" in reach else "dining_hall"
            cands.append((1.2 + max(a.get("hunger", 0) - 60, a.get("thirst", 0) - 50) / 40, "eat", kit, "Goes to find something to eat and drink"))
        # company: stay where liked people are, or go where they are
        best_room, best = None, 0.0
        for rid in reach:
            ppl = [o for o in w.occupants(rid) if o in w.agents and o != cid]
            sc = sum(max(0, a["aff"].get(o, 0)) for o in ppl)
            if sc > best:
                best_room, best = rid, sc
        soc = (100 - n["social"]) / 40 * g
        if liked_here:
            cands.append((soc + 0.4, "talk", here, "Stays to talk"))
        elif best_room:
            cands.append((soc, "visit", best_room, "Goes to find some company"))
        # privacy and safety
        quiet = home if not [o for o in w.occupants(home) if o in w.agents and o != cid] else here
        cands.append(((100 - n["privacy"]) / 40 * (2 - g), "alone", quiet, "Wants a little time alone"))
        ally = max((o for o in w.agents if o != cid), key=lambda o: a["aff"].get(o, 0), default=None)
        if ally and a["aff"].get(ally, 0) >= 2 and w.agents[ally]["room"] in reach:
            cands.append(((100 - n["safety"]) / 30, "safe", w.agents[ally]["room"], f"Seeks out {self.nm(ally)} to feel safer"))
        cands.append(((100 - n["purpose"]) / 45, "search", here, "Looks around for anything useful"))
        scored = [(sc + 0.35 * imp * self.rng.random(), k, r, why) for sc, k, r, why in cands if r in reach or r == here]
        sc, kind, room, why = max(scored)
        d = {"activity": why, "thought": "", "action": "stay", "talk_to": [], "target_room": "", "intent": ""}
        if kind == "rest":
            d["action"] = "rest" if room == here else "stay"
            d["target_room"] = "" if room == here else room
        elif kind in ("eat", "visit", "alone", "safe"):
            d["target_room"] = "" if room == here else room
        elif kind == "talk":
            d["talk_to"] = liked_here[:2]
        elif kind == "search":
            d["action"] = "search"
        d["thought"] = {"rest": "I need to rest.", "eat": "I should eat something.", "visit": "I don't want to be alone.", "talk": "Good to have someone to talk to.",
                        "alone": "I need a moment to myself.", "safe": "I'd feel better near someone I trust.", "search": "There might be something here.", "idle": "Nothing to do right now."}[kind]
        return self.clean_decision(d)
