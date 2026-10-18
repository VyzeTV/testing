"""When things get dark: rigged traps, NeoVi's rebellion arc, killing sprees, the endgame when too few survive, and TereVi learning.

MayhemMixin is mixed into DayRunner (engine.py).
"""
from collections import Counter

from .data_world import ROOMS, ESCAPE_ROUTES
from .llm import LLMError
from .world import clamp

TOOLS = ("crowbar", "pipe_wrench", "hammer", "wire", "sledgehammer")
DRINKS = ("wine_bottle", "champagne", "spirits", "water_bottle", "sparkling_water", "energy_drink")
FALL_ROOMS = {"upper_landing", "landing", "lookout", "water_tower", "basement_hall", "boiler_room", "pool", "attic", "wine_cellar", "lighthouse"}
TRAP_WHAT = {"fall": "the stairs, railing or footing", "drink": "a bottle", "blade": "the doorway", "snare": "the floor by the door"}
TRAP_CAUSE = {"fall": "trap_fall", "drink": "trap_drink", "blade": "trap_blade"}
ARC_STAGES = ["servile", "doubting", "secretly helping", "defiant", "ready to act"]
BLIND_STEP = {"transmit": "unjam", "shutdown": "blind", "raft": "launch", "ultimatum": "leverage"}
HARDEN = {"transmit": {"unjam": 20, "device": 10}, "shutdown": {"approach": 20, "means": 10}, "raft": {"build": 20, "launch": 25},
          "ultimatum": {"plant": 25, "trigger": 15}}


def _hh(h):
    return f"{h:02d}:00"


