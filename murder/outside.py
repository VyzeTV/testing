"""The raft, the world outside, and the rescue countdown.

The raft is small: it carries two, or three if it was built well. Its launch is a live scene on the beach (the engine decides, the model voices):
who goes (those who built it, and the ones they love), who is left behind on the sand, and now and then someone desperate who wades out and
climbs aboard uninvited, which makes the raft riskier. The show goes on for everyone else.

The crew then lives on an off-screen track, rolled once a day at dawn, and the audience gets a short snippet each time (the island does not):
* At sea, a few days: thirst, a storm (worse in TereVi's storms and fog), someone lost overboard, then landfall or a passing boat, or lost.
* Ashore: they must be believed. Proof they carried (the route's proof step, footage, a diary) makes it likelier; without it they are
  dismissed, and they may be found by the show's own people and silenced.
* Believed: a rescue countdown of 2 to 5 days starts for the island.
The island hears only what reaches it: TereVi gloating (truthfully, or lying that they drowned), or her sudden nerves.

A believed broadcast of the truth (the transmit route) starts the same countdown. During it TereVi runs a final episode: she says so on air
and murder plots come easier. Rescue arriving ends the season: a good ending if enough people are still alive, a bittersweet one if it
came too late. If the island empties while a raft crew is still out there, the season ends with them: bittersweet, or bad if they were lost.
OutsideMixin is mixed into DayRunner (engine.py).
"""

SEA = {
    "calm": ["The raft drifts under a white sky. They ration the water by the capful.", "Nothing but sea in every direction. Someone starts singing, badly, and nobody stops them."],
    "rough": ["A squall hits in the night. They lash themselves to the planks and pray.", "Salt sores, cracked lips, a quarrel over the last of the water."],
    "lost_one": ["{who} slips over the side in the dark. By morning there is only the empty place where they sat."],
    "land": ["A line of grey on the horizon: land. They paddle with their hands until their arms give out.", "A fishing boat turns toward the raft. Someone waves a shirt until the boat is close enough to see their faces."],
    "lost": ["The raft is found weeks later by nobody. The audience is shown an empty raft turning in the swell."],
}
ASHORE = {
    "believed": ["A police officer stops writing and looks up. \"Say that again. The island. Where is it?\"", "A journalist listens to the whole story, then quietly makes a phone call."],
    "dismissed": ["\"Murder Channel? The show? Mate, it's a show.\" The officer hands them a leaflet about stress.", "Nobody believes them. A hospital bed, a sedative, a polite smile."],
    "silenced": ["Two men in a black car offer them a lift to the city. The audience never sees them again."],
}


