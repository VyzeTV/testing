"""TereVi's dares made checkable, and her torments of participants (plan H4, option 1).

A dare from TereVi's tease (drama.py) now carries a task the engine can judge, with a deadline a few hours on: go to an unpleasant room, talk
with someone they avoid, give up something they carry, or confess their secret to the house. Whether they go along with it comes from who they
are (courage, vanity and impulsiveness for, independence and orderliness against); a willing person gets a pull in free time toward the task.
A dare done is rewarded a little. A dare failed is never punished on its own: it is listed for the GM ("failed dare: torment them?"), and the
auto-director may act on it (at most one torment a day).

Torments are only ever set off by the GM (Director action "torment") or the auto-director: a humiliation on air, their secret on every screen,
something they treasure taken, a shock collar for the day, or a friend turned against them with a lie. Each costs sanity; people who care about
them are hurt watching. No model calls. TormentMixin is mixed into DayRunner (engine.py).
"""

DARE_ROOMS = ("wine_cellar", "cold_store", "boiler_room", "woods", "maze", "attic", "water_tower")
DARE_KINDS = ("go", "talk", "give_up", "confess")
TORMENTS = ("humiliate", "secret", "taken", "collar", "turned")
DARE_HOURS = 6


def _h2(h):
    return f"{int(h) % 24:02d}:00"


