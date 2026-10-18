"""Departures and the people the game made: last words after a verdict, escaped killers out in the world, and who is able to kill.

* Last words: after the vote, whoever is condemned (the killer, or an innocent the cast got wrong) and a killer who escapes speak before
  they go: why they did it (from the plot that drove them), what they feel, a word to the person they care about most, a word for whoever
  sent them there, and an answer or two from the cast. The engine decides each beat; one voicing call words them.
* Escaped killers out there: TereVi lets a killer go after a wrong verdict, or when the cast cannot agree. Out in the world, at a low
  chance, they try to help the people they left: going to the police or the press risks their reputation and a murder charge, and a
  killer is not easily believed. A remorseful one, or one who left someone they love on the island, tries more often. If believed, help
  is on its way (the rescue countdown in outside.py).
* Nobody kills for the sake of it: an attack the model decides on needs a real reason (a plot, or a motive against that person), unless
  the attacker is twisted (a `twisted` trait, extreme cruelty, a nihilist or saboteur drive) or has lost their mind (sanity under 15).
* A `yandere` trait: obsessive love. Anyone the beloved warms to is a rival worth killing; a beloved who turns cold may be killed too.
* The season has a fixed run (28 days by default, dial `season_days`): at the end of the last day TereVi ends the show her way.
* After the fourth trial no newcomers arrive: TereVi makes NeoVi a contestant instead (kumiko.make_participant), if she is still the maid.
DeparturesMixin is mixed into DayRunner (engine.py).
"""

MOTIVE_LINES = {
    "hatred": ["You all saw what {v} was like. I'm not sorry. ...Maybe a little.", "{v} made every day in this house a little worse. I just made it stop."],
    "jealousy": ["I loved {x}. {v} was taking {x} away from me. What was I supposed to do?", "Every time {x} looked at {v}, something in me broke. So I broke {v}."],
    "deadline": ["Somebody had to. The deadline was coming for all of us. I just went first.", "I did the maths. One of us, or all of us. I chose."],
    "blackmail": ["{v} knew what I did back home. {v} was going to use it. I couldn't let that happen.",],
    "revenge": ["{v} helped send someone I loved to their death. I promised myself.",],
    "vengeance": ["{v} had it coming. I'd do it again.",],
    "fear": ["{v} hurt me. I wasn't going to wait around for the next time.",],
    "retaliation": ["{v} had me helpless once. Never again. Never.",],
    "paranoia": ["I saw {v} standing over my bed with a knife. I saw it. ...Didn't I?",],
    "betrayal": ["{v} stabbed me in the back first. I just did it properly.",],
    "humiliation": ["{v} laughed at me. In front of everyone. Nobody laughs at me.",],
    "envy": ["Everybody loved {v}. Nobody even saw me. Well. You see me now.",],
    "protection": ["{v} was hurting someone I care about. I'd do it again.",],
    "exposure": ["{v} was about to find out. I panicked. That's all it was. Panic.",],
    "silencing": ["{v} saw something. I couldn't let them say it.",],
    "manslaughter": ["I didn't mean it. I swear I didn't mean any of it.", "It was an accident. It was supposed to be a fight, not... this."],
}
GENERIC = ["I don't even know why anymore. This place got inside my head.", "You want a reason? The island is the reason."]
REMORSE = ["I'm sorry. I'm so sorry. Tell {v}'s family I'm sorry.", "I'll see {v}'s face every night. I know that."]
DEFIANT = ["Smile for the cameras, everyone. Hehe. I learned that from her.", "Don't look at me like that. Any of you could have been me."]
INNOCENT = ["I didn't do it. You know I didn't do it.", "You got it wrong. The one who did this is still sitting with you.",
            "Fine. Go on, then. But it wasn't me, and one day you'll know it."]


