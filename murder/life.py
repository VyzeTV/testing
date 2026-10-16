"""Everyday physics of the island: odds of success, building ladders and other links, risky climbs,
seeing people come and go (and remembering it imperfectly), and the vault's traps.

LifeMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS, BUILD_RECIPES, ITEMS

BIG_ITEMS = {"ladder", "planks", "barrel", "sledgehammer", "fuel_can", "rope", "battery", "tarp", "bolt_cutters", "crowbar"}


def _hh(h):
    return f"{h:02d}:00"


class LifeMixin:
    def life_init(self):
        self.busy = set()          # people too distracted this turn to take things in
        self.dice_log = []

    # ------------------------------------------------------------------ odds of success
    def success_p(self, cid, base, bonus=0.0):
        """Chance that an action works: the context sets the base, sanity and health pull it down."""
        a = self.world.agents.get(cid)
        if not a:
            return base
        p = base + bonus - 0.30 * max(0, 55 - a["sanity"]) / 55 - 0.25 * max(0, 55 - a["hp"]) / 55 - self.cond_penalty(cid)
        return max(0.05, min(0.97, p))

    def roll(self, cid, base, bonus=0.0):
        """Roll an action. Returns (ok, luck) where luck is 'bad', 'good' or None: even the best prepared can have plain bad luck."""
        p = self.success_p(cid, base, bonus)
        r = self.rng.random()
        if r < 0.04:
            return False, "bad"
        if r > 0.985:
            return True, "good"
        return r < p, None

    def experiment_dice(self, cid, d):
        """The dice decide how an experiment goes; the game master only narrates it."""
        a = self.world.agents[cid]
        has_tool = any("tool" in ITEMS.get(k, {}).get("tags", []) or "gadget" in ITEMS.get(k, {}).get("tags", []) for k in a["inv"])
        bonus, used = self.experiment_item_bonus(cid, d.get("idea", ""))
        p = self.success_p(cid, 0.66, (0.10 if has_tool else 0.0) + bonus) - 0.015 * self.adapt_level()
        why = ("helped by the " + ", ".join(used)) if used else ""
        r = self.rng.random()
        if r < 0.03:
            return "failure", "plain bad luck", p
        if r < p * 0.62:
            return "success", why, p
        if r < min(0.95, p + 0.1):
            return "partial", why, p
        return "failure", "", p

    # ------------------------------------------------------------------ building links
    def build_lines(self, cid):
        w = self.world
        a = w.agents[cid]
        out = []
        for other, kinds, desc in w.potential_links(a["room"]):
            opts = []
            for k in kinds:
                ok, _, _ = w.build_materials(cid, k)
                opts.append(f"{k}{' (you have what it takes)' if ok else ' (missing materials)'}")
            out.append(f"{w.room_name(other)} ({other}): {desc}; could be built as {', '.join(opts)}")
        mine = [b for b in w.state.get("built", []) if a["room"] in (b["a"], b["b"])]
        if self.lean:
            out = [o for o in out if "you have what it takes" in o]
        if not out and not mine:
            return ""
        txt = ("BUILD: " + " | ".join(out) + ". Use action 'build' with \"build\": {\"kind\": \"ladder|rope|plank\", \"to\": \"<room id>\"}. "
               "Ladders can be crafted from 2 planks + a rope and a hammer, tape or wire. Building can fail, and climbing can make you fall (more so when hurt or panicked). ") if out else ""
        if mine:
            txt += "Links built here: " + ", ".join(f"{b['kind']} to {w.room_name(b['b'] if b['a'] == a['room'] else b['a'])} ({b['id']})" for b in mine) + \
                   ". You can take one down with \"build\": {\"kind\": \"remove\", \"to\": \"<room id>\"}."
        return txt

    def do_build(self, tick, cid, d):
        w = self.world
        a = w.agents[cid]
        spec = d.get("build") or {}
        kind, to = spec.get("kind"), spec.get("to")
        name = self.nm(cid)
        here = [o for o in w.occupants(a["room"]) if o != cid]
        if kind == "remove":
            for b in list(w.state.get("built", [])):
                if a["room"] in (b["a"], b["b"]) and to in (b["a"], b["b"]) and to != a["room"]:
                    w.remove_link(cid, b["id"])
                    back = {"ladder": "ladder", "plank": "planks", "rope": "rope"}[b["kind"]]
                    a["inv"][back] = a["inv"].get(back, 0) + 1
                    self.log_event(tick, {"type": "build", "who": cid, "room": a["room"], "vis": "public",
                                          "text": f"{name} takes down the {b['kind']} to the {w.room_name(to)}."}, witnesses=here, actor=cid)
                    return
            return
        links = {o: ks for o, ks, _ in w.potential_links(a["room"])}
        if kind not in BUILD_RECIPES or to not in links or kind not in links[to]:
            self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm", "text": f"{name} tried to build something that cannot be built here."}, actor=cid)
            return
        ok, spend, note = w.build_materials(cid, kind)
        if not ok:
            self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm", "text": f"{name} could not build the {kind}: {note}."}, actor=cid)
            return
        tool = any(a["inv"].get(t, 0) > 0 for t in ("hammer", "sledgehammer", "wire", "masking_tape", "carabiner"))
        good, luck = self.roll(cid, 0.72, 0.1 if tool else 0.0)
        if not good:
            for k in list(spend):
                if self.rng.random() < 0.5:
                    a["inv"][k] -= spend[k]
                    if a["inv"][k] <= 0:
                        del a["inv"][k]
            self.log_event(tick, {"type": "build", "who": cid, "room": a["room"], "vis": "public",
                                  "text": f"{name} tries to set up a {kind} to the {w.room_name(to)} but it {'slips and clatters down' if luck == 'bad' else 'will not hold'}."}, witnesses=here, actor=cid)
            return
        eid = w.add_link(cid, to, kind, spend)
        self.log_event(tick, {"type": "build", "who": cid, "room": a["room"], "vis": "public",
                              "text": f"{name} sets up a {BUILD_RECIPES[kind]['name']} between the {w.room_name(a['room'])} and the {w.room_name(to)}."}, witnesses=here, actor=cid)
        self.moment(cid, f"built a {kind} linking {w.room_name(a['room'])} and {w.room_name(to)}")
        self.tally(cid, "builds")

    def traversal_risks(self, tick, cid, mv):
        """Climbing a ladder or a rope line can end in a fall; the hurt and the panicked fall more."""
        w = self.world
        a = w.agents.get(cid)
        for e in mv.get("edges", []):
            rec = BUILD_RECIPES.get({"ladder": "ladder", "rope": "rope", "plank": "plank"}.get(e["kind"], ""))
            if not rec:
                continue
            p = rec["risk"] + 0.30 * self.slip_chance(cid) + (0.02 if self.rng.random() < 0.1 else 0)
            if self.rng.random() < p:
                a["room"] = e["from"]
                path = mv["path"]
                if e["to"] in path:
                    del path[path.index(e["to"]):]
                self.log_event(tick, {"type": "mishap", "who": cid, "room": e["from"], "vis": "public",
                                      "text": f"{self.nm(cid)} slips on the {e['kind']} to the {w.room_name(e['to'])} and falls."},
                               witnesses=[o for o in w.occupants(e["from"]) if o != cid], actor=cid)
                dmg_ = self.rng.randint(6, 20)
                self.stat(tick, cid, "hp", -dmg_, "a fall", lethal=f"fell from a {e['kind']}")
                self.stat(tick, cid, "sanity", -2, "a fall")
                if cid in w.agents:
                    self.injure(tick, cid, None, set(), dmg_, "fall")
                    self.maybe_panic(tick, cid, "the fall", 0.2)
                return True
        return False

    def vault_traps(self, tick, cid):
        w, s = self.world, self.s
        a = w.agents.get(cid)
        if not a or a["room"] != "core_vault":
            return
        approach = s["escape"]["routes"]["shutdown"]["plan"]["approach"]
        p = max(0.1, 0.75 - 0.65 * approach / 100)
        if self.blackout_until >= self.idx:
            p *= 0.5
        if self.rng.random() < p:
            dmg = self.rng.randint(12, 30)
            self.log_event(tick, {"type": "mishap", "who": cid, "room": "core_vault", "vis": "public",
                                  "text": f"{self.nm(cid)} sets off the Core Vault's defences: a pressure plate clicks and the ceiling turrets open fire."},
                           witnesses=[o for o in w.occupants("core_vault") if o != cid], actor=cid)
            self.fx(tick, "shake", "core_vault", cid)
            self.stat(tick, cid, "hp", -dmg, "the vault's turrets", lethal="shot down by the Core Vault's turrets")
            self.stat(tick, cid, "sanity", -4, "the vault's turrets")

    # ------------------------------------------------------------------ seeing people come and go
    def visible_details(self, subject, observer=None):
        w = self.world
        a = w.all_agents.get(subject)
        if not a:
            return []
        out = []
        weap = [w.item_name(k) for k in a["inv"] if "weapon" in w.item_spec(k).get("tags", []) and self.sees_concealed(observer, subject, k)]
        big = [w.item_name(k) for k in a["inv"] if k in BIG_ITEMS]
        if weap:
            out.append(f"carrying a {weap[0]}")
        elif big:
            out.append(f"carrying a {big[0]}")
        if a["hp"] < 45:
            out.append("looked hurt and unsteady")
        if a["sanity"] < 30:
            out.append("looked wild-eyed")
        tell = a.get("tell")
        if tell and tell["until"] >= self.day * 24 + self.s.get("_hour", 12):
            out.append(tell["text"])
        return out[:2]

    def memory_reliability(self, observer):
        r = 1.0 - 1.2 * self.slip_chance(observer) - (0.2 if observer in self.busy else 0.0) - (0.15 if self.blackout_until >= self.idx else 0.0)
        return max(0.35, min(1.0, r))

    def render_fact(self, f):
        w = self.world
        who = self.nm(f["who"])
        rn = lambda r: w.room_name(r) if r in ROOMS else r
        if f["type"] == "leave":
            txt = f"{who} leave the {rn(f['room'])}" + (f" for the {rn(f['to'])}" if f.get("to") else "")
        elif f["type"] == "arrive":
            txt = f"{who} arrive in the {rn(f['room'])}" + (f" from the {rn(f['frm'])}" if f.get("frm") else "")
        elif f["type"] == "pass":
            txt = f"{who} pass through the {rn(f['room'])}" + (f" heading for the {rn(f['to'])}" if f.get("to") else "")
        else:
            txt = f"{who} here in the {rn(f['room'])}"
        if f.get("details"):
            txt += "; " + ", ".join(f["details"])
        return f"{_hh(max(0, min(23, f['hour'])))} (you saw) {txt}"

    def witness(self, observer, fact):
        """An observer sees something; if they are distracted, hurt or unwell the memory can come out wrong."""
        w = self.world
        a = w.agents.get(observer)
        if not a or observer == fact["who"]:
            return
        subj = w.all_agents.get(fact["who"])
        if subj and subj.get("sneaking") and fact["type"] in ("leave", "arrive", "pass"):
            if self.rng.random() >= self.notice_p(observer, fact["who"]):
                if self.rng.random() < 0.3:
                    w.remember(observer, f"{_hh(max(0, min(23, fact['hour'])))} (heard) someone slipping past the {w.room_name(fact['room'])}, but you could not tell who.")
                return
        if self.in_dark(observer) and not (w.all_agents.get(fact["who"]) or {}).get("lit"):
            if self.rng.random() < 0.6:
                w.remember(observer, f"{_hh(max(0, min(23, fact['hour'])))} (in the dark) Someone moved through the {w.room_name(fact['room'])}; you could not see who.")
            return
        ident = self.perceived_identity(observer, fact["who"])
        if ident is None:
            if self.rng.random() < 0.7:
                w.remember(observer, f"{_hh(max(0, min(23, fact['hour'])))} (you saw) a figure in a mask or hood {'leave' if fact['type'] == 'leave' else 'arrive in' if fact['type'] == 'arrive' else 'pass through'} the {w.room_name(fact['room'])}; you could not tell who.")
            return
        if ident != fact["who"]:
            fact = dict(fact, who=ident)
        fact = dict(fact, details=self.visible_details(fact["who"], observer))
        true_text = self.render_fact(fact)
        if self.rng.random() < self.memory_reliability(observer):
            w.remember(observer, true_text)
            return
        bad = dict(fact)
        opt = self.rng.choice(["time", "person", "place", "detail"])
        others = [c for c in w.agents if c not in (observer, fact["who"])]
        if opt == "time":
            bad["hour"] = fact["hour"] + self.rng.choice([-2, -1, 1, 2])
        elif opt == "person" and others:
            bad["who"] = self.rng.choice(others)
        elif opt == "place":
            near = [n["room"] for n in w.adjacent("neovi", fact["room"])] or [fact["room"]]
            bad["room"] = self.rng.choice(near)
        else:
            bad["details"] = []
        wrong = self.render_fact(bad)
        if wrong == true_text:
            w.remember(observer, true_text)
            return
        w.remember(observer, wrong)
        fz = a["memory"].setdefault("fuzzy", {})
        fz[wrong] = true_text
        for k in list(fz)[:-12]:
            del fz[k]

    def fix_memories(self, cid, helper_ids, p=0.5):
        """Memories can be set straight when someone else who saw it remembers it right."""
        w = self.world
        a = w.agents.get(cid)
        if not a:
            return 0
        fz = a["memory"].get("fuzzy") or {}
        fixed = 0
        rec = a["memory"]["recent"]
        for wrong, true in list(fz.items()):
            if wrong not in rec:
                del fz[wrong]
                continue
            helper = next((h for h in helper_ids if h != cid and h in w.agents and true in w.agents[h]["memory"]["recent"]
                           and a["aff"].get(h, 0) >= -3), None)
            if helper and self.rng.random() < p:
                rec[rec.index(wrong)] = true + f" (set straight by {self.nm(helper)})"
                del fz[wrong]
                fixed += 1
        return fixed

    def observe_movement(self, tick, hour):
        """People who are standing in a room when someone passes through it see them; people who cross paths pass each other."""
        w = self.world
        moves = {c: m for c, m in tick["moves"].items() if c in w.agents}
        for x, mx in moves.items():
            path = mx["path"]
            if len(path) < 3:
                continue
            for i in range(1, len(path) - 1):
                room = path[i]
                for y, a in w.agents.items():
                    if y == x:
                        continue
                    stays = (y not in moves or moves[y]["to"] == moves[y]["from"]) and a["room"] == room
                    if stays:
                        self.witness(y, {"type": "pass", "who": x, "room": room, "to": path[i + 1], "hour": hour})
        ids = list(moves)
        for i, x in enumerate(ids):
            for y in ids[i + 1:]:
                px, py = moves[x]["path"], moves[y]["path"]
                if len(px) < 2 and len(py) < 2:
                    continue
                crossed = None
                for u, v in zip(px, px[1:]):
                    for u2, v2 in zip(py, py[1:]):
                        if u == v2 and v == u2:
                            crossed = (u, v)
                shared = [r for r in px[1:-1] if r in py[1:-1]]
                if crossed or shared:
                    where = (crossed[0] if crossed else shared[0])
                    self.witness(x, {"type": "pass", "who": y, "room": where, "to": None, "hour": hour})
                    self.witness(y, {"type": "pass", "who": x, "room": where, "to": None, "hour": hour})

    def mark_busy(self, decisions):
        self.busy = {c for c, d in decisions.items() if d.get("action") in ("search", "experiment", "use", "build", "investigate", "interrogate", "pick", "break", "barricade", "craft")}
