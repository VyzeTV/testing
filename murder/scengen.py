"""Procedural scenarios: a season is composed from weighted parts (a premise, a twist, house rules, scheduled island events, gear lying about, a shorter deadline) under a difficulty budget,
the way Dwarf Fortress composes its generated creatures and secrets. The result is an ordinary scenario dict (see scenario.py) so everything downstream (the referee, TereVi's secret
twist, the bible text) works unchanged; scheduled events are real: they black the house out, start a fire, burst a pipe or bring a storm on their day.

`generate(seed, difficulty)` is pure and deterministic. Nothing here seeds relationships or edits the cast (hooks and ties must grow out of events); optional secrets are off by default.
ScenarioEventsMixin runs the scheduled events inside the engine (mixed into DayRunner in engine.py).
"""
import random

EVENT_KINDS = {"blackout": "The power", "fire": "A fire", "flood": "A burst pipe", "storm": "A storm"}

PREMISES = [
    ("Salt and Static", "The island's old relay tower is still half alive, and TereVi keeps its crackle in the walls: every room may be listening."),
    ("The Long Tide", "A spring tide has cut the beach path; whatever the producers planned for the grounds, nobody will be walking there for days."),
    ("House Rules", "TereVi grew bored of her own rules and has handed the cast a rulebook written by the audience. It will not stay polite."),
    ("The Quiet Wing", "Half the house has been sealed off 'for repairs'. TereVi will not say what is behind the dust sheets."),
    ("Dead Reckoning", "Someone has been counting days on the cellar wall. The numbers do not match the calendar."),
    ("Cold Open", "The season began a week before the cast arrived: the house already has a history, and the cameras have been recording it."),
    ("The Understudy", "The producers hold a second cast in reserve. TereVi mentions it often, and never says where they are kept."),
    ("Low Season", "Supplies were cut at the last minute. Everything the island provides is a little less than it should be."),
    ("Echo Chamber", "The audience's voice reaches TereVi live this season, and she acts on the loudest of it."),
    ("Paper Moon", "A storm season: the sky does what it likes, and the house shudders when it does."),
]
TWISTS = [
    ("One of the house cameras was never recording; TereVi has been reading lips instead and she will say which room when it suits her.", 1),
    ("The radio in the Study is real. Its firewall will fail for a single hour, and only TereVi knows when.", 3),
    ("TereVi has been paying one participant's family for their silence, and she will play a recording of the call to the whole house.", 2),
    ("The boats in the Boathouse are not all locked: one chain was cut before the cast arrived, and TereVi knows who cut it.", 3),
    ("The weekly deadline is a bluff for the first week: nobody dies at the Reckoning, and TereVi will laugh when she tells them.", 4),
    ("NeoVi has been told to stop mending doors. Whatever is broken stays broken.", 1),
    ("One participant's name is not on the production's contract at all, and TereVi will read the contract aloud.", 2),
    ("The audience may spare one person at the next trial if enough of them call in; TereVi will announce the number to beat.", 2),
    ("The 'prize' is real and there is exactly one: whoever leaves the island alive takes all of it, and TereVi will announce the sum.", 2),
    ("TereVi has hidden a key to the Core Vault somewhere in the house and will give one clue a day to whoever asks nicely.", 3),
]
RULES = [
    ("Nobody may sit in the same chair twice in one day.", 1), ("Whispering is banned: anything said below a normal voice counts as plotting.", 1),
    ("Everyone must greet NeoVi by name whenever they pass her.", 1), ("No one may eat alone.", 1), ("Doors must be left open when you are not inside the room.", 2),
    ("Nobody may carry more than three items at a time.", 2), ("Speak only to people you have not spoken to yet today until you have spoken to everyone.", 2),
    ("The Library is silent: nothing may be said inside it.", 1), ("Nobody may enter a bedroom that is not their own after dark.", 2),
    ("Each person must name one thing they miss every evening in the Dining Hall.", 1), ("No one may use a name for anyone else other than their full name.", 1),
    ("Nobody may touch the Study door.", 1),
]
EVENTS = [("blackout", None, "The generator coughs and dies: the lights and cameras go out across the house.", 2),
          ("fire", "kitchen", "Grease catches on the kitchen stove: flames lick up the wall.", 2),
          ("fire", "library", "A candle falls in the Library and the carpet catches.", 3),
          ("flood", "boiler_room", "A pipe bursts in the Boiler Room and water floods the floor.", 1),
          ("flood", "bathroom", "A pipe bursts in the Bathroom: water spreads into the corridor.", 1),
          ("storm", None, "A storm rolls in off the sea and hammers the island.", 2)]
