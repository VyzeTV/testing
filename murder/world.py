"""World model: map graph, items, agent state and the rules that govern them."""
import copy
import heapq
import json
import random

from .data_world import ROOMS, EDGES, ITEMS, ROOM_ITEMS, HIDDEN_ITEMS, POTENTIAL_LINKS, BUILD_RECIPES, ESCAPE_ROUTES, COMMON_ITEMS
from .data_cast import CHARACTERS, HOSTS, DEFAULT_DRIVES, DEFAULT_ROUTES

MOVE_BUDGET = 40          # minutes of walking available per one-hour tick
MAX_CARRY = 30            # total item count an agent can carry
MEMORY_RECENT = 20


def build_edges():
    edges = []
    for i, (a, b, cost, kind, extra) in enumerate(EDGES):
        e = {"id": extra.get("id", f"e{i}"), "a": a, "b": b, "cost": cost, "kind": kind,
             "hidden": bool(extra.get("hidden")), "locked": bool(extra.get("locked")),
             "keys": list(extra.get("keys", [])), "needs": list(extra.get("needs", [])),
             "discover": extra.get("discover")}
        edges.append(e)
    return edges


def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, int(round(v))))


CAST_FIELDS = ["name", "short", "role", "gender", "pron", "age", "origin", "home", "color", "card", "persona",
               "secret", "likes", "dislikes", "speech", "candor", "goals", "mock_lines", "body", "objection", "traits", "facets", "values"]
BEDROOMS = ["blue_room", "green_room", "yellow_room", "red_room", "violet_room", "orange_room", "grey_room", "white_room"]      # one each: nobody shares a bedroom
NEWCOMER_COLORS = ["#d96bff", "#6bd9a0", "#ffd36b", "#6bb8ff", "#ff8f6b", "#b0e05a", "#e05a9a", "#5ad0e0"]


def week_of(day, n=7):
    return (day - 1) // n + 1


def deadline_for_death(day, n=7):
    """A death lifts the deadline; the new one is the end of the following "week" (n days; 7 by default, shorter for a faster season)."""
    return (week_of(day, n) + 1) * n


def new_escape():
    return {"progress": 0, "clues": [],
            "routes": {rid: {"plan": {k: 0 for k in r["steps"]}, "contributors": [], "attempts": 0} for rid, r in ESCAPE_ROUTES.items()}}


def shuffled_homes(rng=None):
    """Random bedrooms: the 8 starting characters, one to a room, in a random order of rooms."""
    rng = rng or random.Random()
    ids = list(CHARACTERS)
    rng.shuffle(ids)
    rooms = list(BEDROOMS)
    rng.shuffle(rooms)
    return {cid: rooms[i % len(rooms)] for i, cid in enumerate(ids)}


def new_state(start_day=3, shuffle_rooms=False):
    """Seed the world as of the end of Day 2 (or a fresh Day 1 if start_day == 1). With shuffle_rooms the bedroom pairings are random."""
    agents = {}
    cast = {}
    homes = shuffled_homes() if shuffle_rooms else {}
    for cid, c in CHARACTERS.items():
        s = c["start"] if start_day > 1 else {"hp": 100, "sanity": 100}
        cast[cid] = {k: c[k] for k in CAST_FIELDS if k in c}
        if cid in homes:
            cast[cid]["home"] = homes[cid]
        agents[cid] = {
            "status": "alive", "drive": {"id": DEFAULT_DRIVES.get(cid, "survivor"), "target": None, "arc": ""}, "known_secrets": [],
            "room": cast[cid]["home"], "hp": s["hp"], "sanity": s["sanity"],
            "inv": dict(c["inv"]), "known": [], "activity": "Waking up",
            "aff": dict(c["aff"]) if start_day > 1 else {k: 0 for k in c["aff"]},
            "memory": {"diary": list(c["diary"]) if start_day > 1 else [], "recent": [], "notes": [], "lost": [], "moments": []},
        }
    hidden = {room: [dict(h, found=False) for h in lst] for room, lst in HIDDEN_ITEMS.items()}
    return {
        "day": start_day,
        "cast": cast,
        "agents": agents,
        "npcs": {"neovi": {"room": "laundry", "aff": {}, "scheme": "", "diary": [], "fear": 2,
                           "inv": {"first_aid_kit": 1, "sweets": 2, "bandages": 2, "master_key": 1}}},
        "room_items": copy.deepcopy(ROOM_ITEMS),
        "hidden_items": hidden,
        "found_edges": [],
        "unlocked": [],
        "notable": [],
        "history": [],
        "deadline_day": 7 * week_of(start_day),
        "week_len": 7,
        "case": None,
        "vacancies": [],
        "arrivals": [],
        "graveyard": [],
        "custom_items": {},
        "rule": None,
        "last_rule": None,
        "rule_titles": [],
        "bonds": [],
        "occasion": None,
        "challenge": None,
        "escape": new_escape(),
        "threats": [],
        "island": None,
        "revealed": start_day > 1,          # Day 1 is introductions; the truth is revealed that evening
        "over": None,                       # set when the season ends (the Reckoning, or the truth gets out)
        "plots": {}, "incitements": [], "rumors": [], "saga": [], "factions": [],
        "trail": [], "item_log": {}, "gm_pending": [], "built": [], "map_v2": True,
        "traps": [], "bodies": [], "spree": None, "stats": {}, "san_hist": {}, "scenario": None, "accomplices": {}, "stash": [], "withheld": [], "aftermath": None,
        "locks": {}, "broken": [], "blocks": {}, "crafted": [], "pool_v2": True,
        "hooks": [], "ties": [], "belongings": None, "disturbances": [], "odd": {}, "telemetry": {}, "door_log": [], "vote_log": [], "alliances": [], "chronicle": [], "chron_seq": 0,
    }


