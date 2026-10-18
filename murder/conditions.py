"""Afflictions, injuries and unconsciousness.

A character can carry conditions: afflictions (sickness, poison, madness, panic, blindness, breathlessness, dizziness, hunger, thirst, drunkenness, exhaustion, the cold) and injuries (bleeding,
broken arms and legs, whiplash, concussion, weakness, burns, infection, lost body parts). Each has a severity and modifiers: slower movement, clumsier hands, worse eyesight, a chance of fainting,
slow loss of health or sanity. Conditions come from what happens (blows, falls, fire, poison, bad food, fear, hunger) and are healed by time or treatment (bandages, a splint, water, charcoal, rest, comfort).
Someone who is knocked out, faints, is drugged or falls unconscious is helpless: not present in conversations, unable to act, and open to being carried, searched, stripped, cuffed, locked up or framed.
ConditionMixin is mixed into DayRunner (engine.py).
"""
from .data_world import ROOMS

# id: (name, kind, base duration in turns (None = until treated or healed), modifiers per severity level)
# mods: move (speed factor lost), phys (success penalty), atk (attack penalty), sharp (perception penalty), faint (chance per turn), hp (health lost per turn), san (sanity lost per turn),
#       carry (items less), hands (0 = no use of that hand), noisy (stealth penalty), slip (clumsiness)
COND = {
    "sick": ("sick", "affliction", (6, 12), {"phys": 0.08, "hp": 0.5, "san": 0.5, "faint": 0.01, "slip": 0.05}),
    "poisoned": ("poisoned", "affliction", (4, 8), {"phys": 0.1, "hp": 1.5, "san": 1, "faint": 0.04, "slip": 0.1}),
    "deranged": ("out of their mind", "affliction", None, {"phys": 0.05, "sharp": 0.2, "san": 0, "slip": 0.25}),
    "panicking": ("panicking", "affliction", (1, 3), {"phys": 0.15, "faint": 0.04, "slip": 0.3, "noisy": 0.2}),
    "blinded": ("blinded", "affliction", (2, 4), {"phys": 0.2, "sharp": 0.6, "slip": 0.15}),
    "breathless": ("struggling to breathe", "affliction", (2, 5), {"move": 0.2, "phys": 0.1, "faint": 0.05, "noisy": 0.25}),
    "dizzy": ("dizzy", "affliction", (2, 5), {"phys": 0.1, "faint": 0.03, "slip": 0.15, "move": 0.1}),
    "hungry": ("hungry", "affliction", None, {"phys": 0.04, "san": 0.5, "faint": 0.01}),
    "thirsty": ("thirsty", "affliction", None, {"phys": 0.06, "hp": 0.3, "san": 0.3, "faint": 0.02}),
    "drunk": ("drunk", "affliction", (3, 6), {"phys": 0.08, "sharp": 0.15, "slip": 0.2, "noisy": 0.15}),
    "exhausted": ("exhausted", "affliction", (4, 8), {"phys": 0.1, "sharp": 0.1, "slip": 0.1, "faint": 0.01}),
    "chilled": ("chilled to the bone", "affliction", (3, 6), {"phys": 0.1, "hp": 1, "move": 0.1}),
    "bleeding": ("bleeding", "injury", None, {"hp": 2, "faint": 0.03, "phys": 0.05}),
    "broken_arm": ("a broken arm", "injury", None, {"atk": 0.3, "hands": 1, "carry": 8, "phys": 0.1}),
    "broken_leg": ("a broken leg", "injury", None, {"move": 0.35, "phys": 0.1, "noisy": 0.2, "slip": 0.1}),
    "whiplash": ("whiplash", "injury", None, {"phys": 0.08, "sharp": 0.05, "slip": 0.05}),
    "concussion": ("a concussion", "injury", None, {"sharp": 0.15, "faint": 0.03, "slip": 0.15, "phys": 0.05}),
    "weak": ("weak", "injury", None, {"atk": 0.15, "carry": 6, "phys": 0.1}),
    "burned": ("burned", "injury", None, {"hp": 0.7, "phys": 0.08}),
    "infected": ("infected", "injury", None, {"hp": 1, "san": 0.5, "phys": 0.08, "faint": 0.01}),
    "lost_hand": ("lost a hand", "injury", None, {"atk": 0.3, "hands": 1, "carry": 8, "phys": 0.15}),
    "lost_fingers": ("lost some fingers", "injury", None, {"atk": 0.1, "phys": 0.08}),
    "lost_eye": ("lost an eye", "injury", None, {"sharp": 0.2, "atk": 0.05}),
    "lost_foot": ("lost a foot", "injury", None, {"move": 0.45, "phys": 0.1, "noisy": 0.2}),
    "scratched": ("fresh scratches", "injury", (8, 14), {}),
}
PERMANENT = {"lost_hand", "lost_fingers", "lost_eye", "lost_foot", "deranged"}
HEAL_DAYS = {"broken_arm": 6, "broken_leg": 8, "whiplash": 3, "concussion": 2, "weak": 3, "burned": 4}
FOOD_TAGS = {"food"}
DRINK_TAGS = {"drink"}
KNOCKOUT_TURNS = {"knocked out": 2, "fainted": 1, "drugged": 3, "tased": 1, "choked out": 1, "fell": 2, "exhausted": 2, "overcome": 2, "shock": 1}


def _hh(h):
    return f"{int(h):02d}:00"


