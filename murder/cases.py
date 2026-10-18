"""Deaths, cases, clues, the investigation and the class trial.

The core rule: whoever delivers the killing blow is the one responsible for a death, whether they planned it,
were manipulated or tricked into it, were driven to it, or did it by mistake. Suicides and accidents have no culprit,
but every death still lifts the deadline, haunts the survivors and goes through the same investigation and trial
(the cast may also conclude that nobody is to blame).

Cases are built so that they can be solved by careful investigation, but never by a single glance:
a scene clue, a camera ledger that narrows the suspects without naming them, the history of the weapon or trace item,
what neighbours heard, and (when someone staged the death) a flaw in the staging.
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from .data_world import ROOMS, CAMERA_BLIND
from .llm import LLMError
from .world import clamp, deadline_for_death

BODY_DESC = {
    "sharp": ["lies in a spreading pool of blood, torn open by deep wounds, eyes still wide and fixed on the ceiling",
              "is slumped against the wall, the floor beneath black and wet, both hands still pressed to the wounds that did not stop it",
              "lies where they fell, the blood already tacky, a long smear showing how far they crawled before they stopped"],
    "blunt": ["lies on their side, the skull caved in, a dark halo soaking into the floor",
              "is sprawled face-down, the back of the head split open, one hand still clawing toward the door",
              "lies crumpled and broken, blood and bone in the hair, an expression of pure surprise"],
    "hands": ["lies twisted on the floor, bruises like a necklace around the throat, the tongue swollen and the eyes bulging",
              "is on their back, fingernails broken from clawing, a purple ring of finger marks at the throat"],
    "poison": ["is curled up, lips cracked and flecked with foam, fingers clawed into the sheets, the room sour with vomit",
               "lies rigid, skin grey and slick with sweat, a bitter chemical smell on the breath"],
    "suicide": ["hangs or lies in the aftermath of their own choice, the room terribly quiet",
                "lies still, the last act of a person who decided, with nobody there to stop it"],
    "accident": ["lies broken where the accident left them, limbs bent the wrong way",
                 "lies still at the foot of the danger that took them, the stillness already wrong"],
}
CAUSES = {"trap_fall": "a shattering fall from something that had been tampered with",
          "trap_drink": "agonising poisoning from a tainted drink",
          "trap_blade": "a rigged blade that opened them up",
          "sharp": "deep stab and slash wounds", "blunt": "a fractured skull from a heavy blow",
          "hands": "bruises around the throat", "poison": "froth at the lips and a bitter smell",
          "water": "water in the lungs and bruises on the shoulders where they were held down"}
STAGE_STORY = {"accident": "apparently in a terrible accident", "suicide": "apparently by their own hand"}
STAGE_FLAWS = {
    "accident": ["The 'accident' does not add up: the wound is on the wrong side for the fall it is supposed to come from.",
                 "Whatever caused the 'accident' was tampered with: there are fresh tool marks on it.",
                 "The scene was tidied after the death: scuff marks show the body was moved."],
    "suicide": ["The 'suicide' is wrong: the knot (or the bottle, or the note) was arranged by someone who did not know the victim's habits.",
                "The victim's shoes were put on the wrong feet, as if dressed by someone else.",
                "There are drag marks on the floor, as if the victim was carried here already dead."],
}


def _hh(h):
    return f"{h:02d}:00"


class CaseMixin:
    # ------------------------------------------------------------------ grief and memory
    def body_desc(self, case):
        key = case.get("body_key") or (case.get("method") or "").split(" ")[0]
        if key not in BODY_DESC:
            key = case["kind"] if case["kind"] in BODY_DESC else "sharp"
        return self.rng.choice(BODY_DESC[key])

    @staticmethod
    def close_label(aff):
        return ("very close" if aff >= 6 else "a friend" if aff >= 3 else "an enemy" if aff <= -5 else "an acquaintance")

    def mourn(self, tick, victim, how, hour, weight=1.0):
        """A death of any kind costs the survivors a lot of sanity and is remembered from then on."""
        w, s = self.world, self.s
        vname = self.nm(victim)
        self.death_today = True
        self.note_loss(victim)
        for cid, a in list(w.agents.items()):
            if cid == victim:
                continue
            aff = a["aff"].get(victim, 0)
            loss = 10 if aff > -5 else 4
            if aff >= 6:
                loss = 24
            elif aff >= 3:
                loss = 16
            if any({b["a"], b["b"]} == {cid, victim} and b["kind"] == "romance" for b in s["bonds"]):
                loss += 10
            loss = int(round(loss * weight))
            self.stat(tick, cid, "sanity", -loss, f"mourning {vname}")
            lost = a["memory"].setdefault("lost", [])
            lost.append({"id": victim, "name": vname, "day": self.day, "how": how, "close": self.close_label(aff)})
            del lost[:-8]
            w.remember(cid, f"{_hh(hour)} {vname} is gone ({how}). You will not forget them.")
            if aff >= 3:
                self.moment(cid, f"lost {vname} ({how})")
            if aff >= 6:
                self.fx(tick, "fog", a["room"], cid)

    def lost_lines(self, cid):
        lost = self.world.agents[cid]["memory"].get("lost", [])
        if not lost:
            return ""
        bits = []
        for x in lost[-4:]:
            bits.append(f"{x['name']} (Day {x['day']}, {x['how']}; to you: {x.get('close', 'someone you knew')})")
        return ("THE DEAD YOU CARRY: " + "; ".join(bits) + ". The loss is real: you miss them, blame someone, or are haunted by them, "
                "as suits you, and you bring them up naturally now and then. Never act as if they never existed.")

    # ------------------------------------------------------------------ attacks
    def find_instigator(self, culprit, victim):
        for inc in reversed(self.s.get("incitements", [])):
            if inc["target"] == culprit and inc["victim"] == victim and inc["ttl"] > -4:
                return inc["by"]
        return None

    def resolve_attacks(self, tick, attacks, hour):
        w, s = self.world, self.s
        for cid, d in attacks:
            if cid not in w.agents:
                continue
            a = w.agents[cid]
            name = self.nm(cid)
            if s.get("case"):
                self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm",
                                      "text": f"{name} wanted to attack but a case is already open (TereVi will not allow a second killer)."}, actor=cid)
                continue
            t = d["target"]
            if t in w.agents and t != cid and w.agents[t]["room"] != a["room"] and self.pursue_target(tick, cid, t):
                pass                                    # the attacker caught up with a target who had slipped away
            if t not in w.agents or t == cid or w.agents[t]["room"] != a["room"] or w.agents[t].get("hiding"):
                alt = self.retarget(cid, a)
                if not alt:
                    self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm",
                                          "text": f"{name} planned an attack but the target was not there."}, actor=cid)
                    continue
                self.log_event(tick, {"type": "plot", "who": cid, "room": a["room"], "vis": "viewer",
                                      "text": f"{name} finds the intended victim gone and turns on {self.nm(alt)} instead."}, actor=cid)
                t = alt
            room = a["room"]
            intended = None
            others = [o for o in w.occupants(room) if o in w.agents and o not in (cid, t)]
            if others and self.rng.random() < self.slip_chance(cid) * 0.6:
                intended, t = t, self.rng.choice(others)
                self.log_event(tick, {"type": "system", "who": cid, "room": room, "vis": "gm",
                                      "text": f"{name} is not thinking straight and strikes the WRONG person: {self.nm(t)} instead of {self.nm(intended)}."}, actor=cid)
            method = d["method"] or "hands"
            here = [o for o in w.occupants(room) if o not in (cid, t)]
            if method == "push":
                if self.push_kill(tick, cid, t) is not None:
                    continue
                method = "hands"
            drown = method == "drown" and room in ("pool", "bathroom", "beach", "water_tower")
            if method == "drown":
                method = "hands"
            tname = self.nm(t)
            if self.interrupted(tick, cid, t, here, hour):
                continue
            staged = None
            framed = d.get("frame") if d.get("frame") in w.agents else None
            if method.startswith("poison:"):
                item = method.split(":", 1)[1]
                if a["inv"].get(item, 0) > 0 and "poison" in w.item_spec(item).get("tags", []):
                    self.poison(tick, cid, t, item, here, hour, intended)
                    continue
                method = "hands"
            weapon = None
            if method != "hands":
                if a["inv"].get(method, 0) > 0:
                    weapon = method
                elif s["room_items"].get(room, {}).get(method, 0) > 0 and "weapon" in w.item_spec(method).get("tags", []):
                    w.take(cid, method, 1)
                    self.note_holder(cid, method, hour)
                    weapon = method
            tags = w.item_spec(weapon).get("tags", []) if weapon else []
            kind = "water" if drown else "sharp" if "sharp" in tags else "blunt" if "blunt" in tags else "hands"
            vhp = w.agents[t]["hp"]
            res = self.fight(tick, cid, t, weapon, kind, hour, others=here)     # blow by blow (combat.py)
            good = res["outcome"] == "killed"
            wname = w.item_name(weapon) if weapon else "bare hands"
            if res["scratched"]:
                a["scratched"] = self.day                                  # marks a sharp eye can find
            tick.setdefault("fights", []).append({"by": cid, "on": t, "room": room, "outcome": res["outcome"], "blows": res["blows"]})
            instig = self.find_instigator(cid, t)
            dark = self.blackout_until >= self.idx          # in the dark nobody without a light sees who did it
            seen = here if not dark else [o for o in here if w.agents.get(o, {}).get("lit")]
            if good or vhp - 35 <= 0:
                brutal = {"sharp": f"{name} drives the {wname} into {tname} again and again until {tname} stops moving",
                          "blunt": f"{name} brings the {wname} down on {tname} until the sound changes and {tname} goes limp",
                          "hands": f"{name} wraps their hands around {tname}'s throat and does not let go until the struggling stops",
                          "water": f"{name} holds {tname} under the water until the thrashing stops"}[kind]
                self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "public",
                                      "text": f"{brutal}, in the {w.room_name(room)}."}, witnesses=seen, actor=cid)
                self.log_event(tick, {"type": "fight", "who": cid, "room": room, "vis": "gm", "text": self.fight_text(cid, t, res, wname, kind)})
                if dark:
                    for o in [x for x in here if x not in seen]:
                        w.remember(o, f"{_hh(hour)} (in the dark) You heard a struggle, a gasp and a thud somewhere near you; you could not see who.")
                self.betrayal(tick, cid, t, "murdered")
                self.open_case(tick, "murder", t, culprit=cid, wkind=kind, weapon=weapon, room=room, hour=hour, witnesses=seen,
                               staged=staged, instigator=instig, intended=intended, framed=framed)
                if s.get("case"):
                    s["case"]["wounds"] = res["wounds"]
                    s["case"]["wound_text"] = self.wound_summary(res["wounds"])
                    self.file_set(s["case"], "wounds", s["case"]["wound_text"])
                    s["case"]["killer_scratched"] = bool(res["scratched"])
                also = d.get("also")
                if also in w.agents and also not in (cid, t) and w.agents[also]["room"] == room and s.get("case") and not s.get("spree"):
                    self.double_kill(tick, s["case"], cid, also, kind, wname, hour)
            else:
                if not (w.agents[t].get("asleep") or w.agents[t].get("out")) and self.counter_kill(tick, cid, t, weapon, hour, here):
                    continue
                w.agents[t]["hp"] = max(5, w.agents[t]["hp"])
                w.agents[t].setdefault("harmed_by", []).append([cid, self.day, hour])
                how = {"disarmed": f"{tname} wrestles the {wname} away", "escaped": f"{tname} breaks free and runs", "rescued": f"{tname}'s screams bring people running",
                       "survived": f"{tname} fights them off"}[res["outcome"]] if res["outcome"] in ("disarmed", "escaped", "rescued", "survived") else f"{tname} survives"
                if res["outcome"] == "disarmed" and weapon:
                    w.drop(cid, weapon, 1)
                    w.take(t, weapon, 1)
                elif weapon and self.rng.random() < 0.3:
                    w.drop(cid, weapon, 1)
                if res["outcome"] == "escaped":
                    exits = sorted(e["room"] for e in w.adjacent(t, room) if e["ok"])
                    if exits:
                        w.agents[t]["room"] = self.rng.choice(exits)
                if res["outcome"] == "rescued":
                    self.s.setdefault("_night_noise", {})[room] = 3            # a scream wakes the house
                wounded = ", ".join(sorted({wd["part"] for wd in res["wounds"]}))
                self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "public",
                                      "text": f"{name} attacks {tname} with {wname}, but {how}" + (f" (hurt: {wounded})" if wounded else "") + "!"}, witnesses=here + [t], actor=cid)
                self.log_event(tick, {"type": "fight", "who": cid, "room": room, "vis": "gm", "text": self.fight_text(cid, t, res, wname, kind)})
                w.adjust_aff(t, cid, -5)
                for o in here:
                    w.adjust_aff(o, cid, -3)
                w.remember(t, f"{_hh(hour)} (private) {name} tried to kill you with {wname}.")
                self.moment(t, f"{name} tried to kill you")
                self.betrayal(tick, cid, t, "tried to kill")
                s["plots"].pop(cid, None)

    def lethal_blow(self, tick, cid, t, weapon, hour):
        """An assault that goes too far: the one who lands the final blow is the culprit, intended or not."""
        w, s = self.world, self.s
        if s.get("case") or not self.murders:
            return False
        a = w.agents[cid]
        room = a["room"]
        here = [o for o in w.occupants(room) if o not in (cid, t)]
        tags = w.item_spec(weapon).get("tags", []) if weapon else []
        kind = "sharp" if "sharp" in tags else "blunt" if "blunt" in tags else "hands"
        name, tname = self.nm(cid), self.nm(t)
        wname = w.item_name(weapon) if weapon else "bare hands"
        dark0 = self.blackout_until >= self.idx
        self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "public",
                              "text": f"{name}'s blow lands badly: {tname} goes down and does not get up. It was only meant to hurt."},
                       witnesses=[] if dark0 else here, actor=cid)
        dark = self.blackout_until >= self.idx
        if not dark:
            self.betrayal(tick, cid, t, "killed")
        self.open_case(tick, "manslaughter", t, culprit=cid, wkind=kind, weapon=weapon, room=room, hour=hour, witnesses=[] if dark else here,
                       instigator=self.find_instigator(cid, t), aware=not dark)
        return True

    # ------------------------------------------------------------------ opening a case
    def new_case(self, kind, victim, culprit, room, hour, witnesses, **kw):
        case = {"victim": victim, "killer": culprit, "kind": kind, "method": "", "cause": "", "weapon": None, "room": room,
                "day": self.day, "hour": hour, "witnesses": list(witnesses), "discovered_by": [], "announced": False,
                "announce_day": None, "announce_hour": None, "vote_day": None, "vote_hour": None, "poison_pending": False,
                "resolved": False, "clues": [], "file": [], "staged": None, "instigator": None, "intended": None}
        case.update(kw)
        return case

    def herring_clues(self, case):
        """Other people had reasons too: whoever quarrelled with the victim, hated them or was seen watching them points the investigators somewhere else. They are true, which is what makes them hard to dismiss."""
        w, s = self.world, self.s
        victim, culprit, hour = case["victim"], case["killer"], case["hour"]
        vn = self.nm(victim)
        out, seen = [], set()
        now = self.day * 24 + hour
        for e in reversed(s.get("chronicle", [])[-400:]):
            if len(out) >= 3:
                break
            if e["type"] not in ("friction", "tease", "assault", "betrayal", "plot") or victim not in ([e.get("who")] + list(e.get("with", []))):
                continue
            who = [c for c in ([e.get("who")] + list(e.get("with", []))) if c in w.agents and c not in (victim, culprit)]
            if not who or who[0] in seen or (now - (e["day"] * 24 + e["hour"])) > 30:
                continue
            seen.add(who[0])
            room = e.get("room") if e.get("room") in w.cast.get(victim, {}).get("rooms", []) or e.get("room") else "foyer"
            kindtxt = "had a bitter row with" if e["type"] in ("friction", "tease") else "was seen going for" if e["type"] == "assault" else "was heard making threats about"
            out.append({"room": room if room in ROOMS else "foyer", "scene": False, "found_by": [], "kind": "herring", "text": f"{self.nm(who[0])} {kindtxt} {vn} in the day before the death."})
        for c, a in w.agents.items():
            if len(out) >= 3 or c in seen or c in (victim, culprit):
                continue
            if a["aff"].get(victim, 0) <= -4 and self.rng.random() < 0.7 / max(0.4, self.tune("clue_clarity") + 0.2):
                seen.add(c)
                out.append({"room": "foyer", "scene": False, "found_by": [], "kind": "herring", "text": f"Several people know {self.nm(c)} could not stand {vn}."})
        return out

    def provenance_text(self, item, culprit):
        return self.provenance_base(item, culprit) + self.crafted_hint(item)

    def provenance_base(self, item, culprit):
        log = self.s.get("item_log", {}).get(item) or []
        chain = [(c, d, h) for c, d, h in log if c in self.world.cast]
        if culprit and chain and self.rng.random() < 0.45:
            while chain and chain[-1][0] == culprit:
                chain.pop()                               # sometimes the last link is missing, never the whole chain
        if chain and culprit and all(c == culprit for c, _, _ in chain) and self.rng.random() < 0.6:
            return " Nobody can say who last held it."
        if not chain:
            return ""
        seen, out = set(), []
        for c, d, h in reversed(chain):
            if c in seen:
                continue
            seen.add(c)
            out.append(f"{self.nm(c)} (Day {d})")
            if len(out) >= 3:
                break
        return " People who handled it before: " + ", ".join(reversed(out)) + "."

    def ledger_clues(self, room, culprit, victim, hour, positions=None, label=""):
        """The camera archive (only NeoVi can show it to anyone: evidence.py) and the bedroom door-lock log (the locked Study): together they narrow the field without naming the killer.
        Getting the door log takes a key, so the cast has to cooperate with whoever can open the Study."""
        w = self.world
        dark = self.blackout_until >= self.idx
        pos = positions or {c: a["room"] for c, a in w.agents.items()}
        people = [c for c in pos if c != victim and c in w.cast]
        cam, door, missing = {}, {}, []
        for c in people:
            r = pos[c]
            if not positions and (c == culprit or r == room):
                missing.append(c)
            elif r == w.cast[c]["home"] and self.rng.random() < 0.9:
                door[c] = r
            elif r not in CAMERA_BLIND and not dark and self.rng.random() < 0.85:
                cam[c] = r
            else:
                missing.append(c)
        if not positions:
            target = 3 if len(people) <= 6 else self.rng.choice([3, 4])
            movable = [c for c in list(cam) + list(door) if c != culprit]
            self.rng.shuffle(movable)
            while len(missing) < target and movable:
                c = movable.pop()
                cam.pop(c, None)
                door.pop(c, None)
                missing.append(c)
        rn = w.room_name
        if dark:
            cam_txt = f"The camera archive for {_hh(hour)}{label} is blank: the cameras were dead, so nobody can be placed on camera."
        else:
            on = ", ".join(f"{self.nm(c)} ({rn(r)})" for c, r in cam.items()) or "nobody"
            cam_txt = (f"Camera archive for {_hh(hour)}{label}: seen on camera elsewhere: {on}. Not placed by the cameras: "
                       f"{', '.join(self.nm(c) for c in missing + list(door)) or 'nobody'}"
                       + (f" (the camera covering the {rn(room)} 'glitched' at that moment)" if room not in CAMERA_BLIND and not positions else "")
                       + ".")
        door_txt = (f"Door-lock log (Study) for {_hh(hour)}{label}: " + (", ".join(f"{self.nm(c)} behind their own bedroom door ({rn(r)})" for c, r in door.items())
                                                                         or "no bedroom door was in use") + ".")
        clues = [{"room": "neovi", "scene": True, "found_by": [], "text": cam_txt, "kind": "ledger"},      # only NeoVi can show it (evidence.py)
                 {"room": "study", "scene": True, "found_by": [], "text": door_txt, "kind": "ledger_door"}]
        return clues, {"cam": cam, "door": door, "missing": missing}

    def build_clues(self, case, tick):
        w, s = self.world, self.s
        victim, culprit, room, hour = case["victim"], case["killer"], case["room"], case["hour"]
        vname = self.nm(victim)
        clues = []
        shown = case["cause"]
        scene_txt = (f"{vname} is dead: {shown}." if case["kind"] in ("suicide", "accident") else f"{vname} is dead, with {shown}.")
        clues.append({"room": room, "scene": True, "found_by": [], "kind": "scene",
                      "text": f"{scene_txt} Time of death: around {_hh(hour)} on Day {self.day}."})
        weapon = case.get("weapon")
        if weapon and (culprit is None or self.rng.random() < 0.65):
            pool = s["room_items"].setdefault(room, {})
            pool[weapon] = pool.get(weapon, 0) + 1
            clues.append({"room": room, "scene": True, "found_by": [], "kind": "weapon",
                          "text": f"A {w.item_name(weapon)}, freshly stained, lies near the body." + self.provenance_text(weapon, culprit)})
            if culprit and w.agents[culprit]["inv"].get(weapon, 0) > 0:
                w.drop(culprit, weapon, 1)
        if culprit:
            slip = self.slip_chance(culprit)
            trace_pool = [k for k in w.agents[culprit]["inv"] if k != weapon and not set(w.item_spec(k).get("tags", [])) & {"key", "secret", "weapon"}]
            if trace_pool and self.rng.random() < 0.4 + 0.5 * slip:
                tr = self.rng.choice(trace_pool)
                w.drop(culprit, tr, 1)
                clues.append({"room": room, "scene": True, "found_by": [], "kind": "trace",
                              "text": f"Something was dropped near the body: {w.item_name(tr)}." + self.provenance_text(tr, culprit)})
                case["trace"] = tr
        harmed = [x for x in w.all_agents[victim].get("harmed_by", []) if x[1] >= self.day - 2]
        if harmed:
            clues.append({"room": room, "scene": True, "found_by": [], "kind": "bruises",
                          "text": f"Older bruises on the body show {vname} was beaten earlier (Day {harmed[-1][1]}), before this death."})
        cl, st = self.ledger_clues(room, culprit, victim, hour)
        clues.extend(cl)
        case["ledger"] = st
        clues.extend(self.forensic_clues(case, tick))
        trap = case.get("trap")
        if trap:
            cl2, _ = self.ledger_clues(trap["room"], None, victim, trap["hour"], positions=trap["ledger"], label=" when the trap was set")
            clues.extend(cl2)
            what = {"fall": "Fresh tool marks show the footing was deliberately loosened before it gave way.",
                    "drink": "A bottle in the room was recently re-corked; the dregs smell wrong.",
                    "blade": "A wire-and-blade mechanism was hidden at the doorway, strung by someone patient."}[trap["kind"]]
            prov = self.provenance_text(trap["items"][0], culprit) if trap["items"] and trap["items"][0] in self.s.get("item_log", {}) else ""
            clues.append({"room": trap["room"], "scene": True, "found_by": [], "kind": "tamper", "text": what + prov})
        innocents = [c for c in w.agents if c not in (culprit, victim)]
        self.rng.shuffle(innocents)
        made = 0
        for c in innocents:
            if not culprit or made >= 2 or self.rng.random() > (0.6 if made == 0 else 0.3):
                continue
            pool_ = [k for k in w.agents[c]["inv"] if not set(w.item_spec(k).get("tags", [])) & {"key", "secret", "weapon"}]
            if pool_:
                it = self.rng.choice(pool_)
                clues.append({"room": room, "scene": True, "found_by": [], "kind": "decoy",
                              "text": f"Near the doorway lies a {w.item_name(it)} that several people remember seeing {self.nm(c)} with earlier."})
                made += 1
        if case.get("staged") and culprit:
            clues.append({"room": room, "scene": True, "found_by": [], "kind": "staging",
                          "text": self.rng.choice(STAGE_FLAWS[case["staged"]])})
        if case["kind"] == "suicide":
            note = case.get("note") or "I can't keep doing this."
            clues.append({"room": room, "scene": True, "found_by": [], "kind": "note",
                          "text": f"A note in {vname}'s own handwriting: \"{note[:140]}\" There is no sign of a struggle."})
        elif case["kind"] == "accident":
            clues.append({"room": room, "scene": True, "found_by": [], "kind": "accident",
                          "text": f"The scene is consistent with an accident: {case.get('detail', 'a fall, a slip, a bad moment')}. Nothing suggests anyone else's hand."})
        case["clues"] = clues

    def hearsay(self, case, culprit, room, hour):
        """Neighbours hear the commotion; some glimpse a figure."""
        w = self.world
        if not culprit:
            return
        gender = "man" if w.cast[culprit]["gender"] == "male" else "woman"
        for n in w.adjacent("neovi", room):
            for o in w.occupants(n["room"], include_npcs=False):
                if o in w.agents and o != culprit and self.rng.random() < 0.5:
                    extra = f" and glimpsed a {gender} hurrying away" if self.rng.random() < 0.5 else ""
                    w.remember(o, f"{_hh(hour)} You heard a crash and a cry from the {w.room_name(room)}{extra}.")

    def open_case(self, tick, kind, victim, culprit=None, wkind=None, weapon=None, room=None, hour=None, witnesses=None,
                  cause=None, staged=None, instigator=None, intended=None, note=None, detail=None, aware=True, framed=None, trap=None, mistaken=False, self_defense=False, aggressor=None):
        """Create the case for a death. kind: murder | manslaughter | suicide | accident."""
        w, s = self.world, self.s
        hour = self.s.get("_hour", 12) if hour is None else hour
        room = room or w.agents[victim]["room"]
        witnesses = [x for x in (witnesses or []) if x in w.agents and x not in (victim, culprit)]
        witnesses = self.lookout_filter(culprit, victim, witnesses)
        vname = self.nm(victim)
        true_cause = cause or CAUSES.get(wkind or "hands", CAUSES["hands"])
        shown = f"{STAGE_STORY[staged]}: {true_cause}" if staged else true_cause
        if kind == "suicide":
            shown = f"by their own hand ({true_cause})"
        if staged == "suicide":
            shown = "apparently self-inflicted wounds"
        elif staged == "accident":
            shown = "what looks like a nasty accident"
        desc = ("drowning" if wkind == "water" else f"{wkind} ({w.item_name(weapon) if weapon else 'bare hands'})" if wkind in ("sharp", "blunt", "hands")
                else (true_cause if (kind in ("suicide", "accident") or trap) else str(wkind)))
        case = self.new_case(kind, victim, culprit, room, hour, witnesses, method=desc, cause=shown, true_cause=true_cause, weapon=weapon,
                             staged=staged, instigator=instigator, intended=intended, note=note, detail=detail, culprit_aware=aware,
                             trap=trap, mistaken=mistaken, self_defense=self_defense, aggressor=aggressor, body_key={"trap_fall": "blunt", "trap_drink": "poison", "trap_blade": "sharp"}.get(wkind))
        case["m"] = round(self.minute() or 0.0, 1)                     # the minute of the turn it happened (testimony asks about that moment)
        self.build_clues(case, tick)
        if culprit and culprit in w.agents:
            case["clues"].extend(self.clothes_clue(case))
            self.stain_clothes(culprit)
        if culprit and kind == "murder":
            case["clues"].extend(self.herring_clues(case))
        if culprit:
            self.tally(culprit, "kills")
            self.accomplice_cleanup(case, culprit)
        if self_defense:
            case["clues"].append({"room": room, "scene": True, "found_by": [], "kind": "struggle",
                                  "text": f"Signs of a violent struggle: it looks as if {vname} attacked first, and whoever survived was hurt in the fight."})
        if culprit and framed and framed in w.agents and framed not in (culprit, victim):
            pool_ = [k for k in w.agents[framed]["inv"] if not set(w.item_spec(k).get("tags", [])) & {"key", "secret"}]
            if pool_ and self.roll(culprit, 0.6)[0]:
                it = self.rng.choice(pool_)
                case["clues"].append({"room": room, "scene": True, "found_by": [], "kind": "planted", "by": culprit,
                                      "text": f"At the scene lies a {w.item_name(it)} that several people recall {self.nm(framed)} carrying."})
                w.remember(culprit, f"{_hh(hour)} (private) You planted something of {self.nm(framed)}'s to point the finger at them.")
        self.make_case_file(case, vname, room, shown, hour)               # TereVi's Case File (evidence.py)
        if culprit:
            self.neovi_observe_case(case, culprit, room, hour)
        w.agents[victim]["hp"] = 0
        how = {"murder": "murdered", "manslaughter": "killed", "suicide": "took their own life", "accident": "died in an accident"}[kind]
        w.end_agent(victim, "dead", how)
        s["case"] = case
        self.chron_death(tick, case, desc, shown)
        self.env_scene_marks(case)
        s["deadline_day"] = deadline_for_death(self.day, s.get("week_len", 7))
        for inc in s.get("incitements", []):
            inc["ttl"] = min(inc["ttl"], -5)
        if culprit and aware:
            lines = {"murder": f"You killed {vname} with {desc} in the {w.room_name(room)}. Witnesses: {', '.join(self.nm(x) for x in witnesses) or 'nobody'}.",
                     "manslaughter": f"You did not mean to, but {vname} is DEAD by your hand ({desc}) in the {w.room_name(room)}. Witnesses: {', '.join(self.nm(x) for x in witnesses) or 'nobody'}."}
            w.remember(culprit, f"{_hh(hour)} (private) {lines[kind]}")
            w.agents[culprit]["sanity"] = clamp(w.agents[culprit]["sanity"] - (6 if kind == "murder" else 20))
            self.moment(culprit, f"killed {vname}" + ("" if kind == "murder" else " by accident"))
            if instigator:
                w.remember(culprit, f"{_hh(hour)} (private) {self.nm(instigator)} had been working on you before this happened.")
            if intended:
                w.remember(culprit, f"{_hh(hour)} (private) You meant to hit {self.nm(intended)}, not {vname}.")
            self.hearsay(case, culprit, room, hour)
        if culprit:
            kind_tell = "looked pale and kept wiping their hands" if aware else "seemed shaken and strangely absent"
            w.agents[culprit]["tell"] = {"text": kind_tell, "until": self.day * 24 + hour + 6}
        if culprit and not aware:
            w.remember(culprit, f"{_hh(hour)} (private) Something went badly wrong around {vname}, but you are not sure what.")
        for o in witnesses:
            w.agents[o]["sanity"] = clamp(w.agents[o]["sanity"] - 10)
        if kind in ("suicide", "accident"):
            for o in witnesses:
                w.remember(o, f"{_hh(hour)} You saw {vname} die ({how}).")
            self.log_event(tick, {"type": "attack", "who": victim, "room": room, "vis": "public",
                                  "text": f"{vname} {how} in the {w.room_name(room)}."}, witnesses=witnesses, actor=None)
        self.fx(tick, "shake", room, victim)
        self.day_notable.append(f"{vname} {how} in the {w.room_name(room)}.")
        self.s["plots"].pop(culprit, None) if culprit else None
        sp_ = s.get("spree")
        if sp_ and kind in ("murder", "manslaughter") and (not self.crime_on() or culprit == sp_["by"] or (victim == sp_["by"] and sp_.get("kills", 0) >= 1)):
            case["spree"] = True
            self.spree_death(tick, hour)
        elif sp_ and victim == sp_["by"] and self.crime_on():
            s["spree"] = None                           # the one who 'snapped' never killed anyone and was killed: an ordinary murder, so an ordinary trial
            self.log_event(tick, {"type": "system_notable", "who": culprit, "room": room, "vis": "public", "text": f"The frenzy around {self.nm(victim)} ends with their death."}, actor=culprit)
        return case

    def poison(self, tick, cid, target, item, here, hour, intended=None):
        w, s = self.world, self.s
        a = w.agents[cid]
        room = a["room"]
        a["inv"][item] -= 1
        if a["inv"][item] <= 0:
            del a["inv"][item]
        name, tname = self.nm(cid), self.nm(target)
        case = self.new_case("murder", target, cid, None, hour, [], method=f"poison ({w.item_name(item)})", cause=CAUSES["poison"], true_cause=CAUSES["poison"],
                             weapon=item, poison_pending=True, poisoned_in=room, intended=intended,
                             instigator=self.find_instigator(cid, target))
        cl, st = self.ledger_clues(room, cid, target, hour)
        case["clues"].extend(cl)
        case["ledger"] = st
        if self.rng.random() < 0.5:
            pool = s["room_items"].setdefault(room, {})
            pool[item] = pool.get(item, 0) + 1
            case["clues"].append({"room": room, "scene": True, "found_by": [], "kind": "weapon",
                                  "text": f"An empty {w.item_name(item)} was left in the {w.room_name(room)}." + self.provenance_text(item, cid)})
        s["case"] = case
        self.add_cond(tick, target, "poisoned", 2, "something in their food or drink", turns=12)
        self.log_event(tick, {"type": "attack", "who": cid, "room": room, "vis": "gm",
                              "text": f"{name} secretly poisons {tname} with the {w.item_name(item)}. {tname} will collapse tonight."}, actor=cid)
        w.remember(cid, f"{_hh(hour)} (private) You poisoned {tname} with the {w.item_name(item)}; they will die tonight.")
        for o in here:
            if o in w.agents and self.rng.random() < 0.3:
                w.remember(o, f"{_hh(hour)} You noticed {name} fiddling with {tname}'s food or drink.")
        w.agents[cid]["sanity"] = clamp(w.agents[cid]["sanity"] - 4)
        s["plots"].pop(cid, None)

    def finish_poison(self, tick):
        """At night the poison takes effect: the victim dies in their bed."""
        w, s = self.world, self.s
        case = s.get("case")
        if not (case and case.get("poison_pending")):
            return
        v = case["victim"]
        home = w.cast[v]["home"]
        w.all_agents[v]["room"] = home
        w.all_agents[v]["hp"] = 0
        w.end_agent(v, "dead", "was poisoned")
        case["room"] = home
        case["poison_pending"] = False
        case["day"], case["hour"] = self.day, 22
        self.make_case_file(case, self.nm(v), home, case["cause"], 22, time_text="during the night; the poison was taken hours earlier")
        case["clues"].insert(0, {"room": home, "scene": True, "found_by": [], "kind": "scene",
                                 "text": f"{self.nm(v)} is dead in bed, with {case['cause']}. Time of death: during the night."})
        s["deadline_day"] = deadline_for_death(self.day, s.get("week_len", 7))
        for inc in s.get("incitements", []):
            inc["ttl"] = min(inc["ttl"], -5)
        tick["events"].append({"type": "system", "who": v, "room": home, "vis": "gm",
                               "text": f"{self.nm(v)} collapses and dies in the night from the poison."})
        self.day_notable.append(f"{self.nm(v)} died in the night.")

    def finish_internal(self, tick):
        """Someone beaten badly earlier may die in the night of an injury nobody knew was fatal; the one who beat them does not know."""
        w, s = self.world, self.s
        if s.get("case"):
            return
        for v, a in list(w.agents.items()):
            inj = a.get("internal")
            if not inj:
                continue
            a.pop("internal", None)
            if a["hp"] >= 20 or inj["by"] not in w.agents:
                continue
            home = w.cast[v]["home"]
            a["room"] = home
            tags = w.item_spec(inj.get("weapon")).get("tags", []) if inj.get("weapon") else []
            kind = "sharp" if "sharp" in tags else "blunt" if "blunt" in tags else "hands"
            self.open_case(tick, "manslaughter", v, culprit=inj["by"], wkind=kind, weapon=None, room=home, hour=22, witnesses=[],
                           cause="internal bleeding from a beating earlier", aware=False)
            return

    # ------------------------------------------------------------------ accidents and suicide
    def accident_death(self, tick, cid, cause, detail=None):
        w, s = self.world, self.s
        if s.get("case") or cid not in w.agents:
            return False
        a = w.agents[cid]
        pushed = self.__dict__.get("_pushed_by")
        if pushed and pushed[0] == cid and pushed[1] in w.agents:
            # not an accident: they were pushed (the people who saw the shove are the witnesses)
            self.open_case(tick, "murder", cid, culprit=pushed[1], wkind="blunt", room=a["room"], hour=tick["hour"], witnesses=pushed[2])
            return True
        here = [o for o in w.occupants(a["room"]) if o != cid]
        self.open_case(tick, "accident", cid, room=a["room"], hour=tick["hour"], witnesses=here, cause=cause, detail=detail or cause)
        return True

    HAZARD_ROOMS = {"lookout": "fell from the railing", "water_tower": "fell from the walkway", "pool": "drowned in the pool",
                    "boiler_room": "was scalded in the boiler room", "wine_cellar": "slipped on the cellar steps",
                    "attic": "fell through the rotten attic floor", "lighthouse": "fell on the broken lighthouse stairs"}

    def hazard_check(self, tick, hour):
        """People who are hurt, exhausted or out of their mind have accidents in dangerous places."""
        w, s = self.world, self.s
        if s.get("case") or not self.murders:
            return
        for cid, a in list(w.agents.items()):
            cause = self.HAZARD_ROOMS.get(a["room"])
            if not cause:
                continue
            risk = max(0, 25 - a["hp"]) / 25 * 0.10 + max(0, 15 - a["sanity"]) / 15 * 0.05
            if risk > 0 and self.rng.random() < risk * self.chaos_factor():
                self.accident_death(tick, cid, cause, detail=f"{self.nm(cid)} {cause}, weakened and not thinking straight")
                return

    def resolve_end_lives(self, tick, hour):
        w, s = self.world, self.s
        lives, self.end_lives = self.end_lives, []
        for cid, d in lives:
            if cid not in w.agents or s.get("case"):
                continue
            a = w.agents[cid]
            name = self.nm(cid)
            drive = a["drive"]["id"]
            dread = self.dread_level()
            p = 0.1 + max(0, 35 - a["sanity"]) / 35 * 0.5
            if drive == "martyr" and dread >= 3:
                p += 0.35
            if drive == "nihilist":
                p += 0.2
            if self.days_left() <= 0:
                p += 0.15
            if self.rng.random() >= min(0.9, p):
                self.log_event(tick, {"type": "madness", "who": cid, "room": a["room"], "vis": "public",
                                      "text": f"{name} stands at the edge of something terrible, shaking, and steps back."},
                               witnesses=[o for o in w.occupants(a["room"]) if o != cid], actor=cid)
                self.stat(tick, cid, "sanity", -3, "almost ended it")
                self.moment(cid, "came close to ending it all")
                continue
            here = [o for o in w.occupants(a["room"]) if o in w.agents and o != cid]
            savers = [o for o in here if a["aff"].get(o, 0) >= 0 and w.agents[o]["aff"].get(cid, 0) >= 2 and self.rng.random() < 0.65]
            if savers:
                sv = savers[0]
                self.log_event(tick, {"type": "mercy", "who": sv, "room": a["room"], "vis": "public",
                                      "text": f"{self.nm(sv)} talks {name} down at the last second."}, witnesses=here, actor=sv)
                self.special_boost(tick, cid, 4, "talked down by a friend", "comfort")
                self.adjust_any_aff(cid, sv, 3)
                self.moment(cid, f"{self.nm(sv)} stopped you from ending it")
                self.moment(sv, f"talked {name} out of suicide")
                continue
            method = (d.get("method") or "").strip()[:40]
            cause = method or "took their own life"
            note = d.get("thought") or ""
            sacrifice = drive == "martyr" and dread >= 2
            if sacrifice:
                note = (note + " This way the rest of you live.").strip()
            self.open_case(tick, "suicide", cid, room=a["room"], hour=hour, witnesses=here, cause=f"{cause}", note=note)
            self.s["case"]["sacrifice"] = sacrifice
            return

    # ------------------------------------------------------------------ discovery and announcement
    def reveal_clues(self, tick, cid):
        w, s = self.world, self.s
        case = s.get("case")
        if not case:
            return
        room = w.agents[cid]["room"]
        found = False
        self.found_stained(tick, cid, [k for k in s["room_items"].get(room, {}) if "stained" in self.tags(k)], f"in the {w.room_name(room)}")
        for c in case["clues"]:
            if c.get("kind") in ("weapon", "trace"):
                item = case.get("weapon") if c["kind"] == "weapon" else case.get("trace")
                if item and c["room"] == room and s["room_items"].get(room, {}).get(item, 0) <= 0:
                    continue                      # someone hid it
            if not self.fine_visible(cid, c):
                continue
            if c["room"] == room and cid not in c["found_by"] and (not c["scene"] or cid in case["discovered_by"] or cid == case["killer"] or case["announced"]):
                c["found_by"].append(cid)
                w.remember(cid, f"{_hh(tick['hour'])} CLUE ({w.room_name(room)}): {c['text']}")
                self.note_evidence(cid, "clue", f"({w.room_name(room)}) {c['text']}")
                self.learn_from_clue(tick, c)
                self.log_event(tick, {"type": "clue", "who": cid, "room": room, "vis": "gm", "text": f"{self.nm(cid)} finds a clue: {c['text']}"}, actor=cid)
                self.maybe_withhold_clue(tick, cid, c)
                found = True
        if not found and case["announced"]:
            w.remember(cid, f"{_hh(tick['hour'])} You searched the {w.room_name(room)} and found nothing new.")

    def check_discovery(self, tick, hour):
        w, s = self.world, self.s
        case = s.get("case")
        if not case or case["announced"] or not case.get("room") or case.get("poison_pending"):
            return
        self.wellness_check(tick, hour)
        # whoever walks in first finds it first, at the minute they walk in
        finders = [c for c in w.agents if w.agents[c]["room"] == case["room"]]
        when = {c: self.first_in(c, case["room"]) for c in finders}
        for cid in sorted(finders, key=lambda c: (when[c] if when[c] is not None else 1e9, finders.index(c))):
            if case.get("hidden") and not case["hidden"].get("found"):
                break
            if cid == case["killer"] or cid in case["discovered_by"] or w.agents[cid].get("asleep") or w.agents[cid].get("out"):
                continue
            if w.agents[cid]["room"] == case["room"]:
                case["discovered_by"].append(cid)
                others = [o for o in w.occupants(case["room"]) if o != cid]
                self.log_event(tick, {"type": "body", "who": cid, "room": case["room"], "vis": "public", **({"m": round(when[cid], 1)} if when[cid] is not None and self.minute() is not None else {}),
                                      "text": f"{self.nm(cid)} finds {self.nm(case['victim'])} in the {w.room_name(case['room'])}: {self.nm(case['victim'])} {self.body_desc(case)}."},
                               witnesses=others, actor=cid)
                tick["scene_body"] = {"victim": case["victim"], "by": cid, "room": case["room"], "desc": f"{self.nm(case['victim'])} {self.body_desc(case)}."}
                self.fx(tick, "shake", case["room"], cid)
                self.fx(tick, "dark", case["room"], cid)
                w.agents[cid]["sanity"] = clamp(w.agents[cid]["sanity"] - 6)
                self.maybe_panic(tick, cid, "finding the body", 0.45)
                for c in case["clues"]:
                    if c["room"] == case["room"] and c["scene"] and cid not in c["found_by"]:
                        c["found_by"].append(cid)
                        w.remember(cid, f"{_hh(hour)} CLUE ({w.room_name(case['room'])}): {c['text']}")
                        self.note_evidence(cid, "clue", f"({w.room_name(case['room'])}) {c['text']}")
                        self.maybe_withhold_clue(tick, cid, c)
        if len(case["discovered_by"]) >= 3 and not case["announced"]:
            self.announce_body(tick, hour)
        elif not case["announced"]:
            since = (self.day - case["day"]) * 24 + hour - case["hour"]
            if since >= 12:
                self.announce_body(tick, hour, forced=True)

    def scene_sealed(self, room):
        """The place where the body lies is sealed from the announcement to the trial: nobody may bolt it, barricade it or lock the investigators out."""
        case = self.s.get("case")
        return bool(case and case.get("sealed") and case.get("room") == room and not case.get("resolved"))

    def seal_scene(self, tick, hour):
        """At the announcement NeoVi opens the scene with her master key (unbolting it, taking down any barricade) and TereVi's tape goes across the door."""
        w, s = self.world, self.s
        case = s["case"]
        room = case.get("room")
        if not room:
            return
        opened = []
        if room in s["locks"]:
            del s["locks"][room]
            opened.append("unbolted")
        if room in s["broken"]:
            pass
        for eid, b in list(s.get("blocks", {}).items()):
            e = next((x for x in w.edges if x["id"] == eid), None)
            if e and room in (e["a"], e["b"]):
                del s["blocks"][eid]
                opened.append("cleared")
        case["sealed"] = True
        text = f"NeoVi {'unbolts and clears' if opened else 'opens'} the {w.room_name(room)} with her master key, and TereVi's tape goes across the door: nobody locks it again until the trial."
        self.log_event(tick, {"type": "door", "who": "neovi", "room": room, "vis": "public", "text": text}, witnesses=list(w.agents))
        for cid in w.agents:
            w.remember(cid, f"{_hh(hour)} {text}")

    def wellness_check(self, tick, hour):
        """Somebody who does not turn up for breakfast, lunch or supper is missed: a friend goes to knock, and if the door is locked NeoVi lets them in. Only the killer would not look."""
        w, s = self.world, self.s
        case = s.get("case")
        if not case or case["announced"] or not case.get("room") or hour not in (8, 12, 18):
            return
        if case.get("hidden") and not case["hidden"].get("found"):
            return
        age = (self.day - case["day"]) * 24 + hour - case["hour"]
        if age < 3 or case.get("checked") == (self.day, hour):
            return
        case["checked"] = (self.day, hour)
        victim, room = case["victim"], case["room"]
        cands = [c for c in w.agents if c != case["killer"] and c not in case["discovered_by"] and not w.agents[c].get("out") and not w.agents[c].get("asleep")]
        if not cands:
            return
        finder = max(cands, key=lambda c: (w.agents[c]["aff"].get(victim, 0), self.rng.random()))
        locked = room in s["locks"] or any(e for eid, b in s.get("blocks", {}).items() for e in [next((x for x in w.edges if x["id"] == eid), None)] if e and room in (e["a"], e["b"]))
        mate = next((c for c in cands if c != finder and w.agents[c]["room"] == w.agents[finder]["room"]), None)
        text = f"{self.nm(victim)} did not come to {'breakfast' if hour == 8 else 'lunch' if hour == 12 else 'supper'}. {self.nm(finder)} goes to knock on the {w.room_name(room)}."
        self.log_event(tick, {"type": "door", "who": finder, "room": w.agents[finder]["room"], "vis": "public", "text": text}, witnesses=[o for o in w.occupants(w.agents[finder]["room"]) if o in w.agents], actor=finder)
        if locked:
            s["locks"].pop(room, None)
            for eid in [eid for eid, b in s.get("blocks", {}).items() if (lambda e: e and room in (e["a"], e["b"]))(next((x for x in w.edges if x["id"] == eid), None))]:
                del s["blocks"][eid]
            self.log_event(tick, {"type": "door", "who": "neovi", "room": room, "vis": "public", "text": f"NeoVi, called to the door, opens the {w.room_name(room)} with her master key."}, witnesses=[finder])
        for c in [finder] + ([mate] if mate else []):
            start = w.agents[c]["room"]
            if start != room:
                steps = w.path(c, start, room) or []
                tick["moves"][c] = {"from": start, "path": [start] + [r for r, _, _ in steps], "to": room}
                w.agents[c]["room"] = room

    def announce_body(self, tick, hour, forced=False):
        w, s = self.world, self.s
        case = s["case"]
        if case.get("hidden"):
            case["hidden"]["found"] = True
        if case["killer"] is None:
            # nobody is responsible (an accident or a suicide): no investigation, no trial; TereVi simply informs everyone
            text = self.make_broadcast("death_notice", {"victim": case["victim"], "case_kind": case["kind"], "cause": case["cause"],
                                                        "forced_room": w.room_name(case["room"]) if forced else None})
            tick["broadcasts"].append({"speaker": "terevi", "kind": "verdict", "text": text})
            for cid in w.agents:
                w.remember(cid, f"{_hh(hour)} TereVi announced that {self.nm(case['victim'])} is dead ({case['cause']}). No one is to blame, so there will be no trial. The deadline is lifted.")
                w.agents[cid]["sanity"] = clamp(w.agents[cid]["sanity"] - 4)
            self.mourn(tick, case["victim"], {"suicide": "took their own life", "accident": "died in an accident"}.get(case["kind"], "died"), hour)
            s["vacancies"].append({"gender": w.cast[case["victim"]]["gender"], "reason": f"{w.cast[case['victim']]['name']} left the show"})
            res = f"{self.nm(case['victim'])}'s death was announced: no trial, the deadline is lifted."
            tick["events"].append({"type": "system_notable", "who": case["victim"], "room": case["room"], "vis": "public", "text": res})
            self.day_notable.append(res)
            self.saga(res)
            self.clear_notebooks()
            s["case"] = None
            self.begin_aftermath(tick, hour)
            return
        case["announced"] = True
        if case.get("cf") and case.get("discovered_by"):
            self.file_set(case, "found_by", ", ".join(self.nm(c) for c in case["discovered_by"][:3]), known=True)
        self.seal_scene(tick, hour)
        case["announce_day"], case["announce_hour"] = self.day, hour
        case["vote_day"], case["vote_hour"] = self.day + 1, min(max(hour, 8), 21)
        text = self.make_broadcast("body", {"victim": case["victim"], "vote": self.vote_label(case),
                                            "forced_room": w.room_name(case["room"]) if forced else None})
        tick["broadcasts"].append({"speaker": "terevi", "kind": "body", "text": text})
        for cid in w.agents:
            if forced:
                w.remember(cid, f"{_hh(hour)} TereVi revealed that a body lies in the {w.room_name(case['room'])}.")
            w.remember(cid, f"{_hh(hour)} TereVi announced a body discovery: {self.nm(case['victim'])} is dead and someone is responsible. Class trial at {self.vote_label(case)}. "
                            f"TereVi's file: {' '.join(case['file'])}")
            self.note_evidence(cid, "file", " ".join(case["file"]))
            w.agents[cid]["sanity"] = clamp(w.agents[cid]["sanity"] - 4)
        self.mourn(tick, case["victim"], {"murder": "murdered", "manslaughter": "killed", "suicide": "took their own life",
                                          "accident": "died in an accident"}[case["kind"]], hour)
        for ev in case.get("extra_victims", []):
            self.mourn(tick, ev, "murdered", hour)
        self.alibi_testimonies(case, hour)
        self.ally_alibis(case, hour)
        self.review_knowledge(tick, hour)
        self.day_notable.append(f"A body was announced; the class trial is set for {self.vote_label(case)}.")

    def evidence_text(self, case, limit=12):
        w = self.world
        lines = list(case.get("file", []))
        for c in [x for x in case["clues"] if x["found_by"] and self.clue_on_table(x)][:limit]:
            who = ", ".join(self.nm(x) if x in w.cast else "TereVi" for x in c["found_by"][:3])
            lines.append(f"CLUE (found by {who}): {c['text']}")
        for t in (case.get("testimonies") or [])[-10:]:
            lines.append(f"TESTIMONY ({self.nm(t['by'])}, Day {t['day']} {_hh(t['hour'])}): {t['claim']}" + (" [kept back until pressed]" if t.get("late") else ""))
        return "\n".join(lines)

    def bonus_clue(self, tick, hour):
        case = self.s["case"]
        found = [c for c in case["clues"] if c["found_by"] and self.clue_on_table(c)]
        clar = self.tune("clue_clarity")
        if len(found) >= 3 or clar < 0.3:
            return
        hidden = [c for c in case["clues"] if (not c["found_by"] or not self.clue_on_table(c)) and c.get("kind") in ("ledger", "ledger_door", "tamper", "staging", "note", "accident", "scene", "bruises")]
        hidden.sort(key=lambda c: 0 if c.get("kind") in ("ledger", "ledger_door", "tamper", "staging", "note", "accident") else 1)
        for c in hidden[: 1 if clar < 1.5 else 2]:                       # one free clue, and never one that names the killer outright
            if "terevi" not in c["found_by"]:
                c["found_by"].append("terevi")
            tick["broadcasts"].append({"speaker": "terevi", "kind": "tease",
                                       "text": f"Since you are all so slow, a little gift for the trial: {c['text']}"})
            for cid in self.world.agents:
                self.world.remember(cid, f"{_hh(hour)} TereVi revealed a clue: {c['text']}")