class OutsideMixin:
    def outside(self):
        return self.s.setdefault("outside", {"crews": []})

    def raft_capacity(self):
        rt = self.s["escape"]["routes"]["raft"]
        return 3 if sum(rt.get("parts", {}).values()) >= 6 else 2

    def raft_launch(self, tick, team, p, beats):
        """The launch on the beach as a scene. Returns (ok, outcome, crew)."""
        w, s = self.world, self.s
        B = lambda who, text, move, kind="say": self.scene_beat(beats, who, text, move, kind)
        cap = self.raft_capacity()
        rt = s["escape"]["routes"]["raft"]
        work = lambda c: s.get("stats", {}).get(c, {}).get("route_steps", 0)
        crew = sorted([c for c in team if c in w.agents], key=lambda c: (-work(c), c))[:cap]
        if len(crew) < cap:                                   # a builder takes the one they love
            for c in list(crew):
                lover = max((o for o in w.agents if o not in crew), key=lambda o: (w.agents[c]["aff"].get(o, 0), o), default=None)
                if lover and w.agents[c]["aff"].get(lover, 0) >= 6 and len(crew) < cap:
                    crew.append(lover)
        lead = crew[0]
        B(lead, f"It holds {cap}. That's all it holds.", "count")
        for c in crew[1:]:
            B(c, "wades out and climbs aboard.", "board", "act")
        left = [c for c in team if c in w.agents and c not in crew]
        for c in left[:1]:
            B(c, "stands in the surf, watching the others climb aboard.", "left", "act")
            B(c, "Go. Somebody has to tell them. Go!", "farewell")
        mourner = max((o for o in w.agents if o not in crew), key=lambda o: (max([w.agents[o]["aff"].get(c, 0) for c in crew] or [0]), o), default=None)
        if mourner and max([w.agents[mourner]["aff"].get(c, 0) for c in crew] or [0]) >= 6:
            fav = max(crew, key=lambda c: w.agents[mourner]["aff"].get(c, 0))
            B(mourner, f"{self.nm(fav)}! Don't you dare drown. Don't you dare.", "goodbye")
        stow = min((o for o in w.agents if o not in crew and o not in left), key=lambda o: (w.agents[o]["sanity"], o), default=None)
        if stow and w.agents[stow]["sanity"] < 35 and self.rng.random() < 0.3:
            B(stow, "breaks from the treeline, wades out and hauls themselves aboard before anyone can stop them.", "stowaway", "act")
            B(lead, "We're too heavy! We're too-", "overload")
            crew.append(stow)
            p -= 0.15
        if any(s.get("island", {}).get("id") == x for x in ("storm", "fog")) if s.get("island") else False:
            p -= 0.1
        ok = self.rng.random() < max(0.1, min(0.9, p))
        if ok:
            B(lead, "pushes off from the sand. The raft rides the first wave, then the next, and then it is past the reef.", "launch", "act")
            B("terevi", "Oh, how brave. How very brave. I do hope you can swim.", "tease")
        else:
            B(lead, "is thrown into the surf as the raft breaks apart on the rocks.", "wreck", "act")
        return ok, "launched" if ok else "wrecked", crew

    def raft_away(self, tick, crew, proof):
        """The crew leaves the island (they are 'escaped', no longer on the show) and their journey begins."""
        w, s = self.world, self.s
        names = ", ".join(self.nm(c) for c in crew)
        for c in crew:
            w.end_agent(c, "escaped", "escaped on a raft")
            s["vacancies"].append({"gender": w.cast[c]["gender"], "reason": f"{w.cast[c]['name']} sailed away"})
        provisions = 1 + s["escape"]["routes"]["raft"]["parts"].get("provisions", 0) if s["escape"]["routes"]["raft"].get("parts") else 1
        self.outside()["crews"].append({"ids": list(crew), "alive": list(crew), "stage": "sea", "days": 0, "food": provisions,
                                        "proof": bool(proof), "tries": 0, "day": self.day, "log": []})
        for cid, a in w.agents.items():
            lost = a["memory"].setdefault("lost", [])
            for c in crew:
                lost.append({"id": c, "name": self.nm(c), "day": self.day, "how": "sailed away on a raft (nobody knows if they made it)", "close": self.close_label(a["aff"].get(c, 0))})
            del lost[:-8]
            close = max([a["aff"].get(c, 0) for c in crew] or [0])
            self.stat(tick, cid, "sanity", -6 if close >= 5 else -2, "friends sailed away" if close >= 5 else "people sailed away")
            self.moment(cid, f"watched {names} sail away")

    def outside_dawn(self, tick):
        """One day of the world outside for every crew still out there: a snippet for the audience, and maybe news for the island."""
        w, s = self.world, self.s
        for crew in self.outside()["crews"]:
            if crew["stage"] not in ("sea", "ashore"):
                continue
            crew["days"] += 1
            names = ", ".join(self.nm(c) for c in crew["alive"])
            if crew["stage"] == "sea":
                storm = (s.get("island") or {}).get("id") in ("storm", "fog")
                crew["food"] -= 1
                if crew["alive"] and self.rng.random() < (0.06 if storm else 0.03) and self.raft_returns(tick, crew):      # twists.py
                    continue
                if crew["alive"] and self.rng.random() < (0.25 if storm else 0.08) + (0.15 if crew["food"] < 0 else 0):
                    gone = self.rng.choice(crew["alive"])
                    crew["alive"].remove(gone)
                    for g in s["graveyard"]:
                        if g["id"] == gone and g["how"] == "escaped on a raft":
                            g["how"] = "lost at sea"
                    self.outside_snip(tick, crew, self.rng.choice(SEA["lost_one"]).format(who=self.nm(gone)))
                if not crew["alive"] or (crew["food"] < -1 and self.rng.random() < 0.4) or crew["days"] > 6:
                    crew["stage"] = "lost"
                    for c in crew["alive"]:
                        for g in s["graveyard"]:
                            if g["id"] == c and g["how"] == "escaped on a raft":
                                g["how"] = "lost at sea"
                    crew["alive"] = []
                    self.outside_snip(tick, crew, SEA["lost"][0])
                    self.terevi_says(tick, f"Some news from the sea, darlings. The raft came back. Empty. Hehe. Who's next?")
                elif self.rng.random() < 0.15 + 0.18 * crew["days"] - (0.1 if storm else 0):
                    crew["stage"] = "ashore"
                    self.outside_snip(tick, crew, self.rng.choice(SEA["land"]))
                else:
                    self.outside_snip(tick, crew, self.rng.choice(SEA["rough" if storm or crew["food"] < 0 else "calm"]))
                    if self.rng.random() < 0.2:
                        self.terevi_says(tick, f"Still no word from {names}. The sharks out here are so well fed. Just saying.")
            elif crew.get("kind") == "killer":
                self.escapee_dawn(tick, crew)                          # departures.py
            else:
                crew["tries"] += 1
                p = 0.2 + (0.45 if crew["proof"] else 0) + 0.08 * len(crew["alive"]) - 0.1 * (crew["tries"] - 1)
                roll = self.rng.random()
                if roll < 0.1:
                    crew["stage"] = "silenced"
                    self.outside_snip(tick, crew, ASHORE["silenced"][0])
                elif roll < 0.1 + p:
                    crew["stage"] = "believed"
                    self.outside_snip(tick, crew, self.rng.choice(ASHORE["believed"]))
                    self.start_rescue(tick, "raft", f"{names} reached the mainland and were believed")
                elif crew["tries"] >= 3:
                    crew["stage"] = "dismissed"
                    self.outside_snip(tick, crew, self.rng.choice(ASHORE["dismissed"]))
                else:
                    self.outside_snip(tick, crew, self.rng.choice(ASHORE["dismissed"]))

    def outside_snip(self, tick, crew, text):
        crew["log"].append({"day": self.day, "text": text})
        tick["events"].append({"type": "outside", "who": crew["ids"][0], "room": "beach", "vis": "viewer",
                               "text": f"Meanwhile, out there ({', '.join(self.nm(c) for c in crew['ids'])}): {text}"})

    def terevi_says(self, tick, text):
        tick["broadcasts"].append({"speaker": "terevi", "kind": "tease", "text": text})
        for c in self.world.agents:
            self.world.remember(c, f"TereVi said: {text}")

    # ------------------------------------------------------------------ rescue
    def start_rescue(self, tick, how, why):
        s = self.s
        if s.get("rescue"):
            return
        s["rescue"] = {"arrive": self.day + self.rng.randint(2, 5), "how": how, "why": why, "alive_then": len(self.world.agents), "day": self.day}
        self.terevi_says(tick, "Attention, darlings. Change of schedule: this is now the FINAL EPISODE. Make it count. "
                               "Whoever is still breathing when the credits roll... well. Let's see how many of you that is.")
        tick["events"].append({"type": "system_notable", "who": "terevi", "room": "foyer", "vis": "viewer",
                               "text": f"Help is coming ({why}). It will reach the island on Day {s['rescue']['arrive']}. TereVi does not tell the cast."})
        self.saga(f"Help is on its way: {why}.")

    def rescue_due(self, hour):
        r = self.s.get("rescue")
        return bool(r and not self.s.get("over") and self.day >= r["arrive"] and hour >= 10)

    def run_rescue(self, hour):
        w, s = self.world, self.s
        tick = self.new_tick(hour)
        tick["type"] = "rescue"
        r = s["rescue"]
        self.rescue_loss(tick)                                     # the island may keep one (endings.py)
        alive = list(w.agents)
        out = [c for crew in self.outside()["crews"] for c in crew["alive"] if crew["stage"] in ("believed", "ashore", "sea") and crew.get("kind") != "killer"]
        enough = len(alive) >= max(3, (r.get("alive_then", 6) + 1) // 2)
        text = (f"Helicopters over the island. Boats in the bay. Armed officers kick in the Foyer doors while TereVi screams static. "
                f"{len(alive)} survivors are led out into the daylight.")
        tick["broadcasts"].append({"speaker": "terevi", "kind": "finale", "text": "No. No! This is MY show. You can't just- cut the feed- CUT THE FEED-"})
        self._end_season(tick, "rescue" if enough else "rescue_late", "RESCUE" if enough else "RESCUE, TOO LATE", text, ids=alive + out)
        tick["events"].append({"type": "system_notable", "who": "terevi", "room": "foyer", "vis": "public", "text": text})
        self.day_notable.append(text)
        return tick
