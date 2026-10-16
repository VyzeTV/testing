"""The night.

At 22:00 the lights go out and people go to bed: sleep is a task in a bed, not a skipped stretch of time. The night is played in four two-hour blocks (23:00, 01:00,
03:00, 05:00; the hours run on past midnight as 25, 27, 29 so time only goes forward) and the day ends at 07:00 (DAWN_HOUR) with the diaries.

Anyone can be awake: the ones who chose to stay up ("night": true in their decision), plotters, the seekers on a case, the badly shaken, the stressed and the hungry.
Sleepers wake for a reason: a noise or a fight nearby, fire or smoke, a bad dream, a full bladder, hunger or thirst, or a plan that will not wait. Whoever is awake
lives the block with the free-time machinery (quiet things only, and sooner or later back to bed); the ones who asked to stay up get their own decision in the first
block. A block where everyone sleeps is a quiet block (tick["quiet"]) the viewer can skip. Whoever slept less than SHORT_NIGHT hours wakes up exhausted.
Sleepers are not counted as present, see and hear nothing, and a sleeper can be attacked defencelessly. NightMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS

NIGHT_HOUR = 23
NIGHT_BLOCKS = (23, 25, 27, 29)       # 23:00, 01:00, 03:00, 05:00
DAWN_HOUR = 31                        # 07:00
SHORT_NIGHT = 5                       # hours of sleep below which someone is exhausted the next day
NOISY = ("attack", "assault", "fire", "fight", "outburst", "fall", "punish", "madness", "body", "break", "flood")


def _hh(h):
    return f"{int(h) % 24:02d}:00"


class NightMixin:
    def night_init(self):
        self.night_votes = set()

    def night_allowed(self):
        s = self.s
        return bool(self.revealed and not s.get("over") and self.world.agents and s["deadline_day"] != self.day and not self.endgame_due())

    def night_lines(self, cid, hour):
        w = self.world
        a = w.agents[cid]
        if not self.revealed:
            return []
        if hour >= NIGHT_HOUR:
            asleep = [self.nm(o) for o in w.occupants(a["room"], include_npcs=False, include_hidden=True) if o != cid and w.agents.get(o, {}).get("asleep")]
            return [f"THE NIGHT ({_hh(hour)}): you are up while the house sleeps (a short night will leave you exhausted tomorrow). "
                    + (f"Asleep in this room: {', '.join(asleep)}. " if asleep else "")
                    + "This is the time to move quietly, search, meet someone in secret, or do what you could not do in daylight. Sleepers see and hear nothing."]
        if hour >= 18 and self.night_allowed() and a["hp"] >= 45:
            return ["THE NIGHT: after lights-out you may stay up (\"night\": true) instead of going to bed. A short night leaves you exhausted tomorrow, "
                    "and everyone else will be asleep in their rooms. Worth it if you are planning something, want to search or meet someone unseen, or cannot rest. Normally leave it false."]
        return []

    def night_cast(self):
        """Who is still up when the lights go out (no cap: anyone can be)."""
        w, s = self.world, self.s
        owls = [c for c in self.night_votes if c in w.agents]
        for cid, p in s.get("plots", {}).items():
            if cid in w.agents and cid not in owls:
                if (p.get("stage") in ("stalking", "striking") and self.rng.random() < 0.65) or (p.get("stage") == "preparing" and self.rng.random() < 0.25):
                    owls.append(cid)
        case = s.get("case")
        for cid, a in w.agents.items():
            if cid in owls:
                continue
            stress = self.mind(cid)["stress"] if self.mind_on() else 0
            if case and case.get("announced") and a["drive"]["id"] in ("seeker", "schemer") and a["sanity"] > 40 and self.rng.random() < 0.15:
                owls.append(cid)
            elif a["sanity"] < 30 and self.rng.random() < 0.15:
                owls.append(cid)                                         # insomnia
            elif stress >= 70 and self.rng.random() < 0.2:
                owls.append(cid)
            elif (a.get("hunger", 0) >= 75 or a.get("thirst", 0) >= 70) and self.rng.random() < 0.5:
                owls.append(cid)                                         # a trip to the kitchen first
        return [c for c in owls if not w.agents[c].get("out") and w.agents[c]["room"] not in ("cold_store", "voting_grounds")]

    def bed_down(self, tick, owls):
        """Everyone goes to their bed and falls asleep, except the owls."""
        w = self.world
        self._night_model = {c for c in self.night_votes if c in owls}
        self.night_votes = set()
        for cid, a in w.agents.items():
            a["sneaking"], a["spying"] = False, None
            a["sleep_m"] = 0
            a.pop("slept_at", None)
            if cid in owls:
                a["night_owl"] = True
                a["activity"] = "Up late"
                self.note_use(cid, "night", "model" if cid in self._night_model else "engine")
                continue
            self.send_to_bed(tick, cid)
            self.fall_asleep(cid, 0)

    def fall_asleep(self, cid, m):
        a = self.world.agents[cid]
        a["asleep"], a["activity"], a["slept_at"] = True, "Asleep", m

    def rouse(self, tick, cid, why=None, m=0.0):
        a = self.world.agents[cid]
        if not a.pop("asleep", None):
            return False
        a.pop("slept_at", None)
        a["activity"] = "Awake"
        if why:
            a["woke"] = why
            self.log_event(tick, {"type": "wake", "who": cid, "room": a["room"], "vis": "viewer", "m": float(m), "text": f"{self.nm(cid)} wakes up ({why})."})
        return True

    def wake_reason(self, cid, hour):
        """Why a sleeper wakes at the start of a block, or None."""
        w, s = self.world, self.s
        a = w.agents[cid]
        if a.get("out") or self.restrained(cid):
            return None
        room = a["room"]
        near = {room} | {e["b"] if e["a"] == room else e["a"] for e in w.edges if room in (e["a"], e["b"])}
        if room in (s.get("_night_noise") or {}):
            return "a noise"
        if any(r in near for r in (s.get("_night_noise") or {}) if (s["_night_noise"][r] or 0) >= 2):
            return "a commotion nearby"
        if self.env_on() and (room in self.fire_rooms() or room in self.smoky_rooms()):
            return "smoke"
        if self.body(cid)["bladder"] >= 85:
            return "needs the bathroom"
        if a.get("hunger", 0) >= 85:
            return "hungry"
        if a.get("thirst", 0) >= 80:
            return "thirsty"
        stress = self.mind(cid)["stress"] if self.mind_on() else 0
        if stress >= 60 and self.rng.random() < 0.08 + (stress - 60) / 300:
            return "a bad dream"
        if a["sanity"] < 25 and self.rng.random() < 0.12:
            return "cannot sleep"
        p = s.get("plots", {}).get(cid)
        if p and p.get("stage") in ("stalking", "striking") and self.murders and self.rng.random() < 0.35:
            return "a plan that will not wait"
        return None

    def run_night_block(self, hour):
        """One two-hour block of the night: sleepers may wake, whoever is awake lives it (quietly), and sleep is counted."""
        w, s = self.world, self.s
        first = hour == NIGHT_BLOCKS[0]
        tick = self.new_tick(hour, phase="night")
        s["_hour"] = hour
        self.clock_start()
        self.sim_turn(tick)
        self.convo_reset()
        self.apply_gm(tick, hour)
        self.light_tick()
        for cid in sorted(w.agents):
            if w.agents[cid].get("asleep"):
                why = self.wake_reason(cid, hour)
                if why:
                    self.rouse(tick, cid, why)
        s["_night_noise"] = {}
        awake = [c for c in sorted(w.agents) if not w.agents[c].get("asleep") and not w.agents[c].get("out")]
        decisions, intents, attacks = {}, {}, []
        if not awake:
            tick["quiet"] = True
        else:
            model = [c for c in awake if first and c in (self.__dict__.get("_night_model") or ())]
            for cid, (d, err) in (self.decide_many(model, hour).items() if model else []):
                decisions[cid] = d
                if err:
                    tick["errors"].append(err)
            self.mark_busy(decisions)
            self.plot_tick(tick, hour, decisions)
            for cid in self.apply_order(model):
                self.apply_decision(tick, cid, decisions[cid], intents, attacks)
            self.sim_sync(tick, self._m)
            self.update_plots(tick, decisions, hour)
            self.observe_movement(tick, hour)
            self.resolve_traps(tick, hour)
            self.stealth_passive(tick, hour)
            self.auto_stealth(tick, hour, decisions)
            self.auto_secrets(tick, hour, decisions)
            if attacks:
                self.resolve_attacks(tick, attacks, hour)
            assaults, sabs, self.assaults, self.sabotages = self.assaults, self.sabotages, [], []
            self.resolve_assaults(tick, assaults, hour)
            self.resolve_sabotages(tick, sabs, hour)
            self.resolve_end_lives(tick, hour)
            self.free_time(tick, hour, decisions)
            self.clock_to(100)
            self.hazard_check(tick, hour)
            self.check_discovery(tick, hour)
            self.sim_sync(tick, self._m)
            self.voice_convos(tick, hour)
            self.sim_talk(tick)
            self.reaction_pass(tick, hour)
        # what woke the house up for the next block
        noise = {}
        for e in tick["events"]:
            if e.get("type") in NOISY and e.get("room") in ROOMS:
                noise[e["room"]] = noise.get(e["room"], 0) + 1
        s["_night_noise"] = noise
        # sleep counted: a whole block, or since they went (back) to bed
        for cid, a in w.agents.items():
            if a.get("asleep") or a.get("out"):                 # out cold is not a good night, but it is not a sleepless one either
                a["sleep_m"] = a.get("sleep_m", 0) + max(0, 120 - a.get("slept_at", 0))
                a["slept_at"] = 0
        tick["awake"] = awake
        return tick

    def run_night_turn(self):
        """Bedtime and the first block of the night (kept for callers of the old single night turn). Returns the block, or None if nobody is up."""
        bt = self.run_bedtime()
        if self._night_over:
            return None
        nt = self.run_night_block(NIGHT_BLOCKS[0])
        nt["bedtime"] = bt
        return nt if nt.get("awake") else None

    def night_rest(self, tick, cid):
        """Morning: a full night mends the body a little; a short one leaves them exhausted and tired all day."""
        a = self.world.agents[cid]
        hrs = a.pop("sleep_m", 0) / 60
        a.pop("night_owl", None)
        a["slept"] = round(hrs, 1)
        if hrs >= SHORT_NIGHT:
            from .world import clamp
            a["hp"] = clamp(a["hp"] + 3)
            return hrs
        if self.mind_on():
            n = self.mind(cid)["needs"]
            n["rest"] = min(n["rest"], 20 + 10 * hrs)
        self.add_cond(tick, cid, "exhausted", 2 if hrs < 2 else 1, "a short night" if hrs >= 2 else "no sleep")
        return hrs

    def wake_all(self):
        for a in self.world.agents.values():
            a.pop("asleep", None)
