"""The chaos layer: secret drives, the madness ladder, violence and sabotage, secrets and leaks,
betrayals, island events, the nightly reflection and the episode recap.

ChaosMixin is mixed into DayRunner (engine.py) next to DramaMixin.
"""
from .data_cast import HOSTS, STORY_BIBLE
from .data_world import ROOMS
from .llm import LLMError

DRIVES = {
    "survivor": ("Survivor", "Staying alive is everything. You avoid risks and keep useful allies close."),
    "protector": ("Protector", "You want certain people to live (your target, if you have one) and will take real risks for them."),
    "saboteur": ("Saboteur", "You want to wreck the show: break rules for sport, cut cameras, spoil TereVi's plans and make her look foolish."),
    "schemer": ("Schemer", "You collect secrets and leverage, play people against each other and keep your own hands clean."),
    "avenger": ("Avenger", "You hold a grudge against someone (your target) and want them to suffer."),
    "thrill": ("Thrill-seeker", "You chase excitement: parties, dares, risks, drama. Boredom is the enemy."),
    "romantic": ("Romantic", "You want love or closeness and will bend rules and hearts for it."),
    "seeker": ("Seeker", "You are driven to find a way out, or the truth behind the show."),
    "nihilist": ("Nihilist", "You have stopped caring whether anyone survives, even you. You want to see things break and to hurt people, above all the ones you blame."),
    "martyr": ("Martyr", "You would trade your own safety to save others, even take the blame for them."),
}
MADNESS_NAMES = ["steady", "frayed", "unraveling", "breaking down", "snapped"]
IMPULSES = {
    "hurt": "an urge to physically hurt {t}",
    "lash": "an urge to say the cruelest true thing you know to {t}",
    "wreck": "an urge to smash or ruin something",
    "expose": "an urge to blurt out someone's secret in front of everyone",
    "sabotage": "an urge to plunge the house into darkness",
    "isolate": "an urge to lock yourself away and snap at anyone who comes near",
}
ISLAND_EVENTS = {
    "storm": {"title": "Storm", "dur": 2, "intro": "The sky splits open and a storm slams into the island!",
              "text": "A violent storm batters the island: the power flickers, the cameras glitch, and anyone outside is soaked and battered."},
    "fire": {"title": "Kitchen fire", "dur": 1, "intro": "Alarms shriek: there is a fire in the kitchen!",
             "text": "Smoke pours from the kitchen: something is on fire and it needs people to act NOW (or the kitchen burns)."},
    "power": {"title": "Power cut", "dur": 1, "intro": "Everything goes dark. The power is out.",
              "text": "The power is out: lights, cameras and monitors are dead and the house is full of shadows."},
    "fog": {"title": "Fog and whispers", "dur": 2, "intro": "A cold fog swallows the island, and something whispers in the walls.",
            "text": "A thick fog has rolled in and everyone hears faint whispering in the walls. Nerves fray."},
    "cat": {"title": "A stray cat", "dur": 1, "intro": "A tiny meow echoes somewhere in the house...",
            "text": "A scrawny stray cat is wandering the house; whoever finds it feels a rare moment of warmth. NeoVi loves cats."},
    "package": {"title": "Mystery package", "dur": 1, "intro": "A hatch clanks open in the foyer and something drops inside.",
                "text": "A package addressed 'To whoever dares' sits in the Foyer."},
}
PACKAGE_ITEMS = ["rope", "champagne", "flare_gun", "board_game"]
CHAOS = {"calm": 0.5, "normal": 1.0, "wild": 2.0}
SURPRISE = {"calm": "now and then", "normal": "about one turn in five", "wild": "about one turn in three"}


def madness_level(sanity):
    return 0 if sanity >= 55 else 1 if sanity >= 35 else 2 if sanity >= 20 else 3 if sanity >= 10 else 4


def _hh(h):
    return f"{h:02d}:00"