def upgrade_state(state):
    """Fill in keys added after a state file was first saved."""
    if "cast" not in state:
        state["cast"] = {cid: {k: c[k] for k in CAST_FIELDS if k in c} for cid, c in CHARACTERS.items()}
    for a in state["agents"].values():
        a.setdefault("status", "alive")
    state.setdefault("week_len", 7)
    state.setdefault("deadline_day", state["week_len"] * week_of(state["day"], state["week_len"]))
    for k, v in (("case", None), ("vacancies", []), ("arrivals", []), ("graveyard", []), ("custom_items", {}),
                 ("rule", None), ("last_rule", None), ("rule_titles", []), ("bonds", []), ("occasion", None),
                 ("challenge", None), ("escape", new_escape()), ("threats", []), ("island", None),
                 ("revealed", state["day"] > 1), ("over", None), ("plots", {}), ("incitements", []), ("rumors", []), ("saga", []),
                 ("factions", []), ("trail", []), ("item_log", {}), ("gm_pending", []), ("built", []), ("traps", []), ("bodies", []), ("spree", None), ("stats", {}), ("san_hist", {}), ("scenario", None), ("accomplices", {}), ("stash", []), ("withheld", []), ("aftermath", None), ("locks", {}), ("broken", []), ("blocks", {}), ("crafted", []), ("hooks", []), ("ties", []), ("belongings", None), ("disturbances", []), ("odd", {}), ("telemetry", {}), ("door_log", []), ("vote_log", []), ("alliances", []), ("chronicle", []), ("chron_seq", 0)):
        state.setdefault(k, v)
    for c_ in state["cast"].values():
        c_.pop("hook", None)                          # characters carry no pre-set loose ends; hooks grow out of events
    sh = state["cast"].get("shintaro")
    if sh and "searched his bag" in sh.get("secret", ""):
        # the old, unresolvable "who searched my bag" obsession is now a short-lived hook that fades
        sh["secret"] = sh["secret"].split(" Someone searched his bag")[0]
        sh["goals"] = "Keep his persona intact, test who he can trust, work out what this place really is and who among them is dangerous."
    if not state.get("pool_v2"):
        from .data_items import ROOM_ADDITIONS, HIDDEN_ADDITIONS
        for room, add in ROOM_ADDITIONS.items():
            pool = state["room_items"].setdefault(room, {})
            for k, q in add.items():
                if q > 0 and k not in pool:
                    pool[k] = q
        for room, lst in HIDDEN_ADDITIONS.items():
            have = state.setdefault("hidden_items", {}).setdefault(room, [])
            for h in lst:
                if not any(set(x.get("items", {})) == set(h["items"]) for x in have):
                    have.append(dict(h, found=False))
        state["pool_v2"] = True
    if not state.get("map_v2"):
        # the map grew (voting grounds, core vault, new tools): add what an older save is missing
        for room, items in ROOM_ITEMS.items():
            pool = state["room_items"].setdefault(room, {})
            if room in ("generator_shed", "boathouse", "boiler_room"):
                for it, q in items.items():
                    pool.setdefault(it, q)
        state["map_v2"] = True
    esc = state["escape"]
    old_plan, old_contrib, old_att = esc.pop("plan", None), esc.pop("contributors", None), esc.pop("attempts", None)
    for k, v in new_escape().items():
        esc.setdefault(k, v)
    for rid, r in ESCAPE_ROUTES.items():
        rt = esc["routes"].setdefault(rid, {"plan": {}, "contributors": [], "attempts": 0})
        for k in r["steps"]:
            rt["plan"].setdefault(k, 0)
    if old_plan and sum(esc["routes"]["transmit"]["plan"].values()) == 0:
        for k, v in old_plan.items():
            if k in esc["routes"]["transmit"]["plan"]:
                esc["routes"]["transmit"]["plan"][k] = v
        esc["routes"]["transmit"]["contributors"] = list(old_contrib or [])
        esc["routes"]["transmit"]["attempts"] = old_att or 0
    for g in state.get("graveyard", []):
        g.setdefault("how", g.get("status", "dead"))
    for cid, a in state["agents"].items():
        a.setdefault("drive", {"id": DEFAULT_DRIVES.get(cid, "survivor"), "target": None, "arc": ""})
        a.setdefault("known_secrets", [])
        a.setdefault("route", DEFAULT_ROUTES.get(cid) or ["transmit", "shutdown", "raft", "ultimatum"][sum(map(ord, cid)) % 4])
        a.setdefault("recent_acts", [])
        a.setdefault("harmed_by", [])
        a["memory"].setdefault("lost", [])
        a["memory"].setdefault("moments", [])
    nv = state["npcs"].setdefault("neovi", {"room": "laundry"})
    for k, v in (("aff", {}), ("scheme", ""), ("diary", []), ("fear", 2),
                 ("inv", {"first_aid_kit": 1, "sweets": 2, "bandages": 2, "master_key": 1})):
        nv.setdefault(k, v)
    # Remember the people who died before this save was upgraded (original cast only; newcomers never knew them).
    for g in state.get("graveyard", []):
        for cid, a in state["agents"].items():
            if cid in CHARACTERS and cid != g["id"] and a.get("status", "alive") == "alive" and g["id"] in state["cast"] \
                    and not any(x["id"] == g["id"] for x in a["memory"]["lost"]):
                a["memory"]["lost"].append({"id": g["id"], "name": state["cast"][g["id"]]["short"], "day": g.get("day", 0),
                                            "how": g.get("how", g["status"]), "close": "someone you knew"})
    # Fields added after a save was made (e.g. candor) are filled from the seed data when the character is a known one.
    for cid, c in state["cast"].items():
        seed = CHARACTERS.get(cid)
        for k in CAST_FIELDS:
            if k not in c and seed and k in seed:
                c[k] = seed[k]
    return state


