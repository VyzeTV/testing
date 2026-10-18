"""Two ways out played as live scenes: the night raid on TereVi's core, and the bomb standoff.

Like the gatherings (scenes.py), the engine decides each beat and the model only voices them; the team walks to the site on the live map.

* The raid on the core: the team lifts the hatch in the Lighthouse floor and goes down. Whether TereVi notices depends on how well she was
  blinded (the route's blind step, a blackout, NeoVi). If she notices she counters: she seals the hatch (someone has to force it), floods the
  stairs with gas (everyone hurt, the weakest may fold), or offers the shakiest member their life to walk away and raise the alarm. Then the
  pressure plates (each person can be hurt), then the core itself: the final roll is the route's odds, better if she never saw them coming.
* The bomb standoff: the team holds the trigger at the Generator Shed and makes demands. Over up to three rounds TereVi doubts them,
  bargains (one walks free if they hand it over), works on the shakiest member, or calls the bluff. The team holds, splits or folds; a turned
  member hands her the trigger. If she calls the bluff, the leader decides whether to press it: a real blast (deaths possible, the island
  dark, her cameras down for a while) or backing down. She surrenders when the threat is credible and the team does not break.

FinaleMixin is mixed into DayRunner (engine.py). routes.run_finale calls `live_finale` for these two routes.
"""

LIVE_FINALES = ("shutdown", "ultimatum", "raft")


