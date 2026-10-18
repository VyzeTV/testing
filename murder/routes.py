"""The ways out: several routes to 'defeat the show', each with steps tracked as percentages and a finale that can fail.

RoutesMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ESCAPE_ROUTES, ROOMS


GOOD_ENDINGS = {"truth", "shutdown", "ultimatum", "rescue"}          # "rescue_late" and "raft" are bittersweet
BAD_ENDINGS = {"reckoning", "extinction", "battle", "sole"}


def ending_tier(kind, ids):
    """Good, bittersweet or bad: the show defeated or several walking out together is good; a lone survivor or a partial escape is
    bittersweet; everyone executed, nobody left, a fight to the death or a whim is bad."""
    if kind in GOOD_ENDINGS:
        return "good"
    if kind in BAD_ENDINGS:
        return "bad"
    if kind == "winners":
        return "good" if len(ids) >= 2 else "bittersweet"
    return "bittersweet"


def _hh(h):
    return f"{h:02d}:00"


class RoutesMixin:
    # ------------------------------------------------------------------ progress
    def route_pct(self, rid):
        plan = self.s["escape"]["routes"][rid]["plan"]
        return int(round(sum(plan.values()) / len(plan)))

    def escape_progress(self):
        esc = self.s["escape"]
        if "SP-5" in self.s.get("found_edges", []):
            esc["routes"]["shutdown"]["plan"]["locate"] = 100
        esc["progress"] = max(self.route_pct(r) for r in ESCAPE_ROUTES)
        return esc["progress"]

    def escape_lines(self, cid):
        esc = self.s["escape"]
        self.escape_progress()
        learned = " | ".join(c["text"] for c in esc["clues"][-5:])
        routes = []
        fav = self.world.agents[cid].get("route") if cid in self.world.agents else None
        order = [fav] + [x for x in ESCAPE_ROUTES if x != fav] if fav in ESCAPE_ROUTES else list(ESCAPE_ROUTES)
        for rid in (order[:2] if self.lean else order):
            r = ESCAPE_ROUTES[rid]
            plan = esc["routes"][rid]["plan"]
            routes.append(f"[{rid}] {r['title']} ({self.route_pct(rid)}%): {r['blurb']}. Steps: " +
                          "; ".join(f"{k} {plan[k]}% ({r['steps'][k]})" for k in plan))
        favline = (f"YOUR FAVOURED WAY OUT is [{fav}] ({ESCAPE_ROUTES[fav]['title']}): you believe in it and push the others toward it, but you stay open if another proves better. " if fav in ESCAPE_ROUTES else "")
        return (favline + "WAYS OUT (several; any can fail; none is certain): " + " || ".join(routes) +
                " When every step of a route is complete a team can attempt its finale, which may still go wrong. "
                "If (and only if) you have a genuinely new, concrete idea, use action 'experiment' with an 'idea' (where, with what) that advances ONE step of ONE route; otherwise do something else with your turn. "
                + (f"WHAT THE CAST HAS LEARNED: {learned}" if learned else ""))

    def ready_route(self):
        s = self.s
        if not self.revealed or s.get("over") or s.get("case") or not self.world.agents:
            return None
        self.escape_progress()
        for rid in ESCAPE_ROUTES:
            if all(v >= 100 for v in s["escape"]["routes"][rid]["plan"].values()):
                return rid
        return None

    def escape_apply(self, tick, cid, d, r, hour, dice):
        """Apply the (dice-decided) outcome of an experiment to a route."""
        w, s = self.world, self.s
        esc = s["escape"]
        rid = r.get("route") if r.get("route") in ESCAPE_ROUTES else None
        step = r.get("step") if rid and r.get("step") in ESCAPE_ROUTES[rid]["steps"] else None
        try:
            gain = max(0, min(30, int(r.get("gain", r.get("progress", 0)) or 0)))
        except Exception:
            gain = 0
        gain = 0 if dice == "failure" else (max(1, gain // 2) if dice == "partial" else gain)
        before = self.escape_progress()
        if rid and step and gain:
            nv = s["npcs"]["neovi"]
            plan = esc["routes"][rid]["plan"]
            if step in ("unjam", "blind") and self.neovi_maid() and nv["aff"].get(cid, 0) >= 8:
                gain += 12
                self.log_event(tick, {"type": "mercy", "who": "neovi", "room": nv["room"], "vis": "public",
                                      "text": "NeoVi quietly helps, looking at the floor: a camera feed that stays dark for a while."}, witnesses=[cid], actor=cid)
            plan[step] = min(100 if not self.step_missing(rid, step) else max(50, plan[step]), plan[step] + gain)     # past half way only once the step's needs are met (escape.py)
            self.tally(cid, "route_steps")
            if cid not in esc["routes"][rid]["contributors"]:
                esc["routes"][rid]["contributors"].append(cid)
            self.moment(cid, f"made real progress on the way out ({ESCAPE_ROUTES[rid]['title'].lower()}: {step})")
        after = self.escape_progress()
        return before, after, rid, step, gain

    # ------------------------------------------------------------------ the finale of a route
    def finale_team(self, rid):
        w = self.world
        r = ESCAPE_ROUTES[rid]
        contrib = [c for c in self.s["escape"]["routes"][rid]["contributors"] if c in w.agents]
        extra = [c for c in w.agents if c not in contrib]
        self.rng.shuffle(extra)
        return (contrib + extra)[: r["team"]] if contrib else extra[: r["team"]]

    def finale_odds(self, rid, team):
        w, s = self.world, self.s
        rt = s["escape"]["routes"][rid]
        nv = s["npcs"]["neovi"]
        aid = self.neovi_maid() and any(nv["aff"].get(c, 0) >= 6 for c in team)
        att = rt["attempts"]
        hp = sum(w.agents[c]["hp"] for c in team) / max(1, len(team))
        san = sum(w.agents[c]["sanity"] for c in team) / max(1, len(team))
        skill = sum(1 for c in team if any(k in w.cast[c]["role"].lower() for k in ("hack", "engineer", "tech", "explor", "student")))
        base = {"transmit": 0.45, "shutdown": 0.50, "raft": 0.55, "ultimatum": 0.55}[rid]
        p = base + (0.1 if len(team) >= 2 else 0) + 0.06 * min(2, skill) - 0.05 * att
        if rid in ("transmit", "shutdown") and aid:
            p += 0.15
        if rid in ("transmit", "shutdown") and self.blackout_until >= self.idx:
            p += 0.1
        if rid == "raft":
            if s.get("island") and s["island"]["id"] in ("storm", "fog"):
                p -= 0.3
            if any(w.agents[c]["inv"].get("life_jacket", 0) for c in team):
                p += 0.1
        p -= 0.25 * max(0, 55 - san) / 55 + 0.2 * max(0, 55 - hp) / 55 + 0.07 * self.adapt_level(rid) + self.__dict__.get("_desperate", 0.0)
        return max(0.15, min(0.85, p)), aid

    def run_finale(self, rid, hour):
        """The team gathers and attempts the route's finale. It can fail, with consequences."""
        w, s = self.world, self.s
        r = ESCAPE_ROUTES[rid]
        rt = s["escape"]["routes"][rid]
        rt["attempts"] += 1
        tick = self.new_tick(hour)
        tick["type"] = "finale"
        live = rid in ("shutdown", "ultimatum", "raft")
        if live:
            self.begin_practice(tick)                                # the raid, the standoff and the launch play on the live map (finales.py)
        team = self.finale_team(rid)
        site = r["room"]
        for cid in team:
            a = w.agents[cid]
            start = a["room"]
            steps = w.path(cid, start, site) if start != site else []
            tick["moves"][cid] = {"from": start, "path": [start] + ([x for x, _, _ in steps] if steps else ([site] if start != site else [])), "to": site}
            a["room"] = site
            a["activity"] = r["title"]
            w.remember(cid, f"{_hh(hour)} The team went to the {w.room_name(site)} to go through with it: {r['title'].lower()}.")
        nroom = s["npcs"]["neovi"]["room"]
        tick["moves"]["neovi"] = {"from": nroom, "path": [nroom], "to": nroom}
        self.finale_route = rid
        if live:
            p, aid = self.finale_odds(rid, team)
            ok, self._finale_outcome = self.live_finale(tick, rid, team, hour)
        else:
            self._finale_outcome = None
            self.run_conversations(tick, {site: team + ["terevi"]}, {}, hour, mode="finale")
            p, aid = self.finale_odds(rid, team)
            ok = self.rng.random() < p
        text = self.make_broadcast("finale", {"route": rid, "ok": ok, "team": team, "aid": aid})
        tick["broadcasts"].append({"speaker": "terevi", "kind": "finale", "text": text})
        getattr(self, f"finale_{rid}")(tick, team, ok, text, hour)
        if not ok and not s.get("over"):
            self.terevi_reinforce(tick, rid, "their attempt failed")
        tick["events"].append({"type": "system_notable", "who": team[0], "room": site, "vis": "gm", "text": f"Finale odds were {int(p * 100)}%: {'it worked' if ok else 'it failed'}."})
        self.escape_progress()
        self.saga(f"The cast tried to {r['title'].lower()}: {'it worked' if ok else 'it failed'}.")
        return tick

    def _end_season(self, tick, kind, title, text, ids=None):
        ids = ids if ids is not None else list(self.world.agents)
        tier = ending_tier(kind, ids)
        costs = self.ending_costs(kind, ids)                      # a win that cost too much is bittersweet (endings.py)
        if tier == "good" and costs:
            tier = "bittersweet"
        self.s["over"] = {"kind": kind, "day": self.day, "title": title, "text": text, "tier": tier, "costs": costs}
        eps = self.make_epilogues(tick, kind, ids)
        self.s["over"]["epilogues"] = eps
        tick["ending"] = {"kind": kind, "title": title, "text": text, "ids": ids, "tier": tier, "costs": costs, "epilogues": eps}

    def finale_transmit(self, tick, team, ok, text, hour):
        w, s = self.world, self.s
        esc = s["escape"]["routes"]["transmit"]["plan"]
        if ok:
            self.fx(tick, "confetti", "lighthouse")
            for cid in w.agents:
                self.special_boost(tick, cid, 8, "the truth got out", "comfort")
            res = "The broadcast went out, and this time the world believed it. Somewhere, people are on their way."
            self.start_rescue(tick, "broadcast", "the broadcast of the truth was believed")       # the countdown (outside.py)
        else:
            esc["unjam"] = min(esc["unjam"], 40)
            esc["device"] = max(0, esc["device"] - 40)
            res = "TereVi jammed the broadcast at the last moment. The transmitter is damaged and her grip is tighter."
            for cid in team:
                self.stat(tick, cid, "sanity", -10, "the broadcast failed")
            self.force_tease = "The cast just tried to broadcast the truth and you stopped it. Gloat, and make them regret trying."
            self.fx(tick, "flash", "lighthouse")
        tick["events"].append({"type": "system_notable", "who": team[0], "room": "lighthouse", "vis": "public", "text": res})
        self.day_notable.append(res)

    def finale_shutdown(self, tick, team, ok, text, hour):
        w, s = self.world, self.s
        plan = s["escape"]["routes"]["shutdown"]["plan"]
        if ok:
            self.parting_shot(tick, "shutdown", team)
            self._end_season(tick, "shutdown", "TEREVI IS SHUT DOWN", text)
            self.fx(tick, "dark")
            res = "The core goes dark. TereVi's voice stretches into static and dies. The doors unlock across the island."
        else:
            plan["approach"] = min(plan["approach"], 40)
            plan["means"] = min(plan["means"], 50)
            how = getattr(self, "_finale_outcome", None)
            res = {"sealed in": "TereVi seals the hatch on the raid. Hours later NeoVi lets them out, filthy and shaking.",
                   "betrayed": "One of the raiders runs for the alarm. The vault floods with light and the raid falls apart.",
                   "a death in the vault": "The vault's guns find their mark. The raid ends with a body on the steps."}.get(
                how, "The Core Vault fights back: the turrets wake, the doors slam, and TereVi laughs through the speakers. The attempt collapses.")
            for cid in list(team) if how in (None, "the core held") else []:
                if cid in w.agents:
                    self.stat(tick, cid, "hp", -self.rng.randint(10, 28), "the vault's defences", lethal="cut down in the Core Vault")
                    self.stat(tick, cid, "sanity", -6, "the vault's defences")
                if s.get("case"):
                    break
            self.fx(tick, "shake", "core_vault")
            self.force_tease = "The cast just tried to destroy you in your vault. Be furious, cruel and delighted."
        tick["events"].append({"type": "system_notable", "who": team[0], "room": "core_vault", "vis": "public", "text": res})
        self.day_notable.append(res)

    def finale_raft(self, tick, team, ok, text, hour):
        w, s = self.world, self.s
        plan = s["escape"]["routes"]["raft"]["plan"]
        if ok:
            crew = [c for c in (getattr(self, "_raft_crew", None) or team) if c in w.agents]
            names = ", ".join(self.nm(c) for c in crew)
            res = f"{names} push off from the beach and the raft slips into the dark water, out of TereVi's reach. The show goes on without them."
            tick["raft"] = {"ids": list(crew), "text": text}
            self.raft_away(tick, crew, self.escape_proof())                 # their journey goes on off-screen (outside.py)
            plan["materials"] = plan["build"] = plan["launch"] = 0
            plan["provisions"] = min(plan["provisions"], 30)
            s["escape"]["routes"]["raft"]["parts"] = {}
            if not w.agents:
                self._end_season(tick, "raft", "ONLY THE RAFT GOT AWAY", text, ids=list(crew))
        else:
            plan["build"] = 0
            plan["materials"] = min(plan["materials"], 30)
            res = "The raft breaks apart in the surf before it has cleared the rocks. The sea takes everything."
            for cid in team:
                self.stat(tick, cid, "hp", -self.rng.randint(5, 15), "the wrecked raft")
                self.stat(tick, cid, "sanity", -10, "the wrecked raft")
            if self.rng.random() < 0.3 and not s.get("case"):
                self.accident_death(tick, self.rng.choice(team), "drowned when the raft broke apart", detail="the raft broke apart in the surf")
            self.force_tease = "The cast's raft just fell apart on the rocks. Mock them tenderly."
        tick["events"].append({"type": "system_notable", "who": team[0], "room": "beach", "vis": "public", "text": res})
        self.day_notable.append(res)

    def finale_ultimatum(self, tick, team, ok, text, hour):
        w, s = self.world, self.s
        plan = s["escape"]["routes"]["ultimatum"]["plan"]
        if ok:
            self.parting_shot(tick, "ultimatum", team)
            self._end_season(tick, "ultimatum", "THE SHOW SURRENDERS", text)
            res = "TereVi blinks first. The doors unlock and the boats' chains drop away: the show is over."
        elif getattr(self, "_finale_outcome", None) in ("backed down", "betrayed"):
            plan["plant"] = 0
            plan["trigger"] = 0
            res = ("The trigger is in TereVi's hands now. NeoVi carries the charges away, one by one." if self._finale_outcome == "betrayed"
                   else "They back down. NeoVi disarms the charges while TereVi hums a little tune.")
            self.force_tease = "The cast threatened to blow up your island and folded. Mock them for it."
        else:
            plan["plant"] = 0
            plan["explosives"] = min(plan["explosives"], 30)
            res = "TereVi calls the bluff. The charge goes off in the Generator Shed in a roar of flame and the whole island goes dark."
            for r2, st2 in (("shutdown", "blind"), ("transmit", "unjam")):
                p2 = s["escape"]["routes"][r2]["plan"]
                p2[st2] = min(100, p2[st2] + 30)                     # her cameras and jammers are down for a while
            self.blackout_until = self.idx + 2
            self.env_explosion(tick, "generator_shed")
            for cid in list(team):
                if cid in w.agents:
                    self.stat(tick, cid, "hp", -self.rng.randint(15, 35), "the blast", lethal="killed in the blast at the Generator Shed")
                    self.stat(tick, cid, "sanity", -8, "the blast")
                if s.get("case"):
                    break
            self.fx(tick, "flash", "generator_shed")
            self.fx(tick, "shake", "generator_shed")
            self.force_tease = "The cast threatened to blow up your island and you called their bluff. Savour it."
        tick["events"].append({"type": "system_notable", "who": team[0], "room": "generator_shed", "vis": "public", "text": res})
        self.day_notable.append(res)