class World:
    def __init__(self, state=None):
        self.static_edges = build_edges()
        self.state = upgrade_state(state) if state is not None else new_state()
        self.rng = random.Random()

    @property
    def edges(self):
        out = list(self.static_edges)
        for b in self.state.get("built", []):
            out.append({"id": b["id"], "a": b["a"], "b": b["b"], "cost": b["cost"], "kind": b["kind"], "hidden": False, "locked": False,
                        "keys": [], "needs": [], "discover": None, "built": True})
        return out

    @property
    def edge_by_id(self):
        return {e["id"]: e for e in self.edges}

    # ---------- persistence ----------
    def dump(self):
        return json.loads(json.dumps(self.state))

    @staticmethod
    def load(path):
        with open(path, "r", encoding="utf-8") as f:
            return World(json.load(f))

    # ---------- helpers ----------
    @property
    def agents(self):
        """Living participants only."""
        return {k: v for k, v in self.state["agents"].items() if v.get("status", "alive") == "alive"}

    @property
    def all_agents(self):
        return self.state["agents"]

    @property
    def cast(self):
        return self.state["cast"]

    def char(self, cid):
        return self.state["cast"].get(cid) or HOSTS.get(cid)

    def room_name(self, rid):
        return ROOMS[rid][0]

    def item_spec(self, iid):
        return ITEMS.get(iid) or self.state["custom_items"].get(iid) or {"name": iid, "tags": []}

    def item_name(self, iid):
        return self.item_spec(iid)["name"]

    def end_agent(self, cid, status, how=None):
        """Mark a participant as dead / executed / escaped and record it."""
        a = self.state["agents"][cid]
        a["status"] = status
        self.state["plots"].pop(cid, None)
        for pl in list(self.state["plots"]):
            if self.state["plots"][pl].get("target") == cid:
                del self.state["plots"][pl]
        self.state["graveyard"].append({"id": cid, "status": status, "day": self.state["day"], "room": a["room"], "how": how or status})

    def add_newcomer(self, spec):
        """Create a new participant from user-supplied data. Returns the new id."""
        import re
        name = spec["name"].strip()
        base = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "newcomer"
        cid, n = base, 2
        while cid in self.state["cast"] or cid in HOSTS:
            cid = f"{base}_{n}"; n += 1
        taken = {}
        for k, v in self.agents.items():
            taken[self.state["cast"][k]["home"]] = taken.get(self.state["cast"][k]["home"], 0) + 1
        home = min(BEDROOMS, key=lambda r: taken.get(r, 0))
        gender = spec["gender"]
        color = NEWCOMER_COLORS[len(self.state["cast"]) % len(NEWCOMER_COLORS)]
        self.state["cast"][cid] = {
            "name": name, "short": name.split()[0], "role": spec.get("role") or "Newcomer", "gender": gender,
            "pron": "she" if gender == "female" else "he", "age": int(spec.get("age") or 25),
            "origin": spec.get("origin") or "Unknown", "home": home, "color": color, "card": "",
            "persona": spec.get("persona") or "A newcomer with a story of their own.",
            "secret": spec.get("secret") or "They have something they would rather keep to themselves.",
            "likes": spec.get("likes") or "?", "dislikes": spec.get("dislikes") or "?",
            "speech": spec.get("speech") or "Natural and distinctive.",
            "candor": spec.get("candor") or "Speaks their mind: swears, teases or snaps in line with their personality and how they feel about the person in front of them.",
            "goals": spec.get("goals") or "Survive, understand the others, find a place in the group.",
            "mock_lines": ["Hello? Is this really happening?", "I'm still figuring this place out.", "Nice to meet you. I think."],
        }
        inv = {}
        for i, raw in enumerate([x.strip() for x in (spec.get("items") or "").split(",") if x.strip()][:8]):
            iid = f"custom_{cid}_{i}"
            self.state["custom_items"][iid] = {"name": raw, "tags": ["gear"]}
            inv[iid] = 1
        others = list(self.agents.keys())
        self.state["agents"][cid] = {
            "status": "alive", "room": home, "hp": 100, "sanity": 90, "inv": inv, "known": [],
            "route": (spec.get("route") if spec.get("route") in ("transmit", "shutdown", "raft", "ultimatum") else self.rng.choice(["transmit", "shutdown", "raft", "ultimatum"])),
            "drive": {"id": (spec.get("drive") if spec.get("drive") in ("survivor", "protector", "saboteur", "schemer", "avenger", "thrill", "romantic", "seeker", "nihilist", "martyr")
                              else self.rng.choice(["survivor", "protector", "seeker", "thrill", "schemer", "romantic"])), "target": None, "arc": ""},
            "known_secrets": [],
            "activity": "Just arrived", "aff": {o: 0 for o in others},
            "memory": {"diary": [f"Arrived on the island on Day {self.state['day']}. TereVi welcomed me with a smile that felt like a threat."],
                       "recent": [], "notes": [], "lost": [], "moments": []},
        }
        for o in others:
            self.state["agents"][o]["aff"][cid] = 0
        self.state["arrivals"].append(cid)
        # fill the matching vacancy
        for i, v in enumerate(self.state["vacancies"]):
            if v["gender"] == gender:
                del self.state["vacancies"][i]
                break
        return cid

    def occupants(self, room, include_npcs=True, include_hidden=False):
        ids = [a for a, v in self.agents.items() if v["room"] == room and (include_hidden or not (v.get("hiding") or v.get("asleep") or v.get("out")))]
        if include_npcs:
            ids += [n for n, v in self.state["npcs"].items() if v["room"] == room]
        return ids

    def display_name(self, cid):
        c = self.state["cast"].get(cid)
        if c:
            return c["short"]
        if cid in HOSTS:
            return HOSTS[cid]["name"]
        return cid

    # ---------- graph ----------
    def has_room_key(self, agent_id, room):
        """Who can open a locked room: the master key or skeleton keys, the people who sleep there, and whoever locked it."""
        a = self.agents.get(agent_id)
        if a is None:
            return True
        if a["inv"].get("master_key", 0) > 0 or a["inv"].get("skeleton_keys", 0) > 0:
            return True
        if self.state["cast"].get(agent_id, {}).get("home") == room or a["inv"].get(f"key_{room}", 0) > 0:
            return True
        lk = self.state.get("locks", {}).get(room)
        return bool(lk and lk.get("by") == agent_id)

    def door_state_ok(self, agent_id, e, frm):
        """Player-made obstacles on an ordinary door: a barricade holds out whoever is on the far side, a lock keeps out anyone without a key."""
        to = e["b"] if frm == e["a"] else e["a"]
        here_lk = self.state.get("locks", {}).get(frm)
        if here_lk and here_lk.get("keyed") and not self.has_room_key(agent_id, frm):
            return False, "locked in"
        blk = self.state.get("blocks", {}).get(e["id"])
        if blk and blk["inside"] != frm:
            return False, f"barricaded with {blk.get('prop_name') or blk['prop']}"
        lk = self.state.get("locks", {}).get(to)
        if lk and not self.has_room_key(agent_id, to):
            return False, "locked"
        return True, ""

    def cross_door(self, agent_id, e, frm, to, events):
        """Leaving a room: a barricade is dragged aside, a bolt is drawn back (a key-holder locks up behind them)."""
        name = self.display_name(agent_id)
        blk = self.state.get("blocks", {}).get(e["id"])
        if blk and blk["inside"] == frm:
            del self.state["blocks"][e["id"]]
            if blk["prop"] in ITEMS:
                pool = self.state["room_items"].setdefault(frm, {})
                pool[blk["prop"]] = pool.get(blk["prop"], 0) + 1
            events.append({"type": "door", "who": agent_id, "room": frm, "text": f"{name} drags the {blk.get('prop_name') or blk['prop']} away from the door of the {self.room_name(frm)} and goes out", "vis": "public"})
        lk = self.state.get("locks", {}).get(frm)
        if lk and e["kind"] in ("door", "window"):
            if self.has_room_key(agent_id, frm):
                events.append({"type": "door", "who": agent_id, "room": frm, "text": f"{name} locks the {self.room_name(frm)} behind them", "vis": "public"})
            else:
                del self.state["locks"][frm]
                events.append({"type": "door", "who": agent_id, "room": frm, "text": f"{name} draws the bolt back and leaves the {self.room_name(frm)}", "vis": "public"})

    def edge_passable(self, agent_id, e, consume=False, frm=None):
        """Return (ok, note). Hidden edges require knowledge; locked edges require a key or prior opening."""
        a = self.agents.get(agent_id)
        if a is None:
            # NPCs (NeoVi) hold the master key but do not use secret passages.
            return (not e["hidden"]), ("unknown" if e["hidden"] else "")
        if e["hidden"] and e["id"] not in a["known"]:
            return False, "unknown"
        if frm and e["kind"] in ("door", "window") and not e["hidden"]:
            ok, note = self.door_state_ok(agent_id, e, frm)
            if not ok:
                return False, note
        if e["id"] in self.state["unlocked"]:
            return True, ""
        if e["needs"]:
            tool = next((t for t in e["needs"] if a["inv"].get(t, 0) > 0), None)
            if not tool:
                return False, "stuck (needs a tool such as a crowbar)"
            if consume:
                self.state["unlocked"].append(e["id"])
                return True, f"forces the way open with the {self.item_name(tool)}"
            return True, ""
        if e["locked"]:
            key = next((k for k in e["keys"] if a["inv"].get(k, 0) > 0), None)
            if not key:
                return False, "locked"
            if consume:
                self.state["unlocked"].append(e["id"])
                return True, f"unlocks the way with the {self.item_name(key)}"
            return True, ""
        return True, ""

    def adjacent(self, agent_id, room):
        out = []
        for e in self.edges:
            if e["a"] == room:
                other = e["b"]
            elif e["b"] == room:
                other = e["a"]
            else:
                continue
            ok, note = self.edge_passable(agent_id, e, frm=room)
            if e["hidden"] and note == "unknown":
                continue
            out.append({"room": other, "cost": e["cost"], "edge": e["id"], "ok": ok, "note": note, "kind": e["kind"]})
        return out

    def path(self, agent_id, src, dst):
        """Dijkstra over passable edges. Returns list of (room, edge_id, cost) steps, or None."""
        if src == dst:
            return []
        dist = {src: 0}
        prev = {}
        heap = [(0, src)]
        while heap:
            d, u = heapq.heappop(heap)
            if u == dst:
                break
            if d > dist.get(u, 1e9):
                continue
            for n in self.adjacent(agent_id, u):
                if not n["ok"]:
                    continue
                nd = d + n["cost"]
                if nd < dist.get(n["room"], 1e9):
                    dist[n["room"]] = nd
                    prev[n["room"]] = (u, n["edge"], n["cost"])
                    heapq.heappush(heap, (nd, n["room"]))
        if dst not in prev:
            return None
        steps = []
        cur = dst
        while cur != src:
            u, eid, cost = prev[cur]
            steps.append((cur, eid, cost))
            cur = u
        steps.reverse()
        return steps

    def reachable_rooms(self, agent_id, budget=MOVE_BUDGET):
        """Rooms the agent could reach within the movement budget this hour."""
        src = self.agents[agent_id]["room"]
        dist = {src: 0}
        heap = [(0, src)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist.get(u, 1e9):
                continue
            for n in self.adjacent(agent_id, u):
                if not n["ok"]:
                    continue
                nd = d + n["cost"]
                if nd <= budget and nd < dist.get(n["room"], 1e9):
                    dist[n["room"]] = nd
                    heapq.heappush(heap, (nd, n["room"]))
        dist.pop(src, None)
        return dist  # room -> minutes

    # ---------- actions ----------
    def move(self, agent_id, dst, budget=MOVE_BUDGET):
        """Walk toward dst. Returns dict(path=[rooms], events=[...], arrived=bool, blocked=str|None)."""
        a = self.agents[agent_id]
        res = {"path": [a["room"]], "events": [], "arrived": a["room"] == dst, "blocked": None, "edges": []}
        if dst not in ROOMS or a["room"] == dst:
            return res
        steps = self.path(agent_id, a["room"], dst)
        eb = self.edge_by_id
        if steps is None:
            # Maybe blocked by a lock: report why
            res["blocked"] = self._why_blocked(agent_id, dst)
            return res
        spent = 0
        for room, eid, cost in steps:
            if spent + cost > budget:
                break
            e = eb[eid]
            ok, note = self.edge_passable(agent_id, e, consume=True, frm=a["room"])
            if not ok:
                res["blocked"] = note
                break
            if note:
                res["events"].append({"type": "lock", "who": agent_id, "room": a["room"], "text": f"{self.display_name(agent_id)} {note}", "vis": "public"})
            if e["hidden"]:
                # Anyone in the origin room sees the passage being used.
                for other, ov in self.agents.items():
                    if ov["room"] == a["room"] and e["id"] not in ov["known"] and not (a.get("sneaking") and self.rng.random() < 0.6):
                        ov["known"].append(e["id"])
                if e["id"] not in self.state["found_edges"]:
                    self.state["found_edges"].append(e["id"])
                res["events"].append({"type": "secret", "who": agent_id, "room": a["room"], "edge": e["id"],
                                      "text": f"{self.display_name(agent_id)} slips through a secret passage ({e['id']}) from {self.room_name(a['room'])} to {self.room_name(room)}", "vis": "public"})
            res["edges"].append({"id": eid, "kind": e["kind"], "from": a["room"], "to": room})
            self.cross_door(agent_id, e, a["room"], room, res["events"])
            a["room"] = room
            spent += cost
            res["path"].append(room)
        res["arrived"] = a["room"] == dst
        return res

    def potential_links(self, room):
        """Links that could be built from this room: list of (other room, {kind: minutes}, description)."""
        out = []
        built = {(b["a"], b["b"], b["kind"]) for b in self.state.get("built", [])}
        for a, b, kinds, desc in POTENTIAL_LINKS:
            if room not in (a, b):
                continue
            other = b if room == a else a
            ks = {k: v for k, v in kinds.items() if (a, b, k) not in built and (b, a, k) not in built}
            if ks:
                out.append((other, ks, desc))
        return out

    def build_materials(self, agent_id, kind):
        """Return (ok, spend dict, text) for the materials needed to build `kind`."""
        a = self.agents[agent_id]
        rec = BUILD_RECIPES.get(kind)
        if not rec:
            return False, {}, "unknown kind"
        if all(a["inv"].get(k, 0) >= q for k, q in rec["items"].items()):
            return True, dict(rec["items"]), ""
        if rec.get("alt") and all(a["inv"].get(k, 0) >= q for k, q in rec["alt"].items()) \
                and any(a["inv"].get(t, 0) > 0 for t in ("hammer", "masking_tape", "wire", "sledgehammer")):
            return True, dict(rec["alt"]), "crafts"
        need = ", ".join(f"{q} x {self.item_name(k)}" for k, q in rec["items"].items())
        if rec.get("alt"):
            need += " (or " + ", ".join(f"{q} x {self.item_name(k)}" for k, q in rec["alt"].items()) + " plus a hammer, tape or wire)"
        return False, {}, f"needs {need}"

    def add_link(self, agent_id, other, kind, spend):
        a = self.agents[agent_id]
        for k, q in spend.items():
            a["inv"][k] -= q
            if a["inv"][k] <= 0:
                del a["inv"][k]
        links = {o: ks for o, ks, _ in self.potential_links(a["room"])}
        cost = links[other][kind]
        eid = f"B{len(self.state['built']) + 1}"
        self.state["built"].append({"id": eid, "a": a["room"], "b": other, "kind": kind, "cost": cost, "by": agent_id, "day": self.state["day"]})
        return eid

    def remove_link(self, agent_id, eid):
        built = self.state["built"]
        for b in built:
            if b["id"] == eid:
                built.remove(b)
                return b
        return None

    def _why_blocked(self, agent_id, dst):
        a = self.agents[agent_id]
        # BFS ignoring passability to find the blocking edge near the destination
        for n in self.adjacent(agent_id, dst):
            if not n["ok"]:
                return f"{self.room_name(dst)} is {n['note']}"
        return f"no route to {self.room_name(dst)}"

    def carried(self, agent_id):
        return sum(q for k, q in self.agents[agent_id]["inv"].items() if not k.startswith("acc_"))      # a worn accessory (looks.py) weighs nothing

    def take(self, agent_id, item, qty=1):
        a = self.agents[agent_id]
        pool = self.state["room_items"].setdefault(a["room"], {})
        qty = max(1, int(qty or 1))
        common = item in COMMON_ITEMS.get(a["room"], [])
        have = 999 if common else pool.get(item, 0)
        if have <= 0:
            return None, f"there is no {self.item_name(item)} here"
        qty = min(qty, have, MAX_CARRY - self.carried(agent_id))
        if qty <= 0:
            return None, "hands are full"
        if not common:
            pool[item] = have - qty
            if pool[item] <= 0:
                del pool[item]
        a["inv"][item] = a["inv"].get(item, 0) + qty
        return qty, ""

    def take_from_stash(self, agent_id, item, qty=1):
        a = self.agents[agent_id]
        qty = max(0, min(qty, MAX_CARRY - self.carried(agent_id)))
        if qty:
            a["inv"][item] = a["inv"].get(item, 0) + qty
        return qty, ""

    def drop(self, agent_id, item, qty=1):
        a = self.agents[agent_id]
        have = a["inv"].get(item, 0)
        qty = min(max(1, int(qty or 1)), have)
        if qty <= 0:
            return None, f"{self.display_name(agent_id)} does not have that"
        a["inv"][item] = have - qty
        if a["inv"][item] <= 0:
            del a["inv"][item]
        pool = self.state["room_items"].setdefault(a["room"], {})
        pool[item] = pool.get(item, 0) + qty
        return qty, ""

    def give(self, from_id, to_id, item, qty=1):
        if to_id not in self.agents or self.agents[to_id]["room"] != self.agents[from_id]["room"]:
            return None, "recipient is not here"
        a, b = self.agents[from_id], self.agents[to_id]
        have = a["inv"].get(item, 0)
        qty = min(max(1, int(qty or 1)), have, MAX_CARRY - self.carried(to_id))
        if qty <= 0:
            return None, "cannot give that"
        a["inv"][item] = have - qty
        if a["inv"][item] <= 0:
            del a["inv"][item]
        b["inv"][item] = b["inv"].get(item, 0) + qty
        return qty, ""

    def use(self, agent_id, item, qty=1):
        """Use an item; consumables are spent and apply their effects."""
        a = self.agents[agent_id]
        if a["inv"].get(item, 0) <= 0:
            return None, f"does not have {self.item_name(item)}"
        spec = self.item_spec(item)
        effect = spec.get("use")
        if not effect:
            return {}, ""
        consumable = any(t in spec.get("tags", []) for t in ("food", "drink", "drug", "medical"))
        if consumable:
            a["inv"][item] -= 1
            if a["inv"][item] <= 0:
                del a["inv"][item]
        a["hp"] = clamp(a["hp"] + effect.get("hp", 0))
        a["sanity"] = clamp(a["sanity"] + effect.get("sanity", 0))
        return effect, ""

    def search(self, agent_id, text, mult=1.0):
        """Search the current room. Returns list of discovery events."""
        a = self.agents[agent_id]
        room = a["room"]
        text = (text or "").lower()
        events = []
        # Hidden passages
        for e in self.edges:
            d = e.get("discover")
            if not e["hidden"] or not d or room not in d["rooms"]:
                continue
            if e["id"] in a["known"]:
                continue
            p = d["p"] * mult * (4 if any(k in text for k in d["keywords"]) else 1)
            if self.rng.random() < p:
                a["known"].append(e["id"])
                if e["id"] not in self.state["found_edges"]:
                    self.state["found_edges"].append(e["id"])
                events.append({"type": "discover", "who": agent_id, "room": room, "edge": e["id"],
                               "text": f"{self.display_name(agent_id)} discovers a secret passage ({e['id']}): {d['text']}", "vis": "gm"})
        # Hidden items
        for h in self.state["hidden_items"].get(room, []):
            if h["found"]:
                continue
            p = h["p"] * mult * (4 if any(k in text for k in h["keywords"]) else 1)
            if self.rng.random() < p:
                h["found"] = True
                pool = self.state["room_items"].setdefault(room, {})
                for it, q in h["items"].items():
                    pool[it] = pool.get(it, 0) + q
                events.append({"type": "discover", "who": agent_id, "room": room,
                               "text": f"{self.display_name(agent_id)} finds {h['text']}", "vis": "gm"})
        return events

    # ---------- memory ----------
    def remember(self, agent_id, text):
        a = self.agents.get(agent_id)
        if a is None:
            return
        rec = a["memory"]["recent"]
        rec.append(text)
        del rec[:-MEMORY_RECENT]
        hook = getattr(self, "mem_hook", None)
        if hook is not None:
            hook(agent_id, text)

    def adjust_aff(self, a, b, delta):
        if a in self.agents and b in self.agents[a]["aff"]:
            aff = self.agents[a]["aff"]
            aff[b] = max(-10, min(10, aff[b] + int(delta)))

    # ---------- snapshot for viewer ----------
    def snapshot(self):
        s = self.state
        case = s.get("case")
        case_public = None
        if case:
            case_public = {"victim": case["victim"], "room": case.get("room"), "announced": case["announced"],
                           "discovered": len(case["discovered_by"]), "vote_day": case.get("vote_day"),
                           "vote_hour": case.get("vote_hour"), "body": bool(case.get("room")) and not case.get("poison_pending"),
                           "evidence": ([{"text": c["text"], "by": [x for x in c["found_by"] if x in s["cast"]][:3]} for c in case["clues"] if c["found_by"] and any(x not in c.get("held", []) for x in c["found_by"])]
                                        if case["announced"] else []),
                           "testimonies": ([{"by": t["by"], "claim": t["claim"]} for t in (case.get("testimonies") or [])[-12:]] if case["announced"] else []),
                           "contradictions": ([dict(x) for x in case.get("contradictions", [])] if case["announced"] else [])}
        return {
            "deadline_day": s["deadline_day"], "vacancies": list(s["vacancies"]), "case": case_public,
            "revealed": s.get("revealed", True), "over": s.get("over"),
            "aftermath": bool(s.get("aftermath") and s["aftermath"].get("since") is not None and not case and s["day"] <= s["aftermath"]["until"]),
            "bodies": [{"victim": b["victim"], "room": b["room"]} for b in s.get("bodies", [])], "spree": bool(s.get("spree")),
            "scenario": ({"title": s["scenario"].get("title"), "premise": s["scenario"].get("premise"), "rules": list(s["scenario"].get("rules", []))}
                         if s.get("scenario") and (s["scenario"].get("title") or s["scenario"].get("premise")) else None),
            "stats": {c: dict(v) for c, v in s.get("stats", {}).items()}, "san_hist": {c: list(v) for c, v in s.get("san_hist", {}).items()},
            "plots": [{"who": c, "target": p.get("target"), "stage": p.get("stage"), "step": p.get("step"), "method": p.get("method"),
                       "cover": p.get("cover"), "log": list(p.get("log", []))[-4:]} for c, p in s.get("plots", {}).items()],
            "factions": [dict(f) for f in s.get("factions", [])],
            "graveyard": [dict(g) for g in s.get("graveyard", [])],
            "rule": ({k: v for k, v in s["rule"].items() if k != "violations_log"} if s.get("rule") else None),
            "bonds": [dict(b) for b in s["bonds"]], "escape": {"progress": s["escape"]["progress"], "clues": list(s["escape"]["clues"])[-6:],
                                              "routes": {rid: dict(r["plan"]) for rid, r in s["escape"]["routes"].items()}},
            "island": dict(s["island"]) if s.get("island") else None,
            "threats": [{k: t[k] for k in ("target", "demand", "due_day", "due_hour", "status")} for t in s.get("threats", [])],
            "occasion": ({k: o for k, o in s["occasion"].items() if k in ("kind", "where", "host", "text", "invite")} if s.get("occasion") else None),
            "challenge": s.get("challenge"),
            "withheld": [{"by": e["by"], "kind": e["kind"], "text": e["text"], "why": e["why"], "status": e["status"], "late": e.get("late", False)}
                         for e in s.get("withheld", [])],
            "hooks": [{"kind": h["kind"], "victims": list(h["victims"]), "culprit": h["culprit"], "room": h["room"], "text": h["text"], "status": h["status"],
                       "evidence": h["evidence"], "clues": list(h["clues"])[-4:], "day": h["day"]} for h in s.get("hooks", [])[-12:]],
            "alliances": [{"members": list(a["members"]), "strength": round(a["strength"], 1), "status": a["status"], "secret": a["secret"]} for a in s.get("alliances", [])[-6:]],
            "ties": [dict(t) for t in s.get("ties", [])[-40:]],
            "telemetry": {k: dict(v) for k, v in s.get("telemetry", {}).get(str(s["day"]), {}).items()},
            "locks": {r: lk.get("by") for r, lk in s.get("locks", {}).items()}, "keyed_locks": [r for r, lk in s.get("locks", {}).items() if lk.get("keyed")],
            "blood": {r: sum(1 for b in s.get("blood", []) if b["room"] == r and (s["day"] - b["day"]) * 24 + s.get("_hour", 12) - b["hour"] <= 24) for r in {b["room"] for b in s.get("blood", [])}},
            "broken_doors": list(s.get("broken", [])),
            "barricades": [{"edge": eid, "inside": b["inside"], "prop": b.get("prop_name") or b["prop"]} for eid, b in s.get("blocks", {}).items()],
            "stash": [{"room": x["room"], "spot": x["spot"], "items": dict(x["items"]), "by": x["by"]} for x in s.get("stash", [])],
            "agents": {cid: {"status": v.get("status", "alive"), "room": v["room"], "hp": v["hp"], "sanity": v["sanity"], "hiding": bool(v.get("hiding")), "concealed": list(v.get("concealed", {})), "outfit": v.get("outfit"), "conds": v.get("conds_view") or [], "out": v.get("out_view"), "mind": v.get("mind_view"), "brain": v.get("brain_view"), "beliefs": v.get("beliefs_view") or [],
                             "inv": dict(v["inv"]), "activity": v["activity"], "known": list(v["known"]),
                             "drive": dict(v.get("drive", {})), "secrets": [dict(k) for k in v.get("known_secrets", [])],
                             "lost": [x["name"] for x in v["memory"].get("lost", [])], "moments": list(v["memory"].get("moments", []))[-4:],
                             "quirk": ((s["cast"].get(cid, {}).get("quirks") or [{}])[-1]).get("text", ""),
                             "aff": dict(v["aff"])}
                       for cid, v in s["agents"].items()},
            "npcs": {nid: dict(v) for nid, v in s["npcs"].items()},
            "room_items": {r: dict(it) for r, it in s["room_items"].items() if it},
            "hidden_items": {r: {k: q for h in lst if not h["found"] for k, q in h["items"].items()}
                             for r, lst in s["hidden_items"].items() if any(not h["found"] for h in lst)},
            "found_edges": list(s["found_edges"]),
            "built": [dict(b) for b in s.get("built", [])],
            "unlocked": list(s["unlocked"]),
        }
