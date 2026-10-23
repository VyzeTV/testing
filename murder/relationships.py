"""Persistent bond policy, independent of the simulation runner."""

ROMANCE_AFFECTION = 7
NEW_ROMANCE_HOURS = 24
RECONCILE_HOURS = 48
BETRAYAL_HOURS = 72


def bond_time(day, hour):
    return day * 24 + hour


def record_bond(state, bond, now, action, reason):
    upgrade(state)
    state["bond_seq"] += 1
    history = state.setdefault("bond_history", [])
    history.append({"seq": state["bond_seq"], "a": bond["a"], "b": bond["b"], "kind": bond["kind"],
                    "at": now, "action": action, "reason": reason})
    history[:] = [e for e in history if now - e["at"] <= MEMORY_HOURS][-1024:]


def bond_allowed(state, x, y, kind, now):
    if kind == "romance" and (not romance_ready(state, x, y, now) or partners(state, x) - {y} or partners(state, y) - {x}):
        return False
    if kind in ("romance", "pact") and any(wary(state, a, b, now) and trust(state, a, b) < 2 for a, b in ((x, y), (y, x))):
        return False
    for e in state.get("bond_history", []):
        age = now - e["at"]
        if e["action"] == "ended" and {e["a"], e["b"]} == {x, y} and (e["kind"] == kind or kind in ("romance", "pact") and e["kind"] in ("romance", "pact")):
            cooldown = BETRAYAL_HOURS if e["reason"] in ("betrayal", "affair") else RECONCILE_HOURS
            if age < cooldown:
                return False
        if kind == "romance" and e["kind"] == "romance" and {x, y} & {e["a"], e["b"]} and age < NEW_ROMANCE_HOURS:
            return False
    # Old saves have no history. Existing romances still prevent a rapid new one.
    if kind == "romance":
        for b in state.get("bonds", []):
            if b["kind"] == "romance" and {x, y} & {b["a"], b["b"]} and now - b.get("formed_at", b.get("since", now // 24) * 24) < NEW_ROMANCE_HOURS:
                return False
    return True

# Personal trust is distinct from affection and from the character's trust facet.
CLOSENESS_DAYS = 3
CLOSENESS_HOURS = 48
MEMORY_HOURS = 21 * 24


def upgrade(state):
    state.setdefault("relationships", {})
    state.setdefault("bond_seq", max((e.get("seq", 0) for e in state.get("bond_history", [])), default=0))


def connection(state, who, other):
    return state.get("relationships", {}).get(who, {}).get(other, {})


def _connection(state, who, other):
    upgrade(state)
    return state["relationships"].setdefault(who, {}).setdefault(other, {"trust": 0, "close": [], "hurts": []})


def trust(state, who, other):
    return connection(state, who, other).get("trust", 0)


def wary(state, who, other, now):
    return any(h["at"] <= now < h["at"] + MEMORY_HOURS for h in connection(state, who, other).get("hurts", []))


def closeness(state, a, b, now, source):
    """A checked, welcomed encounter: at most one trust gain and one meeting day per day."""
    if not a or not b or a == b:
        return
    day = int(now // 24)
    for who, other in ((a, b), (b, a)):
        c = _connection(state, who, other)
        c["close"] = [e for e in c["close"] if now - e["at"] <= 7 * 24]
        if any(e["day"] == day for e in c["close"]):
            continue
        c["close"].append({"day": day, "at": now, "source": source})
        earn_trust(state, who, other, now)


def earn_trust(state, who, other, now):
    """Reflection and encounters share a daily budget; reflection invents no meeting."""
    c = _connection(state, who, other)
    day = int(now // 24)
    if c.get("trust_day") != day:
        gain = .25 if wary(state, who, other, now) else 1
        c["trust"] = min(10, c["trust"] + gain)
        c["trust_day"] = day


def distrust(state, who, other, amount):
    if amount > 0 and who != other:
        c = _connection(state, who, other)
        c["trust"] = max(-10, c["trust"] - amount)


def betray(state, victim, offender, now, reason):
    if victim == offender:
        return
    c = _connection(state, victim, offender)
    # Repeated reporting of the same incident does not renew or stack its penalty.
    if any(h["at"] == now and h["reason"] == reason for h in c["hurts"]):
        return
    c["trust"] = max(-10, min(c["trust"] - 8, -6))
    c["close"] = []
    c["hurts"] = [h for h in c["hurts"] if now - h["at"] < MEMORY_HOURS][-7:]
    c["hurts"].append({"at": now, "reason": reason[:180]})


def romance_ready(state, a, b, now):
    for who, other in ((a, b), (b, a)):
        c = connection(state, who, other)
        meetings = [e for e in c.get("close", []) if 0 <= now - e["at"] <= 7 * 24]
        if len({e["day"] for e in meetings}) < CLOSENESS_DAYS or max(e["at"] for e in meetings) - min(e["at"] for e in meetings) < CLOSENESS_HOURS:
            return False
        if c.get("trust", 0) < 2:
            return False
    return True


def partners(state, who):
    def alive(cid):
        a = state.get("agents", {}).get(cid)
        return a is not None and a.get("status", "alive") == "alive"
    out = {b["b"] if b["a"] == who else b["a"] for b in state.get("bonds", [])
           if b["kind"] == "romance" and who in (b["a"], b["b"]) and alive(b["a"]) and alive(b["b"])}
    nv = state.get("npcs", {}).get("neovi", {})
    lover = nv.get("lover")
    if lover and alive(lover) and not nv.get("dead") and not nv.get("participant"):
        if who == "neovi":
            out.add(lover)
        elif who == lover:
            out.add("neovi")
    return out


def rename_person(state, old, new):
    """NeoVi becoming Kumiko changes her ID, not her relationships or their age."""
    records = state.get("relationships", {})
    if old in records:
        records.setdefault(new, {}).update(records.pop(old))
    for links in records.values():
        if old in links:
            links[new] = links.pop(old)
    for event in state.get("bond_history", []):
        for key in ("a", "b"):
            if event[key] == old:
                event[key] = new


def context(state, who, now, names, group=None):
    """Personal history for choices; shared cards convey attitudes without leaking the incident."""
    out = []
    for other, c in sorted(state.get("relationships", {}).get(who, {}).items()):
        if group is not None and other not in group:
            continue
        hurts = [h for h in c.get("hurts", []) if 0 <= now - h["at"] < MEMORY_HOURS]
        if not hurts and abs(c["trust"]) < 2:
            continue
        line = f"{names(other)}: trust {c['trust']:+g}/10"
        if hurts:
            line += "; guarded, warmth has not restored trust"
            if group is None:
                line += "; remembers " + hurts[-1]["reason"]
        out.append(line)
    return "RELATIONSHIP HISTORY: " + " | ".join(out) if out else ""


def signature(state, who):
    """A new betrayal or changed partner invalidates only this person's early decision."""
    return (tuple(sorted(partners(state, who))), tuple((other, c["hurts"][-1]["at"], c["hurts"][-1]["reason"])
            for other, c in sorted(state.get("relationships", {}).get(who, {}).items()) if c.get("hurts")))
