"""Fights in blows: an attack is a few exchanges seconds apart, not one roll.

Each round the attacker goes for a part of the body (chosen from intent and the situation: the throat or head to kill quietly, the chest with a
blade, the head with something heavy; a sleeper or someone taken from behind is hit where it counts) and the defender answers: blocks, dodges,
struggles for the weapon, runs, or screams. Every hit lands on a part and leaves a wound; a struggle leaves scratches on the attacker. The fight ends
when the target is dead, gets away, is rescued by people answering a scream, or the attacker has spent their nerve.

The result feeds the case (the autopsy's wounds), the witnesses (what they saw, blow by blow) and the people within earshot of a scream.
FightMixin is mixed into DayRunner (engine.py); `resolve_attacks` (cases.py) calls `fight`.
"""

PARTS = ("head", "throat", "chest", "belly", "back", "arm", "leg", "hand")
DMG = {  # (kind, part): health per hit
    ("sharp", "throat"): 65, ("sharp", "chest"): 48, ("sharp", "belly"): 38, ("sharp", "back"): 40, ("sharp", "arm"): 12, ("sharp", "leg"): 14, ("sharp", "hand"): 8, ("sharp", "head"): 25,
    ("blunt", "head"): 58, ("blunt", "throat"): 20, ("blunt", "chest"): 18, ("blunt", "belly"): 15, ("blunt", "back"): 15, ("blunt", "arm"): 12, ("blunt", "leg"): 12, ("blunt", "hand"): 8,
    ("hands", "throat"): 26, ("hands", "head"): 10, ("hands", "chest"): 6, ("hands", "belly"): 6, ("hands", "back"): 5, ("hands", "arm"): 4, ("hands", "leg"): 4, ("hands", "hand"): 3,
}
HIT = {"sharp": 0.62, "blunt": 0.58, "hands": 0.52}
VERB = {"sharp": "stabs at", "blunt": "swings at", "hands": "goes for"}
MAX_ROUNDS = 6


class FightMixin:
    def aim(self, cid, t, kind, rnd, helpless):
        """The part of the body the attacker goes for this round."""
        if kind == "hands":
            return "throat" if helpless or rnd > 0 or self.rng.random() < 0.7 else "head"
        if helpless:
            return "throat" if kind == "sharp" else "head"
        pool = {"sharp": ["chest", "chest", "throat", "belly", "back", "arm"], "blunt": ["head", "head", "head", "arm", "back", "chest"]}[kind]
        return self.rng.choice(pool)

    def defend(self, cid, t, kind, weapon, hp, others):
        """The defender's answer this round."""
        cour = self.facet(t, "courage") / 100
        if hp < 30 and self.rng.random() < 0.5:
            return "flee"
        opts = [("block", 1.0), ("dodge", 1.0), ("struggle", 0.6 + cour), ("flee", 0.5 + (1 - cour)), ("scream", 0.4 + (0.6 if others else 0.1))]
        if not weapon:
            opts = [o for o in opts if o[0] != "struggle"] + [("struggle", 0.9 + cour)]
        tot = sum(wt for _, wt in opts)
        x = self.rng.random() * tot
        for name, wt in opts:
            x -= wt
            if x <= 0:
                return name
        return "block"

    def fight(self, tick, cid, t, weapon, kind, hour, others=()):
        """Play the attack out blow by blow. Returns {"outcome": killed | escaped | rescued | disarmed | survived, "blows": [...], "wounds": [...], "scratched": bool}.
        Health is taken here except for a fatal last blow (the caller opens the case)."""
        w = self.world
        a, v = w.agents[cid], w.agents[t]
        helpless = bool(v.get("asleep") or v.get("out") or self.restrained(t))
        hp = v["hp"]
        blows, wounds, scratched = [], [], False
        nerve = 4 + int(self.facet(cid, "cruelty") / 25) + (2 if helpless else 0)
        strength = self.success_p(cid, 1.0)
        grip = False
        for rnd in range(MAX_ROUNDS):
            part = "throat" if grip else self.aim(cid, t, kind, rnd, helpless)
            p = 0.9 if grip else HIT[kind] * (0.75 + 0.25 * strength) + (0.3 if helpless else 0.15 if rnd == 0 else 0)
            surprised = rnd == 0 and self.rng.random() < 0.6                    # the first blow usually comes before they can react
            reply = None if helpless or surprised else ("struggle" if grip else self.defend(cid, t, kind, weapon, hp, others))      # a hand on the throat leaves only the struggle
            if reply == "block":
                p *= 0.5
                part = "arm" if self.rng.random() < 0.45 else part
            elif reply == "dodge":
                p *= 0.55
            elif reply == "struggle":
                p *= 0.7
            blow = {"part": part, "reply": reply, "hit": False}
            if self.rng.random() < min(0.97, p):
                dmg = int(DMG[(kind, part)] * (0.8 + 0.4 * self.rng.random()))
                blow.update(hit=True, dmg=dmg)
                wounds.append({"part": part, "kind": kind})
                hp -= dmg
            blows.append(blow)
            if hp <= 0:
                return {"outcome": "killed", "blows": blows, "wounds": wounds, "scratched": scratched}
            if kind == "hands" and blow["hit"] and part == "throat":
                if grip and reply == "struggle" and self.rng.random() < 0.25 + 0.25 * hp / 100:
                    grip = False                                   # they break the grip
                    blow["broke_free"] = True
                else:
                    grip = True
            if reply == "struggle":
                scratched = scratched or self.rng.random() < 0.6
                if weapon and self.rng.random() < 0.1 + 0.15 * self.facet(t, "courage") / 100:
                    blow["disarm"] = True
                    v["hp"] = max(1, hp)
                    return {"outcome": "disarmed", "blows": blows, "wounds": wounds, "scratched": scratched}
            if reply == "flee" and self.rng.random() < 0.15 + 0.3 * hp / 100:
                v["hp"] = max(1, hp)
                return {"outcome": "escaped", "blows": blows, "wounds": wounds, "scratched": scratched}
            if reply == "scream" and others and self.rng.random() < 0.45:
                v["hp"] = max(1, hp)
                return {"outcome": "rescued", "blows": blows, "wounds": wounds, "scratched": scratched}
            nerve -= 0 if grip else 1
            if nerve <= 0:
                break
        v["hp"] = max(1, hp)
        return {"outcome": "survived", "blows": blows, "wounds": wounds, "scratched": scratched}

    def fight_text(self, cid, t, res, wname, kind):
        """The fight told blow by blow, short."""
        n, tn = self.nm(cid), self.nm(t)
        bits = []
        for b in res["blows"][:5]:
            r = {"block": f"{tn} blocks", "dodge": f"{tn} twists away", "struggle": f"{tn} grabs for the {wname}" if kind != "hands" else f"{tn} claws at {n}",
                 "flee": f"{tn} tries to run", "scream": f"{tn} screams", None: ""}[b.get("reply")]
            hit = f"hits the {b['part']}" if b["hit"] else "misses"
            bits.append(", ".join(x for x in (r, hit) if x))
        return f"{n} {VERB[kind]} {tn} with {wname}: " + "; ".join(bits) + "."

    def wound_summary(self, wounds):
        """For the autopsy: "two blows to the head, one to the arm"."""
        c = {}
        for wd in wounds:
            c[wd["part"]] = c.get(wd["part"], 0) + 1
        words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}
        return ", ".join(f"{words.get(k, k)} {'wound' if wounds and wounds[0]['kind'] == 'sharp' else 'blow'}{'s' if k > 1 else ''} to the {p}" for p, k in sorted(c.items(), key=lambda kv: -kv[1]))
