"""Working on the ways out: escape progress from what people actually do.

Besides the 'experiment' decision (routes.py), anyone free can spend a stretch of free time working on a way out: they walk to where that step
of the route is done, use what they carry that helps (it goes into the route's store of parts), and make progress at a pace set by the dial
`escape_rate`. Skill helps (the hacker with the signal and the cameras, the explorer finding the hatch, the handy with building). A step has
needs in the world: parts gathered, an earlier step finished, the hidden passage found, a way to blind the cameras. Until they are met the
step stops at half way. Work goes wrong now and then (a burnt hand, a collapsed frame, a near blast at the Generator Shed). Those who
see someone at work may believe it, and TereVi's existing counters (mayhem.adapt_check) still answer progress she notices.
EscapeWorkMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ESCAPE_ROUTES

# route -> step -> rooms where the work is done, items that help (and are used up into the route's parts), needs before going past half way
STEP_WORK = {
    "transmit": {
        "device": {"rooms": ["study", "lighthouse"], "helps": ["handheld", "wire", "battery", "laptop", "extension_cord"], "needs": [("parts", 2)]},
        "power": {"rooms": ["generator_shed", "lighthouse"], "helps": ["battery", "fuel_can", "extension_cord", "wire"], "needs": [("parts", 2)]},
        "signal": {"rooms": ["lighthouse", "lookout"], "helps": ["wire", "small_telescope"], "needs": [("step", "device")]},
        "proof": {"rooms": ["study", "library", "lighthouse"], "helps": ["gopro", "notebook", "cipher_notebook", "laptop"], "needs": [("proof",)]},
        "unjam": {"rooms": ["study", "lighthouse"], "helps": ["hacking_drive", "laptop", "wire", "pliers"], "needs": [("aid",)]},
    },
    "shutdown": {
        "locate": {"rooms": ["lighthouse", "study"], "helps": ["cipher_notebook", "notebook", "small_telescope"], "needs": [("found", "SP-5")]},
        "approach": {"rooms": ["lighthouse", "core_vault"], "helps": ["crowbar", "bolt_cutters", "tarp"], "needs": [("step", "locate")]},
        "means": {"rooms": ["generator_shed", "core_vault"], "helps": ["sledgehammer", "hacking_drive", "crowbar", "extension_cord", "wire"], "needs": [("parts", 1)]},
        "blind": {"rooms": ["generator_shed", "study"], "helps": ["hacking_drive", "laptop", "wire", "pliers"], "needs": [("aid",)]},
    },
    "raft": {
        "materials": {"rooms": ["beach", "boathouse"], "helps": ["driftwood", "barrel", "planks", "rope", "tarp", "bed_sheets"], "needs": [("parts", 2)]},
        "build": {"rooms": ["beach", "boathouse"], "helps": ["hammer", "rope", "wire", "duct_tape", "masking_tape", "fishing_line"], "needs": [("step", "materials")]},
        "provisions": {"rooms": ["kitchen", "pantry", "boathouse"], "helps": ["water_bottle", "energy_bar", "life_jacket", "small_telescope"], "needs": [("parts", 1)]},
        "launch": {"rooms": ["boathouse", "beach"], "helps": ["bolt_cutters", "crowbar", "rope"], "needs": [("step", "build")]},
    },
    "ultimatum": {
        "explosives": {"rooms": ["generator_shed", "art_studio"], "helps": ["fuel_can", "chlorine", "paint_thinner", "turpentine", "flares", "matches"], "needs": [("parts", 3)]},
        "plant": {"rooms": ["generator_shed", "lighthouse"], "helps": ["duct_tape", "wire", "masking_tape"], "needs": [("step", "explosives")]},
        "leverage": {"rooms": ["generator_shed", "lookout"], "helps": ["flare_gun", "flares", "gopro"], "needs": [("step", "plant")]},
        "trigger": {"rooms": ["generator_shed"], "helps": ["wire", "battery", "pliers", "handheld"], "needs": [("parts", 1)]},
    },
}
# how quickly work on each route goes: a small raft is simple, a transmitter fiddly, a bomb dangerous
PACE = {"raft": 1.6, "transmit": 1.3, "shutdown": 1.0, "ultimatum": 0.9}
# roles that make someone good at a step
SKILL = {("transmit", "unjam"): "Hacker", ("shutdown", "blind"): "Hacker", ("shutdown", "means"): "Hacker", ("transmit", "device"): "Hacker",
         ("shutdown", "locate"): "Urban Explorer", ("shutdown", "approach"): "Urban Explorer", ("raft", "launch"): "Urban Explorer",
         ("transmit", "proof"): "Photographer", ("ultimatum", "leverage"): "Photographer", ("transmit", "signal"): "Musician"}
MISHAP = {"ultimatum": ("burned", "a flash of fumes at the Generator Shed"), "raft": ("weak", "a frame collapsing on them"),
          "transmit": ("burned", "a shock from bare wire"), "shutdown": ("bleeding", "a fall in the dark below the Lighthouse")}


class EscapeWorkMixin:
    def escape_route_for(self, cid):
        """The route someone would work on now: their favourite unless it is finished, else the most advanced unfinished one."""
        esc = self.s.get("escape") or {}
        routes = esc.get("routes") or {}
        open_ = [r for r in ESCAPE_ROUTES if r in routes and any(v < 100 for v in routes[r]["plan"].values())]
        if not open_:
            return None
        fav = (self.world.agents.get(cid) or {}).get("route")
        best = max(open_, key=lambda r: (self.route_pct(r), r))
        if fav in open_ and self.route_pct(best) - self.route_pct(fav) < 20:
            return fav
        return best                                           # the group's momentum wins over a favourite that has fallen behind

    def escape_step_for(self, rid):
        """The step to work on: the least advanced one whose needs are met, else the least advanced one (it can still reach half way)."""
        plan = self.s["escape"]["routes"][rid]["plan"]
        todo = [st for st in ESCAPE_ROUTES[rid]["steps"] if plan[st] < 100]
        if not todo:
            return None
        ready = [st for st in todo if not self.step_missing(rid, st)]
        pool = ready or todo
        order = list(ESCAPE_ROUTES[rid]["steps"])
        return min(pool, key=lambda st: (plan[st], order.index(st)))      # ties go in the route's own order: materials before building

    def step_missing(self, rid, step):
        """What a step still needs before it can go past half way (empty when nothing)."""
        s = self.s
        rt = s["escape"]["routes"][rid]
        out = []
        for need in STEP_WORK.get(rid, {}).get(step, {}).get("needs", []):
            k = need[0]
            if k == "parts" and rt.get("parts", {}).get(step, 0) < need[1]:
                out.append(f"{need[1] - rt.get('parts', {}).get(step, 0)} more useful parts")
            elif k == "step" and rt["plan"].get(need[1], 0) < 100:
                out.append(f"the {need[1]} step done first")
            elif k == "found" and need[1] not in s.get("found_edges", []):
                out.append("the hidden way down found")
            elif k == "aid" and not self.escape_aid(rid):
                out.append("a way to blind TereVi (a blackout, a hacker's drive, or NeoVi's help)")
            elif k == "proof" and not self.escape_proof():
                out.append("proof nobody could fake (footage of their own, a death on record)")
        return out

    def escape_aid(self, rid):
        s, w = self.s, self.world
        rt = s["escape"]["routes"][rid]
        nv = s["npcs"]["neovi"]
        cut = sum(rt.get("parts", {}).get(st, 0) for st in ("unjam", "blind", "launch")) >= 2           # feeds cut, drones fooled with gathered tools
        return (cut or self.blackout_until >= self.idx or rt.get("parts", {}).get("blind_aid", 0) > 0
                or any(nv["aff"].get(c, 0) >= 6 for c in rt.get("contributors", []))
                or any(w.agents[c]["inv"].get("hacking_drive", 0) > 0 for c in rt.get("contributors", []) if c in w.agents))

    def escape_proof(self):
        s = self.s
        return bool(s.get("graveyard")) or any(r.get("parts", {}).get("proof", 0) > 0 for r in s["escape"]["routes"].values())

    def parts_source(self, cid, rid, step):
        """Where to fetch a part for a step that still needs parts, if the worker carries none: the nearest room with one lying about."""
        w = self.world
        spec = STEP_WORK.get(rid, {}).get(step, {})
        if not any(m.endswith("useful parts") for m in self.step_missing(rid, step)):
            return None
        if any(w.agents[cid]["inv"].get(it, 0) > 0 for it in spec.get("helps", [])):
            return None
        pools = self.s["room_items"]
        cands = sorted(r for r, p in pools.items() if any(p.get(it, 0) > 0 for it in spec.get("helps", [])) and r in w.reachable_rooms(cid, 40))
        here = w.agents[cid]["room"]
        return here if here in cands else (cands[0] if cands else None)

    def escape_work_room(self, cid, rid, step):
        src = self.parts_source(cid, rid, step)
        if src:
            return src
        rooms = STEP_WORK.get(rid, {}).get(step, {}).get("rooms") or [ESCAPE_ROUTES[rid]["room"]]
        if "core_vault" in rooms and "SP-5" not in self.s.get("found_edges", []):
            rooms = [r for r in rooms if r != "core_vault"] or ["lighthouse"]
        here = self.world.agents[cid]["room"]
        return here if here in rooms else rooms[0]

    def escape_work_score(self, cid, mi, f):
        """How much someone wants to spend free time on a way out now."""
        if not self.revealed or self.s.get("over") or not self.escape_route_for(cid):
            return 0.0
        a = self.world.agents[cid]
        rate = self.tune("escape_rate")
        if rate <= 0:
            return 0.0
        days_left = max(0, self.s.get("deadline_day", self.day) - self.day)
        mine = any(cid in r.get("contributors", []) for r in self.s["escape"]["routes"].values())
        return (0.35 + 0.25 * min(1.5, rate) + (100 - mi["purpose"]) / 120 + (f("courage") - 45) / 160 + (f("curiosity") - 45) / 200
                + (0.25 if mine else 0) + (0.2 if days_left <= 2 else 0) + (0.15 if a["sanity"] >= 40 else -0.2))

    def escape_work(self, tick, cid, m):
        """A stretch of work on a way out: parts carried go in, progress comes out (up to half way until the step's needs are met)."""
        w, s = self.world, self.s
        rid = self.escape_route_for(cid)
        if not rid:
            return None
        step = self.escape_step_for(rid)
        if not step:
            return None
        rt = s["escape"]["routes"][rid]
        plan = rt["plan"]
        spec = STEP_WORK.get(rid, {}).get(step, {})
        a = w.agents[cid]
        pool = s["room_items"].get(a["room"], {})
        short = any(x.endswith("useful parts") for x in self.step_missing(rid, step))
        if (short or a["room"] not in spec.get("rooms", [])) and any(pool.get(it, 0) > 0 for it in spec.get("helps", [])):
            got = []
            for it in spec["helps"]:
                if pool.get(it, 0) > 0 and len(got) < 2:
                    q, _ = w.take(cid, it, 1)
                    if q:
                        got.append(it)
            if got:
                parts = rt.setdefault("parts", {})
                for it in got:
                    a["inv"][it] -= 1
                    if a["inv"][it] <= 0:
                        del a["inv"][it]
                parts[step] = parts.get(step, 0) + len(got)
                if cid not in rt["contributors"]:
                    rt["contributors"].append(cid)
                title = ESCAPE_ROUTES[rid]["title"].lower()
                self._fev(tick, cid, m, f"{self.nm(cid)} gathers {', '.join(w.item_name(i) for i in got)} for the way out ({title}: {step}).", etype="escape_work", vis="viewer")
                return {"route": rid, "step": step, "gain": 0, "verdict": "gathered", "used": got}
        used = []
        for it in spec.get("helps", []):
            if a["inv"].get(it, 0) > 0 and len(used) < 2 and it != "hacking_drive":
                a["inv"][it] -= 1
                if a["inv"][it] <= 0:
                    del a["inv"][it]
                used.append(it)
        if a["inv"].get("hacking_drive", 0) > 0 and step in ("unjam", "blind", "means"):
            used.append("hacking_drive")                      # used, not given up
            rt.setdefault("parts", {})["blind_aid"] = rt.get("parts", {}).get("blind_aid", 0) + 1
        parts = rt.setdefault("parts", {})
        parts[step] = parts.get(step, 0) + len([u for u in used if u != "hacking_drive"])
        if step == "proof" and any(u in ("gopro", "notebook", "cipher_notebook", "laptop") for u in used):
            parts["proof"] = parts.get("proof", 0) + 1
        if step == "locate" and "SP-5" not in s.get("found_edges", []) and a["room"] == "lighthouse":
            for ev in w.search(cid, "searches the floor and walls for a hatch, a seam, a way down", 1.5):
                self.log_event(tick, ev, actor=cid)                # looking for the hidden way down (world.search finds secret passages)
        rate = self.tune("escape_rate")
        gain = 9 * rate * PACE.get(rid, 1.0) + 4 * len(used) + (3 if SKILL.get((rid, step)) == w.cast[cid].get("role") else 0) + (self.facet(cid, "orderliness") - 50) / 25
        roll = self.rng.random()
        verdict = "progress"
        if roll < 0.08:
            verdict = "mishap"
            gain = -4
            cond, why = MISHAP.get(rid, ("weak", "an accident"))
            self.add_cond(tick, cid, cond, 1, why=why)
        elif roll < 0.28:
            verdict = "slow"
            gain *= 0.5
        cap = 100 if not self.step_missing(rid, step) else 50
        before = plan[step]
        plan[step] = int(max(0, min(cap, plan[step] + round(gain))))
        if plan[step] > before and cid not in rt["contributors"]:
            rt["contributors"].append(cid)
        self.escape_progress()
        miss = self.step_missing(rid, step)
        title = ESCAPE_ROUTES[rid]["title"].lower()
        text = {"progress": f"{self.nm(cid)} works on the way out ({title}: {step}, now {plan[step]}%)",
                "slow": f"{self.nm(cid)} gets little done on the way out ({title}: {step}, {plan[step]}%)",
                "mishap": f"{self.nm(cid)} has an accident working on the way out ({title}: {step})"}[verdict]
        text += (f", using the {', '.join(w.item_name(u) for u in used)}" if used else "") + "."
        if miss and plan[step] >= 50:
            text += f" Stuck at half way: it still needs {miss[0]}."
        self._fev(tick, cid, m, text, etype="escape_work", vis="viewer")
        self.tally(cid, "route_steps") if plan[step] > before else None
        if plan[step] >= 100 and before < 100:
            self.moment(cid, f"finished a step of the way out ({title}: {step})")
            self.log_event(tick, {"type": "system_notable", "who": cid, "room": a["room"], "vis": "viewer", "m": m,
                                  "text": f"A step of the way out is done: {title}, {step}."}, actor=cid)
        return {"route": rid, "step": step, "gain": plan[step] - before, "verdict": verdict, "used": used}

    # ------------------------------------------------------------------ TereVi's counters, as scenes
    def escape_counter(self, tick, rid, strong=False):
        """TereVi answers progress she has noticed with something people see: parts confiscated, the workroom locked, a worker punished on
        air, or a rumour that one of them works for her. Returns the kinds used."""
        w, s = self.world, self.s
        rt = s["escape"]["routes"][rid]
        team = [c for c in rt.get("contributors", []) if c in w.agents]
        title = ESCAPE_ROUTES[rid]["title"].lower()
        kinds = ["confiscate", "lockdown"] + (["punish", "rumour"] if team else [])
        used = []
        for kind in self.rng.sample(kinds, 2 if strong else 1):
            if kind == "confiscate":
                parts = rt.setdefault("parts", {})
                lost = sum(parts.values())
                for k in list(parts):
                    parts[k] = parts[k] // 2
                text = (f"On TereVi's orders NeoVi sweeps through the hiding places and carries off half of what the cast had gathered for the way out ({title})."
                        if lost else f"NeoVi searches every corner for anything gathered for the way out ({title}), on TereVi's orders.")
            elif kind == "lockdown":
                room = (STEP_WORK.get(rid, {}).get(self.escape_step_for(rid) or "", {}).get("rooms") or [ESCAPE_ROUTES[rid]["room"]])[0]
                s.setdefault("locks", {})[room] = {"by": "terevi", "day": self.day}
                text = f"The {w.room_name(room)} locks itself with a heavy clunk. TereVi: \"Closed for renovations, darlings.\""
            elif kind == "punish":
                c = max(team, key=lambda x: (s.get("stats", {}).get(x, {}).get("route_steps", 0), x))      # the most active worker
                self.stat(tick, c, "hp", -8, "TereVi's punishment for tampering with the set")
                self.stat(tick, c, "sanity", -6, "punished on air")
                text = f"TereVi tases {self.nm(c)} on air for 'tampering with the set'. The audience, she says, loved it."
                self.moment(c, "was punished on air for working on the way out")
            else:
                c = self.rng.choice(sorted(team))
                for o in team:
                    if o != c:
                        w.adjust_aff(o, c, -2)
                        self.belief_rumor(o, "terevi", c, f"{self.nm(c)} has been reporting the escape plans to TereVi", lie=True)
                text = f"TereVi lets it slip, oh so casually, that {self.nm(c)} has been 'such a help' keeping her informed about the plans."
            used.append(kind)
            self.log_event(tick, {"type": "tease", "who": "terevi", "room": "foyer", "vis": "public", "text": text}, witnesses=list(w.agents))
        return used
