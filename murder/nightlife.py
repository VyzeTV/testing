"""What people get up to in a sleeping house: snooping and secret meetings.

Snooping: someone with a suspect (caught them lying, was threatened or wronged by them, a hook points at them) stays up and searches that person's
room, or the scene of the death, quietly. They may find clues and hidden things; if the owner is asleep there, they go through their things and
learn what they keep (a `has` belief: "Seul keeps a kitchen knife"). A sleeper may wake and catch them at it.

Secret meetings: lovers, allies, and a plotter with an accomplice agree at bedtime to meet in a quiet, unwatched room in one of the night blocks.
Both stay up, walk there and talk in whispers. Anyone else awake may see them (sightings) or overhear (conversations are overheard as usual).
NightLifeMixin is mixed into DayRunner (engine.py); free time calls `night_options` for every awake person at night.
"""
from .data_world import ROOMS

MEET_ROOMS = ("linen_store", "wine_cellar", "boiler_room", "greenhouse", "observatory", "attic", "lighthouse", "library", "art_studio")
MEET_BLOCKS = (23, 25, 27)
MAX_MEETS = 2


class NightLifeMixin:
    # ------------------------------------------------------------------ who stays up for it (bedtime)
    def night_extra(self, owls):
        """Bedtime: arrange tonight's secret meetings and pick the snoopers. Returns the extra people who stay up."""
        w, s = self.world, self.s
        extra = []
        s["meets"] = []
        pairs = []
        for b in s.get("bonds", []):
            if b.get("kind") == "romance" and b["a"] in w.agents and b["b"] in w.agents:
                pairs.append((0.35, b["a"], b["b"], "lovers"))
        for al in s.get("alliances", []):
            ms = [m for m in al.get("members", []) if m in w.agents]
            if len(ms) >= 2:
                pairs.append((0.2, ms[0], ms[1], "allies"))
        for by, helpers in sorted((s.get("accomplices") or {}).items()):
            for h in helpers:
                if by in w.agents and h.get("helper") in w.agents:
                    pairs.append((0.6, by, h["helper"], "accomplices"))
        rooms = [r for r in MEET_ROOMS if r in ROOMS]
        used = set()
        for p, a, b, why in sorted(pairs, key=lambda x: (-x[0], x[1], x[2])):
            if len(s["meets"]) >= MAX_MEETS or a in used or b in used or not rooms:
                continue
            if any(w.agents[x].get("out") or self.restrained(x) for x in (a, b)) or self.rng.random() >= p:
                continue
            s["meets"].append({"a": a, "b": b, "room": self.rng.choice(rooms), "block": self.rng.choice(MEET_BLOCKS), "why": why, "day": self.day})
            used |= {a, b}
            extra += [x for x in (a, b) if x not in owls and x not in extra]
        for cid in sorted(w.agents):
            if cid in owls or cid in extra or w.agents[cid].get("out"):
                continue
            t = self.snoop_target(cid)
            if t and self.rng.random() < 0.15 + 0.25 * max(0, self.facet(cid, "curiosity") - 40) / 60:
                w.agents[cid]["snoop"] = {"on": t, "day": self.day}
                extra.append(cid)
        return extra

    def snoop_target(self, cid):
        """Whom `cid` would go snooping on: someone they caught lying, a suspect, or someone who threatened or wronged them."""
        w, s = self.world, self.s
        sus = [x for x in self.suspects(cid) if x in w.agents]
        if sus:
            return sus[0]
        for t in s.get("ties", []):
            if t.get("a") == cid and t.get("kind") in ("threatened", "wronged", "betrayed", "slighted") and t.get("b") in w.agents:
                return t["b"]
        a = w.agents[cid]
        hated = sorted((o for o in a["aff"] if o in w.agents and o != cid and a["aff"][o] <= -4), key=lambda o: (a["aff"][o], o))
        return hated[0] if hated else None

    # ------------------------------------------------------------------ during a night block (free time)
    def night_options(self, tick, cid, hour, m, add, sc):
        """Extra choices for someone awake at night: go to (or hold) a secret meeting, or go snooping."""
        w, s = self.world, self.s
        a = w.agents[cid]
        for mt in s.get("meets") or []:
            if mt.get("day") != self.day or mt.get("done") or cid not in (mt["a"], mt["b"]) or int(hour) != mt["block"] or m >= 90:
                continue
            other = mt["b"] if cid == mt["a"] else mt["a"]
            if other not in w.agents:
                continue
            if a["room"] == mt["room"] and w.agents[other]["room"] == mt["room"] and not w.agents[other].get("asleep"):
                mt["done"] = True
                self.log_event(tick, {"type": "meet", "who": cid, "room": mt["room"], "vis": "viewer", "m": float(m),
                                      "text": f"{self.nm(cid)} and {self.nm(other)} meet in secret in the {w.room_name(mt['room'])}."})
                sc.append((6.0, "chat", mt["room"], None, f"a secret meeting ({mt['why']})", other))
            else:
                add(5.0, "look", room=mt["room"], why="a secret meeting")
            return
        sn = a.get("snoop") or {}
        t = sn.get("on")
        if sn.get("day") == self.day and not sn.get("done") and t in w.agents and m < 90:
            case = s.get("case")
            room = w.cast[t].get("home") if not (case and case.get("announced") and not case.get("resolved") and self.rng.random() < 0.3) else case.get("room")
            if room in ROOMS:
                add(3.0 + 0.5 * (self.facet(cid, "curiosity") - 50) / 50, "snoop", room=room, why=f"snooping on {self.nm(t)}")

    def wake_for_meets(self, tick, hour):
        """At the start of a night block: whoever has a secret meeting in it gets out of bed for it."""
        for mt in self.s.get("meets") or []:
            if mt.get("day") == self.day and mt["block"] == int(hour) and not mt.get("done"):
                for c in (mt["a"], mt["b"]):
                    if c in self.world.agents and self.world.agents[c].get("asleep"):
                        self.rouse(tick, c, "a secret meeting")

    def do_snoop(self, tick, cid, m):
        """`cid` searches the room they are in, quietly. They may find clues and hidden things, and if the person they suspect sleeps here,
        they go through their things (and may wake them)."""
        w = self.world
        a = w.agents[cid]
        sn = a.get("snoop") or {}
        sn["done"] = True
        t = sn.get("on")
        room = a["room"]
        self.log_event(tick, {"type": "snoop", "who": cid, "room": room, "vis": "viewer", "m": float(m),
                              "text": f"{self.nm(cid)} searches the {w.room_name(room)} quietly" + (f", looking for something on {self.nm(t)}." if t else ".")})
        self.reveal_clues(tick, cid)
        self.search_for_hidden(tick, cid, "")
        if t not in w.agents or w.agents[t]["room"] != room:
            return None
        ta = w.agents[t]
        found = sorted(k for k in ta["inv"] if {"weapon", "poison"} & set(w.item_spec(k).get("tags", [])))
        tnow = round(self.abs_now() + m / 60, 2)
        for k in found:
            self.believe(cid, {"k": "has", "s": t, "o": k, "n": f"{self.nm(t)} keeps a {w.item_name(k)}", "src": "seen", "c": 0.9, "t0": tnow, "true": True})
            w.remember(cid, f"Going through {self.nm(t)}'s things at night, you found a {w.item_name(k)}.")
        if ta.get("asleep") and self.rng.random() < 0.15 + 0.25 * self.facet(t, "stress_vulnerability") / 100:
            self.rouse(tick, t, "someone in the room", m)
            self.believe(t, {"k": "did", "s": cid, "o": "snoop", "r": room, "t0": tnow, "n": f"{self.nm(cid)} was going through your things", "src": "seen", "c": 0.95, "true": True})
            if cid in ta["aff"]:
                w.adjust_aff(t, cid, -2)
            self.add_tie(t, cid, "wronged", f"caught them going through their things on night {self.day}")
            self.log_event(tick, {"type": "snoop_caught", "who": t, "room": room, "vis": "public", "m": float(m),
                                  "text": f"{self.nm(t)} wakes and catches {self.nm(cid)} going through their things."}, witnesses=[t], actor=cid)
        return found
