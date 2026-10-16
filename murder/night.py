"""The night turn.

After the last turn of the day everyone normally goes to bed. A character may choose to stay up for one extra turn (the decision field "night": true) at the cost
of some health and their sleep; the plotting and the restless are nudged to do so by the engine. Everyone else sleeps in their own room: they are not
counted as present, see and hear nothing, and a sleeper can be attacked defencelessly. The owls get a normal turn in the dark (sneak, search, meet, strike).
NightMixin is mixed into DayRunner (engine.py).
"""
from concurrent.futures import ThreadPoolExecutor

from .data_world import ROOMS

NIGHT_HOUR = 23
NIGHT_COST = 8                       # defaults; the tuning panel overrides them
MAX_OWLS = 4


def _hh(h):
    return f"{int(h):02d}:00"


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
            return [f"THE NIGHT: you stayed up. The house is dark and everyone else is asleep in their own room (you pay for it in health tomorrow). "
                    + (f"Asleep in this room: {', '.join(asleep)}. " if asleep else "")
                    + "This is the time to move quietly, search, meet someone in secret, or do what you could not do in daylight. Sleepers see and hear nothing."]
        if hour >= 18 and self.night_allowed() and a["hp"] >= 45:
            return [f"NIGHT TURN: after the last turn you may stay up for one more turn in the dark (\"night\": true) instead of going to bed. It costs about {int(self.tune('night_cost'))} health and your sleep, "
                    "and everyone else will be asleep in their rooms. Worth it if you are planning something, want to search or meet someone unseen, or cannot rest. Normally leave it false."]
        return []

    def night_cast(self):
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
            if case and case.get("announced") and a["drive"]["id"] in ("seeker", "schemer") and a["sanity"] > 40 and self.rng.random() < 0.15:
                owls.append(cid)
            elif a["sanity"] < 30 and self.rng.random() < 0.15:
                owls.append(cid)
        owls = [c for c in owls if w.agents[c]["hp"] >= 45 and w.agents[c]["room"] not in ("cold_store", "voting_grounds")]
        self.rng.shuffle(owls)
        return owls[:int(self.tune("night_owls_max"))]

    def run_night_turn(self):
        w, s = self.world, self.s
        votes = set(self.night_votes)
        owls = self.night_cast()
        self.night_votes = set()
        if not owls:
            return None
        hour = NIGHT_HOUR
        s["_hour"] = hour
        for c_ in owls:
            self.note_use(c_, "night", "model" if c_ in votes else "engine")
        self.light_tick()
        tick = self.new_tick(hour, phase="night")
        self.clear_hiding()
        for cid, a in w.agents.items():
            a["sneaking"], a["spying"] = False, None
            if cid in owls:
                a["night_owl"] = True
                self.stat(tick, cid, "hp", -int(self.tune("night_cost")), "staying up through the night")
                self.stat(tick, cid, "sanity", -1, "a sleepless night")
                continue
            self.send_to_bed(tick, cid)
            a["activity"] = "Asleep"
            a["asleep"] = True
        self.auto_night_locks(tick, only_asleep=True)
        self.log_event(tick, {"type": "system", "who": "terevi", "room": "foyer", "vis": "viewer",
                              "text": "The house goes quiet. " + ", ".join(self.nm(c) for c in owls) + (" stays" if len(owls) == 1 else " stay") + " up."})
        # parallel decisions from one snapshot, as in the day
        decisions, intents, attacks = {}, {}, []
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futs = {cid: pool.submit(self.decide, cid, hour) for cid in owls}
            for cid, fut in futs.items():
                if self.should_stop():
                    raise self.StopExc()
                d, err = fut.result()
                decisions[cid] = d
                if err:
                    tick["errors"].append(err)
        self.mark_busy(decisions)
        self.plot_tick(tick, hour, decisions)
        for cid in self.apply_order(list(owls)):
            self.apply_decision(tick, cid, decisions[cid], intents, attacks)
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
        self.hazard_check(tick, hour)
        self.check_discovery(tick, hour)
        groups = {}
        for room in ROOMS:
            hs = [o for o in w.occupants(room, include_npcs=False) if o in w.agents]
            if len(hs) >= 2 and self.rng.random() < 0.85:
                groups[room] = hs
        if groups:
            self.run_conversations(tick, groups, intents, hour)
        self.reaction_pass(tick, hour)
        return tick

    def wake_all(self):
        for a in self.world.agents.values():
            a.pop("asleep", None)