GEAR = [("generator_shed", "Spare fuse box"), ("foyer", "Box of candles"), ("kitchen", "Tin of lamp oil"), ("study", "Brass door key"), ("boathouse", "Coil of rope"),
        ("library", "Reading lamp"), ("laundry", "Bundle of sheets"), ("cold_store", "Heavy padlock"), ("garden", "Garden shears"), ("lighthouse", "Signal flare")]
SECRETS = ["has been secretly promised a way off the island in return for reporting on the others.", "knows exactly where TereVi keeps the Core Vault key.",
           "was told on the boat that nobody would really get hurt.", "has already searched every room in the house once, at night.", "carries a message for someone else and has not decided whether to deliver it."]


def generate(seed, difficulty=5, start_day=3, allow_secrets=False, cast_ids=None):
    """Compose a scenario. Returns {"scenario": {...}, "meta": {...}}. Difficulty 1-10 sets the budget the parts are paid from."""
    rng = random.Random(f"scenario:{seed}")
    difficulty = max(1, min(10, int(difficulty)))
    budget = 3 + 1.5 * difficulty
    spent, parts = 0.0, []
    title, premise = rng.choice(PREMISES)
    sc = {"title": title, "premise": premise, "twist": None, "rules": [], "relationships": [], "secrets": [], "items": [], "deadline_days": None, "events": []}
    # the one twist, paid for first
    twist, cost = rng.choice([t for t in TWISTS if t[1] <= budget] or TWISTS[:1])
    sc["twist"] = {"text": twist, "day": start_day + rng.randint(1, 4)}
    spent += cost
    parts.append(("twist", cost, twist[:60]))
    pool = [("rule", r) for r in RULES] + [("event", e) for e in EVENTS] + [("deadline", None)]
    if allow_secrets and cast_ids:
        pool += [("secret", s) for s in SECRETS]
    rng.shuffle(pool)
    for kind, part in pool:
        if kind == "rule":
            if len(sc["rules"]) >= 3 or spent + part[1] > budget:
                continue
            sc["rules"].append(part[0])
            spent += part[1]
            parts.append(("rule", part[1], part[0][:60]))
        elif kind == "event":
            kd, room, text, cost = part
            if len(sc["events"]) >= 3 or spent + cost > budget:
                continue
            sc["events"].append({"day": start_day + rng.randint(1, 5), "hour": rng.choice([10, 12, 14, 16, 18, 20]), "kind": kd, "room": room or "", "text": text})
            spent += cost
            parts.append(("event", cost, f"{kd} on day {sc['events'][-1]['day']}"))
        elif kind == "deadline":
            days = rng.choice([4, 5, 6])
            cost = 7 - days + 1
            if sc["deadline_days"] or spent + cost > budget:
                continue
            sc["deadline_days"] = start_day + days - 1
            spent += cost
            parts.append(("deadline", cost, f"first deadline on day {sc['deadline_days']}"))
        elif kind == "secret":
            if len(sc["secrets"]) >= 2 or spent + 2 > budget:
                continue
            who = rng.choice(sorted(cast_ids))
            if any(s["id"] == who for s in sc["secrets"]):
                continue
            sc["secrets"].append({"id": who, "text": part})
            spent += 2
            parts.append(("secret", 2, f"{who} {part[:40]}"))
    for room, name in rng.sample(GEAR, min(3, 1 + difficulty // 4)):
        sc["items"].append({"room": room, "name": name})
    sc["events"].sort(key=lambda e: (e["day"], e["hour"]))
    return {"scenario": sc, "meta": {"seed": seed, "difficulty": difficulty, "budget": round(budget, 1), "spent": round(spent, 1), "parts": parts}}


class ScenarioEventsMixin:
    def scenario_events(self, tick, hour):
        """Fire the scenario's scheduled island events on their day and hour (once each)."""
        sc = self.s.get("scenario")
        if not sc or not sc.get("events"):
            return
        done = sc.setdefault("_fired", [])
        for i, ev in enumerate(sc["events"]):
            key = f"{i}:{ev['day']}:{ev['hour']}"
            if key in done or ev["day"] != self.day or hour < ev["hour"]:
                continue
            done.append(key)
            kind, room, text = ev["kind"], ev.get("room") or "", ev.get("text") or ""
            self.log_event(tick, {"type": "island", "who": "terevi", "room": room or "foyer", "vis": "public", "text": text or f"{EVENT_KINDS.get(kind, 'Something')} strikes the island."},
                           witnesses=list(self.world.agents))
            for cid in self.world.agents:
                self.world.remember(cid, f"{hour:02d}:00 {text}")
            if kind == "blackout":
                self.blackout_until = self.idx + 3
                self.fx(tick, "dark")
            elif kind == "fire":
                self.env_ignite_room(tick, room or "kitchen", None, 2)
            elif kind == "flood":
                self.env_burst_pipe(tick, room or "boiler_room")
            elif kind == "storm":
                self.force_island = "storm"