class ConditionMixin:
    # ------------------------------------------------------------------ the list of conditions
    def conds(self, cid):
        a = self.world.agents.get(cid)
        return a.setdefault("conds", {}) if a else {}

    def has_cond(self, cid, cond):
        return cond in ((self.world.agents.get(cid) or {}).get("conds") or {})

    def cond_name(self, cid, cond):
        c = self.conds(cid).get(cond) or {}
        name = COND[cond][0]
        return name + (f" ({c['body']})" if c.get("body") else "")

    def add_cond(self, tick, cid, cond, sev=1, why="", body=None, turns=None, by=None):
        """Give someone a condition (or worsen it). Returns the record, or None if it did not take."""
        w = self.world
        a = w.agents.get(cid)
        if not a or cond not in COND:
            return None
        sev = max(1, min(3, int(round(sev))))
        if cond in ("sick", "exhausted", "chilled", "panicking", "dizzy", "breathless", "blinded") and self.rng.random() >= min(1.0, self.tune("affliction_rate")):
            return None
        cs = self.conds(cid)
        rec = cs.get(cond)
        lo_hi = COND[cond][2]
        dur = turns if turns is not None else (self.rng.randint(*lo_hi) if lo_hi else None)
        if rec:
            rec["sev"] = max(rec["sev"], sev) if sev >= rec["sev"] else rec["sev"]
            if dur is not None and rec.get("left") is not None:
                rec["left"] = max(rec["left"], dur)
            return rec
        rec = {"sev": sev, "left": dur, "why": why, "day": self.day, "hour": tick.get("hour", 12) if tick else 12, "room": a["room"]}
        if by:
            rec["by"] = by
        if body:
            rec["body"] = body
        if cond in HEAL_DAYS:
            rec["until_day"] = self.day + HEAL_DAYS[cond]
        cs[cond] = rec
        name = self.nm(cid)
        txt = {"bleeding": f"{name} is bleeding", "broken_arm": f"{name} breaks their arm", "broken_leg": f"{name} breaks their leg", "whiplash": f"{name} suffers whiplash",
               "concussion": f"{name} has a concussion", "burned": f"{name} is burned", "lost_hand": f"{name} loses a hand", "lost_fingers": f"{name} loses some fingers",
               "lost_eye": f"{name} loses an eye", "lost_foot": f"{name} loses a foot", "poisoned": f"{name} has been poisoned", "blinded": f"{name} is blinded",
               "panicking": f"{name} panics", "deranged": f"{name} has lost their grip on reality", "infected": f"{name}'s wound is infected", "scratched": f"{name} has fresh scratches on their hands"}.get(cond, f"{name} is {COND[cond][0]}")
        if tick is not None:
            self.log_event(tick, {"type": "condition", "who": cid, "room": a["room"], "vis": "public" if cond in ("bleeding", "broken_arm", "broken_leg", "burned", "lost_hand", "lost_foot", "lost_eye", "panicking", "blinded") else "viewer",
                                  "text": txt + (f" ({why})" if why else "") + "."}, witnesses=[o for o in w.occupants(a["room"]) if o != cid and o in w.agents] if cond in ("bleeding", "broken_arm", "broken_leg", "burned", "panicking") else None, actor=cid)
        w.remember(cid, f"{_hh(tick.get('hour', 12) if tick else 12)} (your body) {txt.replace(name, 'You', 1).replace('You is', 'You are').replace('You has', 'You have')}" + (f" ({why})" if why else "") + ".")
        if cond in PERMANENT or cond in ("broken_arm", "broken_leg"):
            self.moment(cid, txt.replace(name, "you", 1))
        return rec

    def remove_cond(self, cid, cond):
        return bool(self.conds(cid).pop(cond, None))

    def sev(self, cid, cond):
        return (self.conds(cid).get(cond) or {}).get("sev", 0)

    # ------------------------------------------------------------------ what conditions do
    def cond_mod(self, cid, key):
        """Sum of one modifier over all of a person's conditions (a splint or a bandage can halve a bone's penalty)."""
        a = self.world.agents.get(cid)
        if not a:
            return 0.0
        tot = 0.0
        for c, rec in (a.get("conds") or {}).items():
            m = COND[c][3].get(key, 0)
            if not m:
                continue
            f = 0.5 if rec.get("splinted") and key in ("move", "atk", "phys") else 1.0
            tot += m * rec["sev"] * f
        return tot

    HEAVY_WORDS = ("fuel", "atlas", "plank", "ladder", "crate", "barrel", "toolbox", "life_ring", "oar", "anchor", "generator", "chain", "log", "boat")

    def load_weight(self, cid):
        """What the person carries, in rough kilos-worth of 'items': most things count one, heavy ones three."""
        a = self.world.agents.get(cid)
        if not a:
            return 0
        return sum(q * (3 if any(k in item for k in self.HEAVY_WORDS) else 1) for item, q in a["inv"].items())

    def move_factor(self, cid):
        """How fast the person walks, as a share of normal: slower when hurt, ill, hungry, loaded down or dragging someone."""
        a = self.world.agents.get(cid)
        f = max(0.15, 1.0 - self.cond_mod(cid, "move"))
        if not a:
            return f
        f *= 0.8 if a.get("hunger", 0) >= 95 else 1.0
        hp = a.get("hp", 100)
        f *= 1.0 if hp >= 60 else max(0.5, 0.5 + 0.5 * (hp - 10) / 50)                  # badly hurt people limp
        load = self.load_weight(cid) / max(10.0, float(self.carry_cap(cid)))
        f *= 1.0 if load <= 0.35 else max(0.5, 1.0 - 0.5 * (load - 0.35) / 0.65)         # heavy loads slow you down
        if self.dragging_now(cid):
            f *= 0.5
        return max(0.2, f)

    def dragging_now(self, cid):
        d = self.s.get("drags") or []
        return bool(d and d[-1].get("by") == cid and d[-1].get("day") == self.day and d[-1].get("hour") == self.s.get("_hour"))

    def cond_penalty(self, cid):
        return min(0.6, self.cond_mod(cid, "phys"))

    def attack_penalty(self, cid):
        return min(0.6, self.cond_mod(cid, "atk"))

    def blind(self, cid):
        return self.has_cond(cid, "blinded")

    def cond_slip(self, cid):
        return min(0.5, self.cond_mod(cid, "slip"))

    def carry_cap(self, cid):
        return max(6, 30 - int(self.cond_mod(cid, "carry")))

    def hand_skill(self, cid):
        """How well someone can do fiddly work with their hands (lockpicking, crafting)."""
        f = 1.0
        if self.has_cond(cid, "lost_hand"):
            f *= 0.35
        if self.has_cond(cid, "lost_fingers"):
            f *= 0.6
        rec = (self.world.agents[cid].get("conds") or {}).get("broken_arm")
        if rec:
            f *= 0.8 if rec.get("splinted") else 0.55
        return f

    def two_hands(self, cid):
        return not (self.has_cond(cid, "broken_arm") or self.has_cond(cid, "lost_hand"))

    # ------------------------------------------------------------------ what others see
    def condition_note(self, cid):
        a = self.world.agents.get(cid)
        if not a:
            return ""
        if a.get("out"):
            return " (lying unconscious)"
        cs = a.get("conds") or {}
        bits = []
        if "bleeding" in cs:
            bits.append("bleeding")
        if "broken_leg" in cs or "lost_foot" in cs:
            bits.append("limping badly")
        if "broken_arm" in cs or "lost_hand" in cs:
            bits.append("holding an injured arm")
        if "blinded" in cs:
            bits.append("clawing at their eyes")
        if "breathless" in cs:
            bits.append("wheezing")
        if "burned" in cs:
            bits.append("burned")
        if "sick" in cs or "poisoned" in cs:
            bits.append("pale and sweating")
        if "drunk" in cs:
            bits.append("drunk")
        if "dizzy" in cs or "concussion" in cs:
            bits.append("unsteady")
        if "panicking" in cs:
            bits.append("panicking")
        if "deranged" in cs:
            bits.append("wild-eyed and muttering")
        return f" ({', '.join(bits[:3])})" if bits else ""

    def cond_lines(self, cid):
        a = self.world.agents.get(cid)
        if not a:
            return []
        cs = a.get("conds") or {}
        out = []
        if cs:
            bits = []
            for c, rec in cs.items():
                eff = {"bleeding": "you are losing blood and need a bandage", "broken_arm": "you cannot fight or lift with that arm", "broken_leg": "you can barely walk",
                       "blinded": "you cannot see for now", "breathless": "you cannot catch your breath", "dizzy": "the room swims", "poisoned": "you feel violently ill: something you ate or drank was wrong",
                       "sick": "you are ill", "panicking": "you are in a blind panic", "deranged": "you see and hear things that are not there and trust nothing", "hungry": "you are hungry",
                       "thirsty": "you are very thirsty", "drunk": "you are drunk and your tongue is loose", "concussion": "your head is foggy and you may black out", "weak": "you are physically weak",
                       "burned": "your burns hurt", "infected": "your wound is infected and you feel feverish", "exhausted": "you are exhausted", "chilled": "you are freezing",
                       "whiplash": "your neck is stiff and painful", "lost_hand": "you have lost a hand", "lost_fingers": "you have lost some fingers", "lost_eye": "you have lost an eye", "lost_foot": "you have lost a foot"}.get(c, "")
                bits.append(f"{self.cond_name(cid, c)}{' (severe)' if rec['sev'] >= 3 else ''}: {eff}")
            out.append("YOUR BODY: " + "; ".join(bits[:5]) + ". Let it shape what you do and say; you can treat it (action 'treat') or ask someone to help.")
        here = [o for o in self.world.occupants(a["room"], include_hidden=True) if o in self.world.agents and o != cid and self.world.agents[o].get("out")]
        if here:
            out.append("UNCONSCIOUS HERE: " + ", ".join(self.nm(o) for o in here) + ". They are helpless: you could help them (action 'wake' or 'treat'), or do something to them.")
        return out

    # ------------------------------------------------------------------ unconsciousness
    def knock_out(self, tick, cid, cause, turns=None, by=None, quiet=False):
        """Someone loses consciousness (knocked out, fainted, drugged...). They are helpless until they come round."""
        w = self.world
        a = w.agents.get(cid)
        if not a or a.get("out"):
            return False
        n = turns if turns is not None else KNOCKOUT_TURNS.get(cause, 1)
        a["out"] = {"abs": True, "until": self.abs_now(tick.get("hour")) + n * max(1, self.step), "cause": cause, "by": by, "day": self.day, "hour": tick.get("hour", 12), "seen_by": []}
        a["asleep"] = False
        a.pop("hiding", None)
        a["activity"] = "Unconscious"
        self.drop_held(tick, cid, "as they go down")
        if not quiet:
            verb = {"fainted": "faints", "knocked out": "is knocked out", "drugged": "slumps, drugged", "tased": "convulses and drops", "choked out": "goes limp",
                    "fell": "is knocked senseless by the fall", "exhausted": "collapses from exhaustion", "overcome": "is overcome and collapses", "shock": "faints from shock"}.get(cause, "collapses")
            self.log_event(tick, {"type": "faint", "who": cid, "room": a["room"], "vis": "public", "cause": cause, "text": f"{self.nm(cid)} {verb}."},
                           witnesses=[o for o in w.occupants(a["room"]) if o != cid and o in w.agents], actor=cid)
        return True

    def wake_up(self, tick, cid, how="comes round"):
        w = self.world
        a = w.agents.get(cid)
        if not a or not a.get("out"):
            return
        out = a.pop("out")
        a["activity"] = "Groggy"
        if a.get("gagged") and not self.restrained(cid):
            a.pop("gagged")                                          # they tear the gag off as soon as their hands are free
        bl = self.s.setdefault("blackouts", [])
        bl.append({"who": cid, "cause": out["cause"], "by": out.get("by"), "room": a["room"], "day": out["day"], "hour": out["hour"], "woke_day": self.day, "woke_hour": tick.get("hour", 12),
                   "seen_by": list(out.get("seen_by", []))})
        del bl[:-30]
        self.log_event(tick, {"type": "faint", "who": cid, "room": a["room"], "vis": "public", "text": f"{self.nm(cid)} {how}."},
                       witnesses=[o for o in w.occupants(a["room"]) if o != cid and o in w.agents], actor=cid)
        hour = tick.get("hour", 12)
        cause = out["cause"]
        # memory: the moments before are gone, and the one who did it may or may not be remembered
        if cause in ("knocked out", "choked out", "tased", "fell") or self.has_cond(cid, "concussion"):
            rec = a["memory"]["recent"]
            if len(rec) > 3 and self.rng.random() < 0.6:
                del rec[-self.rng.randint(1, 3):]
        w.remember(cid, f"{_hh(hour)} (private) You come to on the floor of the {w.room_name(a['room'])}, head swimming.")
        if a.pop("missed_reveal", False):
            w.remember(cid, f"{_hh(hour)} (private) While you were out TereVi told everyone the truth: the show is real, nobody leaves, and if nobody dies before the deadline everyone does. The others look at you differently now.")
            self.stat(tick, cid, "sanity", -12, "learning the truth")
        if cause in ("knocked out", "choked out", "tased", "fell") or self.has_cond(cid, "concussion"):
            by = out.get("by")
            if by in w.agents:
                if self.rng.random() < 0.3 + 0.3 * self.sharpness(cid):
                    w.remember(cid, f"{_hh(hour)} (private) You remember who hit you: {self.nm(by)}.")
                    self.add_tie(cid, by, "wronged", "knocked you out", -5)
                    self.stat(tick, cid, "sanity", -4, "being attacked")
                else:
                    w.remember(cid, f"{_hh(hour)} (private) Someone hit you. You did not see who.")
        lb = a.pop("locked_by", None)
        if lb in w.agents and (self.s["locks"].get(a["room"]) or {}).get("keyed"):
            w.remember(cid, f"{_hh(hour)} (private) The door is locked from outside. {self.nm(lb)} must have shut you in.")
            self.add_tie(cid, lb, "wronged", f"locked you in the {w.room_name(a['room'])}", -4)
        rb = a.pop("robbed_by", None)
        if rb in w.agents and self.rng.random() < 0.5 + 0.3 * self.sharpness(cid):
            w.remember(cid, f"{_hh(hour)} (private) Your things have been gone through, and you think it was {self.nm(rb)}.")
            self.add_tie(cid, rb, "wronged", "went through your things while you were out", -3)
        beside = a.pop("staged_beside", None)
        if beside:
            weapon = next((k for k in a["inv"] if "weapon" in self.tags(k)), None)
            w.remember(cid, f"{_hh(hour)} (private) You wake beside {self.nm(beside)}'s body" + (f" with a {w.item_name(weapon)} in your hand" if weapon else "") + ", your clothes stained. Someone has done this to you.")
            self.stat(tick, cid, "sanity", -12, "waking beside a body")
            self.maybe_panic(tick, cid, "waking beside a body", 0.9)
        if cause in ("knocked out", "choked out", "fell") and self.rng.random() < 0.35:
            self.add_cond(tick, cid, "dizzy", 1, "coming round")
        self.stat(tick, cid, "sanity", -3, "waking up helpless")

    # ------------------------------------------------------------------ each turn
    def condition_tick(self, tick, hour):
        w, s = self.world, self.s
        self.environment_effects(tick, hour)
        for cid in list(w.agents):
            a = w.agents.get(cid)
            if not a:
                continue
            self.hunger_thirst(tick, cid)
            self.derive_mind(tick, cid)
            cs = a.get("conds") or {}
            for c in list(cs):
                rec = cs[c]
                m = COND[c][3]
                hp_loss = m.get("hp", 0) * rec["sev"]
                if hp_loss and (not a.get("out") or c == "bleeding"):
                    k = int(hp_loss) + (1 if self.rng.random() < hp_loss - int(hp_loss) else 0)
                    if k:
                        if c in ("bleeding", "infected", "burned") and a["hp"] - k <= 0 and self.murders and not s.get("case"):
                            self.condition_death(tick, cid, c, rec)
                            break
                        self.stat(tick, cid, "hp", -k, COND[c][0])
                        if cid not in w.agents:
                            break
                if m.get("san"):
                    k = m["san"] * rec["sev"]
                    k = int(k) + (1 if self.rng.random() < k - int(k) else 0)
                    if k:
                        self.stat(tick, cid, "sanity", -k, COND[c][0])
                if rec.get("left") is not None:
                    rec["left"] -= 1
                    if rec["left"] <= 0:
                        del cs[c]
                        w.remember(cid, f"{_hh(hour)} (your body) You are no longer {COND[c][0]}.")
                        continue
                if rec.get("until_day") and self.day >= rec["until_day"]:
                    del cs[c]
                    w.remember(cid, f"{_hh(hour)} (your body) Your {COND[c][0]} has healed.")
                    continue
                if c == "bleeding":
                    if rec["sev"] == 1 and self.rng.random() < 0.3:
                        del cs[c]
                        w.remember(cid, f"{_hh(hour)} (your body) The bleeding has stopped by itself.")
                        continue
                    rec["ticks"] = rec.get("ticks", 0) + 1
                    self.leave_blood(tick, cid)
                    if rec["ticks"] >= 5 and rec["sev"] >= 2 and "infected" not in cs and self.rng.random() < 0.25:
                        self.add_cond(tick, cid, "infected", 1, "an untreated wound")
                if c == "burned":
                    rec["ticks"] = rec.get("ticks", 0) + 1
                    if rec["ticks"] >= 6 and "infected" not in cs and self.rng.random() < 0.2 and not rec.get("treated"):
                        self.add_cond(tick, cid, "infected", 1, "untreated burns")
                if c == "sick" and self.rng.random() < 0.15:
                    for o in w.occupants(a["room"]):
                        if o in w.agents and o != cid and not w.agents[o].get("conds", {}).get("sick") and self.rng.random() < 0.3:
                            self.add_cond(tick, o, "sick", 1, f"caught it from {self.nm(cid)}")
                            break
            if self.has_cond(cid, "deranged") and w.agents[cid]["sanity"] >= 25:
                self.remove_cond(cid, "deranged")
                w.remember(cid, f"{_hh(hour)} (your body) The world settles; you can tell what is real again.")
            self.faint_roll(tick, cid)
        self.auto_care(tick, hour)
        self.unconscious_tick(tick, hour)

    def faint_roll(self, tick, cid):
        a = self.world.agents.get(cid)
        if not a or a.get("out"):
            return
        p = self.cond_mod(cid, "faint")
        if a["hp"] <= 12:
            p += 0.1
        if a.get("hunger", 0) >= 95 or a.get("thirst", 0) >= 90:
            p += 0.025
        p *= 0.7 * self.tune("faint_rate")
        if p > 0 and self.rng.random() < min(0.5, p):
            cause = "overcome" if self.has_cond(cid, "breathless") else "fainted"
            self.knock_out(tick, cid, cause, 1)

    def unconscious_tick(self, tick, hour):
        """The unconscious come round when their time is up; whoever finds them lying there knows it."""
        w = self.world
        for cid, a in list(w.agents.items()):
            out = a.get("out")
            if not out:
                continue
            if not out.get("abs") or self.abs_now(hour) >= out["until"]:          # (no "abs" mark: an older save that counted ticks, wake them)
                self.wake_up(tick, cid)
                continue
            for o in w.occupants(a["room"]):
                if o in w.agents and o != cid and o not in out["seen_by"] and not w.agents[o].get("out"):
                    out["seen_by"].append(o)
                    w.remember(o, f"{_hh(hour)} (you found) {self.nm(cid)} lying unconscious in the {w.room_name(a['room'])}.")

    def leave_blood(self, tick, cid):
        """A bleeding person leaves drops of blood where they go: a trail for an investigator."""
        s = self.s
        a = self.world.agents[cid]
        tr = s.setdefault("blood", [])
        tr.append({"room": a["room"], "by": cid, "day": self.day, "hour": tick.get("hour", 12)})
        del tr[:-30]
        self.env_mark("blood", cid)

    # ------------------------------------------------------------------ hunger and thirst
    def hunger_thirst(self, tick, cid):
        a = self.world.agents[cid]
        rate = self.tune("hunger_rate")
        a["hunger"] = min(100, a.get("hunger", 20) + 4 * rate)
        a["thirst"] = min(100, a.get("thirst", 20) + 6 * rate)
        cs = self.conds(cid)
        for cond, val, th in (("hungry", a["hunger"], (60, 80, 95)), ("thirsty", a["thirst"], (50, 70, 90))):
            sev = 3 if val >= th[2] else 2 if val >= th[1] else 1 if val >= th[0] else 0
            if sev:
                if cond not in cs:
                    cs[cond] = {"sev": sev, "left": None, "why": "", "day": self.day}
                    self.world.remember(cid, f"{_hh(tick.get('hour', 12))} (your body) You are {COND[cond][0]}.")
                cs[cond]["sev"] = sev
            else:
                cs.pop(cond, None)
        self.auto_eat(tick, cid)

    def auto_eat(self, tick, cid):
        """Someone who is hungry or thirsty and has food or drink to hand eats and drinks (the models rarely think of it)."""
        w, s = self.world, self.s
        a = w.agents[cid]
        if a.get("out") or (a["hunger"] < 60 and a["thirst"] < 50) or self.rng.random() > 0.8:
            return
        from .data_world import COMMON_ITEMS
        for need, tags, key in (("thirst", DRINK_TAGS, "thirst"), ("hunger", FOOD_TAGS, "hunger")):
            if a[key] < (50 if key == "thirst" else 60):
                continue
            pool = list(a["inv"]) + list(s["room_items"].get(a["room"], {})) + list(COMMON_ITEMS.get(a["room"], []))
            item = next((k for k in pool if set(w.item_spec(k).get("tags", [])) & tags and "poison" not in w.item_spec(k).get("tags", [])), None)
            if item:
                self.consume(tick, cid, item)

    def consume(self, tick, cid, item):
        """Eat or drink something: hunger and thirst go down, and the item's own effect applies."""
        w, s = self.world, self.s
        a = w.agents[cid]
        tags = set(w.item_spec(item).get("tags", []))
        from .data_world import COMMON_ITEMS
        if a["inv"].get(item, 0) > 0:
            a["inv"][item] -= 1
            if a["inv"][item] <= 0:
                del a["inv"][item]
        elif s["room_items"].get(a["room"], {}).get(item, 0) > 0:
            s["room_items"][a["room"]][item] -= 1
            if s["room_items"][a["room"]][item] <= 0:
                del s["room_items"][a["room"]][item]
        elif item not in COMMON_ITEMS.get(a["room"], []):
            return False
        if tags & FOOD_TAGS:
            a["hunger"] = max(0, a.get("hunger", 0) - 40)
        if tags & DRINK_TAGS:
            a["thirst"] = max(0, a.get("thirst", 0) - (60 if item in ("water_bottle", "sparkling_water") else 30))
            if item in ("wine_bottle", "champagne", "spirits"):
                self.add_cond(tick, cid, "drunk", 1 if self.rng.random() < 0.7 else 2, "drinking")
        eff = w.item_spec(item).get("use")
        if eff:
            a["hp"] = max(1, min(100, a["hp"] + eff.get("hp", 0)))
            a["sanity"] = max(0, min(100, a["sanity"] + eff.get("sanity", 0)))
        self.log_event(tick, {"type": "use", "who": cid, "room": a["room"], "vis": "viewer", "text": f"{self.nm(cid)} {'drinks' if tags & DRINK_TAGS else 'eats'} {w.item_name(item).lower()}."}, actor=cid)
        return True

    def meal_for(self, tick, group):
        """A shared meal feeds everyone at it."""
        for cid in group:
            if cid in self.world.agents:
                a = self.world.agents[cid]
                a["hunger"] = max(0, a.get("hunger", 0) - 50)
                a["thirst"] = max(0, a.get("thirst", 0) - 30)

    # ------------------------------------------------------------------ the mind
    def derive_mind(self, tick, cid):
        a = self.world.agents[cid]
        if a["sanity"] < 10 and not self.has_cond(cid, "deranged") and self.rng.random() < 0.5:
            self.add_cond(tick, cid, "deranged", 2 if a["sanity"] < 5 else 1, "their mind gave way")

    def maybe_panic(self, tick, cid, why, p=0.4):
        a = self.world.agents.get(cid)
        if not a or a.get("out"):
            return
        weak = 1.0 + max(0, 55 - a["sanity"]) / 55
        if self.rng.random() < min(0.9, p * weak) and self.tune("affliction_rate") > 0:
            self.add_cond(tick, cid, "panicking", 1 if a["sanity"] > 40 else 2, why)
            if self.rng.random() < 0.3:
                self.add_cond(tick, cid, "breathless", 1, "hyperventilating")

    # ------------------------------------------------------------------ treatment
    MEDICAL = ("bandages", "first_aid_kit", "splint", "antibiotics", "paracetamol", "water_bottle", "charcoal", "ice", "rags", "towels", "sweets", "smelling_salts")

    def treat_options(self, cid):
        """What someone can treat with: what they carry, plus medical supplies lying in the room they are in (the green room and the bathroom keep the stock)."""
        a = self.world.agents[cid]
        inv = a["inv"]
        out = {k: inv.get(k, 0) for k in self.MEDICAL if inv.get(k, 0) > 0}
        for k, q in (self.s["room_items"].get(a["room"]) or {}).items():
            if k in self.MEDICAL and q > 0 and k not in out:
                out[k] = q
        return out

    def fetch_medical(self, cid):
        """Pick up the room's medical supplies before treating (they come from the shelf, not from nowhere)."""
        a = self.world.agents[cid]
        stock = self.s["room_items"].get(a["room"]) or {}
        for k in list(stock):
            if k in self.MEDICAL and stock[k] > 0 and a["inv"].get(k, 0) < 2:
                a["inv"][k] = a["inv"].get(k, 0) + 1
                stock[k] -= 1
                if stock[k] <= 0:
                    del stock[k]

    def medic_bonus(self, cid):
        """Practice makes a better carer: each treatment given adds a little skill."""
        return min(0.25, 0.04 * (self.s.get("stats", {}).get(cid, {}).get("treatments", 0)))

    def rest_heal(self, tick, cid):
        """Resting somewhere quiet where the medicine is kept helps wounds knit faster."""
        a = self.world.agents[cid]
        if a["room"] not in ("green_room", "bathroom") or a.get("out"):
            return
        for c, rec in (a.get("conds") or {}).items():
            if rec.get("until_day") and rec["until_day"] > self.day and self.rng.random() < 0.2:
                rec["until_day"] -= 1
                self.world.remember(cid, f"{_hh(tick.get('hour', 12))} (your body) Resting here, your {COND[c][0]} feels a little better.")
                break

    def do_treat(self, tick, cid, d):
        """Tend to someone (or yourself): stop bleeding, set a bone, cool a burn, flush a poison, calm a panic, wake a faint."""
        w, s = self.world, self.s
        a = w.agents[cid]
        t = d.get("target") or cid
        if t not in w.agents or w.agents[t]["room"] != a["room"]:
            return
        ta = w.agents[t]
        item = d.get("item") or ""
        self.fetch_medical(cid)
        have = self.treat_options(cid)
        name, tname = self.nm(cid), ("themselves" if t == cid else self.nm(t))
        cs = ta.get("conds") or {}
        if ta.get("out"):
            return self.do_wake(tick, cid, {"target": t})
        skill = 0.45 + 0.35 * self.sharpness(cid) + self.medic_bonus(cid) - (0.15 if t == cid else 0.0) - 0.2 * self.cond_penalty(cid)
        did = []

        def use(k):
            if a["inv"].get(k, 0) > 0:
                a["inv"][k] -= 1
                if a["inv"][k] <= 0:
                    del a["inv"][k]
                return True
            return False
        for cond in list(cs):
            rec = cs[cond]
            if cond == "bleeding":
                for k, p in (("first_aid_kit", 0.9), ("bandages", 0.8), ("towels", 0.5), ("rags", 0.45)):
                    if (not item or item == k) and a["inv"].get(k, 0) > 0 and self.rng.random() < p * skill + 0.2:
                        use(k) if k in ("bandages", "first_aid_kit") else None
                        rec["sev"] -= 2 if k in ("first_aid_kit", "bandages") else 1
                        did.append(f"stops the bleeding with the {w.item_name(k).lower()}")
                        if rec["sev"] <= 0:
                            del cs[cond]
                        break
            elif cond in ("broken_arm", "broken_leg"):
                if (not item or item in ("splint", "first_aid_kit")) and (a["inv"].get("splint", 0) > 0 or a["inv"].get("first_aid_kit", 0) > 0) and self.rng.random() < skill + 0.15:
                    use("splint") or use("first_aid_kit")
                    rec["splinted"] = True
                    rec["until_day"] = max(self.day + 1, rec.get("until_day", self.day + 4) - 2)
                    did.append("splints it")
            elif cond == "burned":
                for k in ("ice", "water_bottle", "bandages"):
                    if (not item or item == k) and (a["inv"].get(k, 0) > 0 or k in ("ice",) and a["room"] == "cold_store") and self.rng.random() < skill + 0.2:
                        use(k)
                        rec["treated"] = True
                        rec["sev"] = max(1, rec["sev"] - 1)
                        did.append(f"cools and dresses the burn with the {w.item_name(k).lower()}")
                        break
            elif cond in ("infected", "sick") and (not item or item in ("antibiotics", "paracetamol", "water_bottle")):
                for k, p in (("antibiotics", 0.9), ("paracetamol", 0.4), ("water_bottle", 0.2)):
                    if a["inv"].get(k, 0) > 0 and self.rng.random() < p * (0.6 + skill * 0.4):
                        use(k)
                        if k == "antibiotics" or self.rng.random() < 0.3:
                            del cs[cond]
                        else:
                            rec["sev"] = max(1, rec["sev"] - 1)
                        did.append(f"gives {tname} the {w.item_name(k).lower()}")
                        break
            elif cond == "poisoned":
                for k, p in (("charcoal", 0.7), ("first_aid_kit", 0.5), ("water_bottle", 0.4)):
                    if (not item or item == k) and (a["inv"].get(k, 0) > 0) and self.rng.random() < p * (0.5 + skill * 0.5):
                        use(k)
                        del cs[cond]
                        self.cure_poison(tick, t)
                        did.append(f"makes {tname} bring it up with the {w.item_name(k).lower()}")
                        break
            elif cond in ("panicking", "breathless", "dizzy", "blinded", "drunk") and self.rng.random() < skill + 0.1:
                if cond == "blinded" and a["inv"].get("water_bottle", 0) > 0:
                    use("water_bottle")
                del cs[cond]
                did.append(f"calms {tname} down" if cond in ("panicking", "breathless") else f"helps {tname} through the {COND[cond][0]}")
            elif cond == "thirsty" and a["inv"].get("water_bottle", 0) > 0:
                use("water_bottle")
                ta["thirst"] = max(0, ta.get("thirst", 0) - 60)
                del cs[cond]
                did.append(f"gives {tname} water")
        if did:
            self.log_event(tick, {"type": "treat", "who": cid, "room": a["room"], "vis": "public", "text": f"{name} {', '.join(did[:2])}."},
                           witnesses=[o for o in w.occupants(a["room"]) if o != cid], actor=cid)
            if t != cid:
                self.add_tie(t, cid, "helped", f"{name} tended their injuries", 2)
            self.tally(cid, "treatments")
        else:
            w.remember(cid, f"{_hh(tick['hour'])} You tried to help {tname} but could do nothing useful (you lack the means, or it did not work).")

    def cure_poison(self, tick, victim):
        """A poisoned person who is treated in time lives: the murder attempt fails and the case is closed."""
        s, w = self.s, self.world
        case = s.get("case")
        if case and case.get("poison_pending") and case.get("victim") == victim:
            culprit = case.get("killer")
            s["case"] = None
            w.remember(victim, f"{_hh(tick['hour'])} (private) You were poisoned. Someone meant you to die. You will not forget it.")
            self.moment(victim, "survived being poisoned")
            if culprit in w.agents:
                w.remember(culprit, f"{_hh(tick['hour'])} (private) Your poison failed: {self.nm(victim)} is alive.")
            self.log_event(tick, {"type": "attack", "who": victim, "room": w.agents[victim]["room"], "vis": "viewer", "text": f"{self.nm(victim)} survives being poisoned."}, actor=victim)

    def do_wake(self, tick, cid, d):
        """Slap, shake, splash water or hold smelling salts under the nose."""
        w = self.world
        a = w.agents[cid]
        t = d.get("target")
        if t not in w.agents or w.agents[t]["room"] != a["room"] or not w.agents[t].get("out"):
            return
        aid = 0.2 if a["inv"].get("smelling_salts", 0) > 0 else 0.1 if a["inv"].get("water_bottle", 0) > 0 or a["inv"].get("first_aid_kit", 0) > 0 else 0.0
        out = w.agents[t]["out"]
        if out["cause"] in ("drugged",):
            aid -= 0.2
        p = 0.35 + aid + 0.2 * self.sharpness(cid)
        if self.rng.random() < p:
            self.wake_up(tick, t, f"is shaken awake by {self.nm(cid)}")
            self.add_tie(t, cid, "helped", f"{self.nm(cid)} brought them round", 2)
        else:
            w.remember(cid, f"{_hh(tick['hour'])} You try to bring {self.nm(t)} round, and fail.")

    # ------------------------------------------------------------------ snapshot
    def cond_snapshot(self, cid):
        a = self.world.agents.get(cid) or {}
        return [{"id": c, "name": self.cond_name(cid, c), "sev": r["sev"]} for c, r in (a.get("conds") or {}).items()]

    # ------------------------------------------------------------------ the world around the body
    def environment_effects(self, tick, hour):
        w = self.world
        for cid, a in list(w.agents.items()):
            if a["room"] == "cold_store" and not self.has_cond(cid, "chilled") and self.rng.random() < 0.5:
                self.add_cond(tick, cid, "chilled", 1, "the cold store")
            if self.blackout_until >= self.idx and not a.get("lit") and a["sanity"] < 50 and len([o for o in w.occupants(a["room"]) if o in w.agents]) <= 1:
                self.maybe_panic(tick, cid, "alone in the dark", 0.1)

    def after_use(self, tick, cid, item):
        """Using an item also feeds or waters the person (hunger and thirst), and strong drink makes them drunk."""
        a = self.world.agents[cid]
        tags = set(self.world.item_spec(item).get("tags", []))
        if tags & FOOD_TAGS:
            a["hunger"] = max(0, a.get("hunger", 0) - 40)
        if tags & DRINK_TAGS:
            a["thirst"] = max(0, a.get("thirst", 0) - (60 if item in ("water_bottle", "sparkling_water") else 30))
            if item in ("wine_bottle", "champagne", "spirits"):
                self.add_cond(tick, cid, "drunk", 1, "drinking")

    def condition_acts(self, cid):
        if not self.revealed:
            return ""
        w, s = self.world, self.s
        a = w.agents[cid]
        here = [o for o in w.occupants(a["room"], include_hidden=True) if o in w.agents and o != cid]
        helpless = [o for o in here if w.agents[o].get("out") or w.agents[o].get("restrained")]
        acts = ""
        if self.murders and here and not s.get("case"):
            acts += "|knockout"
        if any(w.agents[o].get("out") for o in here):
            acts += "|wake"
        if helpless:
            acts += "|carry|rob"
        if a.get("conds") or any(w.agents[o].get("conds") for o in here):
            acts += "|treat"
        case = s.get("case")
        if case and case.get("killer") == cid and not case.get("announced") and case.get("room") == a["room"] and any(w.agents[o].get("out") for o in here):
            acts += "|stage"
        return acts

    # ------------------------------------------------------------------ people look after each other (the models rarely think of it)
    def seek_care(self, cid, d):
        """A badly hurt person with nothing to treat themselves, who has no other plans this turn, heads for the medicine shelves."""
        a = self.world.agents[cid]
        cs = a.get("conds") or {}
        bad = [c for c in ("bleeding", "broken_leg", "burned", "infected", "poisoned") if c in cs and (cs[c]["sev"] >= 2 or c != "bleeding")]
        if not bad or d.get("action") not in ("stay", "rest") or d.get("target_room") or self.treat_options(cid) or a["room"] in ("bathroom", "green_room"):
            return
        if self.rng.random() > 0.8:
            return
        dest = min(("bathroom", "green_room"), key=lambda r_: len(self.world.path(cid, a["room"], r_) or [0] * 99))
        go = self.step_toward(cid, dest)
        if go:
            d.update(action="stay", target_room=go, activity=f"Hurries to the {self.world.room_name(dest)} to find something for the pain")
            self.note_use(cid, "seek_care", "engine")

    def auto_care(self, tick, hour):
        w = self.world
        for cid, a in list(w.agents.items()):
            if a.get("out"):
                continue
            cs = a.get("conds") or {}
            if any(c in cs for c in ("bleeding", "burned", "infected", "poisoned", "broken_arm", "broken_leg")) and self.treat_options(cid) and self.rng.random() < 0.6:
                self.do_treat(tick, cid, {"target": cid})
                self.note_use(cid, "treat", "engine")
                continue
            for o in [x for x in w.occupants(a["room"], include_hidden=True) if x in w.agents and x != cid]:
                ta = w.agents[o]
                if a["aff"].get(o, 0) < 1 or a["sanity"] < 25:
                    continue
                if ta.get("out") and self.rng.random() < 0.35 and ta["out"]["cause"] not in ("drugged",):
                    self.do_wake(tick, cid, {"target": o})
                    self.note_use(cid, "wake", "engine")
                    break
                if (ta.get("conds") or {}).keys() & {"bleeding", "burned", "broken_arm", "broken_leg", "poisoned", "panicking", "breathless"} and self.rng.random() < 0.4:
                    self.do_treat(tick, cid, {"target": o})
                    self.note_use(cid, "treat", "engine")
                    break
