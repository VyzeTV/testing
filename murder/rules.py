"""Daily rules ("the roulette"). Each rule can be checked by the engine; NeoVi punishes violators."""
from .data_world import ROOMS

PUNISHMENT_TEXT = ("Anyone who breaks it is punished by NeoVi: tased (heavy health and sanity loss) or dragged to detention in the Cold Store.")

CATALOG = [
    ("leader", "Follow the Leader"),
    ("buddy", "Buddy System"),
    ("no_alone", "Never Alone"),
    ("ground_only", "Ground Floor Only"),
    ("mealtime", "Mandatory Mealtimes"),
    ("no_weapons", "Weapons Ban"),
]


def catalog():
    return [{"id": i, "title": t} for i, t in CATALOG]


def title_of(rule_id):
    return dict(CATALOG).get(rule_id, rule_id)


def make_rule(rule_id, world, rng):
    """Create the rule for today. Returns a dict stored in world.state['rule']."""
    alive = list(world.agents.keys())
    nm = world.display_name
    params = {}
    if rule_id == "leader":
        leader = rng.choice(alive)
        params["leader"] = leader
        text = (f"{nm(leader)} has been drawn as today's LEADER. The leader decides where to go first and everyone else must be "
                f"in the same room as the leader at the end of every turn. The leader may give orders; obeying is the safe choice.")
        short = f"Leader: {nm(leader)}"
    elif rule_id == "buddy":
        order = alive[:]
        rng.shuffle(order)
        groups = [order[i:i + 2] for i in range(0, len(order), 2)]
        if len(groups) > 1 and len(groups[-1]) == 1:
            groups[-2].extend(groups.pop())
        params["groups"] = groups
        text = ("BUDDY SYSTEM: you have been paired up. At the end of every turn each person must share a room with at least one of their buddies. "
                "Pairs: " + "; ".join(" + ".join(nm(x) for x in g) for g in groups) + ".")
        short = "Pairs: " + ", ".join("/".join(nm(x) for x in g) for g in groups)
    elif rule_id == "no_alone":
        text = "NEVER ALONE: at the end of every turn each person must share a room with at least one other participant (until bedtime)."
        short = "Nobody may be alone"
    elif rule_id == "ground_only":
        text = "GROUND FLOOR ONLY: until 20:00 everyone must stay on the ground floor or outside. No basement, no upstairs, no roof."
        short = "Ground floor / outside only until 20:00"
    elif rule_id == "mealtime":
        text = "MANDATORY MEALTIMES: everyone must be in the Dining Hall at the 12:00 turn and again at the 18:00 turn."
        short = "Dining Hall at 12:00 and 18:00"
    elif rule_id == "no_weapons":
        text = ("WEAPONS BAN: carrying any weapon (knives, tools meant to hurt, bats, poles and so on; musical instruments excepted) at the end "
                "of a turn is a violation and the item is confiscated.")
        short = "No weapons"
    else:
        raise ValueError(f"unknown rule {rule_id}")
    return {"id": rule_id, "title": title_of(rule_id), "text": text + " " + PUNISHMENT_TEXT, "short": short,
            "params": params, "strikes": {}}


def roulette(rng, last=None):
    ids = [i for i, _ in CATALOG if i != last]
    return rng.choice(ids)


def check(rule, world, hour):
    """Return {agent id: {"reason": str, "confiscate": [item ids]}} for current violations."""
    out = {}
    if not rule:
        return out
    agents = world.agents
    rid, params = rule["id"], rule["params"]
    if rid == "leader":
        leader = params["leader"]
        if leader not in agents:
            return out
        room = agents[leader]["room"]
        for cid, a in agents.items():
            if cid != leader and a["room"] != room:
                out[cid] = {"reason": f"not with the leader ({world.display_name(leader)})", "confiscate": []}
    elif rid == "buddy":
        for g in params["groups"]:
            living = [x for x in g if x in agents]
            if len(living) < 2:
                continue
            for cid in living:
                if not any(agents[o]["room"] == agents[cid]["room"] for o in living if o != cid):
                    out[cid] = {"reason": "left their buddy", "confiscate": []}
    elif rid == "no_alone":
        if hour < 21:
            for cid, a in agents.items():
                if not any(o != cid and b["room"] == a["room"] for o, b in agents.items()):
                    out[cid] = {"reason": "alone", "confiscate": []}
    elif rid == "ground_only":
        if hour < 20:
            for cid, a in agents.items():
                if ROOMS[a["room"]][1] not in ("ground", "grounds"):
                    out[cid] = {"reason": f"in the {ROOMS[a['room']][0]}", "confiscate": []}
    elif rid == "mealtime":
        if hour in (12, 18):
            for cid, a in agents.items():
                if a["room"] != "dining_hall":
                    out[cid] = {"reason": "missed the meal", "confiscate": []}
    elif rid == "no_weapons":
        for cid, a in agents.items():
            bad = [k for k in a["inv"] if "weapon" in world.item_spec(k).get("tags", []) and "instrument" not in world.item_spec(k).get("tags", [])]
            if bad:
                out[cid] = {"reason": "carrying " + ", ".join(world.item_name(k) for k in bad), "confiscate": bad}
    return out


PLACE_WORDS = {"indoors": "in", "inside": "in", "outdoors": "out", "outside": "out"}


def consistent_title(title, short, text):
    """A generated rule once called itself 'Whisper Only Indoors' while its text said to whisper outdoors. The text is the rule; if the title names the opposite place, the short line becomes the title."""
    import re as _re

    def places(t):
        return {PLACE_WORDS[w] for w in _re.findall(r"indoors|inside|outdoors|outside", (t or "").lower())}
    tp, sp = places(title), places(short)
    if tp and sp and tp != sp:
        return (short.rstrip(". ")[:60]) or title
    return title