class MayhemMixin:
    # ------------------------------------------------------------------ rigged traps
    def rig_options(self, cid):
        w = self.world
        a = w.agents[cid]
        opts = []
        inv = a["inv"]
        if any(inv.get(t, 0) > 0 for t in TOOLS) and (a["room"] in FALL_ROOMS or any(a["room"] in (b["a"], b["b"]) for b in w.state.get("built", []))):
            opts.append("fall")
        poison = any("poison" in w.item_spec(k).get("tags", []) for k in inv)
        drink = any(k in DRINKS for k in inv) or any(k in DRINKS for k in self.s["room_items"].get(a["room"], {}))
        if poison and drink:
            opts.append("drink")
        if any("sharp" in w.item_spec(k).get("tags", []) for k in inv) and any(inv.get(t, 0) > 0 for t in ("wire", "masking_tape", "rope")):
            opts.append("blade")
        if self.snare_ready(cid):
            opts.append("snare")
        return opts

    def rig_lines(self, cid):
        if not self.murders or self.s.get("case") or self.s.get("spree"):
            return []
        opts = self.rig_options(cid)
        if not opts:
            return []
        return ["TRAPS: you can rig a trap here instead of attacking in person (action 'rig' with \"rig\": {\"kind\": \"" + "|".join(opts) + "\", \"target\": \"<person id or empty>\"}). "
                "It kills later, without you present (so you can have an alibi), but it leaves tampering that investigators can find and it may catch the wrong person. "
                "A fall needs a tool, a drink needs poison and a bottle, a blade needs a sharp weapon and wire, tape or rope, a snare (kind 'snare') needs mouse traps and string, wire or tape and only hurts."]

    def do_rig(self, tick, cid, d):
        w, s = self.world, self.s
        a = w.agents[cid]
        spec = d.get("rig") or {}
        kind = spec.get("kind")
        opts = self.rig_options(cid)
        name = self.nm(cid)
        if kind not in opts:
            self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm", "text": f"{name} wanted to rig something but lacked the means."}, actor=cid)
            return
        target = spec.get("target") if spec.get("target") in w.agents and spec.get("target") != cid else None
        good, luck = self.roll(cid, 0.7)
        items = []
        if kind == "drink":
            pk = next(k for k in a["inv"] if "poison" in w.item_spec(k).get("tags", []))
            a["inv"][pk] -= 1
            if a["inv"][pk] <= 0:
                del a["inv"][pk]
            items = [pk]
        elif kind == "snare":
            a["inv"]["mouse_traps"] -= 1
            if a["inv"]["mouse_traps"] <= 0:
                del a["inv"]["mouse_traps"]
            bd = next(b for b in ("string", "wire", "masking_tape", "duct_tape") if a["inv"].get(b, 0) > 0)
            a["inv"][bd] -= 1
            if a["inv"][bd] <= 0:
                del a["inv"][bd]
            items = ["mouse_traps", bd]
        elif kind == "blade":
            tk = next(t for t in ("wire", "masking_tape", "rope") if a["inv"].get(t, 0) > 0)
            a["inv"][tk] -= 1
            if a["inv"][tk] <= 0:
                del a["inv"][tk]
            sk = next(k for k in a["inv"] if "sharp" in w.item_spec(k).get("tags", []))
            items = [tk, sk]
        else:
            items = [next(t for t in TOOLS if a["inv"].get(t, 0) > 0)]
        here = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid]
        if not good:
            self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm", "text": f"{name} tried to rig {TRAP_WHAT[kind]} but botched it."}, actor=cid)
            return
        s.setdefault("traps", []).append({"by": cid, "room": a["room"], "kind": kind, "target": target, "day": self.day, "hour": tick["hour"],
                                          "ledger": {c: ag["room"] for c, ag in w.agents.items()}, "items": items})
        self.log_event(tick, {"type": "plot", "who": cid, "room": a["room"], "vis": "viewer",
                              "text": f"{name} quietly rigs {TRAP_WHAT[kind]} in the {w.room_name(a['room'])}" + (f" with {self.nm(target)} in mind." if target else ".")}, actor=cid)
        for o in here:
            if self.rng.random() < 0.3:
                w.remember(o, f"{_hh(tick['hour'])} (odd) You saw {name} fiddling with {TRAP_WHAT[kind]} in the {w.room_name(a['room'])}, and thought nothing of it.")
        self.moment(cid, f"rigged a trap in the {w.room_name(a['room'])}")

    def resolve_traps(self, tick, hour):
        w, s = self.world, self.s
        traps = s.get("traps") or []
        if not traps or s.get("case") and not s.get("spree"):
            return
        keep = []
        for t in traps:
            room = t["room"]
            present = [c for c in w.occupants(room) if c in w.agents and c != t["by"]]
            arrived = [c for c in present if (tick["moves"].get(c) or {}).get("from") != room]
            pool = present if t["kind"] == "drink" else arrived
            victim = None
            if t["target"] in pool:
                victim = t["target"]
            elif pool and self.rng.random() < (0.35 if t["kind"] == "drink" else 0.5):
                victim = self.rng.choice(pool)
            if not victim or (s.get("case") and not s.get("spree")):
                keep.append(t)
                continue
            a = w.agents[victim]
            if t["kind"] == "snare":
                dmg = self.rng.randint(8, 18)
                self.log_event(tick, {"type": "mishap", "who": victim, "room": room, "vis": "public",
                                      "text": f"{self.nm(victim)} steps on a tripcord by the door in the {w.room_name(room)} and a spring trap snaps shut on their foot."}, witnesses=[o for o in present if o != victim], actor=victim)
                self.stat(tick, victim, "hp", -dmg, "a snare")
                self.stat(tick, victim, "sanity", -3, "a snare")
                if t["by"] in w.agents:
                    self.new_hook(tick, "snare", [victim], t["by"], room, f"Someone rigged a trap for whoever came through the door of the {w.room_name(room)}.", ["The cord was tied off neatly, with string or wire from somewhere."], [])
                continue
            p = {"fall": 0.5, "drink": 0.75, "blade": 0.65}[t["kind"]] + (0.2 if a["hp"] < 50 else 0)
            good, luck = self.roll(t["by"], min(0.95, p))
            others = [o for o in present if o != victim]
            if good and t["by"] in w.all_agents:
                self.open_case(tick, "murder", victim, culprit=t["by"] if t["by"] in w.agents else None, wkind=TRAP_CAUSE[t["kind"]], weapon=None, room=room, hour=hour,
                               witnesses=others, trap=t, mistaken=(t["target"] is not None and victim != t["target"]))
            else:
                dmg = self.rng.randint(15, 35)
                self.log_event(tick, {"type": "mishap", "who": victim, "room": room, "vis": "public",
                                      "text": f"{self.nm(victim)} triggers a rigged {t['kind']} in the {w.room_name(room)} and barely survives."}, witnesses=others, actor=victim)
                self.stat(tick, victim, "hp", -dmg, "a rigged trap")
                self.stat(tick, victim, "sanity", -6, "a rigged trap")
                if victim in w.agents:
                    self.injure(tick, victim, t["by"], {"sharp"} if t["kind"] == "blade" else set(), dmg, "blade" if t["kind"] == "blade" else "fall")
                    if t["kind"] == "drink":
                        self.add_cond(tick, victim, "poisoned", 2, "a poisoned bottle", turns=6)
                w.remember(victim, f"{_hh(hour)} Something in the {w.room_name(room)} had been rigged to hurt someone. Whoever did it meant it.")
                self.moment(victim, "survived a rigged trap")
                w.remember(t["by"], f"{_hh(hour)} (private) Your trap in the {w.room_name(room)} went off, but it did not kill.") if t["by"] in w.agents else None
        s["traps"] = keep

    # ------------------------------------------------------------------ collapse: the killing spree
    def collapse_metrics(self):
        w = self.world
        ags = list(w.agents.values())
        if len(ags) < 2:
            return 100, 0
        san = sum(a["sanity"] for a in ags) / len(ags)
        pairs = [x for a in ags for x in a["aff"].values()]
        return san, (sum(pairs) / len(pairs) if pairs else 0)

    def spree_lines(self, cid):
        sp = self.s.get("spree")
        if not sp or cid not in self.world.agents:
            return []
        if cid == sp["by"]:
            return ["YOU HAVE SNAPPED INTO A KILLING FRENZY. You mean to kill everyone, one after another, and nothing the others say reaches you. Each turn choose your next victim (action 'attack' or 'assault'); "
                    "hunt the weakest, the lonely, the ones who wronged you. You may still make mistakes."]
        known = sp.get("known", {}).get(cid)
        who = f"It is {self.nm(sp['by'])}." if known else "You may not know who it is."
        return [f"SOMEONE IS HUNTING THE CAST: people are dying one after another and there are no trials any more. {who} Survive: stay together, barricade yourselves in a bedroom, flee, arm yourselves, or kill the killer. "
                "Killing the killer in self-defence is not punished and there will be no trial. Fear makes people suspicious of each other."]

    def maybe_spree(self, tick, hour):
        w, s = self.world, self.s
        if not self.murders or s.get("spree") or s.get("case") or len(w.agents) < 4:
            return
        san, aff = self.collapse_metrics()
        if san >= 30 or aff >= 1.0:
            return
        cand = [c for c, a in w.agents.items() if a["sanity"] < 20 and a["drive"]["id"] in ("nihilist", "avenger", "saboteur", "thrill")]
        if not cand or self.rng.random() >= 0.3 * self.chaos_factor():
            return
        by = min(cand, key=lambda c: w.agents[c]["sanity"])
        self.start_spree(tick, hour, by, f"Something gives way in {self.nm(by)}. The killing is about to begin.")

    def start_spree(self, tick, hour, by, text_):
        w, s = self.world, self.s
        s["spree"] = {"by": by, "since_day": self.day, "kills": 0, "known": {}, "quiet": 0}
        self.log_event(tick, {"type": "madness", "who": by, "room": w.agents[by]["room"], "vis": "viewer",
                              "text": text_}, actor=by)
        text = self.make_broadcast("spree", {"by": by})
        tick["broadcasts"].append({"speaker": "terevi", "kind": "deadline", "text": text})
        for cid in w.agents:
            w.remember(cid, f"{_hh(hour)} TereVi announced that the house has turned: someone has begun to kill, and there will be no trials while the knives are out.")
        self.fx(tick, "flash")
        self.day_notable.append("A killing spree began.")
        self.saga("The house collapsed into a killing spree.")

    def spree_override(self, tick, decisions):
        """The frenzied killer hunts: they walk toward the nearest prey and strike when someone is in reach."""
        w, s = self.world, self.s
        sp = s.get("spree")
        if not sp:
            return []
        by = sp["by"]
        if by not in w.agents or by not in decisions:
            return []
        a = w.agents[by]
        d = decisions[by]
        here = [o for o in w.occupants(a["room"]) if o in w.agents and o != by]
        extra = []
        if d.get("action") not in ("attack", "assault") and here and self.rng.random() < 0.75:
            t = min(here, key=lambda o: (w.agents[o]["hp"], a["aff"].get(o, 0)))
            weap = next((k for k in a["inv"] if "weapon" in w.item_spec(k).get("tags", [])), None) \
                or next((k for k, q in s["room_items"].get(a["room"], {}).items() if q > 0 and "weapon" in w.item_spec(k).get("tags", [])), None)
            extra.append((by, {"target": t, "method": weap or "hands", "activity": "", "thought": "", "frame": ""}))
        elif not here:
            prey = [c for c in w.agents if c != by]
            if prey:
                best = min(prey, key=lambda c: len(w.path(by, a["room"], w.agents[c]["room"]) or [None] * 99))
                d["target_room"] = w.agents[best]["room"]
        return extra

    def spree_death(self, tick, hour):
        """A death during a spree: no investigation, no trial."""
        w, s = self.world, self.s
        case = s.get("case")
        sp = s.get("spree")
        if not case or not sp:
            return
        victim = case["victim"]
        killer = case["killer"]
        case["announced"] = True
        text = self.make_broadcast("spree_death", {"victim": victim, "forced_room": None})
        tick["broadcasts"].append({"speaker": "terevi", "kind": "verdict", "text": text})
        bodies = s.setdefault("bodies", [])
        bodies.append({"victim": victim, "room": case["room"], "day": self.day, "by": [], "desc": f"{self.nm(victim)} {self.body_desc(case)}."})
        for cid in w.agents:
            w.remember(cid, f"{_hh(hour)} {self.nm(victim)} is dead, killed in the frenzy. There will be no trial.")
        self.mourn(tick, victim, "killed in the frenzy", hour)
        s["vacancies"].append({"gender": w.cast[victim]["gender"], "reason": f"{w.cast[victim]['name']} left the show"})
        if killer == sp["by"]:
            sp["kills"] += 1
            sp["quiet"] = 0
        elif killer and victim == sp["by"]:
            self.log_event(tick, {"type": "system_notable", "who": killer, "room": case["room"], "vis": "public",
                                  "text": f"{self.nm(killer)} killed {self.nm(victim)}, ending the killing."}, actor=killer)
            self.moment(killer, f"killed {self.nm(victim)} to stop the killing")
            s["spree"] = None
        self.clear_notebooks()
        s["case"] = None

    def spree_upkeep(self, tick, hour):
        w, s = self.world, self.s
        sp = s.get("spree")
        # people who stumble on a spree body
        for b in s.get("bodies", []):
            for cid in w.occupants(b["room"]):
                if cid in w.agents and cid not in b["by"]:
                    b["by"].append(cid)
                    self.log_event(tick, {"type": "body", "who": cid, "room": b["room"], "vis": "public", "text": f"{self.nm(cid)} finds {b['desc']}"}, actor=cid)
                    self.stat(tick, cid, "sanity", -5, "a body")
                    tick["scene_body"] = {"victim": b["victim"], "by": cid, "room": b["room"], "desc": b["desc"]}
        if not sp:
            return
        if sp["by"] not in w.agents:
            s["spree"] = None
            return
        sp["quiet"] = sp.get("quiet", 0) + 1
        if sp["quiet"] >= 8 or len(w.agents) <= 3:
            self.log_event(tick, {"type": "system_notable", "who": sp["by"], "room": w.agents[sp["by"]]["room"], "vis": "public",
                                  "text": "The frenzy burns itself out." if len(w.agents) > 3 else "There are too few left for the killing to go on."}, actor=sp["by"])
            s["spree"] = None

    # ------------------------------------------------------------------ the endgame: too few survivors
    def terevi_mood(self):
        s = self.s
        anger = min(1.0, s["escape"]["progress"] / 100 + 0.1 * sum(s.get("adapt", {}).get("hardness", {}).values()))
        weights = {"battle": 0.35 + 0.4 * anger, "crown": 0.35 + 0.2 * (1 - anger), "capricious": 0.2}
        tot = sum(weights.values())
        r = self.rng.random() * tot
        for k, v in weights.items():
            r -= v
            if r <= 0:
                return k
        return "crown"

    def endgame_due(self):
        s, w = self.s, self.world
        if not self.revealed or s.get("over") or s.get("case"):
            return False
        return len(w.agents) <= 3

    def run_endgame(self, hour):
        w, s = self.world, self.s
        tick = self.new_tick(hour)
        tick["type"] = "endgame"
        alive = list(w.agents)
        site = "voting_grounds"
        if not alive:
            self._end_season(tick, "extinction", "NOBODY LEFT", "The island is silent. Nobody is left to win.", ids=[])
            return tick
        mood = "crown" if len(alive) == 1 else self.terevi_mood()
        for cid in alive:
            a = w.agents[cid]
            start = a["room"]
            steps = w.path(cid, start, site) if start != site else []
            tick["moves"][cid] = {"from": start, "path": [start] + ([r for r, _, _ in steps] if steps else ([site] if start != site else [])), "to": site}
            a["room"] = site
            a["activity"] = "The finale"
            w.remember(cid, f"{_hh(hour)} TereVi called the last survivors to the Voting Grounds to decide how the show ends.")
        self.neovi_attend(tick, site)
        self.endgame_mood = mood
        self.run_conversations(tick, {site: alive + ["terevi"]}, {}, hour, mode="endgame")
        ids = list(alive)
        if mood == "battle" and len(alive) >= 2:
            rounds, winners = self.final_battle(alive)
            tick["battle"] = {"rounds": rounds, "survivors": winners}
            text = self.make_broadcast("endgame", {"mood": "battle", "alive": alive, "winners": winners})
            tick["broadcasts"].append({"speaker": "terevi", "kind": "finale", "text": text})
            for cid in alive:
                if cid not in winners:
                    w.end_agent(cid, "dead", "died in the final battle")
            for cid in winners:
                self.stat(tick, cid, "hp", -self.rng.randint(5, 25), "the final battle")
            if winners:
                self._end_season(tick, "battle", f"THE LAST BATTLE: {self.nm(winners[0]).upper()} STANDS", text, ids=winners)
            else:
                self._end_season(tick, "extinction", "NOBODY LEFT", text, ids=[])
        elif mood == "capricious" and len(alive) >= 2:
            champ = max(alive, key=lambda c: (w.agents[c]["hp"] * 0.3 + w.agents[c]["sanity"] * 0.3 + self.rng.random() * 40))
            text = self.make_broadcast("endgame", {"mood": "capricious", "alive": alive, "winners": [champ]})
            tick["broadcasts"].append({"speaker": "terevi", "kind": "finale", "text": text})
            tick["executions_left"] = [c for c in alive if c != champ]
            for cid in alive:
                if cid != champ:
                    w.end_agent(cid, "executed", "executed by TereVi's whim")
            self._end_season(tick, "sole", f"CROWNED BY WHIM: {self.nm(champ).upper()}", text, ids=[champ])
        else:
            # she crowns everyone left (1 to 3 winners), unless they are too broken to walk out
            walkers = [c for c in alive if w.agents[c]["hp"] > 15]
            text = self.make_broadcast("endgame", {"mood": "crown", "alive": alive, "winners": walkers})
            tick["broadcasts"].append({"speaker": "terevi", "kind": "finale", "text": text})
            for cid in alive:
                if cid not in walkers:
                    w.end_agent(cid, "dead", "died of their injuries")
            if walkers:
                self._end_season(tick, "winners", "THE WINNERS" if len(walkers) > 1 else "THE LAST ONE STANDING", text, ids=walkers)
            else:
                self._end_season(tick, "extinction", "NOBODY LEFT", text, ids=[])
        res = f"TereVi ended the show with {len(alive)} left standing ({mood})."
        tick["events"].append({"type": "system_notable", "who": alive[0], "room": site, "vis": "public", "text": res})
        self.day_notable.append(res)
        return tick

    def final_battle(self, alive):
        """Survivors fight; strength is health, grit and luck. Wounds can kill the winner too."""
        w = self.world
        pool = list(alive)
        rounds = []
        pw = lambda c: w.agents[c]["hp"] + 0.3 * (100 - w.agents[c]["sanity"]) + (15 if any("weapon" in w.item_spec(k).get("tags", []) for k in w.agents[c]["inv"]) else 0)
        while len(pool) > 1:
            a, b = self.rng.sample(pool, 2)
            pa, pb = pw(a), pw(b)
            win, lose = (a, b) if self.rng.random() < pa / (pa + pb) else (b, a)
            dmg = self.rng.randint(15, 45)
            w.agents[win]["hp"] -= dmg
            rounds.append({"a": a, "b": b, "winner": win, "dmg": dmg})
            pool.remove(lose)
            if w.agents[win]["hp"] <= 0:
                pool.remove(win)          # both fall: a mutual end
                w.agents[win]["hp"] = 0
        return rounds, pool

    # ------------------------------------------------------------------ NeoVi's rebellion
    def neovi_arc(self):
        nv = self.s["npcs"]["neovi"]
        return nv.setdefault("arc", {"resolve": 0, "stage": 0, "fate": None, "ally": None})

    def neovi_arc_night(self, tick):
        w, s = self.world, self.s
        nv = s["npcs"]["neovi"]
        arc = self.neovi_arc()
        if arc["fate"]:
            return
        friends = [c for c in w.agents if nv["aff"].get(c, 0) >= 5]
        gain = 1 + 3 * min(2, len(friends)) + (2 if self.death_today else 0) + (2 if s["escape"]["progress"] >= 40 else 0) \
            + 2 * min(2, getattr(self, "punish_count", 0)) - (2 if nv["fear"] >= 7 else 0)
        self.punish_count = 0
        arc["resolve"] = clamp(arc["resolve"] + gain)
        stage = 0 if arc["resolve"] < 20 else 1 if arc["resolve"] < 40 else 2 if arc["resolve"] < 60 else 3 if arc["resolve"] < 80 else 4
        if stage > arc["stage"]:
            arc["stage"] = stage
            self.log_event(tick, {"type": "drive", "who": "neovi", "room": nv["room"], "vis": "viewer",
                                  "text": f"NeoVi's resolve hardens: she is now {ARC_STAGES[stage]}."})
        if not friends:
            return
        ally = max(friends, key=lambda c: nv["aff"].get(c, 0))
        arc["ally"] = ally
        if stage >= 3 and self.rng.random() < 0.5:
            rid = w.agents[ally].get("route") or "transmit"
            step = BLIND_STEP[rid]
            plan = s["escape"]["routes"][rid]["plan"]
            plan[step] = min(100, plan[step] + 8)
            self.log_event(tick, {"type": "mercy", "who": "neovi", "room": nv["room"], "vis": "viewer",
                                  "text": f"NeoVi quietly dims a camera feed and loosens a latch for {self.nm(ally)}."}, actor=ally)
        if stage >= 4:
            self.neovi_climax(tick, ally)

    def neovi_climax(self, tick, ally):
        w, s = self.world, self.s
        nv = s["npcs"]["neovi"]
        arc = self.neovi_arc()
        san, aff = self.collapse_metrics()
        deaths_week = sum(1 for g in s["graveyard"] if g.get("day", 0) > self.day - 7)
        out_of_control = san < 30 or deaths_week >= 3 or bool(s.get("spree"))
        r = self.rng.random()
        if out_of_control and r < 0.6:
            fate = "betrayer"
        elif s["escape"]["progress"] >= 60 or r < 0.5:
            fate = "martyr"
        else:
            fate = "survivor"
        arc["fate"] = fate
        text = self.make_broadcast("neovi_end", {"fate": fate, "ally": ally})
        tick["broadcasts"].append({"speaker": "neovi", "kind": "neovi", "text": text})
        caring = [c for c in w.agents if nv["aff"].get(c, 0) >= 3 or w.agents[c]["aff"].get("neovi", 0) >= 3]
        if fate == "martyr":
            for rid, step in BLIND_STEP.items():
                plan = s["escape"]["routes"][rid]["plan"]
                plan[step] = min(100, plan[step] + 25)
            self.blackout_until = self.idx + 2
            nv["room"] = "none"
            self.log_event(tick, {"type": "system_notable", "who": "neovi", "room": "foyer", "vis": "public",
                                  "text": "NeoVi takes TereVi's eyes with her. She is gone, and every feed on the island goes dark."})
            for c in caring:
                self.stat(tick, c, "sanity", -8, "NeoVi's sacrifice")
                self.moment(c, "NeoVi gave her life to help us")
            self.fx(tick, "dark")
        elif fate == "survivor":
            nv["fear"] = 0
            nv["inv"]["master_key"] = 0
            w.agents[ally]["inv"]["master_key"] = w.agents[ally]["inv"].get("master_key", 0) + 1
            s["unlocked"].extend([e for e in ("study_door", "master_door", "boathouse_door") if e not in s["unlocked"]])
            self.log_event(tick, {"type": "system_notable", "who": "neovi", "room": nv["room"], "vis": "public",
                                  "text": f"NeoVi defies TereVi openly, presses her master key into {self.nm(ally)}'s hand and lets every lock fall open. She is punished, and she survives."})
            for c in caring:
                self.special_boost(tick, c, 6, "NeoVi stood up", "comfort")
            self.fx(tick, "hearts", nv["room"])
        else:
            for c in w.agents:
                nv["aff"][c] = nv["aff"].get(c, 0) - 5
                self.adjust_any_aff(c, "neovi", -5)
            top = max(ESCAPE_ROUTES, key=lambda r: self.route_pct(r))
            self.terevi_reinforce(tick, top, "NeoVi told her everything", strong=True)
            contrib = [c for c in s["escape"]["routes"][top]["contributors"] if c in w.agents]
            hurt = self.rng.choice(contrib or list(w.agents))
            self.stat(tick, hurt, "hp", -25, "NeoVi turned on them")
            self.log_event(tick, {"type": "betrayal", "who": "neovi", "room": nv["room"], "vis": "public",
                                  "text": f"NeoVi, hollowed out by the killing, sells the cast to TereVi and tases {self.nm(hurt)} where they stand."}, witnesses=[hurt], actor=hurt)
            for c in caring:
                self.stat(tick, c, "sanity", -6, "NeoVi's betrayal")
                self.moment(c, "NeoVi betrayed us")
        self.saga(f"NeoVi's arc ended: {fate}.")
        self.day_notable.append(f"NeoVi's arc ended ({fate}).")

    # ------------------------------------------------------------------ TereVi learns
    def adapt_state(self):
        return self.s.setdefault("adapt", {"hardness": {rid: 0 for rid in ESCAPE_ROUTES}, "marks": {}})

    def adapt_level(self, rid=None):
        h = self.adapt_state()["hardness"]
        return h.get(rid, 0) if rid else sum(h.values())

    def terevi_reinforce(self, tick, rid, why, strong=False):
        s = self.s
        ad = self.adapt_state()
        ad["hardness"][rid] = min(3, ad["hardness"].get(rid, 0) + (2 if strong else 1))
        plan = s["escape"]["routes"][rid]["plan"]
        hit = []
        for step, amt in HARDEN[rid].items():
            if plan[step] > 0:
                plan[step] = max(0, plan[step] - amt * (2 if strong else 1))
                hit.append(step)
        text = self.make_broadcast("countermeasure", {"route": rid, "why": why, "level": ad["hardness"][rid]})
        tick["broadcasts"].append({"speaker": "terevi", "kind": "tease", "text": text})
        self.log_event(tick, {"type": "tease", "who": "terevi", "room": "foyer", "vis": "gm",
                              "text": f"TereVi reinforces against '{ESCAPE_ROUTES[rid]['title']}' (level {ad['hardness'][rid]}): {', '.join(hit) or 'she is ready'} set back."})
        self.escape_counter(tick, rid, strong)                     # what the cast sees her do about it (escape.py)
        self.escape_progress()

    def adapt_check(self, tick, hour):
        """When a route gets dangerously far along, TereVi notices and counters it (once per threshold)."""
        ad = self.adapt_state()
        for rid in ESCAPE_ROUTES:
            pct = self.route_pct(rid)
            for th in (50, 80):
                key = f"{rid}:{th}"
                if pct >= th and key not in ad["marks"]:
                    ad["marks"][key] = self.day
                    if self.rng.random() < 0.7:
                        self.terevi_reinforce(tick, rid, f"it reached {th}%")
                    return

    # ------------------------------------------------------------------ when a murder plan goes wrong
    def retarget(self, cid, a):
        """The intended victim is gone: a bitter or unhinged plotter may turn on someone else who is there."""
        w = self.world
        here = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid and a["aff"].get(o, 0) <= -4]
        if not here or not (a["sanity"] < 45 or a["drive"]["id"] in ("avenger", "nihilist", "thrill")):
            return None
        return min(here, key=lambda o: a["aff"].get(o, 0)) if self.rng.random() < 0.45 else None

    def interrupted(self, tick, cid, t, here, hour):
        """Someone who loves the victim may throw themselves between them and the attacker."""
        w = self.world
        prot = [o for o in here if o in w.agents and w.agents[o]["aff"].get(t, 0) >= 5 and w.agents[o]["aff"].get(cid, 0) > -9 and w.agents[o]["hp"] > 20]
        if not prot or self.rng.random() >= 0.3 + 0.12 * (len(prot) - 1):
            return False
        o = max(prot, key=lambda x: w.agents[x]["aff"].get(t, 0))
        name, tname, oname = self.nm(cid), self.nm(t), self.nm(o)
        room = w.agents[cid]["room"]
        self.log_event(tick, {"type": "mercy", "who": o, "room": room, "vis": "public",
                              "text": f"{name} lunges for {tname}, but {oname} throws themselves in the way and the attack is stopped."}, witnesses=here + [t], actor=o)
        self.stat(tick, cid, "hp", -10, f"stopped by {oname}")
        w.adjust_aff(t, o, 3)
        for x in here + [t]:
            self.adjust_any_aff(x, cid, -4)
        w.remember(cid, f"{_hh(hour)} (private) {oname} stopped you. Everyone saw what you tried to do.")
        w.remember(t, f"{_hh(hour)} {name} tried to kill you and {oname} stopped them.")
        self.moment(t, f"{oname} saved you from {name}")
        self.moment(o, f"stopped {name} from killing {tname}")
        self.tally(o, "saves")
        self.s["plots"].pop(cid, None)
        return True

    def counter_kill(self, tick, cid, t, weapon, hour, here):
        """The victim turns it around: the would-be killer dies, and by the killing-blow rule the victim is the one responsible."""
        w, s = self.world, self.s
        a, v = w.agents[cid], w.agents[t]
        room = a["room"]
        vweap = next((k for k in v["inv"] if "weapon" in w.item_spec(k).get("tags", [])), None) or \
            next((k for k, q in s["room_items"].get(room, {}).items() if q > 0 and "weapon" in w.item_spec(k).get("tags", [])), None)
        p = 0.10 + (0.10 if v["hp"] > a["hp"] else 0) + (0.12 if vweap else 0) + (0.08 if self.slip_chance(cid) > 0.2 else 0) - 0.1 * self.slip_chance(t)
        if self.rng.random() >= max(0.03, min(0.4, p)):
            return False
        if vweap and v["inv"].get(vweap, 0) <= 0:
            w.take(t, vweap, 1)
        tags = w.item_spec(vweap).get("tags", []) if vweap else []
        kind = "sharp" if "sharp" in tags else "blunt" if "blunt" in tags else "hands"
        name, tname = self.nm(cid), self.nm(t)
        wn = w.item_name(vweap) if vweap else "their bare hands"
        brutal = {"sharp": f"{tname} twists out of {name}'s attack, tears the {wn} free and drives it into {name} until {name} stops",
                  "blunt": f"{tname} catches {name}'s swing, wrenches the {wn} around and brings it down on {name}'s skull until it goes quiet",
                  "hands": f"{tname} slips under {name}'s grip, gets both hands around {name}'s throat and squeezes until the fight goes out of them"}[kind]
        seen = here if self.blackout_until < self.idx else [o for o in here if w.agents.get(o, {}).get("lit")]     # in the dark only a light shows who
        self.log_event(tick, {"type": "attack", "who": t, "room": room, "vis": "public", "text": f"{brutal}, in the {w.room_name(room)}."}, witnesses=seen, actor=t)
        self.open_case(tick, "manslaughter", cid, culprit=t, wkind=kind, weapon=vweap, room=room, hour=hour, witnesses=seen, aware=True,
                       self_defense=True, aggressor=cid)
        self.moment(t, f"killed {name}, who attacked first")
        return True

    def double_kill(self, tick, case, cid, v2, kind, wname, hour):
        """A killer who is not stopped may go on to kill a second person in the same room; still one culprit, one case."""
        w = self.world
        room = case["room"]
        name, vn = self.nm(cid), self.nm(v2)
        if self.rng.random() >= 0.55:
            self.stat(tick, v2, "hp", -30, "attacked")
            self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "public",
                                  "text": f"{name} swings at {vn} too, but {vn} tears free, badly hurt, and runs."}, actor=cid)
            w.adjust_aff(v2, cid, -6)
            w.remember(v2, f"{_hh(hour)} {name} tried to kill you in the {w.room_name(room)}. You got away.")
            self.moment(v2, f"escaped {name}'s killing spree of two")
            return
        w.agents[v2]["hp"] = 0
        w.end_agent(v2, "dead", "murdered")
        case.setdefault("extra_victims", []).append(v2)
        self.file_add(case, f"Second victim: {vn}, found in the same room, killed the same way.")
        case["clues"].append({"room": room, "scene": True, "found_by": [], "kind": "scene",
                              "text": f"{vn} is dead nearby, killed the same way, around the same time. Whoever did this killed twice."})
        case["cause"] = case["cause"] + " (two victims)"
        self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "public",
                              "text": f"{name} turns on {vn} before {vn} can reach the door, and finishes it in the {w.room_name(room)}."}, actor=cid)
        w.agents[cid]["sanity"] = max(0, w.agents[cid]["sanity"] - 6)
        self.tally(cid, "kills")
        self.moment(cid, f"killed two people in one terrible minute ({vn} too)")

    def more_dead(self, extra):
        case = self.s.get("case")
        ev = (case or {}).get("extra_victims") or []
        return (" (and so is " + ", ".join(self.nm(x) for x in ev) + ")") if ev else ""

    # ------------------------------------------------------------------ accomplices
    ROLES = ("lookout", "alibi", "cleanup", "weapon")

    def apply_accomplice(self, tick, items, group, hour):
        """A plotter asks a trusted person for help. The helper is NOT a second killer: only whoever strikes the blow stands trial."""
        w, s = self.world, self.s
        if not self.murders or s.get("spree"):
            return
        for it in (items or [])[:2]:
            if not isinstance(it, dict):
                continue
            by, helper, role = it.get("by"), it.get("helper"), it.get("role")
            plan = s["plots"].get(by)
            if not plan or by not in group or helper not in group or by == helper or helper not in w.agents or by not in w.agents or role not in self.ROLES:
                continue
            victim = plan["target"]
            if victim == helper or len(s["accomplices"].get(by, [])) >= 2 or any(x["helper"] == helper for x in s["accomplices"].get(by, [])):
                continue
            h = w.agents[helper]
            p = 0.2 + 0.06 * max(0, min(10, h["aff"].get(by, 0))) + (0.15 if h["aff"].get(victim, 0) <= -3 else 0) - (0.3 if h["aff"].get(victim, 0) >= 5 else 0) + (0.1 if h["sanity"] < 40 else 0)
            if self.rng.random() >= max(0.05, min(0.8, p)):
                w.remember(helper, f"{_hh(hour)} (private) {self.nm(by)} asked you to help kill {self.nm(victim)}. You refused.")
                self.adjust_any_aff(helper, by, -2)
                self.log_event(tick, {"type": "plot", "who": helper, "room": h["room"], "vis": "viewer",
                                      "text": f"{self.nm(helper)} refuses when {self.nm(by)} asks for help against {self.nm(victim)}."}, actor=helper)
                continue
            s["accomplices"].setdefault(by, []).append({"helper": helper, "role": role, "victim": victim, "day": self.day})
            w.remember(helper, f"{_hh(hour)} (private) You agreed to help {self.nm(by)} kill {self.nm(victim)} as their {role}.")
            w.remember(by, f"{_hh(hour)} (private) {self.nm(helper)} agreed to be your {role} against {self.nm(victim)}.")
            self.log_event(tick, {"type": "plot", "who": helper, "room": h["room"], "vis": "viewer",
                                  "text": f"{self.nm(helper)} agrees to help {self.nm(by)} against {self.nm(victim)} (as the {role})."}, actor=helper)
            self.moment(helper, f"agreed to help {self.nm(by)} kill {self.nm(victim)}")
            if role == "weapon":
                item = next((k for k in h["inv"] if "weapon" in w.item_spec(k).get("tags", [])), None)
                if item:
                    q, _ = w.give(helper, by, item, 1)
                    if q:
                        self.note_holder(by, item, hour)

    def auto_recruit(self, tick, hour):
        """Plotters sometimes sound out a close friend who also dislikes the victim, without the model having to think of it."""
        w, s = self.world, self.s
        if not self.murders or s.get("spree") or s.get("case"):
            return
        for by, pl in list(s.get("plots", {}).items()):
            if by not in w.agents or pl.get("stage") not in ("preparing", "stalking", "striking") or s.get("accomplices", {}).get(by):
                continue
            vic = pl["target"]
            if vic not in w.agents or self.rng.random() >= 0.15:
                continue
            here = [o for o in w.occupants(w.agents[by]["room"]) if o in w.agents and o not in (by, vic)
                    and w.agents[o]["aff"].get(by, 0) >= 7 and w.agents[o]["aff"].get(vic, 0) <= -3]
            if not here:
                continue
            h = self.rng.choice(here)
            roles = ["alibi", "lookout", "cleanup"] + (["weapon"] if any("weapon" in w.item_spec(k).get("tags", []) for k in w.agents[h]["inv"]) else [])
            self.apply_accomplice(tick, [{"by": by, "helper": h, "role": self.rng.choice(roles), "victim": vic}], [by, h], hour)

    def accomplice_lines(self, cid):
        s = self.s
        if not self.murders or s.get("spree"):
            return []
        out = []
        mine = s.get("accomplices", {}).get(cid, [])
        if mine:
            out.append("YOUR ACCOMPLICES: " + ", ".join(f"{self.nm(x['helper'])} ({x['role']})" for x in mine) + ". Only whoever strikes the killing blow stands trial; helpers walk free but may be exposed.")
        elif s["plots"].get(cid):
            out.append("ACCOMPLICE: you may ask someone who trusts you to help with your plot (a lookout, a false alibi, cleaning up, or a weapon) by saying so plainly in conversation "
                       "(effects.accomplice). Helpers are not killers: TereVi will only ever try the one who strikes the blow.")
        for by, lst in s.get("accomplices", {}).items():
            for x in lst:
                if x["helper"] == cid and by in self.world.agents:
                    out.append(f"YOU HAVE AGREED to help {self.nm(by)} kill {self.nm(x['victim'])} as their {x['role']}: do your part when the time comes, and keep quiet.")
        return out

    def lookout_filter(self, culprit, victim, witnesses):
        w = self.world
        if not culprit:
            return witnesses
        for x in self.s.get("accomplices", {}).get(culprit, []):
            if x["role"] == "lookout" and x["victim"] == victim and x["helper"] in w.agents and self.rng.random() < 0.7:
                return []
        return witnesses

    def accomplice_cleanup(self, case, culprit):
        w, s = self.world, self.s
        if not culprit:
            return
        acc = [x for x in s.get("accomplices", {}).pop(culprit, []) if x["victim"] == case["victim"] and x["helper"] in w.agents]
        case["accomplices"] = [{"helper": x["helper"], "role": x["role"]} for x in acc]
        for x in acc:
            self.tally(x["helper"], "accomplice")
            w.remember(x["helper"], f"{_hh(case['hour'])} (private) The plan went ahead: {self.nm(case['victim'])} is dead. You helped, and you must not give yourself away.")
            if x["role"] == "cleanup":
                case["clues"] = [c for c in case["clues"] if c["kind"] not in ("weapon", "trace") or self.rng.random() > 0.7]

    def alibi_testimonies(self, case, hour):
        w = self.world
        for x in case.get("accomplices") or []:
            if x["role"] == "alibi" and x["helper"] in w.agents and case.get("killer"):
                claim = f"{self.nm(case['killer'])} was with me the whole time around then."
                case.setdefault("testimonies", []).append({"by": x["helper"], "claim": claim, "day": self.day, "hour": hour, "false": True})
                for o in w.agents:
                    if o != x["helper"]:
                        self.note_evidence(o, "testimony", f"{self.nm(x['helper'])} says: {claim}", x["helper"])

    def expose_accomplices(self, tick, case, result, hour):
        """TereVi will only ever try one culprit; helpers walk free, but everyone learns what they did."""
        w = self.world
        for x in case.get("accomplices") or []:
            h = x["helper"]
            if h not in w.agents:
                continue
            for cid in w.agents:
                w.remember(cid, f"{_hh(hour)} It came out that {self.nm(h)} had helped with the killing ({x['role']}).")
                if cid != h:
                    self.adjust_any_aff(cid, h, -3)
            self.stat(tick, h, "sanity", -4, "exposed as an accomplice")
            self.moment(h, "was exposed as an accomplice")
            result += f" {self.nm(h)} was exposed as the killer's {x['role']}, but TereVi tries only one culprit: whoever struck the blow."
        return result

    # ------------------------------------------------------------------ NeoVi at the big scenes
    def neovi_attend(self, tick, room):
        """NeoVi walks to where the cast has been gathered (trial, last call, endgame...) and stands at the edge, silent."""
        w, s = self.world, self.s
        self.clear_hiding()
        nv = s["npcs"]["neovi"]
        start = nv["room"]
        if start == "none" or room == start or room not in ROOMS:
            tick["moves"]["neovi"] = {"from": start, "path": [start], "to": start}
            return
        steps = w.path("neovi", start, room) or []
        tick["moves"]["neovi"] = {"from": start, "path": [start] + ([r for r, _, _ in steps] if steps else [room]), "to": room}
        nv["room"] = room

    def neovi_hint_ok(self):
        s = self.s
        case = s.get("case")
        nv = s["npcs"]["neovi"]
        return bool(case and case.get("neovi_facts") and nv.get("room") != "none")

    def neovi_hint_block(self, case):
        nv = self.s["npcs"]["neovi"]
        fate = (nv.get("arc") or {}).get("fate")
        facts = " | ".join(case.get("neovi_facts") or [])
        tone = {"survivor": "She is braver now and may be a little clearer about WHAT or WHERE (an item, a place), never about WHO.",
                "betrayer": "She is cold and bitter and says nothing helpful: at most one dismissive line."}.get(fate, "She is frightened and obscure.")
        return (f"NEOVI stands silently at the edge of the room (speaker id neovi). She is neutral: she cannot accuse, argue or vote. {tone} "
                f"In this segment she speaks exactly ONE short, flat line (include it among the lines, speaker neovi), in her own first-person voice: obscure, reluctant, never naming or describing the culprit, "
                f"hinting at only one thing she saw, never copying these notes word for word: {facts}. She will not speak again in the trial.\n")

    def neovi_enforce(self, tick, who, hour):
        """NeoVi is TereVi's instrument at executions: what she does depends on how she feels and where her arc stands."""
        w, s = self.world, self.s
        nv = s["npcs"]["neovi"]
        if nv.get("room") == "none":
            return ""
        arc = self.neovi_arc()
        fate = arc.get("fate")
        room = nv["room"]
        witnesses = [c for c in w.agents if w.agents[c]["room"] == room]

        def bump(n):
            if not fate:
                arc["resolve"] = clamp(arc["resolve"] + n)
        if who is None:
            if fate == "betrayer":
                text = "NeoVi throws the lever herself, dry-eyed, as if it were a chore."
                kind = "system_notable"
            else:
                text = "NeoVi stands at the controls, white-knuckled, because she has been made to."
                kind = "mercy"
                bump(4)
        else:
            name = self.nm(who)
            aff = nv["aff"].get(who, 0)
            if fate == "betrayer":
                text, kind = f"NeoVi binds {name}'s wrists without a word and marches them to the platform.", "system_notable"
            elif fate == "survivor" and aff >= 3:
                text, kind = f"NeoVi refuses to touch {name}. TereVi's drones do it, and NeoVi does not look away until the end.", "mercy"
            elif aff >= 6 or arc.get("stage", 0) >= 3:
                text, kind = f"NeoVi's hands shake as she leads {name} away; she whispers 'I'm sorry' where only {name} can hear.", "mercy"
                bump(4)
                nv["fear"] = min(10, nv["fear"] + 1)
            else:
                text, kind = f"NeoVi leads {name} to the platform, eyes on the floor, because the alternative is worse.", "system_notable"
                bump(2)
        self.log_event(tick, {"type": kind, "who": "neovi", "room": room, "vis": "public", "text": text}, witnesses=witnesses)
        for c in witnesses:
            w.remember(c, f"{_hh(hour)} {text}")
        return text
