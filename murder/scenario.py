"""Custom scenarios and house rules: a premise, a secret twist, standing rules, and seeded relationships, secrets and items."""
import copy

KINDS = {"exes": -2, "rivals": -6, "enemies": -8, "friends": 5, "old friends": 5, "siblings": 6, "lovers": 7, "mentor and student": 3, "strangers": 0, "custom": 0}

TEMPLATES = [
    {"id": "blank", "name": "Blank (no scenario)", "scenario": {}},
    {"id": "old_wounds", "name": "Old Wounds",
     "scenario": {"title": "Old Wounds",
                  "premise": "The producers did not pick this cast at random: several of them have history, and TereVi enjoys reopening old wounds.",
                  "twist": {"text": "Everyone's oldest grudge was submitted to the producers in writing, and TereVi will read one aloud every few days.", "day": 4},
                  "rules": ["Nobody may leave a room while someone is mid-sentence about them."],
                  "relationships": [{"a": "seul", "b": "vixen", "kind": "exes", "text": "They split badly, and neither has said why."},
                                    {"a": "szymon", "b": "shintaro", "kind": "rivals", "text": "Their public feud made both of them famous."},
                                    {"a": "noah", "b": "chloe", "kind": "old friends", "text": "They grew up two streets apart."}]}},
    {"id": "informant", "name": "The Informant",
     "scenario": {"title": "The Informant",
                  "premise": "TereVi has quietly promised one participant a way off the island in exchange for reporting on the others.",
                  "twist": {"text": "There is an informant among you. TereVi has been reading your private conversations through them, and she will not say who.", "day": 3},
                  "rules": ["No whispering: anything said out of earshot of the cameras counts as plotting."],
                  "secrets": [{"id": "ayden", "text": "TereVi's offer reached him on the first night, and he has not said no."}]}},
    {"id": "blackout", "name": "Blackout Week",
     "scenario": {"title": "Blackout Week",
                  "premise": "The island's power is failing all week. Cameras and lights drop out unpredictably, and the dark has its own rules.",
                  "twist": {"text": "The generator will die completely on the night of the fifth day, and with it every camera on the island.", "day": 3},
                  "deadline_days": 5, "rules": ["Nobody may carry a light into a bedroom that is not their own."],
                  "items": [{"room": "generator_shed", "name": "Spare fuse box"}, {"room": "foyer", "name": "Box of candles"}]}},
]


def _s(v, n):
    return str(v or "").strip()[:n]


def clean(raw, cast_ids, room_ids):
    """Validate a scenario coming from the UI."""
    raw = raw if isinstance(raw, dict) else {}
    out = {"title": _s(raw.get("title"), 60), "premise": _s(raw.get("premise"), 800), "twist": None, "rules": [], "relationships": [],
           "secrets": [], "items": [], "deadline_days": None, "events": []}
    tw = raw.get("twist") or {}
    if isinstance(tw, dict) and _s(tw.get("text"), 500):
        try:
            day = max(2, min(60, int(tw.get("day") or 4)))
        except Exception:
            day = 4
        out["twist"] = {"text": _s(tw.get("text"), 500), "day": day, "done": bool(tw.get("done"))}
    out["rules"] = [_s(x, 200) for x in (raw.get("rules") or []) if _s(x, 200)][:6]
    for r in (raw.get("relationships") or [])[:12]:
        if isinstance(r, dict) and r.get("a") in cast_ids and r.get("b") in cast_ids and r.get("a") != r.get("b"):
            kind = r.get("kind") if r.get("kind") in KINDS else "custom"
            try:
                val = int(r["value"]) if r.get("value") not in (None, "") else KINDS[kind]
            except Exception:
                val = KINDS[kind]
            out["relationships"].append({"a": r["a"], "b": r["b"], "kind": kind, "value": max(-10, min(10, val)), "text": _s(r.get("text"), 140)})
    for r in (raw.get("secrets") or [])[:8]:
        if isinstance(r, dict) and r.get("id") in cast_ids and _s(r.get("text"), 200):
            out["secrets"].append({"id": r["id"], "text": _s(r.get("text"), 200)})
    for r in (raw.get("items") or [])[:8]:
        if isinstance(r, dict) and r.get("room") in room_ids and _s(r.get("name"), 40):
            out["items"].append({"room": r["room"], "name": _s(r.get("name"), 40)})
    try:
        d = int(raw.get("deadline_days")) if raw.get("deadline_days") not in (None, "") else None
        out["deadline_days"] = max(3, min(21, d)) if d else None
    except Exception:
        out["deadline_days"] = None
    for ev in (raw.get("events") or [])[:6]:
        if isinstance(ev, dict) and ev.get("kind") in ("blackout", "fire", "flood", "storm"):
            try:
                day, hour = max(2, min(60, int(ev.get("day")))), max(8, min(22, int(ev.get("hour", 12))))
            except Exception:
                continue
            room = ev.get("room") if ev.get("room") in room_ids else ""
            out["events"].append({"day": day, "hour": hour, "kind": ev["kind"], "room": room, "text": _s(ev.get("text"), 200)})
    out["_placed"] = list(raw.get("_placed") or [])
    out["_fired"] = list(raw.get("_fired") or [])
    if isinstance(raw.get("_meta"), dict):
        out["_meta"] = raw["_meta"]
    return out


