"""How a season ends, and what becomes of whoever walks out.

* The price of winning: a way out that works (TereVi shut down or surrendering, a rescue, crowned winners) is a good ending only if it
  did not cost too much. It is bittersweet when someone died in the finale itself or in TereVi's parting shot, when NeoVi gave her life
  to make it possible, when one survivor or fewer walks out of the house, or when crowned winners are all that is left of a killing game.
* TereVi's parting shot: when she loses she may take someone with her: a last execution of whoever hurt her most, or the lower floors
  flooding as the doors open (whoever is still inside has seconds, so only part of the island gets out).
* The rescue may leave someone behind: missing in the house and never found, or refusing to leave without someone they loved.
* Epilogues: every survivor gets a short aftermath built from the state: how broken they are, a lover who walked out with them or one
  who did not, a best friend, an enemy, a killing nobody outside knows about, and what they make of their old life. NeoVi (Kumiko) gets
  hers if she is still alive. One voicing call words them all; the template stands if the model gives nothing.
EndingsMixin is mixed into DayRunner (engine.py).
"""

GOOD = ("truth", "shutdown", "ultimatum", "rescue")
SHOT_P = 0.15
CAREER = ["{n}'s next project is about the island. It does very well, and {n} hates every minute of it.",
          "{n} turns down every interview. The one they finally give is three words long.",
          "{n} goes back to being {ar}, and is better at it, and does not know why that makes them angry.",
          "{n} quits being {ar} altogether and gets a job where nobody films anything.",
          "{n} writes a memoir. The publisher cuts the island chapters for being 'too much'. {n} laughs for the first time in months.",
          "{n} starts a podcast about true crime and quits after one episode, because it turns out it is not entertaining at all.",
          "{n} buys a house with no basement, no pool and no cameras, and is happy in it, mostly.",
          "{n} gets fan mail from people who thought it was all scripted. {n} answers every single one with the same photo of the island."]
STATE = [(60, ["{n} walks off the island steadier than anyone expected.", "{n} walks out into the daylight and, for a long moment, just stands in it.",
               "{n} is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight.",
               "{n} sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle.",
               "{n} gives the officers a full statement, calmly, in order, and then throws up in a bin."]),
         (30, ["{n} sleeps with the lights on for a year.", "{n} still checks every room twice before sitting down.",
               "{n} cannot stand the sound of a doorbell, or of anyone humming.", "{n} keeps a chair under the door handle, even at home, even with friends over."]),
         (0, ["{n} does not really come back from the island. There are good days, and there are days they count the doors.",
              "{n} is led out wrapped in a foil blanket, still whispering to someone who is not there."])]


