"""Murder plots that are designed over time and follow through.

A plot is a campaign, not a turn: brooding -> preparing (a weapon, a method) -> stalking (learning the target's habits, waiting for a window) -> striking.
The engine owns the stages and the checklist, so the plan keeps moving across turns and days even when the model only thinks about escape. Plotters can
abandon the plan (calming down, a change of heart) or have it overtaken by the deadline; a plan that reaches the strike either lands or fails.
PlotMixin is mixed into DayRunner (engine.py).
"""
from .data_world import CAMERA_BLIND
from .world import MOVE_BUDGET

STAGES = ["brooding", "preparing", "stalking", "striking"]
MIN_TICKS = {"brooding": 2, "preparing": 3, "stalking": 3}
MAX_TICKS = {"brooding": 6, "preparing": 9, "stalking": 8}
AGGRESSIVE = {"avenger", "saboteur", "schemer", "nihilist"}
GENTLE = {"protector", "romantic", "martyr"}
COVERS = ["Was with the others the whole time and noticed nothing.", "Was resting in my room, alone, sadly.", "Was looking for a way out and lost track of time.",
          "Was in the library and will point at whoever had a reason to hate them."]


def _hh(h):
    return f"{int(h):02d}:00"


class PlotMixin:
    # ------------------------------------------------------------------ helpers
    def plot_defaults(self, p):
        for k, v in (("ticks", 0), ("stage_ticks", 0), ("seen", 0), ("days", 0), ("plan", []), ("weapon", None), ("auto", True), ("reason", ""), ("window", "")):
            p.setdefault(k, v)
        return p

    def plot_weapon(self, cid):
        """A weapon the plotter carries, or failing that a poison."""
        w = self.world
        inv = w.agents[cid]["inv"]
        return (next((k for k in inv if "weapon" in w.item_spec(k).get("tags", [])), None)
                or next((k for k in inv if "poison" in w.item_spec(k).get("tags", [])), None))

    def plot_method(self, p):
        item = p.get("weapon")
        if not item:
            return "hands"
        return f"poison:{item}" if "poison" in self.world.item_spec(item).get("tags", []) else item

    def step_toward(self, cid, dest):
        """The reachable room (this turn) that gets cid closest to dest."""
        w = self.world
        a = w.agents[cid]
        if a["room"] == dest:
            return None
        reach = w.reachable_rooms(cid, MOVE_BUDGET * self.step)
        if dest in reach:
            return dest
        best, bl = None, 10 ** 9
        for rr in reach:
            if rr == a["room"]:
                continue
            pth = w.path(cid, rr, dest)
            if pth is None:
                continue
            n = sum(c for _, _, c in pth)
            if n < bl:
                best, bl = rr, n
        return best

    def weapon_room(self, cid):
        """The nearest room that holds a weapon someone could pick up."""
        w, s = self.world, self.s
        best, bl = None, 10 ** 9
        for room, items in s["room_items"].items():
            if any(q > 0 and "weapon" in w.item_spec(k).get("tags", []) and "instrument" not in w.item_spec(k).get("tags", []) for k, q in items.items()):
                pth = w.path(cid, w.agents[cid]["room"], room)
                if pth is None:
                    continue
                n = sum(c for _, _, c in pth)
                if n < bl:
                    best, bl = room, n
        return best

    def plan_note(self, p, text):
        p["plan"].append(f"Day {self.day}: {text}"[:120])
        del p["plan"][:-8]

    # ------------------------------------------------------------------ starting a plot
    def plot_motives(self, cid):
        """Every reason this person might have to want someone dead right now: a list of (score, target, why, kind). The strongest wins."""
        w, s = self.world, self.s
        a = w.agents[cid]
        others = [o for o in w.agents if o != cid]
        if not others:
            return []
        pr = self.pressure()
        drive = a["drive"]["id"]
        cands = []
        hated = min(others, key=lambda o: a["aff"].get(o, 0))
        low = a["aff"].get(hated, 0)
        base = 0.0
        if low <= -4:
            base += (-low - 3) / 7.0
        if a["sanity"] < 40:
            base += 0.3
        if self.mind_on():
            base += 0.12 * (self.facet(cid, "vengefulness") - 50) / 50 + 0.08 * (self.facet(cid, "anger") - 50) / 50 + 0.06 * (self.facet(cid, "cruelty") - 50) / 50 - 0.1 * (self.facet(cid, "altruism") - 50) / 50
        if drive in AGGRESSIVE:
            base += 0.15
        if base > 0 and low <= -4:
            cands.append((base, hated, f"{self.nm(hated)} has become unbearable", "hatred"))
        dt = a["drive"].get("target")
        if drive == "avenger" and dt in w.agents:
            cands.append((base + 0.5, dt, f"{self.nm(dt)} must pay", "vengeance"))
        imp = self.impulses.get(cid)
        if imp and imp.get("kind") == "hurt" and imp.get("target") in w.agents and imp.get("level", 0) >= 3:
            cands.append((base + 0.4, imp["target"], "an urge that will not go away", "urge"))
        if pr > 0.5 and not s.get("case"):
            t = min(others, key=lambda o: (a["aff"].get(o, 0), w.agents[o]["hp"]))
            cands.append((base + 0.7 * pr * pr, t, "somebody has to die before the deadline, and it will not be you", "deadline"))
        # jealousy: the person you love loves someone else more
        for bnd in s.get("bonds", []):
            if bnd["kind"] == "romance" and cid in (bnd["a"], bnd["b"]):
                partner = bnd["b"] if bnd["a"] == cid else bnd["a"]
                if partner in w.agents:
                    rivals = [o for o in others if o != partner and w.agents[partner]["aff"].get(o, 0) >= 6 and w.agents[partner]["aff"].get(o, 0) > w.agents[partner]["aff"].get(cid, 0)]
                    if rivals:
                        cands.append((0.55 + (0.2 if a["sanity"] < 50 else 0), max(rivals, key=lambda o: w.agents[partner]["aff"].get(o, 0)), f"{self.nm(partner)} is slipping away toward them", "jealousy"))
        for x in others:
            if a["aff"].get(x, 0) >= 6 and w.agents[x]["aff"].get(cid, 0) <= 0:
                rivals = [o for o in others if o != x and w.agents[x]["aff"].get(o, 0) >= 5]
                if rivals and a["sanity"] < 55:
                    cands.append((0.4, max(rivals, key=lambda o: w.agents[x]["aff"].get(o, 0)), f"{self.nm(x)} will never look at you while they are around", "jealousy"))
        # blackmail: someone holds your secret over you
        for x in others:
            if any(k.get("of") == cid for k in w.agents[x].get("known_secrets", [])) and a["aff"].get(x, 0) <= 1:
                threat = any(t["target"] == cid for t in s.get("threats", []))
                cands.append((0.45 + (0.3 if threat else 0.0) + (0.15 if a["sanity"] < 45 else 0), x, f"{self.nm(x)} knows your secret and will use it", "blackmail"))
        # revenge for someone wrongly condemned
        for rec in s.get("vote_log", [])[-4:]:
            acc = rec["accused"]
            lost = next((x for x in a["memory"].get("lost", []) if x.get("id") == acc), None)
            if rec["wrongful"] and lost and a["aff"].get(acc, 0) + (3 if lost.get("close") in ("a close friend", "someone they loved") else 0) >= 3:
                voters = [v for v in rec["voters"] if v in w.agents and v != cid]
                if voters:
                    cands.append((0.65, min(voters, key=lambda v: a["aff"].get(v, 0)), f"{self.nm(min(voters, key=lambda v: a['aff'].get(v, 0)))} helped send {self.nm(acc)} to their death", "revenge"))
        # retaliation for what was done to them while helpless
        for tie in s.get("ties", []):
            if tie["a"] == cid and tie["kind"] == "wronged" and tie["b"] in w.agents and any(x in tie["text"] for x in ("knocked you out", "locked you in", "went through your things", "stripped")):
                why = "attacked you and may do it again" if "knocked" in tie["text"] else "had you at their mercy"
                cands.append((0.5 + (0.15 if a["sanity"] < 50 else 0) + 0.05 * max(0, -a["aff"].get(tie["b"], 0)), tie["b"], f"{self.nm(tie['b'])} {why}", "retaliation"))
        # protecting someone who is being hurt
        for h in s.get("hooks", []):
            if h["status"] in ("solved", "open") and h["culprit"] in w.agents and h["culprit"] != cid:
                for v in h["victims"]:
                    if v in w.agents and v != cid and a["aff"].get(v, 0) >= 6 and h["evidence"] >= 2:
                        cands.append((0.5, h["culprit"], f"{self.nm(h['culprit'])} is hurting {self.nm(v)}", "protection"))
        # staying hidden: someone is close to exposing what you did
        for h in s.get("hooks", []):
            if h["culprit"] == cid and h["status"] == "open" and h["evidence"] >= 2:
                for v in h["victims"]:
                    if v in w.agents:
                        cands.append((0.55, v, f"{self.nm(v)} is close to proving it was you", "exposure"))
                for wit in h["seen_by"]:
                    if wit in w.agents and wit != cid:
                        cands.append((0.4, wit, f"{self.nm(wit)} saw you", "silencing"))
        now = self.day * 24 + self.s.get("_hour", 12)
        chron = s.get("chronicle", [])[-260:]
        # fear: somebody hurt you and may do it again (not the same as hatred: you would rather be left alone, but not at their mercy)
        for rec_ in (a.get("harmed_by") or [])[-3:]:
            who, d_ = rec_[0], rec_[1]
            if who in w.agents and who != cid and self.day - d_ <= 2:
                cands.append((0.4 + (0.2 if a["sanity"] < 50 else 0.0) + 0.1 * max(0, -a["aff"].get(who, 0)) / 5, who, f"{self.nm(who)} hurt you and you will not wait for the next time", "fear"))
        # betrayal: somebody you trusted turned on you
        for e in chron:
            if e["type"] == "betrayal" and cid in e.get("with", []) and e.get("who") in w.agents and e["who"] != cid and now - (e["day"] * 24 + e["hour"]) <= 72:
                cands.append((0.5 + (0.1 if self.mind_on() and self.facet(cid, "vengefulness") > 60 else 0.0), e["who"], f"{self.nm(e['who'])} betrayed you", "betrayal"))
                break
        # humiliation: a vain person seen in a state they cannot forgive
        vain = self.facet(cid, "vanity") if self.mind_on() else 50
        for e in reversed(chron):
            if e["type"] == "embarrassed" and e.get("who") == cid and now - (e["day"] * 24 + e["hour"]) <= 30:
                watchers = [x for x in e.get("seen", []) if x in w.agents and x != cid]
                if watchers and vain >= 55:
                    t = min(watchers, key=lambda x: a["aff"].get(x, 0))
                    cands.append((0.28 + 0.2 * (vain - 55) / 45, t, f"{self.nm(t)} saw you humiliated and will not let it go", "humiliation"))
                break
        # envy: everybody else likes them more than you
        if len(others) >= 3 and a["sanity"] < 70:
            def pop_(x):
                return sum(w.agents[o]["aff"].get(x, 0) for o in w.agents if o != x) / max(1, len(w.agents) - 1)
            star = max(others, key=pop_)
            if pop_(star) - pop_(cid) >= 3 and a["aff"].get(star, 0) <= 1 and vain >= 50:
                cands.append((0.3 + 0.05 * (pop_(star) - pop_(cid) - 3), star, f"everybody loves {self.nm(star)} and nobody notices you", "envy"))
        # the prize: if only one can leave with it, the strongest rival is in the way
        twist = ((s.get("scenario") or {}).get("twist") or {}).get("text", "").lower()
        if "prize" in twist and drive in ("schemer", "survivor", "saboteur", "thrill") and self.day >= ((s.get("scenario") or {}).get("twist") or {}).get("day", 0):
            t = max(others, key=lambda o: w.agents[o]["hp"] + w.agents[o]["sanity"] + 3 * max(0, w.agents[o]["aff"].get(cid, 0)))
            cands.append((0.3, t, f"there is exactly one prize and {self.nm(t)} is the one to beat", "prize"))
        # the end game: when few remain, ambition
        if len(w.agents) <= 5 and drive in ("survivor", "schemer") and not s.get("case"):
            t = max(others, key=lambda o: w.agents[o]["hp"] + w.agents[o]["sanity"])
            cands.append((0.3, t, f"only {len(w.agents)} are left and {self.nm(t)} is the one to beat", "ambition"))
        # greed: someone holds the thing that opens every door
        if drive in ("schemer", "saboteur"):
            for x in others:
                if w.agents[x]["inv"].get("master_key", 0) or w.agents[x]["inv"].get("skeleton_keys", 0):
                    cands.append((0.25, x, f"{self.nm(x)} carries the keys that would get you out of here", "greed"))
        if drive in GENTLE and pr < 0.9:
            cands = [(sc - 0.4, t, why, k) for sc, t, why, k in cands if k not in ("protection",)] + [c for c in cands if c[3] == "protection"]
        if sum(a["aff"].get(o, 0) for o in others) / len(others) > 3:
            cands = [(sc - 0.2, t, why, k) for sc, t, why, k in cands]
        return [c for c in cands if c[1] in w.agents]

    def plot_motive(self, cid):
        """(score, target, reason, kind) for the strongest reason this person has to want someone dead."""
        cands = self.plot_motives(cid)
        if not cands:
            return 0.0, None, "", ""
        return max(cands, key=lambda c: c[0] + self.rng.uniform(0, 0.05))

    def maybe_start_plots(self, tick, hour):
        w, s = self.world, self.s
        if not self.murders or not self.revealed or s.get("case") or s.get("spree") or hour not in (10, 16) or self.aftermath_active():
            return
        plots = s.setdefault("plots", {})
        if getattr(self, "plot_started_day", -1) == self.day:
            return
        cands = []
        for cid, a in w.agents.items():
            if cid in plots or a["room"] in ("cold_store",):
                continue
            sc, target, why, mk = self.plot_motive(cid)
            if sc > 0.1 and target in w.agents and not any(p["target"] == target and len(plots) >= 1 for p in plots.values()):
                pr_ = min(0.5, sc * 0.35 * self.tune("plot_rate"))
                if plots.get(target, {}).get("target") == cid:
                    pr_ *= 0.1                                              # two people plotting each other's deaths is rare, not the default outcome of a quarrel
                cands.append((pr_, cid, target, why, mk))
        self.rng.shuffle(cands)
        for p, cid, target, why, mk in cands:
            if self.rng.random() < p:
                self.plot_start(tick, cid, target, why, hour, mk)
                self.plot_started_day = self.day
                return

    def plot_pileup(self, tick, hour):
        """Three or more plots at once is more than a house can hold: somebody may break first and start the killing."""
        w, s = self.world, self.s
        plots = {c: p for c, p in s.get("plots", {}).items() if c in w.agents}
        if len(plots) <= 2 or s.get("spree") or s.get("case") or not self.murders or hour not in (10, 14, 18) or len(w.agents) < 4:
            return
        if self.rng.random() >= min(0.4, 0.08 * (len(plots) - 2) * self.chaos_factor()):
            return
        by = min(plots, key=lambda c: w.agents[c]["sanity"] + (15 if plots[c].get("stage") in ("stalking", "striking") else 0) * -1)
        self.start_spree(tick, hour, by, f"There are too many knives in this house. {self.nm(by)} is the first to stop waiting.")

    def plot_start(self, tick, cid, target, why, hour, motive="hatred"):
        w, s = self.world, self.s
        p = self.plot_defaults({"target": target, "stage": "brooding", "method": "", "step": "", "cover": self.rng.choice(COVERS), "log": [], "quiet": 0,
                                "since": f"Day {self.day} {_hh(hour)}", "reason": why, "origin": "engine", "motive": motive})
        s.setdefault("plots", {})[cid] = p
        self.plan_note(p, f"began to want {self.nm(target)} dead ({why})")
        w.remember(cid, f"{_hh(hour)} (private) You have decided {self.nm(target)} has to die: {why}. You will have to be patient and careful.")
        self.log_event(tick, {"type": "plot", "who": cid, "room": w.agents[cid]["room"], "vis": "viewer",
                              "text": f"{self.nm(cid)} starts plotting to kill {self.nm(target)} ({motive}: {why})."}, actor=cid)
        self.moment(cid, f"decided {self.nm(target)} must die")
        self.tally(cid, "plots")

    # ------------------------------------------------------------------ advancing a plot, turn by turn
    def plot_tick(self, tick, hour, decisions):
        """Advance every plot one turn and steer the plotter's turn toward the next thing on the checklist."""
        w, s = self.world, self.s
        if not self.murders:
            return
        for cid, p in list(s.get("plots", {}).items()):
            if cid not in w.agents:
                s["plots"].pop(cid, None)
                continue
            t = p["target"]
            if t not in w.agents:
                continue
            self.plot_defaults(p)
            a, d = w.agents[cid], decisions.get(cid)
            p["ticks"] += 1
            p["stage_ticks"] += 1
            if a["room"] == w.agents[t]["room"]:
                p["seen"] += 1
            if not p["weapon"] or a["inv"].get(p["weapon"], 0) <= 0:
                p["weapon"] = self.plot_weapon(cid)
                if p["weapon"] and p["stage"] in ("brooding", "preparing"):
                    self.plan_note(p, f"has the {w.item_name(p['weapon'])}")
            stage = p["stage"]
            ready = {"preparing": bool(p["weapon"]) or p["stage_ticks"] >= MAX_TICKS["preparing"],
                     "stalking": p["seen"] >= 2 or p["stage_ticks"] >= MAX_TICKS["stalking"]}
            urgent = self.days_left() <= 0 or (self.pressure() > 0.8 and a["sanity"] < 50)
            nxt = None
            if stage in MIN_TICKS and p["stage_ticks"] >= MIN_TICKS[stage]:
                if stage == "brooding" or ready.get(stage):
                    if self.rng.random() < (0.9 if urgent else 0.55) or p["stage_ticks"] >= MAX_TICKS[stage]:
                        nxt = STAGES[STAGES.index(stage) + 1]
            if p["stage"] in ("preparing", "stalking", "striking") and not p.get("scheme"):
                self.choose_scheme(tick, cid, p)                    # how they mean to do it (planner.py)
            if nxt:
                p["stage"], p["stage_ticks"] = nxt, 0
                if nxt == "preparing" and not p.get("scheme"):
                    self.choose_scheme(tick, cid, p)
                self.plan_note(p, {"preparing": "settled on a method", "stalking": "is ready and watching for a window", "striking": "will strike at the first chance"}[nxt])
                self.log_event(tick, {"type": "plot", "who": cid, "room": a["room"], "vis": "viewer",
                                      "text": f"{self.nm(cid)} ({nxt}) against {self.nm(t)}: {p['plan'][-1].split(': ', 1)[-1]}"}, actor=cid)
            if d is None or d["action"] not in ("stay", "rest", "search", "take", "use", "give", "drop", "investigate", "hide", "spy"):
                continue
            if d.get("target_room") and self.rng.random() < 0.5:
                continue
            self.plot_steer(tick, cid, p, d, hour, urgent)

    def plot_steer(self, tick, cid, p, d, hour, urgent):
        before = dict(d)
        self._plot_steer(tick, cid, p, d, hour, urgent)
        if d != before:
            d["_src"] = "engine"

    def _plot_steer(self, tick, cid, p, d, hour, urgent):
        w, s = self.world, self.s
        a, t = w.agents[cid], p["target"]
        ta = w.agents[t]
        stage = p["stage"]
        gate = 0.9 if stage == "striking" else 0.7
        if self.rng.random() > gate:
            return
        if stage == "brooding":
            return
        if stage == "preparing":
            sc = p.get("scheme") or {}
            if "gag" in self.scheme_needs(cid, p):                  # something to keep them quiet (planner.py)
                from .combat import GAG_ITEMS
                here_g = [k for k in GAG_ITEMS if s["room_items"].get(a["room"], {}).get(k, 0) > 0]
                if here_g:
                    d.update(action="take", item=here_g[0], qty=1, target_room="", activity=f"Tucks the {w.item_name(here_g[0])} away", step="takes something to gag them with")
                    return
                gr = self.gag_room(cid)
                go = self.step_toward(cid, gr) if gr and self.rng.random() < 0.5 else None
                if go:
                    d.update(target_room=go, action="stay", activity="Looks for something useful", step="looks for a gag")
                    return
            if sc.get("kind") == "trap" and not p.get("rigged"):
                if a["room"] == sc["room"] and sc.get("rig") in self.rig_options(cid):
                    d.update(action="rig", rig={"kind": sc["rig"], "target": t}, target_room="", activity="Busy with something, out of sight", step="rigs the trap")
                    p["rigged"] = True
                    return
                go = self.step_toward(cid, sc["room"])
                if go:
                    d.update(target_room=go, action="stay", activity="Heads off somewhere quiet", step="goes to set the trap")
                    return
            if p["weapon"]:
                return
            here = [k for k, q in s["room_items"].get(a["room"], {}).items() if q > 0 and "weapon" in w.item_spec(k).get("tags", []) and "instrument" not in w.item_spec(k).get("tags", [])]
            if here:
                d.update(action="take", item=here[0], qty=1, target_room="", activity=f"Pockets the {w.item_name(here[0])} when nobody is looking", step="takes a weapon")
                return
            rid = self.craft_weapon_option(cid)
            if rid and self.rng.random() < 0.7:
                d.update(action="craft", craft=rid, target_room="", activity="Busy with their hands, out of the way", step="makes a weapon")
                return
            dest = self.weapon_room(cid)
            go = self.step_toward(cid, dest) if dest else None
            if go:
                d.update(target_room=go, action="stay", activity="Heads somewhere with something useful in it", step="looks for a weapon")
            return
        if stage == "stalking":
            if a["room"] != ta["room"]:
                if self.pick_tool(cid) and self.door_assault(cid, ta["room"], d):
                    return
                go = self.step_toward(cid, ta["room"])
                if go:
                    d.update(target_room=go, action="stay", activity=f"Follows {self.nm(t)} at a distance", step="tracks the target")
            else:
                d.update(action="stay", target_room="", activity=f"Keeps {self.nm(t)} in sight and waits", step="watches for a window")
            return
        # striking
        if a["room"] != ta["room"]:
            if self.door_assault(cid, ta["room"], d):
                return
            go = self.step_toward(cid, ta["room"])
            if go:
                d.update(target_room=go, action="stay", activity=f"Goes after {self.nm(t)}", step="closes in")
            return
        if ta.get("out") and a["room"] == ta["room"]:
            return self.plot_helpless(tick, cid, p, d, hour)
        humans = [o for o in w.occupants(a["room"]) if o in w.agents]
        alone = len(self.perceivers_of(cid, a["room"], "quiet", exclude=(t,))) == 0 if self.perception_on() else len(humans) <= 2
        window = alone or a["room"] in CAMERA_BLIND or self.blackout_until >= self.idx or bool(ta.get("asleep"))
        subdue = p.get("motive") in ("blackmail", "exposure", "silencing", "jealousy") or (not ta.get("asleep") and (self.has(cid, "sleeping_pills") or (p["weapon"] and "blunt" in self.tags(p["weapon"]))))
        if (window or urgent) and not s.get("case") and subdue and self.rng.random() < 0.5:      # an awake target is put down first, then finished (plot_helpless)
            p["window"] = "alone" if alone else "blind spot"
            d.update(action="knockout", target=t, method=self.plot_method(p) if not p["weapon"] or "blunt" in self.tags(p["weapon"]) else "hands", target_room="", activity="Moves on them from behind", step="knocks them out")
            self.plan_note(p, f"put {self.nm(t)} out of action ({p['window']})")
            return
        if not self.scheme_allows(cid, p, urgent):
            d.update(action="stay", target_room="", activity=f"Keeps an eye on {self.nm(t)} and bides their time", step="waits for the planned moment")
            return
        if (window or urgent) and not s.get("case") and self.rng.random() < (0.8 if window else 0.5):
            p["window"] = "alone" if alone else "blind spot" if a["room"] in CAMERA_BLIND else "dark" if self.blackout_until >= self.idx else "deadline"
            d.update(action="attack", target=t, method=self.scheme_method(cid, p) or self.plot_method(p), target_room="", activity="Something finally snaps into place", step="strikes")
            self.plan_note(p, f"struck at {self.nm(t)} ({p['window']})")
        else:
            d.update(action="stay", target_room="", activity=f"Waits beside {self.nm(t)} for the right moment", step="waits for a window")

    # ------------------------------------------------------------------ overnight
    def plot_nightly(self, tick):
        """Plots survive the night. Calm and fondness can end them; the clock can harden them."""
        w, s = self.world, self.s
        for cid, p in list(s.get("plots", {}).items()):
            if cid not in w.agents or p["target"] not in w.agents:
                continue
            self.plot_defaults(p)
            p["days"] += 1
            a = w.agents[cid]
            if a["sanity"] >= 65 and a["aff"].get(p["target"], 0) >= 0 and a["drive"]["id"] not in AGGRESSIVE and self.rng.random() < 0.18:
                self.log_event(tick, {"type": "plot", "who": cid, "room": a["room"], "vis": "viewer",
                                      "text": f"{self.nm(cid)} lies awake and decides they cannot do it. The plan against {self.nm(p['target'])} is over."}, actor=cid)
                w.remember(cid, f"(private) You could not do it. You let {self.nm(p['target'])} live.")
                del s["plots"][cid]
                continue
            if self.days_left() <= 1 and p["stage"] in ("brooding", "preparing"):
                p["stage"], p["stage_ticks"] = "stalking", 0
                self.plan_note(p, "the deadline is too close for patience")

    def plot_lines2(self, cid):
        """Extra plot context for the plotter's prompt: the timeline so far and what the plan needs next."""
        p = self.s.get("plots", {}).get(cid)
        if not p or p["target"] not in self.world.agents:
            return []
        self.plot_defaults(p)
        needs = {"brooding": "time to think; keep your head down", "preparing": "a weapon or a method" + (f" (you have the {self.world.item_name(p['weapon'])})" if p["weapon"] else ""),
                 "stalking": "learn where they go and wait until they are alone, in a blind spot or in the dark", "striking": "strike the moment the window opens"}[p["stage"]]
        return [f"YOUR PLAN (stage {p['stage']}; your reason: {p.get('reason') or 'your own'}): needs {needs}. Timeline: {' | '.join(p['plan'][-4:]) or 'just started'}. "
                "The plan runs over several days; patience is part of it. Do not act out of order, and do not reveal it."]

    def plot_helpless(self, tick, cid, p, d, hour):
        """The target lies helpless in front of the plotter: take what they have, put them somewhere, or finish it."""
        w, s = self.world, self.s
        a, t = w.agents[cid], p["target"]
        r = self.rng.random()
        if r < 0.45 and w.agents[t]["inv"]:
            d.update(action="rob", target=t, item="", target_room="", activity=f"Goes through {self.nm(t)}'s pockets", step="searches them")
        elif r < 0.7 and not s.get("case"):
            d.update(action="attack", target=t, method=self.plot_method(p), target_room="", activity="Takes the chance", step="strikes")
            self.plan_note(p, f"killed {self.nm(t)} while they were helpless")
        elif r < 0.85:
            go = self.step_toward(cid, "cold_store")
            if go and self.can_carry(cid, t):
                d.update(action="carry", target=t, target_room=go, activity=f"Drags {self.nm(t)} out of sight", step="moves them")
