"""Electricity as a way to kill: an appliance dropped into an occupied bath, and a live wire rigged as a trap.

* The bath (planner scheme `shock`): a plotter with something on a cord (a lamp, the tape recorder, an extension cord) waits in the bathroom until the target is in
  the bath or the shower, and drops it in. It is dressed up as an accident (a lamp knocked into the water). It only works while the power is on.
* The live wire (trap kind `shock`, mayhem.py): a cord or wire spliced into the mains and laid where someone will touch it: under the water on a wet floor in a
  bathroom, kitchen, laundry or the boiler room, or on a metal door handle anywhere else. Like any trap it can catch the wrong person.
Either way the current trips the fuses: the lights and cameras die across the house for a while, and everyone notices the time. What it leaves for the trial:
burn marks on the victim's hands and feet, a scorched socket with a spliced cord, the minute the fuses tripped (`fuse` clue at the fuse box in the boiler room), and
sometimes a small burn on the killer's fingers from handling the live wire. A shock that does not kill leaves the victim burned and shaking, and they know who was
there. ElectricMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS

ELECTRIC = ("bedside_lamp", "reading_lamp", "tape_recorder", "extension_cord")          # things on a cord that can go into a bath
LIVE_WIRE = ("extension_cord", "wire", "jump_leads")                                    # what a live-wire trap is made from
WET_ROOMS = {"bathroom", "kitchen", "laundry", "boiler_room", "pool"}
FUSE_ROOM = "boiler_room"


def _hm(hour, m):
    t = int(hour) * 60 + int(m or 0)
    return f"{t // 60 % 24:02d}:{t % 60:02d}"


class ElectricMixin:
    def abs_min(self, hour=None, m=None):
        """Absolute game time in minutes (for things that last part of a block, like a bath)."""
        hour = self.s.get("_hour", 12) if hour is None else hour
        m = (self.minute() or 0) if m is None else m
        return self.day * 1440 + int(hour) * 60 + int(m)

    def bathing(self, cid):
        """Is `cid` in the bath or the shower right now?"""
        a = self.world.agents.get(cid) or {}
        b = a.get("bathing")
        return bool(b and b[0] <= self.abs_min() < b[1] and a.get("room") == b[2])

    def electric_item(self, cid):
        inv = self.world.agents[cid]["inv"]
        return next((k for k in ELECTRIC if inv.get(k, 0) > 0), None)

    # ------------------------------------------------------------------ the bath
    def shock_kill(self, tick, cid, t, hour, intended=None, here=None):
        """`cid` drops something live into `t`'s bath. True if it was tried (it may not kill)."""
        w = self.world
        a, ta = w.agents[cid], w.agents.get(t)
        item = self.electric_item(cid)
        if not ta or not item or not self.power_on() or a["room"] != ta["room"] or not self.bathing(t):
            return False
        room = a["room"]
        here = [o for o in (here if here is not None else w.occupants(room)) if o in w.agents and o not in (cid, t)]
        good, _ = self.roll(cid, 0.8)
        w.drop(cid, item, 1)                                               # it stays in the water: part of the scene
        m = self.minute() or 0
        if good:
            self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "public",
                                  "text": f"{self.nm(cid)} drops the {w.item_name(item)}, still plugged in, into the bath with {self.nm(t)} in it."}, witnesses=here, actor=cid)
            self.open_case(tick, "murder", t, culprit=cid, wkind="shock", weapon=None, room=room, hour=hour, witnesses=here, staged="accident", intended=intended)
            self.electric_clues(self.s.get("case"), room, hour, m, item=item, culprit=cid)
        else:
            self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "public",
                                  "text": f"{self.nm(cid)} drops the {w.item_name(item)} into the bath with {self.nm(t)}; a crack, a scream, and {self.nm(t)} scrambles out alive."},
                           witnesses=here + [t], actor=cid)
            self.stat(tick, t, "hp", -self.rng.randint(15, 30), "an electric shock")
            if t in w.agents:
                self.add_cond(tick, t, "burned", 2, "an electric shock in the bath")
                self.adjust_any_aff(t, cid, -8)
                w.remember(t, f"{_hm(hour, m)} {self.nm(cid)} dropped a live {w.item_name(item)} into your bath. You barely got out. They tried to kill you.")
        self.trip_fuses(tick, hour, m, room)
        return True

    def shock_window(self, tick, cid, t, hour, m, busy):
        """The target has just got into the bath: the plotter walks in with the lamp and does it, if nobody else is there. True if they went."""
        w = self.world
        a, ta = w.agents[cid], w.agents[t]
        room = ta["room"]
        if not (self.bathing(t) and self.electric_item(cid) and self.power_on()) or room not in w.reachable_rooms(cid, 30):
            return False
        if [o for o in w.occupants(room) if o in w.agents and o not in (cid, t)]:
            return False
        nerve = 0.55 + 0.1 * (self.facet(cid, "cruelty") - 50) / 50 + 0.1 * (self.facet(cid, "impulsiveness") - 50) / 50
        if self.rng.random() >= self.gm_roll("strike", self.goal_odds("strike", min(0.9, max(0.3, nerve)), cid, t), cid, t,
                                             f"{self.nm(cid)} walking in on {self.nm(t)} in the bath with a live {w.item_name(self.electric_item(cid))}"):
            return False
        if not self._walk(tick, cid, room, m) or a["room"] != room or not self.bathing(t):
            return False
        p = self.s["plots"][cid]
        self.plan_note(p, f"walked in on {self.nm(t)} in the bath")
        self._slice_m = m
        try:
            self.resolve_attacks(tick, [(cid, {"target": t, "method": "shock", "frame": None, "staged": "accident"})], hour)
        finally:
            self._slice_m = None
        busy[cid] = m + 15
        self._seg(tick, cid, m, m + 15, room, "attack", "attacking")
        p["wait"] = 0
        return True

    # ------------------------------------------------------------------ the live wire
    def live_wire_item(self, cid):
        inv = self.world.agents[cid]["inv"]
        return next((k for k in LIVE_WIRE if inv.get(k, 0) > 0), None)

    def can_rig_shock(self, cid):
        a = self.world.agents[cid]
        return bool(self.live_wire_item(cid) and self.power_on() and ROOMS.get(a["room"], ("", ""))[1] != "grounds")

    def shock_where(self, room):
        return "a live wire under the water on the wet floor" if room in WET_ROOMS else "a door handle wired to the mains"

    def shock_trap_hit(self, tick, t, victim, hour, others, good):
        """A live-wire trap goes off on `victim`. Returns True if it killed."""
        w = self.world
        room = t["room"]
        m = self.minute() or 0
        if good and t["by"] in w.all_agents:
            self.open_case(tick, "murder", victim, culprit=t["by"] if t["by"] in w.agents else None, wkind="trap_shock", weapon=None, room=room, hour=hour,
                           witnesses=others, trap=t, mistaken=(t["target"] is not None and victim != t["target"]))
            self.electric_clues(self.s.get("case"), room, hour, m, item=(t.get("items") or [None])[0], culprit=None)
            self.trip_fuses(tick, hour, m, room)
            return True
        self.log_event(tick, {"type": "mishap", "who": victim, "room": room, "vis": "public",
                              "text": f"{self.nm(victim)} touches {self.shock_where(room)} in the {w.room_name(room)} and is thrown back by the current, alive."}, witnesses=others, actor=victim)
        self.stat(tick, victim, "hp", -self.rng.randint(15, 30), "an electric shock")
        if victim in w.agents:
            self.add_cond(tick, victim, "burned", 2, "an electric shock")
            w.remember(victim, f"{_hm(hour, m)} Someone had wired {self.shock_where(room)} in the {w.room_name(room)}. It was meant to kill.")
        self.trip_fuses(tick, hour, m, room)
        return False

    # ------------------------------------------------------------------ what it leaves
    def trip_fuses(self, tick, hour, m, room):
        """The current trips the fuses: a blackout across the house, and everyone notices the time."""
        w = self.world
        self.blackout_until = max(self.blackout_until, self.idx + 1)
        when = _hm(hour, m)
        self.log_event(tick, {"type": "island", "who": "terevi", "room": FUSE_ROOM, "vis": "public",
                              "text": f"At {when} the lights flicker and die across the house: the fuses have tripped."}, witnesses=list(w.agents))
        for o in w.agents:
            w.remember(o, f"{when} The lights flickered and died across the house: the fuses tripped.")
        st = self.s.setdefault("electric", {})
        st["fuses"] = st.get("fuses", 0) + 1

    def electric_clues(self, case, room, hour, m, item=None, culprit=None):
        """The marks an electrocution leaves for the investigators (and the killer's own small burn)."""
        if not case:
            return
        w = self.world
        v = self.nm(case["victim"])
        cl = [{"room": room, "scene": True, "found_by": [], "kind": "burns",
               "text": f"Burn marks on {v}'s palms and the soles of the feet, the kind a live current leaves where it goes in and out."},
              {"room": room, "scene": True, "found_by": [], "kind": "socket",
               "text": f"A scorched socket in the {w.room_name(room)}" + (f", the {w.item_name(item)}'s plug still in it, blackened." if item else ", with a cord spliced into it.")},
              {"room": FUSE_ROOM, "scene": False, "found_by": [], "kind": "fuse",
               "text": f"In the fuse box the main breaker had tripped; everyone remembers the lights going out at {_hm(hour, m)}."}]
        case["clues"].extend(cl)
        if culprit and culprit in w.agents and self.rng.random() < 0.35:
            self.add_cond(None, culprit, "burned", 1, "handling a live wire")
        st = self.s.setdefault("electric", {})
        st["kills"] = st.get("kills", 0) + 1