class EndingsMixin:
    # ------------------------------------------------------------------ the price
    def ending_costs(self, kind, ids):
        """What made a win cost too much (a list of short reasons; empty means a clean win)."""
        w, s = self.world, self.s
        if kind not in GOOD + ("winners",):
            return []
        out = []
        if kind == "winners":
            out.append("only the last few of a killing game walked out")
        shot = s.get("_parting") or {}
        if shot.get("dead"):
            out.append("TereVi took " + ", ".join(self.nm(c) for c in shot["dead"]) + " with her")
        arc = s["npcs"]["neovi"].get("arc") or {}
        if arc.get("fate") == "martyr" and self.day - arc.get("fate_day", self.day) <= 3:
            out.append("NeoVi gave her life for it")
        if s.get("_left_behind"):
            out.append(f"{self.nm(s['_left_behind'])} never came out of the house")
        walkers = [c for c in ids if (w.all_agents.get(c) or {}).get("status", "alive") == "alive"]
        if len(walkers) <= 1:
            out.append("one survivor or fewer walked out of the house")
        return out

    def parting_shot(self, tick, kind, team=()):
        """TereVi loses, and takes someone with her. Returns the dead."""
        w, s = self.world, self.s
        if self.rng.random() >= SHOT_P * self.tune("parting_shot") or len(w.agents) < 2:
            return []
        dead = []
        if self.rng.random() < 0.5 and team:
            stats = s.get("stats", {})
            c = max([c for c in team if c in w.agents] or sorted(w.agents), key=lambda x: (stats.get(x, {}).get("route_steps", 0), x))
            text = (f"As her voice dies, one last panel slides open: TereVi's final segment. {self.nm(c)}, who hurt her most, does not make it to the doors. "
                    "'Brought to you by spite,' she manages, and then nothing.")
            dead = [c]
        else:
            inside = [c for c in sorted(w.agents) if c not in team and w.agents[c]["room"] not in ("beach", "garden", "maze", "woods", "pool", "lighthouse", "lookout", "boathouse", "generator_shed")]
            dead = [c for c in inside if self.rng.random() < 0.4][:3]
            if not dead:
                return []
            text = (f"As the doors unlock, the lower floors flood. Whoever is still inside has seconds. {', '.join(self.nm(c) for c in dead)} "
                    f"{'does' if len(dead) == 1 else 'do'} not get out. Half the island walks into the daylight; the other half is still in there.")
        for c in dead:
            w.agents[c]["hp"] = 0
            w.end_agent(c, "dead", "taken by TereVi's parting shot")
            self.moment(c, "was taken by TereVi's parting shot")
        s["_parting"] = {"dead": dead, "text": text}
        self.log_event(tick, {"type": "system_notable", "who": dead[0], "room": "foyer", "vis": "public", "text": text}, witnesses=list(w.agents))
        self.saga(text)
        return dead

    def rescue_loss(self, tick):
        """Rescuers search the house; someone may never come out of it."""
        w, s = self.world, self.s
        if len(w.agents) < 3 or self.rng.random() >= 0.3:
            return None
        grieving = [c for c in sorted(w.agents) if any(g["id"] in w.cast and w.agents[c]["aff"].get(g["id"], 0) >= 7 for g in s["graveyard"])
                    and w.agents[c]["sanity"] < 40]
        if grieving:
            c = grieving[0]
            lost = max((g["id"] for g in s["graveyard"] if g["id"] in w.cast), key=lambda d: (w.agents[c]["aff"].get(d, 0), d))
            text = f"{self.nm(c)} will not leave without {self.nm(lost)}. When the boats go, {self.nm(c)} is still on the beach, digging. Nobody can make them stop."
            how = f"stayed behind with {self.nm(lost)}"
        else:
            c = min(sorted(w.agents), key=lambda x: (w.agents[x]["sanity"], x))
            text = f"The officers search every room twice. {self.nm(c)} is not in any of them. The island keeps one."
            how = "never found"
        w.end_agent(c, "dead", how)
        s["_left_behind"] = c
        self.log_event(tick, {"type": "system_notable", "who": c, "room": "foyer", "vis": "public", "text": text})
        self.saga(text)
        return c

    def last_stand_route(self):
        """With only a few left and TereVi about to end it her way, the survivors may try a way out that is not finished (once a season).
        Odds drop with how unfinished it is."""
        s = self.s
        if s.get("_last_stand") or s.get("over") or s.get("case") or not self.world.agents:
            return None
        from .data_world import ESCAPE_ROUTES
        rid = max(ESCAPE_ROUTES, key=lambda r: (self.route_pct(r), r))
        pct = self.route_pct(rid)
        if pct < 70 * self.tune("last_stand"):
            return None
        s["_last_stand"] = {"day": self.day, "route": rid, "pct": pct}
        self._desperate = 0.5 * (100 - pct) / 100
        self.saga(f"With only {len(self.world.agents)} left, they try the {ESCAPE_ROUTES[rid]['title'].lower()} before it is ready.")
        return rid

    # ------------------------------------------------------------------ epilogues
    def _pick(self, pool, **kw):
        """A line from `pool` not used yet in this season's epilogues."""
        used = self.__dict__.setdefault("_ep_used", set())
        fresh = [x for x in pool if x not in used] or pool
        line = self.rng.choice(fresh)
        used.add(line)
        return line.format(**kw)

    def epilogue_for(self, cid, kind):
        """Two or three sentences: how they come out of it, the person who matters most (alive or dead), and what they carry."""
        w, s = self.world, self.s
        a, c = s["agents"][cid], w.cast[cid]
        n, r = c.get("short") or c["name"], (c.get("role") or "celebrity").lower()
        ar = ("an " if r[:1] in "aeiou" else "a ") + r
        out = [self._pick(next(lines for floor, lines in STATE if a.get("sanity", 50) >= floor), n=n)]
        out_ids = [o for o in (s.get("_epilogue_ids") or []) if o != cid]
        aff = a.get("aff", {})
        nm = self.nm
        lovers = [o for o in sorted(aff) if o in w.cast and o != cid and (any(b.get("kind") == "romance" and {b["a"], b["b"]} == {cid, o} for b in s.get("bonds", []))
                                                                          or any({x["a"], x["b"]} == {cid, o} for x in s.get("nights", [])))]
        dead = {g["id"]: g for g in s["graveyard"] if g["id"] in w.cast and g["status"] in ("dead", "executed")}
        wronged = [t for t in s.get("ties", []) if t["a"] == cid and t["kind"] in ("betrayed", "wronged") and t["b"] in w.cast]
        lover_out = next((o for o in lovers if o in out_ids), None)
        lover_dead = next((o for o in sorted(lovers, key=lambda x: -aff.get(x, 0)) if o in dead), None)
        if lover_out:
            pair = tuple(sorted((cid, lover_out)))
            fate = self.__dict__.setdefault("_ep_love", {}).get(pair)
            if fate is None:
                fate = self._ep_love[pair] = "split" if self.rng.random() < 0.3 else "together"
                out.append(self._pick(["{n} and {o} stay together. The tabloids call them 'the couple who survived Murder Channel'; they call it something else, and only to each other.",
                                       "{n} and {o} move in together within a month, which everyone says is too fast, and which is the only thing about the last year that has felt right."]
                                      if fate == "together" else
                                      ["{n} and {o} last eight months on the outside. It turns out the island was holding them together; nobody is surprised, least of all them."],
                                      n=n, o=nm(lover_out)))
            else:
                out.append(f"{n} still keeps a spare key to {nm(lover_out)}'s door, and uses it." if fate == "together"
                           else f"{n} keeps {nm(lover_out)}'s hoodie from the island and gives back everything else.")
        elif lover_dead:
            out.append(self._pick(["{n} keeps something of {o}'s and talks to it when nobody is listening.",
                                   "Every year, on the day {o} died, {n} sets a second place at the table.",
                                   "{n} has {o}'s name tattooed somewhere only the next lover will see, and has to explain."], n=n, o=nm(lover_dead)))
        else:
            loved_dead = sorted((d for d in dead if aff.get(d, 0) >= 5), key=lambda x: -aff.get(x, 0))
            friends = sorted((o for o in out_ids if aff.get(o, 0) >= 3), key=lambda x: -aff.get(x, 0))
            foes = sorted((o for o in out_ids if aff.get(o, 0) <= -4), key=lambda x: aff.get(x, 0))
            if wronged and wronged[-1]["b"] in out_ids:
                o = wronged[-1]["b"]
                out.append(self._pick(["{n} never forgives {o}, who {why}. They see each other once, across a street, and both keep walking.",
                                       "{n} tells one interviewer about {o}, who {why}. {o}'s lawyers are in touch by morning."], n=n, o=nm(o), why=wronged[-1]["text"]))
            elif friends and (friends[0], cid) in self.__dict__.setdefault("_ep_pairs", set()):
                out.append(f"{n} is always the one who books the table with {nm(friends[0])}, and always the one who leaves first.")
            elif friends:
                self._ep_pairs.add((cid, friends[0]))
                out.append(self._pick(["{n} and {o} meet every year on the day they got out. They mostly talk about anything else.",
                                       "{n} is godparent to {o}'s first child. Nobody at the christening asks why they both flinch at the doorbell.",
                                       "{n} and {o} have a group chat with one other member. The other member is a picture of the island, with a rude caption."],
                                      n=n, o=nm(friends[0])))
            elif foes:
                out.append(self._pick(["{n} and {o} never speak again. They once end up at the same awards show and sit very, very far apart.",
                                       "{n} sues {o} over something said on the island. Both lose."], n=n, o=nm(foes[0])))
            elif loved_dead:
                out.append(self._pick(["{n} visits {o}'s family once, and cannot bring themselves to tell them how it really went.",
                                       "{n} still turns to tell {o} things, and {o} is still not there."], n=n, o=nm(loved_dead[0])))
        kills = s.get("stats", {}).get(cid, {}).get("kills", 0)
        if kills:
            out.append(self._pick(["Nobody outside ever learns what {n} did on the island. {n} does, every night.",
                                   "{n} has a good lawyer and a better story, and a face in the dark that the story leaves out."], n=n))
        elif len(out) < 3:
            moment = next((m.split(": ", 1)[-1] for m in reversed(a.get("memory", {}).get("moments", [])) if any(k in m for k in ("died", " die", "dead", "body", "killed", "executed"))), None)
            if moment and self.rng.random() < 0.5:
                out.append(f"{n} never talks about the day they {moment}.")
            else:
                out.append(self._pick(CAREER, n=n, r=r, ar=ar))
        return " ".join(out)

    def neovi_epilogue(self, kind):
        s = self.s
        nv = s["npcs"]["neovi"]
        fate = (nv.get("arc") or {}).get("fate")
        if fate == "martyr" or nv.get("participant") or kind not in GOOD + ("rescue_late", "winners"):
            return None
        if fate == "betrayer":
            return "NeoVi is led away with the rest of TereVi's equipment. Nobody stands up for her. In the van, she finally says her real name, to no one."
        lover = nv.get("lover")
        if lover and (self.world.all_agents.get(lover) or {}).get("status", "alive") == "alive":
            return (f"Kumiko Akimoto walks out behind the others, out of uniform for the first time in years, and takes {self.nm(lover)}'s hand at the gate. "
                    "She gets a small flat with a window that catches the afternoon sun, and a cat, and makes every decision herself, slowly.")
        return ("Kumiko Akimoto walks out behind the others, out of uniform, and gives the first officer her real name. "
                "She gets a small flat, a cat, and a job where nobody tells her what to clean.")

    def make_epilogues(self, tick, kind, ids):
        """One short aftermath per survivor, voiced in one call (template if the model gives nothing)."""
        w, s = self.world, self.s
        ids = [c for c in ids if c in w.cast and c in s["agents"]]
        s["_epilogue_ids"] = ids
        self._ep_used, self._ep_pairs, self._ep_love = set(), set(), {}
        eps = [{"id": c, "text": self.epilogue_for(c, kind)} for c in ids]
        nv = self.neovi_epilogue(kind)
        if nv:
            eps.append({"id": "neovi", "text": nv})
        if not eps:
            return []
        listing = "\n".join(f"{i}. {e['id']}: {e['text']}" for i, e in enumerate(eps))
        sysm = f"{self.bible()}\nThe season is over. You write the epilogue cards shown over the credits. Reply with JSON only."
        user = (f"The show ended: {s['over']['title']}. Rewrite each numbered epilogue in 2 or 3 sentences: same facts and relationships, no new deaths, "
                f"mature and bittersweet with a dry, dark wit, nothing explicit.\n{listing}\n" + 'Reply as JSON: {"lines": [{"i": <number>, "text": "..."}]}')
        try:
            res = self.llm.voice(sysm, user, {"beats": len(eps), "epilogue": True}) or {}
        except Exception as e:  # noqa: BLE001
            if getattr(e, "fatal", False):
                raise
            res = {}
        for ln in res.get("lines") or []:
            if isinstance(ln, dict) and isinstance(ln.get("i"), int) and 0 <= ln["i"] < len(eps) and str(ln.get("text", "")).strip():
                eps[ln["i"]]["text"] = str(ln["text"]).strip()[:420]
        return eps