def is_empty(sc):
    return not sc or not any([sc.get("title"), sc.get("premise"), sc.get("twist"), sc.get("rules"), sc.get("relationships"),
                              sc.get("secrets"), sc.get("items"), sc.get("deadline_days"), sc.get("events")])


def apply_seeds(state):
    """Write the scenario's relationships, secrets, items and first deadline into the saved state (safe to repeat)."""
    sc = state.get("scenario")
    if is_empty(sc):
        return
    cast, agents = state["cast"], state["agents"]
    for r in sc["relationships"]:
        a, b = r["a"], r["b"]
        if a in agents and b in agents:
            agents[a]["aff"][b] = r["value"]
            agents[b]["aff"][a] = r["value"]
            note = f"{r['kind']} with {{}}" + (f": {r['text']}" if r["text"] else "")
            for x, y in ((a, b), (b, a)):
                m = agents[x]["memory"].setdefault("moments", [])
                line = "Backstory: " + note.format(cast[y]["short"])
                if line not in m:
                    m.insert(0, line)
    extras = {}
    for r in sc["secrets"]:
        extras.setdefault(r["id"], []).append(r["text"])
    for cid, texts in extras.items():
        if cid in cast:
            base = cast[cid].setdefault("secret_base", cast[cid]["secret"])
            cast[cid]["secret"] = (base + " Also: " + " ".join(texts)).strip()
    for cid in cast:
        if cid in cast and "secret_base" in cast[cid] and cid not in extras:
            cast[cid]["secret"] = cast[cid]["secret_base"]
    placed = sc.setdefault("_placed", [])
    for it in sc["items"]:
        key = f"{it['room']}|{it['name']}"
        if key in placed:
            continue
        iid = f"sc_{len(state['custom_items']) + 1}"
        state["custom_items"][iid] = {"name": it["name"], "tags": ["gear"]}
        state["room_items"].setdefault(it["room"], {})[iid] = 1
        placed.append(key)
    if sc.get("deadline_days") and not state.get("case") and state["day"] <= sc["deadline_days"]:
        state["deadline_day"] = max(state["day"], sc["deadline_days"])


def bible_extra(sc, revealed):
    """What goes into every prompt once the show is revealed."""
    if is_empty(sc) or not revealed:
        return ""
    bits = []
    if sc.get("premise"):
        bits.append(f"SEASON PREMISE: {sc['premise']}")
    tw = sc.get("twist")
    if tw and tw.get("done"):
        bits.append(f"TWIST (now known to everyone): {tw['text']}")
    return ("\n" + " ".join(bits)) if bits else ""


def host_extra(sc):
    """What TereVi knows from the start, including a twist not yet announced."""
    if is_empty(sc):
        return ""
    bits = []
    if sc.get("premise"):
        bits.append(f"SEASON PREMISE: {sc['premise']}")
    tw = sc.get("twist")
    if tw and not tw.get("done"):
        bits.append(f"YOUR SECRET TWIST (announced on Day {tw['day']}, not before): {tw['text']}")
    return ("\n" + " ".join(bits)) if bits else ""


def template_list():
    return [{"id": t["id"], "name": t["name"], "scenario": copy.deepcopy(t["scenario"])} for t in TEMPLATES]
