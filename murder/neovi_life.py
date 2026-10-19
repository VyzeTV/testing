"""NeoVi's own body and mind, while she is still the housemaid (kumiko.py makes her a person; this makes her mortal).

She has health and sanity of her own (`nv["hp"]`, `nv["sanity"]`); both carry over if TereVi makes her a participant.
- What moves her most is how she is treated: cruel words, being attacked, and TereVi's torment at night (`nv_torment`, likelier after she was soft
  on the cast or helped them). What lifts her: kind words, a welcome at a door, a lover, someone sitting with her. Deaths cost her little. Her
  health comes back a little each night.
- Her grudge against TereVi (`nv["tv_grudge"]`, 0-100) grows with every death and every punishment and makes helping the cast likelier.
- She can be attacked: by someone with a grudge against her, by someone who snaps, by someone after her master key, or by a model decision aimed
  at "neovi". For the fight she is briefly a person on the board (`nv_embody`), so the ordinary blow-by-blow fight runs. She carries a taser.
- Killed by a participant, she is murdered like anyone else: a body, a Case File, a trial. Nobody replaces her, so no newcomers come after that.
- She defends herself. If she kills an attacker while she is the housemaid, TereVi holds no trial ("staff are not contestants"); the witnesses
  remember, and someone raises it at the next trial (`nv_trial_pressure`). As a participant the ordinary rules apply to her.
- Low sanity, from her nightly upkeep (`nv_night`): cracks in the mask below 40 (her hand shakes on the taser), favourites below 30 (mercy for those
  she likes, a harder jolt for those she does not), sabotage of TereVi below 25, breakdowns below 20 (someone may comfort her), and below 10 one of
  three dangers: going for the person she blames, a suicide attempt someone may stop, or running off alone into the woods.
Dial `neovi_risk` scales how readily the cast turns on her. NeoViLifeMixin is mixed into DayRunner (engine.py).
"""
from .data_cast import HOSTS
from .kumiko import KUMIKO, KUMIKO_ID

NV_HP = 100
LOW = ((40, "the mask is cracking"), (30, "she has started picking favourites"), (25, "she has started working against TereVi"),
       (20, "she is breaking down"), (10, "she is close to doing something terrible"))


def _cl(x, hi=100):
    return max(0, min(hi, int(round(x))))