class TormentMixin:
    # ------------------------------------------------------------------ dares
    def dare_set(self, tick, cid, text=""):
        """Give TereVi's dare for `cid` a task the engine can judge. Returns the dare."""
        w, s = self.world, self.s
        a = w.agents[cid]
        kinds = list(DARE_KINDS)
        others = sorted(o for o in w.agents if o != cid)
        carried = sorted(k for k, q in a["inv"].items() if q > 0 and not k.startswith("clothes_") and "key" not in w.item_spec(k).get("tags", []))
        if not others:
            kinds.remove("talk")
        if not carried:
            kinds.remove("give_up")
        if any(k["of"] == cid for c in others for k in w.agents[c]["known_secrets"]) and len(kinds) > 1:
            kinds.remove("confess")                                 # half the house knows already: no bite
        kind = self.rng.choice(kinds)
        now = self.abs_now()
        d = {"who": cid, "kind": kind, "day": self.day, "due": min(now + DARE_HOURS, self.day * 24 + 22), "status": "open", "text": text[:200]}
        if kind == "go":
            d["room"] = self.rng.choice([r for r in DARE_ROOMS if r != a["room"]])
            task = f"go to the {w.room_name(d['room'])}"
        elif kind == "talk":
            d["with"] = min(others, key=lambda o: (a["aff"].get(o, 0), o))
            task = f"sit down and talk with {self.nm(d['with'])}"
        elif kind == "give_up":
            d["item"] = max(carried, key=lambda k: (("weapon" in w.item_spec(k).get("tags", [])) * 2 + k.startswith("acc_"), k))
            task = f"hand the {w.item_name(d['item'])} over to TereVi's hatch"
        else:
            task = "confess their secret to the whole house"
        d["task"] = task
        f = lambda k: self.facet(cid, k)
        d["will"] = round(max(0.05, min(0.95, 0.45 + (f("courage") - 50) / 120 + (f("vanity") - 50) / 200 + (f("impulsiveness") - 50) / 200
                                       - (f("orderliness") - 50) / 250 - (self.value_of(cid, "independence") - 50) / 200)), 2)
        s.setdefault("dares", []).append(d)
        del s["dares"][:-30]
        w.remember(cid, f"TereVi's dare for you: {task}, before {_h2(d['due'] % 24)}.")
        return d

    def value_of(self, cid, k):
        try:
            return self.mind(cid)["values"].get(k, 50)
        except KeyError:
            return 50

    def dare_open(self, cid):
        return next((d for d in reversed(self.s.get("dares") or []) if d["who"] == cid and d["status"] == "open"), None)

    def dare_options(self, tick, cid, hour, m, add):
        """Free time: a willing person feels the pull of their dare."""
        d = self.dare_open(cid)
        if not d or d["kind"] not in ("go", "talk") or not d.get("willing"):
            return
        w = self.world
        if d["kind"] == "go" and w.agents[cid]["room"] != d["room"]:
            add(1.6 + d["will"], "look", room=d["room"], why="TereVi's dare", far=True)
        elif d["kind"] == "talk" and d["with"] in w.agents:
            add(1.6 + d["will"], "chat", room=w.agents[d["with"]]["room"], why="TereVi's dare", partner=d["with"])

    def dare_check(self, tick):
        """At the end of each block: dares done, dares failed. Failed ones wait for the GM or the auto-director."""
        w, s = self.world, self.s
        now = self.abs_now()
        for d in s.get("dares") or []:
            if d["status"] != "open":
                continue
            cid = d["who"]
            if cid not in w.agents:
                d["status"] = "void"
                continue
            if "willing" not in d:
                d["willing"] = self.rng.random() < d["will"]
            a = w.agents[cid]
            done = False
            if d["kind"] == "go":
                done = a["room"] == d["room"] or any(sg.get("room") == d["room"] for sg in (tick.get("free") or {}).get(cid, []))
            elif d["kind"] == "talk":
                done = any(cid in (g.get("members") or []) and d["with"] in (g.get("members") or []) for g in tick.get("talk") or [])
            elif d["kind"] == "give_up" and d["willing"]:
                if a["inv"].get(d["item"], 0) > 0:
                    a["inv"][d["item"]] -= 1
                    if a["inv"][d["item"]] <= 0:
                        del a["inv"][d["item"]]
                    pool = s["room_items"].setdefault("laundry", {})
                    pool[d["item"]] = pool.get(d["item"], 0) + 1
                done = True
            elif d["kind"] == "confess" and d["willing"]:
                self.reveal_secret(tick, cid, cid, sorted(w.agents), how="confesses")
                done = True
            if done:
                d["status"] = "done"
                self.stat(tick, cid, "sanity", 3, "did TereVi's dare")
                self.log_event(tick, {"type": "tease", "who": cid, "room": a["room"], "vis": "public",
                                      "text": f"{self.nm(cid)} did TereVi's dare ({d['task']}). TereVi applauds, slowly."}, witnesses=list(w.agents), actor=cid)
            elif now >= d["due"]:
                d["status"] = "failed"
                self.log_event(tick, {"type": "tease", "who": cid, "room": a["room"], "vis": "public",
                                      "text": f"{self.nm(cid)} did not do TereVi's dare ({d['task']}). TereVi says nothing. Yet."}, witnesses=list(w.agents), actor=cid)
                w.remember(cid, "You ignored TereVi's dare. She has not said anything about it. Yet.")

    def dares_failed(self):
        """Failed dares not yet answered, for the GM's Director panel and the auto-director."""
        return [d for d in self.s.get("dares") or [] if d["status"] == "failed" and d["who"] in self.world.agents]

    # ------------------------------------------------------------------ torments
    def torment(self, tick, cid, kind=None, why="the director"):
        """TereVi torments one participant. `kind` one of TORMENTS, or None to let her pick. Returns the kind used, or None."""
        w, s = self.world, self.s
        if cid not in w.agents or s.get("over"):
            return None
        a = w.agents[cid]
        name = self.nm(cid)
        others = sorted(o for o in w.agents if o != cid)
        friends = sorted([o for o in others if w.agents[o]["aff"].get(cid, 0) >= 3 and a["aff"].get(o, 0) >= 2], key=lambda o: (-a["aff"].get(o, 0), o))
        prized = sorted([k for k, q in a["inv"].items() if q > 0 and not k.startswith("clothes_") and "key" not in w.item_spec(k).get("tags", [])],
                        key=lambda k: (-(k.startswith("acc_") * 2 + ("weapon" in w.item_spec(k).get("tags", []))), k))
        secret_known = sum(1 for o in others if any(k["of"] == cid for k in w.agents[o]["known_secrets"]))
        able = [k for k in TORMENTS if not (k == "taken" and not prized) and not (k == "turned" and not friends) and not (k == "secret" and (secret_known >= len(others) or not others))]
        if kind not in able:
            kind = self.rng.choice(able)
        room = a["room"]
        if kind == "humiliate":
            text = self.rng.choice([f"TereVi plays {name}'s worst moments on the island on every screen, slowed down, with a laugh track.",
                                    f"TereVi makes {name} stand on a chair in the Foyer and read out a list of their failings, written by the audience."])
            loss, hp = 8, 0
        elif kind == "secret":
            self.reveal_secret(tick, "terevi", cid, others, how="plays on every screen")
            text = f"Every screen in the house lights up with {name}'s secret. TereVi reads it out twice, in case anyone missed it."
            loss, hp = 10, 0
        elif kind == "taken":
            it = prized[0]
            q = a["inv"].pop(it, 0)
            pool = s["room_items"].setdefault("laundry", {})
            pool[it] = pool.get(it, 0) + q
            text = f"A hatch opens beside {name} and a mechanical arm takes the {w.item_name(it)} away. \"You weren't using it properly, darling.\""
            loss, hp = 6, 0
        elif kind == "collar":
            a["collared"] = self.day
            text = f"TereVi fits {name} with a shock collar for the day, and gives the audience the button."
            loss, hp = 6, 10
        else:
            f_ = friends[0]
            w.adjust_aff(f_, cid, -4)
            w.remember(f_, f"TereVi showed you {name} saying cruel things about you. It looked real.")
            text = f"TereVi shows {self.nm(f_)} a clip of {name} mocking them behind their back. It never happened. {self.nm(f_)} does not know that."
            loss, hp = 6, 0
        self.stat(tick, cid, "sanity", -loss, "TereVi's torment")
        if hp:
            self.stat(tick, cid, "hp", -hp, "the shock collar")
        public = kind != "turned"
        self.log_event(tick, {"type": "torment", "who": cid, "room": room, "vis": "public" if public else "viewer", "kind": kind, "text": text},
                       witnesses=list(w.agents) if public else [friends[0]], actor=cid)
        w.remember(cid, "TereVi tormented you: " + text)
        self.moment(cid, f"TereVi tormented them ({kind})")
        if public:
            for o in others:
                if w.agents[o]["aff"].get(cid, 0) >= 3:
                    self.stat(tick, o, "sanity", -1, f"watching TereVi torment {name}")
        for d in self.dares_failed():
            if d["who"] == cid:
                d["status"] = "tormented"
        s.setdefault("torments", []).append({"day": self.day, "who": cid, "kind": kind, "why": why})
        self.day_notable.append(text[:120])
        return kind

    def torment_auto(self, tick):
        """The auto-director: torment someone who ignored a dare, at most once a day. Returns the kind, or None."""
        s = self.s
        if s.get("torment_day") == self.day:
            return None
        failed = self.dares_failed()
        if not failed:
            return None
        s["torment_day"] = self.day
        return self.torment(tick, failed[0]["who"], None, why="ignored a dare")