class FinaleMixin:
    def finale_leader(self, team):
        return max(team, key=lambda c: (self.facet(c, "courage") + self.facet(c, "assertiveness"), c))

    def finale_weakest(self, team):
        """The one TereVi works on: low sanity, little loyalty to the others, self-interest."""
        w = self.world
        loyal = lambda c: sum(w.agents[c]["aff"].get(o, 0) for o in team if o != c) / max(1, len(team) - 1)
        return min(team, key=lambda c: (w.agents[c]["sanity"] / 2 + loyal(c) * 4 + self.facet(c, "altruism") / 3, c))

    def turned(self, cid, team):
        """Does `cid` take TereVi's offer?"""
        w = self.world
        loyal = sum(w.agents[cid]["aff"].get(o, 0) for o in team if o != cid) / max(1, len(team) - 1)
        p = 0.15 + max(0, 50 - w.agents[cid]["sanity"]) / 120 + max(0, 50 - self.facet(cid, "altruism")) / 200 - max(0, loyal) / 25
        return self.rng.random() < max(0.03, min(0.6, p))

    def live_finale(self, tick, rid, team, hour):
        """Play the finale as a scene. Returns (ok, outcome)."""
        p, aid = self.finale_odds(rid, team)
        beats = []
        if rid == "raft":
            ok, outcome, self._raft_crew = self.raft_launch(tick, team, p, beats)       # outside.py
        else:
            ok, outcome = (self.raid_core(tick, team, p, aid, beats) if rid == "shutdown" else self.bomb_standoff(tick, team, p, beats))
        site = {"shutdown": "core_vault", "ultimatum": "generator_shed", "raft": "beach"}[rid]
        if (self.s.get("locks") or {}).get(site, {}).get("by") == "terevi":       # her lockdown (escape.escape_counter) does not stop them tonight
            del self.s["locks"][site]
            self.log_event(tick, {"type": "door", "who": team[0], "room": site, "vis": "public", "text": f"{self.nm(team[0])} forces the lock TereVi put on the {self.world.room_name(site)}."})
        self.run_scene_live(tick, rid, site, [c for c in team if c in self.world.agents], hour, beats)
        said = [ln["m"] for g in tick.get("talk") or [] for ln in g.get("lines") or [] if "m" in ln]
        if said:
            self.clock_to(min(self.sim_turn(tick).dur - 1.0, max(said) + 0.5))    # what follows (a blast, a fire, a launch) comes after the last word
        tick["events"].append({"type": "system_notable", "who": team[0], "room": site, "vis": "gm",
                               "text": f"Finale ({rid}): base odds {int(p * 100)}%, outcome {outcome}."})
        return ok, outcome

    # ------------------------------------------------------------------ the raid on the core
    def raid_core(self, tick, team, p, aid, beats):
        w, s = self.world, self.s
        plan = s["escape"]["routes"]["shutdown"]["plan"]
        lead = self.finale_leader(team)
        B = lambda who, text, move, kind="say": self.scene_beat(beats, who, text, move, kind)
        B(lead, "lifts the hatch in the Lighthouse floor and starts down the steps.", "descend", "act")
        B(lead, "Stay close. Nobody talks unless they have to.", "lead")
        for c in team:
            if c != lead:
                B(c, self.pick_line(beats, ["This is a mistake. This is a huge mistake.", "If I die down here, I'm haunting you."]) if self.facet(c, "courage") < 45
                  else self.pick_line(beats, ["Right behind you.", "Let's end her."]), "follow")
        hidden = 0.25 + plan.get("blind", 0) / 250 + (0.2 if self.blackout_until >= self.idx else 0) + (0.2 if aid else 0)
        seen = self.rng.random() > min(0.9, hidden)
        if seen:
            B("terevi", "Oh, darlings. Did you really think I couldn't see you?", "noticed")
            counter = self.rng.choice(["seal", "gas", "turn"])
            if counter == "seal":
                B("terevi", "Let's keep you down there, shall we?", "seal")
                forcer = max(team, key=lambda c: (self.facet(c, "courage") + self.build_bonus(c), c))
                if self.rng.random() < 0.5 + (self.facet(forcer, "courage") - 50) / 150:
                    B(forcer, "throws their whole weight against the sealed hatch until it gives.", "force", "act")
                    p -= 0.05
                else:
                    B(forcer, "hammers on the sealed hatch until their hands bleed. It does not move.", "trapped", "act")
                    for c in team:
                        self.stat(tick, c, "sanity", -8, "sealed in under the Lighthouse")
                    return False, "sealed in"
            elif counter == "gas":
                B("terevi", "Breathe deep. It's good for you.", "gas")
                for c in team:
                    self.stat(tick, c, "hp", -self.rng.randint(6, 16), "gas in the vault stairs")
                    self.stat(tick, c, "sanity", -4, "gas in the vault stairs")
                weak = min(team, key=lambda c: (w.agents[c]["hp"] if c in w.agents else 999, c))
                B(weak, "doubles over coughing, eyes streaming.", "choke", "act")
                p -= 0.12
            else:
                mark = self.finale_weakest(team)
                B("terevi", f"{self.nm(mark)}, sweetheart. Walk away now and you live. The others won't. Your choice.", "offer")
                if self.turned(mark, team):
                    B(mark, "backs up the stairs without a word and runs for the alarm.", "turn", "act")
                    for c in team:
                        if c != mark:
                            w.adjust_aff(c, mark, -6)
                    self.moment(mark, "sold out the raid on TereVi's core to save themselves")
                    return False, "betrayed"
                B(mark, "I'd rather die down here than owe you anything.", "refuse")
                p += 0.05
        else:
            B(lead, "No alarms. No voice. She hasn't seen us.", "unseen")
            p += 0.15
        for c in list(team):
            if c not in w.agents:
                continue
            if self.rng.random() < 0.25 - plan.get("approach", 0) / 600:
                B(c, "steps on a pressure plate. Something fires from the ceiling.", "plate", "act")
                self.stat(tick, c, "hp", -self.rng.randint(8, 25), "a turret in the Core Vault", lethal="cut down in the Core Vault")
                if s.get("case"):
                    return False, "a death in the vault"
        B(lead, "There it is. The core.", "core")
        ok = self.rng.random() < max(0.1, min(0.92, p))
        if ok:
            B(lead, "brings everything they have down on the core.", "strike", "act")
            B("terevi", "No. No, no, no, you can't, you can't, you c-", "dies")
        else:
            B(lead, "strikes the core, and it holds. The lights come up red.", "fail", "act")
            B("terevi", "Was that it? That was your big finale?", "laugh")
        return ok, "shut down" if ok else "the core held"

    def build_bonus(self, cid):
        return {"short": -10, "medium": 0, "tall": 10}.get(self.build_of(cid)["height"], 0)

    # ------------------------------------------------------------------ the bomb standoff
    def bomb_standoff(self, tick, team, p, beats):
        w, s = self.world, self.s
        plan = s["escape"]["routes"]["ultimatum"]["plan"]
        lead = self.finale_leader(team)
        B = lambda who, text, move, kind="say": self.scene_beat(beats, who, text, move, kind)
        cred = (plan.get("leverage", 0) / 100 + sum(self.facet(c, "courage") for c in team) / (100 * len(team))) / 2
        B(lead, "holds up the trigger where every camera can see it.", "show", "act")
        B(lead, "Open the gates and let everyone go, or the generator, your vault and this whole island go up. You have one hour.", "demand")
        for c in team:
            if c != lead:
                B(c, self.pick_line(beats, ["We mean it. Every word.", "Do what they say."]) if self.facet(c, "courage") >= 45
                  else self.pick_line(beats, ["Please just do it. Please.", "...We're really doing this."]), "back")
        for rnd in range(3):
            if rnd and self.rng.random() < p * 0.35 + cred * 0.2:
                B("terevi", "...Fine. Fine! The gates are open. Take your little lives and go. The show is over.", "surrender")
                return True, "surrender"
            move = self.rng.choice(["doubt", "bargain", "turn"] if rnd < 2 else ["call"])
            if move == "doubt":
                B("terevi", "You won't press it. You haven't got it in you, darling.", "doubt")
                waver = min(team, key=lambda c: (w.agents[c]["sanity"], c))
                if w.agents[waver]["sanity"] < 40 and self.rng.random() < 0.5:
                    B(waver, "Maybe she's right. Maybe we should just stop.", "waver")
                    cred -= 0.1
                else:
                    B(lead, "Try me.", "hold")
                    cred += 0.05
            elif move == "bargain":
                B("terevi", "Hand me the trigger and one of you walks out tonight. Just one. Pick.", "bargain")
                taker = self.finale_weakest(team)
                if self.turned(taker, team):
                    B(taker, "Me. It should be me.", "split")
                    B(lead, f"{self.nm(taker)}, don't you dare.", "plead")
                    cred -= 0.15
                else:
                    B(lead, "Nobody's for sale.", "hold")
            elif move == "turn":
                mark = self.finale_weakest(team)
                B("terevi", f"{self.nm(mark)}. Take the trigger off them and I'll make sure you're the last one standing.", "offer")
                if mark != lead and self.turned(mark, team):
                    B(mark, "snatches the trigger and throws it out of reach.", "betray", "act")
                    for c in team:
                        if c != mark:
                            w.adjust_aff(c, mark, -7)
                    self.moment(mark, "betrayed the bomb threat to TereVi")
                    return False, "betrayed"
                B(mark, "Go to hell.", "refuse")
                cred += 0.05
        B("terevi", "Then press it. Go on. Ten seconds. Nine. Eight...", "call")
        if self.rng.random() < 0.35 + (self.facet(lead, "courage") - 50) / 150 + max(0, 40 - w.agents[lead]["sanity"]) / 150:
            B(lead, "presses it.", "detonate", "act")
            return False, "detonated"
        B(lead, "lowers the trigger. Their hand is shaking.", "fold", "act")
        B("terevi", "That's what I thought. Disarm it, NeoVi. Gently.", "gloat")
        return False, "backed down"