class NeoViLifeMixin:
    def nv_stats(self):
        nv = self.s["npcs"]["neovi"]
        nv.setdefault("hp", NV_HP)
        nv.setdefault("sanity", 70)
        nv.setdefault("tv_grudge", 0)
        nv.setdefault("blame", {})
        return nv

    def nv_where(self):
        nv = self.s["npcs"]["neovi"]
        return nv["room"] if nv.get("room") not in (None, "none") else "laundry"

    def nv_stat(self, tick, key, delta, why=""):
        """Change her health or sanity (her own, kept on her record). Returns the new value."""
        nv = self.nv_stats()
        before = nv[key]
        nv[key] = _cl(before + delta)
        if key == "hp" and nv[key] <= 0:
            nv[key] = 1                                     # only a fight kills her (nv_attacked)
        if key == "sanity":
            self.nv_threshold(tick, before, nv[key])
        if tick is not None and abs(nv[key] - before) >= 2:
            self.log_event(tick, {"type": "stat", "who": "neovi", "room": self.nv_where(), "vis": "gm", "text": f"NeoVi {key} {nv[key] - before:+d}" + (f" ({why})" if why else "")})
        return nv[key]

    def nv_threshold(self, tick, before, after):
        if tick is None or after >= before:
            return
        for lim, text in LOW:
            if after < lim <= before:
                self.log_event(tick, {"type": "drive", "who": "neovi", "room": self.nv_where(), "vis": "viewer", "text": f"NeoVi's sanity falls below {lim}: {text}."})

    def nv_grudge(self, d):
        nv = self.nv_stats()
        nv["tv_grudge"] = _cl(nv["tv_grudge"] + d)

    def nv_blame(self, cid, d):
        b = self.nv_stats()["blame"]
        b[cid] = b.get(cid, 0) + d

    # ------------------------------------------------------------------ drivers
    def nv_kind(self, cid, d):
        """How the cast treats her is what moves her most: a kind word lifts her, a cruel one hurts more."""
        if self.neovi_maid():
            self.nv_stat(None, "sanity", 2 * d if d > 0 else 3 * d)
            if d < 0:
                self.nv_blame(cid, 1)

    def nv_after_punish(self, tick, cid):
        """She tased or locked someone up: it costs her more if she likes them, and they resent her for it."""
        nv = self.nv_stats()
        if nv["aff"].get(cid, 0) >= 2:
            self.nv_stat(tick, "sanity", -2, f"punishing {self.nm(cid)}")
        self.nv_grudge(2)
        if self.rng.random() < 0.75:
            self.nv_feel_add(cid, -1)

    def nv_taser_force(self, tick, cid):
        """How hard her taser bites: a shaking hand below 40, favourites below 30 (1.0 is normal)."""
        nv = self.nv_stats()
        san, aff = nv["sanity"], nv["aff"].get(cid, 0)
        if san < 30 and aff <= -2:
            return 1.5
        if san < 40 and self.rng.random() < 0.35:
            self.log_event(tick, {"type": "neovi", "who": "neovi", "room": self.world.agents[cid]["room"], "vis": "public",
                                  "text": f"NeoVi's hand shakes. The taser catches {self.nm(cid)} late and half-hearted, and for a second she looks as if she might cry."},
                           witnesses=[o for o in self.world.occupants(self.world.agents[cid]["room"]) if o in self.world.agents])
            return 0.5
        return 1.0

    def nv_mercy_shift(self, cid):
        """Below 30 she plays favourites: more mercy for those she likes, none for those she does not. Returns a change to her mercy odds."""
        nv = self.nv_stats()
        if nv["sanity"] >= 30:
            return 0.0
        aff = nv["aff"].get(cid, 0)
        return 0.3 if aff >= 3 else -1.0 if aff <= -2 else 0.0

    def nv_absent_punish(self, tick, cid, v, hour):
        """No housemaid to enforce the rule: TereVi does it herself, through the floor."""
        w = self.world
        a = w.agents[cid]
        room = a["room"]
        text = f"The floor under {self.nm(cid)} crackles: with no housemaid left, TereVi punishes them herself for breaking the rule ({v['reason']})."
        self.stat(tick, cid, "hp", -14, "TereVi's shock floor")
        self.stat(tick, cid, "sanity", -6, "TereVi's shock floor")
        self.log_event(tick, {"type": "punish", "kind": "shock", "who": cid, "room": room, "vis": "public", "text": text},
                       witnesses=[o for o in w.occupants(room) if o != cid], actor=cid)
        self.day_notable.append(text)

    def nv_night(self, tick):
        """Her nightly upkeep: the deaths since yesterday, a little healing, a little recovery when someone cares, then whatever her sanity drives her to."""
        if not self.revealed or not self.neovi_maid():
            return None
        w, s = self.world, self.s
        nv = self.nv_stats()
        seen = nv.get("mourned", 0)
        grave = s.get("graveyard") or []
        for g in grave[seen:]:
            if g.get("status") in ("dead", "executed") and g["id"] != KUMIKO_ID:
                liked = nv["aff"].get(g["id"], 0) >= 4
                self.nv_stat(tick, "sanity", -(3 if liked else 1), f"cleaning up after {self.nm(g['id'])}")
                self.nv_grudge(6 if liked else 3)
        nv["mourned"] = len(grave)
        died = any(g.get("day") == self.day for g in grave)
        self.nv_stat(tick, "hp", 8, "rest")
        if self.day > 3:
            self.nv_stat(tick, "sanity", -1, "another night on the island")
        carers = [c for c in sorted(w.agents) if self.nv_feel(c) >= 5]
        if carers and not died:
            self.nv_stat(tick, "sanity", 2 + min(2, len(carers) - 1), "someone cares")
        self.nv_torment(tick)
        out = self.nv_low(tick)
        return out

    def nv_torment(self, tick):
        """TereVi's nightly cruelty toward her housemaid: likelier when she has been soft on the cast, helped them, or TereVi is bored. Returns the kind, or None."""
        s = self.s
        nv = self.nv_stats()
        p = 0.2 + (0.25 if nv.get("slipped") == self.day else 0) + (0.2 if nv.get("helped", 0) > nv.get("_helped_seen", 0) else 0) \
            + (0.15 if not self.death_today and self.day > 3 else 0)
        nv["_helped_seen"] = nv.get("helped", 0)
        if self.rng.random() >= p:
            return None
        kind, text, loss, public = self.rng.choice([
            ("names", "TereVi spends an hour on the laundry speaker reading NeoVi's old life back to her, and laughing at the good parts.", 5, False),
            ("chores", "TereVi has NeoVi scrub the Foyer floor on her knees until dawn, live, and keeps moving the bucket.", 4, True),
            ("toy", "TereVi makes NeoVi taser herself on air, once for every rule broken today. The audience votes for an encore.", 8, True),
            ("rabbit", "TereVi takes NeoVi's stuffed rabbit away for the night and hangs it in front of a camera where she can see it.", 6, False),
            ("praise", "TereVi praises NeoVi to the cast, warmly and in detail, for things she never did to them. Some of them believe it.", 5, True),
        ])
        if kind == "praise":
            for c in sorted(self.world.agents):
                if self.nv_feel(c) < 5 and self.rng.random() < 0.4:
                    self.nv_feel_add(c, -1)
        self.nv_stat(tick, "sanity", -loss, "TereVi's torment")
        self.nv_grudge(5)
        nv.setdefault("tormented", []).append({"day": self.day, "kind": kind})
        self.log_event(tick, {"type": "neovi", "who": "neovi", "room": "foyer" if public else self.nv_where(), "vis": "public" if public else "viewer", "text": text},
                       witnesses=list(self.world.agents) if public else None)
        if public:
            for c in sorted(self.world.agents):
                if self.nv_feel(c) >= 3:
                    self.stat(tick, c, "sanity", -1, "watching TereVi torment NeoVi")
        return kind

    # ------------------------------------------------------------------ low sanity
    def nv_low(self, tick):
        nv = self.nv_stats()
        san = nv["sanity"]
        if nv.get("away"):
            return self.nv_come_back(tick)
        if san < 10 and nv.get("danger_day", -9) < self.day - 1 and not self.s.get("case"):
            nv["danger_day"] = self.day
            blamed = self.nv_blamed()
            opts = [("run", 1.0), ("suicide", 1.0)] + ([("attack", 1.2)] if blamed else [])
            x = self.rng.random() * sum(wt for _, wt in opts)
            for k, wt in opts:
                x -= wt
                if x <= 0:
                    break
            return {"attack": lambda: self.nv_lash_out(tick, blamed), "suicide": lambda: self.nv_suicide_attempt(tick), "run": lambda: self.nv_run(tick)}[k]()
        if san < 20 and self.rng.random() < 0.5:
            return self.nv_breakdown(tick)
        if san < 25 and self.rng.random() < 0.35:
            return self.nv_sabotage(tick)
        return None

    def nv_blamed(self):
        nv = self.nv_stats()
        cands = [(v, c) for c, v in nv["blame"].items() if c in self.world.agents and v >= 4]
        return max(cands)[1] if cands else None

    def nv_breakdown(self, tick):
        """She comes apart where someone can see. Someone kind may sit with her: that is how she climbs back."""
        w = self.world
        room = self.nv_where()
        near = sorted(w.agents, key=lambda c: (-(self.nv_feel(c) + self.facet(c, "altruism") / 20), c))
        comfort = next((c for c in near if self.nv_feel(c) >= 2 or self.facet(c, "altruism") >= 65), None)
        if comfort and self.rng.random() < 0.6:
            text = (f"{self.nm(comfort)} finds NeoVi on the floor of the {w.room_name(room)}, shaking, a towel pressed to her face. They sit with her until it passes, "
                    "and she lets them.")
            self.nv_stat(tick, "sanity", 8, f"{self.nm(comfort)} sat with her")
            self.nv_feel_add(comfort, 1)
            self.adjust_any_aff("neovi", comfort, 2)
            self.moment(comfort, "sat with NeoVi while she fell apart")
            self.log_event(tick, {"type": "neovi", "who": "neovi", "room": room, "vis": "viewer", "text": text}, actor=comfort)
            return "comforted"
        text = f"Somewhere in the {w.room_name(room)}, NeoVi is crying where she thinks the cameras cannot hear. They can."
        self.nv_stat(tick, "sanity", -1, "alone with it")
        self.log_event(tick, {"type": "neovi", "who": "neovi", "room": room, "vis": "viewer", "text": text})
        return "breakdown"

    def nv_sabotage(self, tick):
        """She turns on TereVi in small ways; TereVi may notice."""
        s = self.s
        nv = self.nv_stats()
        kind = self.rng.choice(["cameras", "locks", "returned"])
        if kind == "cameras":
            self.blackout_until = max(self.blackout_until, self.idx + 1)
            text = "A camera bank in the laundry corridor goes dark tonight. Someone pulled a fuse and put the cover back neatly."
        elif kind == "locks":
            s["locks"] = {r: v for r, v in (s.get("locks") or {}).items() if v.get("by") != "terevi"}
            text = "The doors TereVi locked open again tonight, one by one. Nobody signed for the master key."
        else:
            pool = s["room_items"].setdefault("laundry", {})
            text = "Things TereVi confiscated start turning up again, left where their owners will find them."
            for it in sorted(pool)[:2]:
                pool.pop(it, None)
        nv["sabotaged"] = nv.get("sabotaged", 0) + 1
        self.nv_grudge(-4)
        self.log_event(tick, {"type": "neovi", "who": "neovi", "room": self.nv_where(), "vis": "viewer", "text": text})
        if self.rng.random() < 0.15:
            return self.neovi_caught(tick, None)
        return "sabotage"

    def nv_go(self, tick, room):
        nv = self.s["npcs"]["neovi"]
        start = nv["room"]
        if start in (None, "none") or start == room:
            return
        steps = self.world.path("neovi", start, room) or []
        mv = tick["moves"].setdefault("neovi", {"from": start, "path": [start], "to": start})
        mv["path"] += [r for r, _, _ in steps] or [room]
        mv["to"] = room
        nv["room"] = room

    def nv_lash_out(self, tick, cid):
        """She goes for the person she blames. As the housemaid, a death she causes has no trial."""
        w = self.world
        if cid not in w.agents:
            return None
        self.nv_go(tick, w.agents[cid]["room"])
        self.log_event(tick, {"type": "neovi", "who": "neovi", "room": w.agents[cid]["room"], "vis": "viewer",
                              "text": f"NeoVi stops outside {self.nm(cid)}'s door with the taser in her hand, and this time she does not knock."})
        return self.nv_fight(tick, cid, attacker="neovi", why="blame")

    def nv_suicide_attempt(self, tick):
        """She tries to end it. Someone who cares about her, or TereVi, who will not lose her housemaid, may stop it."""
        w, nv = self.world, self.nv_stats()
        lover = self.neovi_lover()
        carers = sorted([c for c in w.agents if self.nv_feel(c) >= 4], key=lambda c: (-self.nv_feel(c), c))
        saver = lover or (carers[0] if carers else None)
        p = 0.65 if lover else 0.45 if saver else 0.0
        room = self.nv_where()
        if saver and self.rng.random() < p:
            text = (f"{self.nm(saver)} finds NeoVi in the {w.room_name(room)} in time, and does not let go of her until morning. "
                    "She does not say what she was trying to do. She does not have to.")
            self.nv_stat(tick, "sanity", 18, f"{self.nm(saver)} saved her")
            self.nv_feel_add(saver, 2)
            self.adjust_any_aff("neovi", saver, 3)
            self.moment(saver, "saved NeoVi from herself")
            self.log_event(tick, {"type": "neovi", "who": "neovi", "room": room, "vis": "viewer", "text": text}, actor=saver)
            return "saved"
        if self.rng.random() < 0.5:
            text = "TereVi's drones reach NeoVi before it is over. \"Nobody quits my show, darling. Least of all the help.\" She is back at work by morning."
            self.nv_stat(tick, "hp", -20, "the attempt")
            self.nv_stat(tick, "sanity", 4, "still here")
            self.nv_grudge(10)
            self.log_event(tick, {"type": "neovi", "who": "neovi", "room": room, "vis": "viewer", "text": text})
            return "stopped"
        return self.nv_dies(tick, None, "suicide", room=room)

    def nv_run(self, tick):
        """She walks out into the woods alone. TereVi brings her back, or the island keeps her."""
        nv = self.nv_stats()
        self.nv_go(tick, "woods")
        nv["away"] = self.day
        self.log_event(tick, {"type": "neovi", "who": "neovi", "room": "woods", "vis": "viewer",
                              "text": "NeoVi takes off her apron, folds it, and walks out into the woods alone. Nobody stops her."})
        return "ran"

    def nv_come_back(self, tick):
        nv = self.nv_stats()
        nv.pop("away", None)
        if self.rng.random() < 0.25 and not self.s.get("case"):
            return self.nv_dies(tick, None, "accident", room="woods")
        self.nv_stat(tick, "hp", -15, "dragged back")
        self.nv_stat(tick, "sanity", 6, "a night alone")
        self.nv_grudge(8)
        self.log_event(tick, {"type": "neovi", "who": "neovi", "room": "woods", "vis": "viewer",
                              "text": "TereVi's drones find NeoVi in the woods and bring her back, scratched and soaked. She goes straight to the laundry and starts folding."})
        self.nv_go(tick, "laundry")
        return "back"

    # ------------------------------------------------------------------ fights
    def nv_embody(self):
        """Put her on the board as a person for a fight (her own health, sanity and pockets). False if she already is one."""
        w, s = self.world, self.s
        if KUMIKO_ID in s["agents"]:
            return False
        nv = self.nv_stats()
        cast = dict(KUMIKO)
        cast.update({"name": "NeoVi", "short": "NeoVi", "role": "Housemaid", "pron": "she", "color": HOSTS["neovi"]["color"], "card": "", "home": "laundry",
                     "mock_lines": ["Please put that down.", "I clean up after all of you. I know what you do."]})
        s["cast"][KUMIKO_ID] = cast
        s["agents"][KUMIKO_ID] = {"status": "alive", "room": self.nv_where(), "hp": nv["hp"], "sanity": nv["sanity"], "inv": dict(nv.get("inv") or {}),
                                  "known": [], "route": None, "drive": {"id": "survivor", "target": None, "arc": ""}, "known_secrets": [], "maid": True,
                                  "activity": "Doing her rounds", "aff": {c: nv["aff"].get(c, 0) for c in w.agents if c != KUMIKO_ID},
                                  "memory": {"diary": [], "recent": [], "notes": [], "lost": [], "moments": []}}
        return True

    def nv_disembody(self):
        """Back to being staff: her health and pockets go back on her own record."""
        w, s = self.world, self.s
        a = s["agents"].pop(KUMIKO_ID, None)
        s["cast"].pop(KUMIKO_ID, None)
        if a:
            nv = self.nv_stats()
            nv["hp"] = max(1, a["hp"])
            nv["inv"] = a["inv"]
        for o in s["agents"].values():
            o.get("aff", {}).pop(KUMIKO_ID, None)

    def nv_threats(self, tick, hour):
        """Anyone in her room who might turn on her: a deep grudge, a mind that has snapped, or someone who wants her master key. At most one a block."""
        if not self.neovi_maid() or not self.revealed or not self.murders or self.s.get("case") or self.s.get("over"):
            return None
        w = self.world
        nv = self.nv_stats()
        room = nv["room"]
        risk = self.tune("neovi_risk")
        for cid in sorted(w.occupants(room)):
            a = w.agents.get(cid)
            if not a or a.get("asleep") or a.get("out") or a["hp"] < 40:
                continue
            feel = self.nv_feel(cid)
            temper = (self.facet(cid, "anger") + self.facet(cid, "vengefulness") + self.facet(cid, "cruelty")) / 150
            p, why = 0.0, None
            if feel <= -4:
                p, why = 0.025 * (-feel - 3) * temper, "grudge"
            if a["sanity"] < 20 and feel <= -1 and 0.05 > p:
                p, why = 0.05, "snap"
            if nv["inv"].get("master_key", 0) and feel <= 1 and a.get("route") in ("boat", "raft", "shutdown") and self.facet(cid, "courage") >= 55 \
                    and self.facet(cid, "cruelty") >= 35 and 0.01 > p:
                p, why = 0.01, "key"
            if why and self.rng.random() < p * risk:
                return self.nv_fight(tick, cid, why=why)
        return None

    def nv_attacked(self, tick, cid, method, hour):
        """A model decision aimed at NeoVi."""
        w = self.world
        if not self.neovi_maid() or cid not in w.agents or w.agents[cid]["room"] != self.s["npcs"]["neovi"]["room"]:
            self.log_event(tick, {"type": "system", "who": cid, "room": w.agents[cid]["room"] if cid in w.agents else "foyer", "vis": "gm",
                                  "text": f"{self.nm(cid)} meant to go for NeoVi, but she was not there."}, actor=cid)
            return None
        return self.nv_fight(tick, cid, why="decided", method=method)

    def nv_fight(self, tick, cid, why="grudge", attacker=None, method=None):
        """A fight between NeoVi and `cid`, blow by blow. `attacker` "neovi" when she is the one who strikes. Returns the outcome."""
        w, s = self.world, self.s
        if s.get("case") or cid not in w.agents or not self.nv_embody():
            return None
        nv = self.nv_stats()
        room = w.agents[cid]["room"]
        s["agents"][KUMIKO_ID]["room"] = room
        here = [o for o in w.occupants(room) if o in w.agents and o not in (cid, KUMIKO_ID)]
        hour = s.get("_hour", 12)
        name = self.nm(cid)
        nv.setdefault("fights", []).append({"day": self.day, "with": cid, "why": why, "she_struck": attacker == "neovi"})
        if attacker == "neovi":
            res = self.fight(tick, KUMIKO_ID, cid, None, "hands", hour, others=here)
            tick.setdefault("fights", []).append({"by": "neovi", "on": cid, "room": room, "outcome": res["outcome"], "blows": res["blows"]})
            self.nv_disembody()
            if res["outcome"] == "killed":
                return self.nv_kills(tick, cid, room, here, "she went for them")
            w.agents[cid]["hp"] = max(5, w.agents[cid]["hp"])
            self.stat(tick, cid, "sanity", -10, "NeoVi came for them")
            self.log_event(tick, {"type": "attack", "who": "neovi", "room": room, "vis": "public",
                                  "text": f"NeoVi goes for {name} with the taser and her bare hands, and {name} only just fights her off."}, witnesses=here + [cid])
            self.nv_feel_add(cid, -4)
            w.remember(cid, f"NeoVi attacked you in the {w.room_name(room)}. The housemaid.")
            self.moment(cid, "NeoVi tried to kill them")
            nv["blame"][cid] = 0
            return "she_attacked"
        a = w.agents[cid]
        weapon = method if method and a["inv"].get(method, 0) > 0 and "weapon" in w.item_spec(method).get("tags", []) else \
            next((k for k in sorted(a["inv"]) if "weapon" in w.item_spec(k).get("tags", [])), None)
        tags = w.item_spec(weapon).get("tags", []) if weapon else []
        kind = "sharp" if "sharp" in tags else "blunt" if "blunt" in tags else "hands"
        wname = w.item_name(weapon) if weapon else "bare hands"
        if self.rng.random() < (0.45 if self.must_draw(cid, weapon) else 0.25):
            self.nv_disembody()                                         # she is quicker with the taser than they are with the weapon
            self.stat(tick, cid, "hp", -15, "NeoVi's taser")
            self.knock_out(tick, cid, "tased", 1, by="neovi")
            self.log_event(tick, {"type": "punish", "kind": "taser", "who": cid, "room": room, "vis": "public",
                                  "text": f"{name} goes for NeoVi with {wname}, but her taser is out first. {name} hits the floor twitching."}, witnesses=here, actor=cid)
            self.nv_stat(tick, "sanity", -4, f"{name} came at her")
            self.nv_feel_add(cid, -2)
            self.adjust_any_aff("neovi", cid, -5)
            w.remember(cid, f"You went for NeoVi in the {w.room_name(room)}. Her taser was faster.")
            return "tased"
        res = self.fight(tick, cid, KUMIKO_ID, weapon, kind, hour, others=here)
        tick.setdefault("fights", []).append({"by": cid, "on": "neovi", "room": room, "outcome": res["outcome"], "blows": res["blows"]})
        self.nv_blame(cid, 5)
        if res["scratched"]:
            a["scratched"] = self.day
            self.scratch(tick, cid, "NeoVi clawed at them")
        if res["outcome"] == "killed":
            return self.nv_murdered(tick, cid, kind, weapon, room, here, res, why)
        down = s["agents"][KUMIKO_ID]["hp"] < 30
        hp_left = s["agents"][KUMIKO_ID]["hp"]
        self.nv_disembody()
        out = "survived"
        took = None
        if nv["inv"].get("master_key", 0) and (down or why == "key") and self.rng.random() < (0.7 if why == "key" else 0.35):
            nv["inv"]["master_key"] = 0
            w.agents[cid]["inv"]["master_key"] = w.agents[cid]["inv"].get("master_key", 0) + 1
            took = f" {name} pulls the master key off her belt" + (" while she is down." if down else " in the struggle.")
            w.remember(cid, "You took NeoVi's master key. It opens every locked door on the island.")
        self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "public",
                              "text": f"{name} goes for NeoVi with {wname}. She takes the blows" + (", goes down" if down else "") + " and gets her taser out." + (took or "")},
                       witnesses=here, actor=cid)
        self.log_event(tick, {"type": "fight", "who": cid, "room": room, "vis": "gm", "text": self.fight_text(cid, "neovi", res, wname, kind)})
        self.nv_stat(tick, "sanity", -10, f"{name} attacked her")
        self.nv_feel_add(cid, -3)
        self.adjust_any_aff("neovi", cid, -6)
        for o in here:
            w.adjust_aff(o, cid, -2)
        # her answer: the taser, and once in a while more than that
        if (a["hp"] < 30 and nv["sanity"] < 40) or self.rng.random() < 0.06 + (0.12 if nv["sanity"] < 25 else 0) + (0.1 if res["outcome"] == "disarmed" else 0):
            return self.nv_kills(tick, cid, room, here, "self-defence")
        self.stat(tick, cid, "hp", -18 if hp_left >= 15 else -10, "NeoVi's taser")
        if self.rng.random() < 0.6:
            self.knock_out(tick, cid, "tased", 1, by="neovi")
        self.log_event(tick, {"type": "punish", "kind": "taser", "who": cid, "room": room, "vis": "public",
                              "text": f"NeoVi's taser drops {name} to the floor. TereVi's voice, delighted: \"Hands off the staff, darling.\""},
                       witnesses=here, actor=cid)
        w.remember(cid, f"You attacked NeoVi in the {w.room_name(room)}. She tased you.")
        self.moment(cid, "attacked NeoVi")
        nv["harmed_by"] = nv.get("harmed_by", []) + [[cid, self.day]]
        return out if not took else "robbed"

    def nv_kills(self, tick, cid, room, here, why):
        """She kills someone while she is the housemaid: no trial (staff are not contestants), but nobody forgets."""
        w, s = self.world, self.s
        nv = self.nv_stats()
        name = self.nm(cid)
        text = (f"NeoVi's taser is not enough. She does not stop until {name} stops moving, in the {w.room_name(room)}." if why == "self-defence"
                else f"NeoVi does not stop until {name} stops moving, in the {w.room_name(room)}.")
        self.log_event(tick, {"type": "attack", "who": "neovi", "room": room, "vis": "public", "text": text}, witnesses=here)
        self.open_case(tick, "manslaughter", cid, culprit=None, wkind="hands", room=room, witnesses=here, self_defense=why == "self-defence", aggressor=cid if why == "self-defence" else None,
                       cause="killed by the housemaid, NeoVi" + (", who was defending herself" if why == "self-defence" else ""))
        nv.setdefault("kills", []).append({"day": self.day, "who": cid, "why": why, "witnesses": list(here), "raised": False})
        self.nv_stat(tick, "sanity", -14, f"she killed {name}")
        self.nv_grudge(10)
        for o in sorted(w.agents):
            if o in here or w.agents[o]["aff"].get(cid, 0) >= 3:
                self.nv_feel_add(o, -3 if why == "self-defence" else -6)
        self.terevi_says(tick, "The housemaid was defending herself, darlings. Staff are not contestants: no trial. Do try not to make her do that again. Hehe."
                         if why == "self-defence" else "Oh dear. The help has had a bad night. Staff are not contestants, darlings: no trial. Hehe.")
        self.saga(f"NeoVi killed {name} ({why}). TereVi held no trial.")
        return "she_killed"

    def nv_murdered(self, tick, cid, kind, weapon, room, here, res, why):
        """A participant kills her: a murder like any other, with a body, a Case File and a trial."""
        w, s = self.world, self.s
        nv = self.nv_stats()
        name = self.nm(cid)
        wname = w.item_name(weapon) if weapon else "bare hands"
        if nv["inv"].get("master_key", 0) and why == "key":
            w.agents[cid]["inv"]["master_key"] = w.agents[cid]["inv"].get("master_key", 0) + 1
            s["agents"][KUMIKO_ID]["inv"].pop("master_key", None)
        brutal = {"sharp": f"{name} drives the {wname} into NeoVi until the taser falls out of her hand",
                  "blunt": f"{name} brings the {wname} down on NeoVi until she stops trying to get up",
                  "hands": f"{name} gets their hands around NeoVi's throat and does not let go",
                  "water": f"{name} holds NeoVi under the water until the thrashing stops"}[kind]
        self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "public", "text": f"{brutal}, in the {w.room_name(room)}."}, witnesses=here, actor=cid)
        self.open_case(tick, "murder", KUMIKO_ID, culprit=cid, wkind=kind, weapon=weapon, room=room, witnesses=here)
        if s.get("case"):
            s["case"]["wounds"] = res["wounds"]
            s["case"]["killer_scratched"] = bool(res["scratched"])
            s["case"]["wound_text"] = self.wound_summary(res["wounds"])
            self.file_set(s["case"], "wounds", s["case"]["wound_text"])
        self.nv_gone(tick, "murdered", by=cid)
        return "murdered"

    def nv_dies(self, tick, killer, kind, room=None):
        """She dies with nobody to blame (her own hand, the island): a body is found and TereVi announces it; no trial."""
        if self.s.get("case") or not self.nv_embody():
            return None
        room = room or self.nv_where()
        self.s["agents"][KUMIKO_ID]["room"] = room
        cause = {"suicide": "she took her own life", "accident": "a fall in the woods, alone"}.get(kind, kind)
        self.open_case(tick, kind, KUMIKO_ID, culprit=None, room=room, cause=cause)
        self.nv_gone(tick, kind)
        return kind

    def nv_gone(self, tick, how, by=None):
        """She is dead: nobody replaces the housemaid, so no newcomers come after this."""
        w, s = self.world, self.s
        nv = self.nv_stats()
        nv["hp"] = 0
        nv["dead"] = {"day": self.day, "how": how, "by": by}
        nv["room"] = "none"
        self.neovi_arc()["fate"] = "dead"
        s["no_newcomers"] = True
        rec = s["agents"].get(KUMIKO_ID)
        if rec and rec.get("inv", {}).get("master_key"):
            pool = s["room_items"].setdefault(rec["room"], {})
            pool["master_key"] = pool.get("master_key", 0) + rec["inv"].pop("master_key")
        for c in sorted(w.agents):
            if self.nv_feel(c) >= 3:
                self.moment(c, "lost NeoVi (Kumiko)")
        self.saga("NeoVi is dead. Nobody will replace the housemaid: no newcomers will come.")
        self.log_event(tick, {"type": "system", "who": "terevi", "room": "foyer", "vis": "gm", "text": "NeoVi is dead: no newcomers for the rest of the season."})

    # ------------------------------------------------------------------ at the trial
    def nv_trial_pressure(self, tick):
        """Someone who saw her kill brings it up before the trial. TereVi is not interested."""
        w = self.world
        nv = self.s["npcs"]["neovi"]
        for k in nv.get("kills") or []:
            if k["raised"]:
                continue
            k["raised"] = True
            who = next((c for c in k["witnesses"] if c in w.agents), None) or next((c for c in sorted(w.agents) if w.agents[c]["aff"].get(k["who"], 0) >= 3), None)
            if not who:
                continue
            text = (f"Before anything else, {self.nm(who)} wants to know why NeoVi never stood trial for killing {self.nm(k['who'])}. "
                    "TereVi laughs. \"The help is not on trial, darling. You are.\"")
            self.log_event(tick, {"type": "system_notable", "who": who, "room": "voting_grounds", "vis": "public", "text": text}, witnesses=list(w.agents), actor=who)
            self.nv_feel_add(who, -1)
            if self.neovi_maid():
                self.nv_stat(tick, "sanity", -3, "everyone staring at her")
            return text
        return None