class ChaosMixin:
    def chaos_init(self, chaos="normal"):
        self.chaos = chaos if chaos in CHAOS else "normal"
        self.impulses = {}
        self.assaults = []
        self.sabotages = []
        self.impulse_done = set()

    def chaos_factor(self):
        return CHAOS[self.chaos]

    def fx(self, tick, kind, room=None, who=None):
        m = self.minute()
        tick.setdefault("fx", []).append({"kind": kind, "room": room, "who": who, **({"m": round(m, 1)} if m is not None else {})})

    # ------------------------------------------------------------------ prompt material
    def island_live(self, isl):
        """Is this island event still going on? (Events saved by an older version, measured in ticks, count as over.)"""
        return "until_abs" in isl and self.abs_now() <= isl["until_abs"]

    def island_line(self):
        isl = self.s.get("island")
        if isl and self.island_live(isl):
            where = f" (in the {self.world.room_name(isl['room'])})" if isl.get("room") else ""
            return f"ISLAND EVENT NOW: {isl['title']}{where}: {ISLAND_EVENTS[isl['id']]['text']}"
        return ""

    def current_island(self):
        isl = self.s.get("island")
        if isl and self.island_live(isl):
            return {"id": isl["id"], "title": isl["title"], "room": isl.get("room")}
        return None

    def chaos_decision_lines(self, cid, hour):
        w, s = self.world, self.s
        if not self.revealed:
            return []
        a = w.agents[cid]
        d = a["drive"]
        title, desc = DRIVES.get(d["id"], DRIVES["survivor"])
        tgt = f" Your target: {self.nm(d['target'])}." if d.get("target") in w.agents else ""
        arc = f" How you have been changing: {d['arc']}" if d.get("arc") else ""
        out = [f"YOUR SECRET DRIVE: {title}. {desc}{tgt}{arc} Nobody else knows it. It outweighs generic caution when they conflict, and not every drive cares about surviving. "
               f"SURPRISE: {SURPRISE[self.chaos]}, do something your usual self wouldn't if your drive, your sanity, a grudge or a juicy opportunity justifies it "
               "(confess, sabotage, flirt, defect, protect an enemy, leak a secret, throw a party at a terrible moment, go looking for trouble). Stay believable."]
        sec = [k for k in a["known_secrets"] if k["of"] != cid and k["of"] in w.cast]
        if sec:
            out.append("SECRETS YOU KNOW: " + " | ".join(f"{self.nm(k['of'])}: {k['text'][:120]}" for k in sec[:4]) +
                       ". You may use, trade, hide or leak them (a leak happens in conversation).")
        lvl = madness_level(a["sanity"])
        if lvl >= 1:
            out.append(f"MIND: your sanity is {a['sanity']}: you are {MADNESS_NAMES[lvl]}."
                       + (" Dark thoughts keep intruding and you care less and less about consequences." if lvl >= 2 else ""))
        imp = self.impulses.get(cid)
        if imp:
            t = self.nm(imp["target"]) if imp.get("target") else "someone"
            out.append(f"DARK IMPULSE: you feel {IMPULSES[imp['kind']].format(t=t)}. You can resist or give in; the lower your sanity, the harder resisting is. "
                       "If you give in, do it for real (action 'assault' to hurt someone present, 'sabotage' for the lights, or a cruel remark in conversation).")
        isl = self.island_line()
        if isl:
            out.append(isl)
        return out

    def card_extras(self, pid, group):
        w = self.world
        if not self.revealed:
            return ""
        a = w.agents[pid]
        title, desc = DRIVES.get(a["drive"]["id"], DRIVES["survivor"])
        tgt = f" (target: {self.nm(a['drive']['target'])})" if a["drive"].get("target") in w.agents else ""
        bits = [f" Secret drive (the others do not know): {title}{tgt}: {desc}"]
        imp = self.impulses.get(pid)
        if imp:
            t = self.nm(imp["target"]) if imp.get("target") else "someone"
            bits.append(f" DARK IMPULSE right now: {IMPULSES[imp['kind']].format(t=t)}; if they give in, show it.")
        for o in group:
            if o != pid and o in w.agents:
                k = next((k for k in a["known_secrets"] if k["of"] == o), None)
                if k:
                    bits.append(f" Knows {self.nm(o)}'s secret: {k['text'][:110]}.")
        return "".join(bits)

    # ------------------------------------------------------------------ madness
    def check_madness(self, tick, cid, before):
        a = self.world.agents.get(cid)
        if not a:
            return
        lo, hi = madness_level(before), madness_level(a["sanity"])
        if hi > lo and hi >= 2:
            text = {2: f"{self.nm(cid)} is unraveling; something in their eyes has changed.",
                    3: f"{self.nm(cid)} is breaking down.", 4: f"{self.nm(cid)} has snapped."}[hi]
            self.log_event(tick, {"type": "madness", "who": cid, "room": a["room"], "vis": "public", "text": text},
                           witnesses=[o for o in self.world.occupants(a["room"]) if o != cid], actor=cid)
            if hi >= 3:
                self.fx(tick, "shake", a["room"], cid)

    def roll_impulses(self, hour):
        """Low-sanity characters get dark impulses; they may resist or give in."""
        w = self.world
        self.impulses, self.impulse_done = {}, set()
        f = self.chaos_factor()
        for cid, a in w.agents.items():
            lvl = madness_level(a["sanity"])
            if lvl < 2:
                continue
            base = {2: 0.12, 3: 0.28, 4: 0.5}[lvl]
            drive = a["drive"]["id"]
            if drive in ("nihilist", "avenger", "saboteur"):
                base *= 1.5
            if self.rng.random() >= min(0.85, base * f):
                continue
            here = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid]
            pool = here or [o for o in w.agents if o != cid]
            tgt = min(pool, key=lambda o: a["aff"].get(o, 0)) if pool else None
            kinds = ["lash", "wreck", "isolate", "sabotage", "expose"]
            if here and self.murders:
                kinds += ["hurt"] * (3 if lvl >= 3 or drive in ("nihilist", "avenger") else 1)
            kind = self.rng.choice(kinds)
            if kind == "expose" and not [k for k in a["known_secrets"] if k["of"] != cid]:
                kind = "lash"
            self.impulses[cid] = {"kind": kind, "target": tgt if kind in ("hurt", "lash") else None, "level": lvl}

    def resolve_impulses(self, tick, hour, decisions, intents):
        """If someone with an impulse did not act on it themselves, it may boil over anyway."""
        w = self.world
        for cid, imp in list(self.impulses.items()):
            if cid not in w.agents:
                continue
            d = decisions.get(cid, {})
            if d.get("action") in ("assault", "attack", "sabotage"):
                continue
            p = {2: 0.2, 3: 0.4, 4: 0.6}[imp["level"]] * min(2.0, self.chaos_factor())
            if self.rng.random() < p:
                self.perform_impulse(tick, hour, cid, imp, intents)

    def perform_impulse(self, tick, hour, cid, imp, intents):
        w, s = self.world, self.s
        a = w.agents[cid]
        name, room = self.nm(cid), a["room"]
        here = [o for o in w.occupants(room) if o in w.agents and o != cid]
        kind = imp["kind"]
        if kind == "hurt" and (not here or not self.murders):
            kind = "wreck"
        if kind == "expose":
            sec = [k for k in a["known_secrets"] if k["of"] != cid]
            if sec and here:
                k = self.rng.choice(sec)
                self.reveal_secret(tick, cid, k["of"], [o for o in here] + [], "blurts out")
                return
            kind = "lash"
        if kind == "hurt":
            t = imp["target"] if imp.get("target") in here else self.rng.choice(here)
            self.do_assault(tick, cid, t, None, hour)
        elif kind == "wreck" and room == "boathouse" and self.wreck_raft(tick, cid, self.rng.choice(["kicks the raft's frame apart", "slashes the lashings", "smashes the deck"])):
            self.fx(tick, "shake", room, cid)
        elif kind == "wreck":
            pool = [k for k, q in s["room_items"].get(room, {}).items() if q > 0 and not set(w.item_spec(k).get("tags", [])) & {"key", "mystery"}]
            if pool:
                it = self.rng.choice(pool)
                s["room_items"][room][it] -= 1
                if s["room_items"][room][it] <= 0:
                    del s["room_items"][room][it]
                verb = self.rng.choice(["hurls", "smashes", "kicks across the room"])
                text = f"{name} {verb} the {w.item_name(it)} in a fit of rage."
            else:
                self.stat(tick, cid, "hp", -3, "punched a wall")
                text = f"{name} punches the wall until their knuckles bleed."
            self.log_event(tick, {"type": "outburst", "who": cid, "room": room, "vis": "public", "text": text}, witnesses=here, actor=cid)
            for o in here:
                self.stat(tick, o, "sanity", -1, f"{name}'s outburst")
            self.fx(tick, "shake", room, cid)
        elif kind == "sabotage":
            self.blackout_until = self.idx + 1
            self.log_event(tick, {"type": "outburst", "who": cid, "room": room, "vis": "public",
                                  "text": f"{name} rips the fuse box open: the lights and cameras die across the house."},
                           witnesses=here, actor=cid)
            for o in w.agents:
                if o not in here and o != cid:
                    w.remember(o, f"{_hh(hour)} The lights and cameras suddenly died across the house.")
            self.fx(tick, "flash", room, cid)
            self.day_notable.append(f"{name} cut the power in a fit of madness.")
        elif kind == "isolate":
            home = w.cast[cid]["home"]
            if room != home:
                steps = w.path(cid, room, home)
                if steps:
                    m = tick["moves"].setdefault(cid, {"from": room, "path": [room], "to": room})
                    m["path"] = list(m["path"]) + [r for r, _, _ in steps]
                    m["to"] = home
                    a["room"] = home
                    self.log_event(tick, {"type": "outburst", "who": cid, "room": room, "vis": "public",
                                          "text": f"{name} storms off to lock themselves in their room."}, witnesses=here, actor=cid)
        else:   # lash
            t = imp.get("target")
            if t in w.agents:
                intents[cid] = f"LASH OUT at {self.nm(t)}: say the cruelest true thing you know."
        self.impulse_done.add(cid)

    # ------------------------------------------------------------------ violence and sabotage
    def resolve_assaults(self, tick, assaults, hour):
        w = self.world
        for cid, d in assaults:
            if cid not in w.agents:
                continue
            t = d["target"]
            if t not in w.agents or t == cid or w.agents[t]["room"] != w.agents[cid]["room"]:
                self.log_event(tick, {"type": "system", "who": cid, "room": w.agents[cid]["room"], "vis": "gm",
                                      "text": f"{self.nm(cid)} wanted to hurt someone who was not there."}, actor=cid)
                continue
            self.do_assault(tick, cid, t, d.get("method"), hour)

    def do_assault(self, tick, cid, t, method, hour):
        """A non-lethal beating: heavy damage but health never drops below 5. Murder stays a separate action."""
        w = self.world
        a, v = w.agents[cid], w.agents[t]
        room = a["room"]
        name, tname = self.nm(cid), self.nm(t)
        here = [o for o in w.occupants(room) if o not in (cid, t)]
        weapon = method if method and a["inv"].get(method, 0) > 0 and "weapon" in w.item_spec(method).get("tags", []) else None
        tags = w.item_spec(weapon).get("tags", []) if weapon else []
        lo, hi = (15, 25) if "sharp" in tags else (12, 20) if "blunt" in tags else (8, 14)
        with_ = f" with the {w.item_name(weapon)}" if weapon else ""
        self.env_fight(tick, room)
        if self.rng.random() < 0.8:
            dmg = self.rng.randint(lo, hi)
            v.setdefault("harmed_by", []).append([cid, self.day, hour])
            if (v["hp"] - dmg <= 0 or (v["hp"] <= 30 and self.rng.random() < self.slip_chance(cid) * 0.5)) and self.lethal_blow(tick, cid, t, weapon, hour):
                return
            self.stat(tick, t, "hp", -dmg, f"assaulted by {name}")
            self.injure(tick, t, cid, set(tags), dmg, "blow", weapon)
            self.maybe_ko(tick, cid, t, set(tags), dmg)
            if self.murders and not self.s.get("case") and 1 <= v["hp"] <= 8 and self.rng.random() < 0.4:
                v["internal"] = {"by": cid, "weapon": weapon}           # a hidden injury that may kill them in the night
            self.stat(tick, t, "sanity", -4, "assaulted")
            self.adjust_any_aff(t, cid, -5)
            for o in here:
                self.adjust_any_aff(o, cid, -2)
                self.stat(tick, o, "sanity", -1, "witnessed violence")
            verb = self.rng.choice(["slams", "beats", "hurls themselves at", "lashes out at"])
            self.log_event(tick, {"type": "assault", "who": cid, "room": room, "vis": "public",
                                  "text": f"{name} {verb} {tname}{with_}, leaving them hurt."}, witnesses=here + [t], actor=cid)
            w.remember(t, f"{hhmm_(hour)} (private) {name} attacked you{with_}.")
            self.fx(tick, "shake", room, cid)
            self.fx(tick, "flash", room, t)
            self.betrayal(tick, cid, t, "attacked")
            self.moment(t, f"{name} attacked you")
            self.tally(cid, "assaults")
            self.day_notable.append(f"{name} assaulted {tname}.")
        else:
            self.adjust_any_aff(t, cid, -2)
            self.log_event(tick, {"type": "assault", "who": cid, "room": room, "vis": "public",
                                  "text": f"{name} swings at {tname}{with_} and misses."}, witnesses=here + [t], actor=cid)
            self.fx(tick, "shake", room, cid)

    def resolve_sabotages(self, tick, sabs, hour):
        w, s = self.world, self.s
        for cid, d in sabs:
            if cid not in w.agents:
                continue
            a = w.agents[cid]
            name, room = self.nm(cid), a["room"]
            here = [o for o in w.occupants(room) if o != cid]
            m = (d.get("method") or "").lower()
            self.tally(cid, "sabotages")
            if m == "lights":
                self.blackout_until = self.idx + 1
                self.log_event(tick, {"type": "sabotage", "who": cid, "room": room, "vis": "public",
                                      "text": f"{name} trips the breakers: the lights and cameras go out across the house."}, witnesses=here, actor=cid)
                for o in w.agents:
                    if o not in here and o != cid:
                        w.remember(o, f"{hhmm_(hour)} The lights and cameras suddenly went out across the house.")
                self.fx(tick, "flash", room, cid)
            elif m == "raft" and self.wreck_raft(tick, cid):
                pass
            elif m == "occasion" and s.get("occasion"):
                oc = s["occasion"]
                s["occasion"] = None
                self.log_event(tick, {"type": "sabotage", "who": cid, "room": room, "vis": "public",
                                      "text": f"{name} sabotages {self.nm(oc['host'])}'s {oc['kind']}: it is off."}, witnesses=list(w.agents), actor=cid)
                self.adjust_any_aff(oc["host"], cid, -2)
            elif m == "steal":
                t, item = d.get("target"), d.get("item")
                if t in w.agents and t != cid and w.agents[t]["room"] == room and w.agents[t]["inv"].get(item, 0) > 0 \
                        and not set(w.item_spec(item).get("tags", [])) & {"secret"} and self.rng.random() < 0.55:
                    w.agents[t]["inv"][item] -= 1
                    if w.agents[t]["inv"][item] <= 0:
                        del w.agents[t]["inv"][item]
                    a["inv"][item] = a["inv"].get(item, 0) + 1
                    noticed = self.rng.random() < 0.5
                    self.log_event(tick, {"type": "sabotage", "who": cid, "room": room, "vis": "public" if noticed else "gm",
                                          "text": f"{name} steals the {w.item_name(item)} from {self.nm(t)}" + ("" if noticed else " without being noticed") + "."},
                                   witnesses=here, actor=cid)
                    self.hook_from_steal(tick, cid, t, item, noticed)
                    if noticed:
                        self.add_tie(t, cid, "wronged", f"{name} stole their {w.item_name(item)} and they saw it", -0)
                        self.adjust_any_aff(t, cid, -3)
                        w.remember(t, f"{hhmm_(hour)} (private) You caught {name} stealing your {w.item_name(item)}.")
                else:
                    self.log_event(tick, {"type": "system", "who": cid, "room": room, "vis": "gm",
                                          "text": f"{name} tried to steal something and failed."}, actor=cid)

    # ------------------------------------------------------------------ betrayals
    def betrayal(self, tick, actor, victim, what):
        w, s = self.world, self.s
        b = next((e for e in s["bonds"] if {e["a"], e["b"]} == {actor, victim} and e["kind"] in ("romance", "pact")), None)
        if not b:
            return
        s["bonds"] = [e for e in s["bonds"] if e is not b]
        self.adjust_any_aff(victim, actor, -6)
        self.stat(tick, victim, "sanity", -7 if b["kind"] == "romance" else -5, "betrayed")
        self.log_event(tick, {"type": "betrayal", "who": actor, "room": w.agents[actor]["room"], "vis": "public",
                              "text": f"BETRAYAL: {self.nm(actor)} {what} {self.nm(victim)}, shattering their {'romance' if b['kind'] == 'romance' else 'pact'}."},
                       witnesses=[o for o in w.occupants(w.agents[actor]["room"]) if o in w.agents] + [victim], actor=actor)
        self.fx(tick, "flash", w.agents[actor]["room"], victim)
        self.moment(victim, f"{self.nm(actor)} betrayed you ({what})")
        self.tally(actor, "betrayals")
        self.tally(victim, "betrayed")
        self.saga(f"{self.nm(actor)} betrayed {self.nm(victim)}.")

    # ------------------------------------------------------------------ secrets, leaks, threats
    def learn_secret(self, cid, about, how):
        w = self.world
        a = w.agents.get(cid)
        if not a or about not in w.cast or cid == about or any(k["of"] == about for k in a["known_secrets"]):
            return False
        a["known_secrets"].append({"of": about, "text": w.cast[about]["secret"], "how": how, "day": self.day})
        w.remember(cid, f"(learned secret) {self.nm(about)}: {w.cast[about]['secret'][:160]}")
        return True

    def reveal_secret(self, tick, by, about, to, how="lets slip"):
        """`by` may be a participant who knows the secret, TereVi, or the person themselves (a confession)."""
        w = self.world
        if about not in w.cast or about not in w.all_agents:
            return False
        if by not in ("terevi", about) and not (by in w.agents and any(k["of"] == about for k in w.agents[by]["known_secrets"])):
            return False
        newly = [c for c in dict.fromkeys(to) if c in w.agents and c not in (about, by) and self.learn_secret(c, about, f"{how} by {self.nm(by)}")]
        if not newly:
            return False
        room = w.agents[by]["room"] if by in w.agents else (w.agents[about]["room"] if about in w.agents else "foyer")
        who = "TereVi" if by == "terevi" else self.nm(by)
        txt = (f"{self.nm(about)} confesses a secret to {', '.join(self.nm(c) for c in newly)}." if by == about
               else f"{who} {how} {self.nm(about)}'s secret to {', '.join(self.nm(c) for c in newly)}: {w.cast[about]['secret'][:120]}")
        self.log_event(tick, {"type": "leak", "who": by if by in w.agents else about, "room": room, "vis": "public", "text": txt},
                       witnesses=newly + ([about] if about in w.agents else []), actor=about if about in w.agents else None)
        if about in w.agents and by != about:
            self.stat(tick, about, "sanity", -3, "secret exposed")
            self.moment(about, f"your secret was exposed" + (f" by {self.nm(by)}" if by in w.agents else ""))
            if by in w.agents:
                self.adjust_any_aff(about, by, -3)
                self.betrayal(tick, by, about, "exposed the secret of")
        self.fx(tick, "flash", room, about)
        if by in w.agents:
            self.tally(by, "leaks")
        self.day_notable.append(txt[:140])
        return True

    def create_threat(self, tick, hour, target, demand):
        w, s = self.world, self.s
        if target not in w.agents or any(t["status"] == "active" for t in s["threats"]):
            return False
        due_day, due_hour = (self.day, hour + 6) if hour + 6 <= 20 else (self.day + 1, 12)
        s["threats"].append({"target": target, "secret": w.cast[target]["secret"], "demand": demand[:300], "due_day": due_day,
                             "due_hour": due_hour, "status": "active"})
        return True

    def check_threats(self, tick, hour):
        """When a threat comes due, TereVi judges whether the target complied and leaks the secret if not."""
        w, s = self.world, self.s
        for th in s["threats"]:
            if th["status"] != "active" or (self.day, hour) < (th["due_day"], th["due_hour"]):
                continue
            th["status"] = "done"
            t = th["target"]
            if t not in w.agents:
                continue
            recent = " | ".join(w.agents[t]["memory"]["recent"][-12:]) or "nothing notable"
            sysm = (f"{self.bible()}\nYou are TereVi. {HOSTS['terevi']['persona']} Reply with a single JSON object and nothing else.")
            user = (f"You threatened to broadcast {self.nm(t)}'s secret unless they did this: {th['demand']}\nWhat {self.nm(t)} has done since: {recent}\n"
                    'Did they comply? Reply as JSON: {"complied": true|false, "text": "<your on-air reaction, max 40 words>"}')
            try:
                r = self.llm.host_json(sysm, user, {"kind": "threat"})
            except LLMError as e:
                if e.fatal:
                    raise
                continue
            except Exception:
                continue
            text = str(r.get("text", "")).strip()[:300] or "Time's up, darling."
            tick["broadcasts"].append({"speaker": "terevi", "kind": "tease", "text": text})
            if r.get("complied") is True:
                self.log_event(tick, {"type": "tease", "who": t, "room": w.agents[t]["room"], "vis": "public",
                                      "text": f"{self.nm(t)} met TereVi's demand, and the secret stays buried."}, witnesses=list(w.agents), actor=t)
                self.special_boost(tick, t, 3, "relief", "comfort")
            else:
                self.reveal_secret(tick, "terevi", t, list(w.agents.keys()), "broadcasts")
                self.stat(tick, t, "sanity", -6, "exposed on air")

    # ------------------------------------------------------------------ island events
    def maybe_island_event(self, tick, hour):
        w, s = self.world, self.s
        isl = s.get("island")
        if isl and not self.island_live(isl):
            s["island"] = isl = None
        if isl or not self.revealed:
            return
        forced = self.force_island if self.force_island in ISLAND_EVENTS else None
        self.force_island = None
        p = {0.5: 0.03, 1.0: 0.07, 2.0: 0.15}[self.chaos_factor()]
        if not forced and (hour == 8 or self.rng.random() >= p):
            return
        eid = forced or self.rng.choice(list(ISLAND_EVENTS))
        ev = ISLAND_EVENTS[eid]
        room = None
        if eid == "fire":
            room = "kitchen"
        elif eid == "cat":
            room = self.rng.choice([r for r, v in ROOMS.items() if v[1] not in ("roof", "basement")])
        elif eid == "package":
            room = "foyer"
        s["island"] = {"id": eid, "title": ev["title"], "room": room, "until_abs": self.abs_now(hour) + (ev["dur"] - 1) * max(1, self.step) + 1}
        tick["broadcasts"].append({"speaker": "terevi", "kind": "tease", "text": ev["intro"]})
        self.log_event(tick, {"type": "island", "who": "terevi", "room": room or "foyer", "vis": "public", "text": f"{ev['title']}: {ev['intro']}"},
                       witnesses=list(w.agents))
        for cid in w.agents:
            w.remember(cid, f"{_hh(hour)} ISLAND EVENT: {ev['title']}: {ev['text']}")
        if eid in ("storm", "power"):
            self.blackout_until = self.idx + 1
            self.fx(tick, "rain" if eid == "storm" else "dark")
        elif eid == "fog":
            self.fx(tick, "fog")
        elif eid == "fire":
            self.fx(tick, "fire", room)
            self.env_ignite_room(tick, room)
        elif eid == "cat":
            self.fx(tick, "cat", room)
        elif eid == "package":
            item = self.rng.choice(PACKAGE_ITEMS)
            pool = s["room_items"].setdefault("foyer", {})
            pool[item] = pool.get(item, 0) + 1
            self.fx(tick, "flash", "foyer")
        self.day_notable.append(f"{ev['title']} hit the island.")

    def island_tick_effects(self, tick, hour):
        """End-of-turn consequences of the active island event."""
        w, s = self.world, self.s
        isl = s.get("island")
        if not isl or not self.island_live(isl):
            return
        eid = isl["id"]
        if eid == "storm":
            for cid, a in w.agents.items():
                if ROOMS[a["room"]][1] == "grounds":
                    self.stat(tick, cid, "hp", -5, "storm", lethal="struck down outside in the storm")
                    if cid in w.agents and self.rng.random() < 0.35:
                        self.add_cond(tick, cid, "chilled", 1, "the storm")
                    self.stat(tick, cid, "sanity", -2, "storm")
                    self.log_event(tick, {"type": "island", "who": cid, "room": a["room"], "vis": "gm", "text": f"{self.nm(cid)} is battered by the storm outside."}, actor=cid)
        elif eid == "fog":
            for cid in list(w.agents):
                self.stat(tick, cid, "sanity", -1, "whispers in the fog")
                self.maybe_panic(tick, cid, "the whispers in the fog", 0.06)
        elif eid == "fire":
            present = [c for c, a in w.agents.items() if a["room"] == "kitchen"]
            for c in present:
                self.stat(tick, c, "hp", -6, "smoke", lethal="overcome by smoke in the kitchen fire")
                if c in w.agents:
                    self.injure(tick, c, None, set(), 6, "fire")
                self.stat(tick, c, "sanity", -2, "fire")
            if len(present) >= 2:
                self.log_event(tick, {"type": "island", "who": present[0], "room": "kitchen", "vis": "public",
                                      "text": f"{', '.join(self.nm(c) for c in present)} put out the kitchen fire together."}, witnesses=list(w.agents), actor=present[0])
                for c in present:
                    self.special_boost(tick, c, 3, "put out the fire together", "comfort")
            else:
                pool = s["room_items"].get("kitchen", {})
                for k in list(pool)[:3]:
                    del pool[k]
                self.log_event(tick, {"type": "island", "who": "terevi", "room": "kitchen", "vis": "public",
                                      "text": "Nobody was there in time: the kitchen burns and its contents are lost."}, witnesses=list(w.agents))
        elif eid == "cat":
            room = isl.get("room")
            for cid, a in w.agents.items():
                if a["room"] == room:
                    self.special_boost(tick, cid, 3, "found the stray cat", "comfort")
                    self.log_event(tick, {"type": "island", "who": cid, "room": room, "vis": "public", "text": f"{self.nm(cid)} finds the stray cat and melts."}, actor=cid)
            if s["npcs"]["neovi"]["room"] == room:
                for cid, a in w.agents.items():
                    if a["room"] == room:
                        self.adjust_any_aff("neovi", cid, 1)

    # ------------------------------------------------------------------ nightly reflection and recap
    def reflect_prompt(self, cid):
        """One call per night per character: a diary entry plus a possible change of drive. Returns (system, user, ctx) for the call."""
        w = self.world
        a, c = w.agents[cid], w.cast[cid]
        d = a["drive"]
        known = {k: v for k, v in a["aff"].items() if k in w.agents}
        ranked = sorted(known.items(), key=lambda kv: kv[1])
        rel = ", ".join(f"{self.nm(k)} {v:+d}" for k, v in (ranked[:2] + ranked[-2:]))
        lvl = madness_level(a["sanity"])
        mem = a["memory"]
        sysm = ("You write a character's private end-of-day reflection in a drama. Reply with a single JSON object and nothing else.")
        options = ", ".join(DRIVES)
        user = (f"Character: {c['name']} ({c['role']}). Day {self.day}. Sanity {a['sanity']} ({MADNESS_NAMES[lvl]}), health {a['hp']}. "
                f"Current secret drive: {d['id']}{' targeting ' + self.nm(d['target']) if d.get('target') in w.agents else ''}. Feelings: {rel}.\n"
                f"What they lived through today:\n" + "\n".join(mem["recent"][-20:]) + "\n"
                + (self.lost_lines(cid) + "\n" if a["memory"].get("lost") else "")
                + ("Their mind is breaking: a turn toward nihilist or avenger is very plausible. " if lvl >= 3 else "")
                + f"Write the diary entry (first person, plain, max 60 words), and decide whether today changed what they want. Drive options: {options}."
                + self.reflect_menu(cid) + " "
                  'Reply as JSON: {"diary": "...", "drive": "keep or a drive id", "target": "<person id or empty>", "arc": "<one sentence on how they are changing>", "choices": []}')
        return sysm, user, {"events": mem["recent"], "ids": list(w.agents.keys()), "cid": cid}

    def reflect_apply(self, cid, tick, r, err=None):
        """Apply one night's reflection (the model's answer, or None after an error). Returns the diary text."""
        w = self.world
        a = w.agents[cid]
        d = a["drive"]
        known = {k: v for k, v in a["aff"].items() if k in w.agents}
        mem = a["memory"]
        if err is not None or not isinstance(r, dict):
            return " ".join(mem["recent"][-3:])[:300]
        diary = str(r.get("diary", "")).strip() or " ".join(mem["recent"][-3:])[:300]
        new = r.get("drive")
        tgt = r.get("target") if r.get("target") in w.agents and r.get("target") != cid else None
        if isinstance(r.get("arc"), str) and r["arc"].strip():
            d["arc"] = r["arc"].strip()[:200]
        if new in DRIVES and new != d["id"]:
            old = d["id"]
            d["id"], d["target"] = new, tgt
            tick["events"].append({"type": "drive", "who": cid, "room": a["room"], "vis": "gm",
                                   "text": f"{self.nm(cid)}'s drive shifts from {old} to {new}" + (f" (target: {self.nm(tgt)})" if tgt else "")})
        elif tgt and d["id"] in ("avenger", "protector"):
            d["target"] = tgt
        # a mind that has snapped turns dark on its own
        if a["sanity"] < 10 and d["id"] not in ("nihilist", "avenger") and self.rng.random() < 0.5 * min(2.0, self.chaos_factor()):
            worst = min(known, key=known.get) if known else None
            d["id"] = "avenger" if (worst and known[worst] <= -3) else "nihilist"
            d["target"] = worst if d["id"] == "avenger" else None
            tick["events"].append({"type": "madness", "who": cid, "room": a["room"], "vis": "public",
                                   "text": f"{self.nm(cid)} has snapped for good and now wants to {'make ' + self.nm(worst) + ' pay' if d['id'] == 'avenger' else 'watch it all burn'}."})
        return diary

    def make_recap(self, tick):
        w, s = self.world, self.s
        notable = self.day_notable[-18:]
        if not notable:
            return
        sysm = (f"{self.bible()}\nYou are TereVi writing the 'previously on' recap and the awards for tonight's episode. Reply with a single JSON object and nothing else.")
        cast = ", ".join(f"{k}={w.cast[k]['name']}" for k in w.all_agents)
        user = (f"Episode of Day {self.day}. Cast ids: {cast}. The day's events: {'; '.join(notable)}\n"
                'Reply as JSON: {"title": "<punchy episode title, max 7 words>", "recap": "<3 to 4 sentences in your gleeful voice, naming specifics>", '
                '"awards": [{"title": "<MVP|Villain of the Day|Heartthrob|Biggest Betrayal|Most Pitiful|Wildcard>", "who": "<person id>", "why": "<max 14 words>"}]} '
                "Give 2 to 4 awards, only ones that the events support.")
        try:
            r = self.llm.host_json(sysm, user, {"kind": "recap", "ids": list(w.all_agents.keys())})
        except LLMError as e:
            if e.fatal:
                raise
            return
        except Exception:
            return
        awards = [{"title": str(x.get("title", ""))[:40], "who": x.get("who"), "why": str(x.get("why", ""))[:120]}
                  for x in (r.get("awards") or []) if isinstance(x, dict) and x.get("who") in w.all_agents][:4]
        title, recap = str(r.get("title", "")).strip()[:80], str(r.get("recap", "")).strip()[:600]
        if title and recap:
            tick["recap"] = {"title": title, "recap": recap, "awards": awards}


def hhmm_(h):
    return f"{h:02d}:00"