class DeparturesMixin:
    # ------------------------------------------------------------------ last words
    def remorse_of(self, cid):
        f = self.facet
        return (f(cid, "altruism") - f(cid, "cruelty")) / 100 + (0.2 if self.world.all_agents[cid].get("sanity", 50) < 35 else 0)

    def farewell_beats(self, cid, case, votes, condemned, innocent):
        """What `cid` says before going, and the cast's answers."""
        w, s = self.world, self.s
        a = w.all_agents[cid]
        victim = case.get("victim")
        B = []
        say = lambda who, text, move, kind="say": self.trial_beat(B, who, text, move, kind)
        alive = [o for o in sorted(w.agents) if o != cid]
        if innocent:
            say(cid, self.rng.choice(INNOCENT), "innocent")
            voters = [v["voter"] for v in votes if v["target"] == cid and v["voter"] in w.agents]
            trusted = max(voters, key=lambda o: (a["aff"].get(o, 0), o), default=None)
            if trusted and a["aff"].get(trusted, 0) >= 3:
                say(cid, f"{self.nm(trusted)}. You too? ...Okay.", "betrayed")
                say(trusted, "I'm sorry. I'm so sorry.", "sorry")
        else:
            mot = case.get("motive") or {}
            kind = "manslaughter" if case.get("kind") == "manslaughter" else mot.get("kind")
            x = None
            if kind == "jealousy":
                x = max((o for o in w.all_agents if o not in (cid, victim)), key=lambda o: (a["aff"].get(o, 0), o), default=None)
            pool = MOTIVE_LINES.get(kind) or GENERIC
            say(cid, self.rng.choice(pool).format(v=self.nm(victim), x=self.nm(x) if x else "someone"), "motive")
            rem = self.remorse_of(cid)
            say(cid, (self.rng.choice(REMORSE) if rem > 0.1 else self.rng.choice(DEFIANT)).format(v=self.nm(victim)), "remorse" if rem > 0.1 else "defiant")
            case["remorse"] = rem
        loved = max(alive, key=lambda o: (a["aff"].get(o, 0), o), default=None)
        if loved and a["aff"].get(loved, 0) >= 5:
            say(cid, f"{self.nm(loved)}. Don't watch this part." if condemned else f"{self.nm(loved)}. I'll find a way. I promise.", "goodbye")
            back = w.agents[loved]["aff"].get(cid, 0)
            if innocent or back >= 6:
                say(loved, self.rng.choice(["I'll never forget you.", "I'll find out who really did it. I swear.", "Go. ...Go. I can't."])
                    if innocent else self.rng.choice(["I hate what you did. I don't hate you. I wish I did.", "...Goodbye."]), "answer")
            else:
                say(loved, "turns away and does not answer.", "turn", "act")
        if not innocent:
            angry = min(alive, key=lambda o: (w.agents[o]["aff"].get(cid, 0), o), default=None)
            if angry and w.agents[angry]["aff"].get(cid, 0) <= -3:
                say(angry, self.rng.choice([f"Save it. {self.nm(victim)} doesn't get a goodbye.", "I hope it hurts.", "Get them out of here."]), "curse")
        return B

    def trial_farewells(self, tick, hour, case, votes, accused, found, wrongful):
        """The condemned and an escaping killer speak before they go (one sequence, one voicing call)."""
        killer = case.get("killer")
        beats = []
        if found and killer:
            beats += self.farewell_beats(killer, case, votes, condemned=True, innocent=False)
        elif wrongful:
            beats += self.farewell_beats(accused, case, votes, condemned=True, innocent=True)
        if killer and not found:
            self.trial_beat(beats, "terevi", f"And our real culprit, {self.nm(killer)}, gets to walk out of here a free person! Any last words, darling?", "host")
            beats += self.farewell_beats(killer, case, votes, condemned=False, innocent=False)
        if beats:                                                  # voiced like a trial sequence, shown after the verdict (not one of the trial's sequences)
            seg = {"kind": "farewell", "title": "LAST WORDS", "n": 7, "of": 7, "meter": {}, "susp": {}, "theory": None}
            lines = self.voice_trial_lines(tick, beats, seg)
            if lines:
                g = {"room": "voting_grounds", "lines": lines, "segment": seg}
                said = [ln["m"] for x in tick.get("talk") or [] for ln in x.get("lines") or [] if "m" in ln]
                if said:                                           # on the clock after the trial's last line (claimtrial.stage_trial_live)
                    dur = self.sim_turn(tick).dur
                    m = min(dur - 2.0, max(said) + 1.0)
                    step = max(0.3, min(1.5, (dur - 1.0 - m) / (len(lines) + 1)))
                    g.update(live=True, m=round(m, 1), ended="trial", joined=[], left=[], members=sorted({ln["speaker"] for ln in lines}))
                    for ln in lines:
                        ln["m"], ln["room"] = round(min(dur - 1.0, m), 2), "voting_grounds"
                        m += step
                tick["talk"].append(g)
                for cid in self.world.agents:
                    for ln in lines[:8]:
                        who = "You" if cid == ln["speaker"] else self.nm(ln["speaker"])
                        self.world.remember(cid, f"{hour % 24:02d}:00 (last words) {who}: {ln['text'][:100]}")

    # ------------------------------------------------------------------ escaped killers
    def escapee_free(self, tick, killer, case):
        """A killer let go by TereVi. At a low chance they try to help from outside; mostly they keep quiet."""
        w, s = self.world, self.s
        a = w.all_agents.get(killer) or {}
        rem = case.get("remorse", self.remorse_of(killer) if killer in w.all_agents else 0)
        ties = max([a.get("aff", {}).get(o, 0) for o in w.agents] or [0])
        p = (0.06 + 0.12 * max(0.0, rem) + (0.08 if ties >= 6 else 0) - 0.05 * max(0, self.facet(killer, "vanity") - 60) / 40) * self.tune("escapee_help")
        crew = {"ids": [killer], "alive": [killer], "stage": "ashore", "kind": "killer", "days": 0, "food": 9, "tries": 0, "proof": False, "log": [], "day": self.day}
        if self.rng.random() >= max(0.0, p):
            crew["stage"] = "quiet"
            self.outside()["crews"].append(crew)
            self.outside_snip(tick, crew, self.rng.choice(KEEPS_QUIET).format(n=self.nm(killer)))
            return False
        self.outside()["crews"].append(crew)
        self.outside_snip(tick, crew, self.rng.choice(TRIES).format(n=self.nm(killer)))
        self.twist("killer_helps")
        return True

    def escapee_dawn(self, tick, crew):
        """An escaped killer trying to be believed: harder than for a raft crew, and the risk to themselves may stop them."""
        crew["tries"] += 1
        n = self.nm(crew["ids"][0])
        roll = self.rng.random()
        if roll < 0.15:
            crew["stage"] = "quiet"
            self.outside_snip(tick, crew, self.rng.choice(GIVES_UP).format(n=n))
        elif roll < 0.15 + 0.12 + 0.04 * crew["tries"]:
            crew["stage"] = "believed"
            self.outside_snip(tick, crew, f"{n} walks into a police station, puts both hands on the desk and confesses to a murder on a reality show. This time someone checks.")
            self.start_rescue(tick, "killer", f"{n}, a killer the show let go, confessed and was believed")
            self.twist("killer_believed")
        elif crew["tries"] >= 4:
            crew["stage"] = "dismissed"
            self.outside_snip(tick, crew, f"{n} has told the story to three newsrooms. One ran it, as satire.")
        else:
            self.outside_snip(tick, crew, self.rng.choice(STILL_TRYING).format(n=n))

    # ------------------------------------------------------------------ who is able to kill
    def twisted(self, cid):
        return (self.has_trait(cid, "twisted") or self.facet(cid, "cruelty") >= 80
                or (self.world.agents.get(cid) or {}).get("drive", {}).get("id") in ("nihilist", "saboteur"))

    def motive_ok(self, cid, target, d):
        """Nobody kills for the sake of it: an attack needs a plot or a motive against that person, unless the attacker is twisted or broken."""
        s = self.s
        if target not in self.world.agents:
            return True                                                  # resolve_attacks retargets or drops it
        if d.get("engine") or s.get("spree") or self.twisted(cid) or self.world.agents[cid]["sanity"] < 15:
            return True
        if (s.get("plots") or {}).get(cid, {}).get("target") == target:
            return True
        return any(t == target and sc >= 0.25 for sc, t, _, _ in self.plot_motives(cid))

    def yandere_motives(self, cid):
        """Obsessive love: rivals of the beloved, or the beloved who turned cold."""
        w = self.world
        if not self.has_trait(cid, "yandere"):
            return []
        a = w.agents[cid]
        others = [o for o in sorted(w.agents) if o != cid]
        beloved = max(others, key=lambda o: (a["aff"].get(o, 0), o), default=None)
        if not beloved or a["aff"].get(beloved, 0) < 6:
            return []
        out = []
        b = w.agents[beloved]
        rivals = [o for o in others if o != beloved and b["aff"].get(o, 0) >= 4]
        if rivals:
            r = max(rivals, key=lambda o: (b["aff"].get(o, 0), o))
            out.append((0.6 + 0.1 * (b["aff"].get(r, 0) - 4), r, f"{self.nm(beloved)} smiles at {self.nm(r)} the way they should only smile at you", "jealousy"))
        if b["aff"].get(cid, 0) <= -2 and a["sanity"] < 45:
            out.append((0.55, beloved, f"if you cannot have {self.nm(beloved)}, nobody will", "obsession"))
        return out

    # ------------------------------------------------------------------ the season's run, and the fourth trial
    def season_cap(self):
        return int(self.tune("season_days") or 28)

    def season_over_due(self, hour):
        return self.revealed and not self.s.get("over") and self.day >= self.season_cap() and hour >= 18          # the last turn of the day (18:00 to 20:00)

    def after_trial_count(self, tick):
        s = self.s
        s["trials_held"] = s.get("trials_held", 0) + 1
        if s["trials_held"] >= 4 and not s.get("no_newcomers"):
            s["no_newcomers"] = True
            if self.neovi_maid() and not s.get("over"):
                self.make_participant(tick, reason="fourth trial")
            else:
                self.saga("After the fourth trial, TereVi closes the doors: no more newcomers.")


KEEPS_QUIET = ["{n} is free. {n} changes their name, moves to a new city, and never says a word about the island.",
               "{n} sits in a hotel room for three days with the TV on mute. Then {n} books a flight somewhere far away and says nothing to anyone.",
               "{n} thinks about calling someone. Then {n} thinks about prison. The phone stays in the drawer."]
TRIES = ["{n} is free, and cannot stand it. {n} starts making calls, knowing every one of them could end in handcuffs.",
         "{n} walks out of TereVi's boat and straight to the nearest journalist. 'You'll want to sit down,' {n} says."]
GIVES_UP = ["{n}'s lawyer explains, very slowly, what a confession to murder means. {n} stops making calls.",
            "{n} sees their own face on a gossip site under the word 'MONSTER' and goes quiet."]
STILL_TRYING = ["{n} tells the story again, to a different officer. The officer takes notes, then looks at the clock.",
                "{n} posts the island's coordinates online. Most replies are memes. One is not.",
                "{n} finds a reporter who listens all the way to the end, and then asks for proof."]
