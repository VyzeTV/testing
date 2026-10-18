"""How everyone looks, and the traces that looks leave: hair, fibres, a lost accessory, a silhouette in the dark.

Each character's looks follow their portrait: hair (length and colour), eyes, build (hand size, the hand they use, height; read by marks.py),
an accessory they always wear, and an outfit whose fabrics shed fibres. None of it needs a lab: a long lavender hair caught in the victim's
fingers, red wool snagged on a doorframe, a cross earring under the body, or a hood glimpsed against a window in the dark are things anyone can
see and match by eye. Clothes change what is seen: fibres come from what the killer was wearing (someone else's clothes point at their owner),
a hood or a fur collar belongs to the garment, a mask or a cloak hides the hair. Whoever loses an accessory is visibly without it until they
get it back. LooksMixin is mixed into DayRunner (engine.py).
"""

# hair, eyes, build, the accessory always worn, what the silhouette shows without clothes or accessory
LOOKS = {
    "szymon": {"hair": ("short", "ginger-blond"), "eyes": "eyes hidden above a red face scarf", "hand": "large", "handed": "right", "height": "tall",
               "accessory": ("red knitted face scarf", "red wool"), "shape": []},
    "seul": {"hair": ("long", "lavender"), "eyes": "violet eyes with tired shadows", "hand": "small", "handed": "right", "height": "short",
             "accessory": None, "shape": ["long hair"]},
    "vixen": {"hair": ("short", "blue"), "eyes": "cyan eyes", "hand": "small", "handed": "left", "height": "medium",
              "accessory": ("dark blue knitted scarf", "dark blue wool"), "shape": ["scarf"]},
    "noah": {"hair": ("short", "blond"), "eyes": "green eyes", "hand": "medium", "handed": "left", "height": "tall",
             "accessory": ("grey fedora", "grey felt"), "shape": ["hat"]},
    "ayden": {"hair": ("locs", "dark brown"), "eyes": "grey eyes", "hand": "large", "handed": "right", "height": "medium",
              "accessory": ("small silver cross earring", None), "shape": ["locs"]},
    "shintaro": {"hair": ("long", "dark green"), "eyes": "red eyes", "hand": "medium", "handed": "right", "height": "short",
                 "accessory": None, "shape": ["ponytail", "long hair"]},
    "chloe": {"hair": ("short", "ash-brown"), "eyes": "pink eyes", "hand": "small", "handed": "right", "height": "medium",
              "accessory": ("pair of red-framed glasses", None), "shape": ["glasses"]},
    "cail": {"hair": ("long", "orange"), "eyes": "teal eyes", "hand": "medium", "handed": "right", "height": "tall",
             "accessory": ("green hair ribbon", "green satin"), "shape": ["ponytail", "long hair"]},
    "kumiko": {"hair": ("long", "dark purple"), "eyes": "red eyes", "hand": "small", "handed": "right", "height": "short",
               "accessory": ("purple stuffed rabbit with button eyes", "purple plush fluff"), "shape": ["long hair", "ahoge"]},
}
# each character's own outfit and swimsuit (clothing.py), the fabrics the outfit sheds, and what it adds to a silhouette
OUTFITS = {
    "szymon": ("dark green hooded parka covered in patches", "board shorts", ["dark green nylon"], ["hood"]),
    "seul": ("light blue hoodie and joggers", "sporty one-piece swimsuit", ["light blue fleece"], ["hood"]),
    "vixen": ("black strappy top and dark jacket", "black bikini", ["black synthetic"], []),
    "noah": ("mint shirt open over a white tee", "patterned swim shorts", ["mint cotton"], []),
    "ayden": ("red hooded jacket over a white tee", "plain swim trunks", ["red jacket fabric"], ["hood"]),
    "shintaro": ("brown jacket with a white fur collar", "navy swim trunks", ["white fur", "brown suede"], ["fur collar"]),
    "chloe": ("dark teal wrap top", "floral swimsuit", ["dark teal knit"], []),
    "cail": ("white sailor uniform with a green neckerchief", "designer bikini", ["white cotton", "green silk"], ["sailor collar"]),
    "kumiko": ("black blazer with white trim, white shirt, red tie, black pleated skirt and dark purple thigh-high socks", "plain black swimsuit",
               ["black wool", "dark purple knit"], ["pleated skirt"]),
}
HAIRS = (("short", "black"), ("long", "black"), ("short", "brown"), ("long", "brown"), ("short", "red"), ("long", "blond"))
COAT_SHAPE = {"raincoat": ["hood", "long coat"], "trench_coat": ["long coat"], "jacket": [], "sheet_cloak": ["cloaked"]}


def looks_of(cid, cast=None):
    """The looks record for anyone: the portrait's, or derived from the id for a newcomer."""
    if cid in LOOKS and not (cast or {}).get("looks"):
        return LOOKS[cid]
    if (cast or {}).get("looks"):
        return cast["looks"]
    n = sum(map(ord, cid))
    big = 1 if (cast or {}).get("gender") == "male" else 0
    hair = HAIRS[n % len(HAIRS)]
    return {"hair": hair, "eyes": ("brown", "grey", "green", "blue")[n % 4] + " eyes", "hand": ("small", "medium", "large")[min(2, n % 2 + big)],
            "handed": "left" if n % 9 == 0 else "right", "height": ("short", "medium", "tall")[min(2, n % 2 + big)], "accessory": None,
            "shape": ["long hair"] if hair[0] == "long" else []}


def describe(cid, cast=None):
    """One line of what anyone sees: hair, eyes, build, what they wear."""
    lk = looks_of(cid, cast)
    hl, hc = lk["hair"]
    hair = f"{hc} locs" if hl == "locs" else f"{hl} {hc} hair" + (" in a ponytail" if "ponytail" in lk["shape"] else "")
    out = OUTFITS.get(cid, ("everyday clothes",))[0]
    acc = lk["accessory"][0] if lk.get("accessory") else None
    if acc and acc.replace("pair of ", "") in lk["eyes"]:
        acc = None
    tall = {"short": "Short", "medium": "Of medium height", "tall": "Tall"}[lk["height"]]
    art = lambda x: ("an " if x[0] in "aeiou" else "a ") + x
    wear = f"Wears {'' if out.endswith('clothes') else 'a '}{out}" + (f" and {art(acc)}" if acc else "")
    return f"{tall}, with {hair} and {lk['eyes']}. {wear}. {lk['handed'].capitalize()}-handed."


class LooksMixin:
    def looks(self, cid):
        return looks_of(cid, self.world.cast.get(cid))

    def looks_line(self, cid, short=False):
        """How someone looks right now, for the prompts: the portrait's looks with what they actually wear, a missing accessory and visible marks."""
        w = self.world
        lk = self.looks(cid)
        hl, hc = lk["hair"]
        hair = f"{hc} locs" if hl == "locs" else f"{hl} {hc} hair" + (" in a ponytail" if "ponytail" in lk["shape"] else "")
        worn = self.worn(cid) if cid in w.agents else None
        own = worn == f"clothes_{cid}"
        outfit = OUTFITS.get(cid, ("everyday clothes",))[0] if own else self.outfit_label(cid) if cid in w.agents else ""
        if worn and not own and self.owner_of(worn) not in (None, cid) and self.nm(self.owner_of(worn)) not in outfit:
            outfit += f" (not their own: {self.nm(self.owner_of(worn))}'s)"
        acc = (lk.get("accessory") or (None,))[0]
        acc_txt = "" if not acc else (f", {acc}" if self.wears_accessory(cid) else f", without their usual {acc.replace('pair of ', '')}")
        marks = [x for x, on in (("fresh scratches on the hands", self.has_cond(cid, "scratched")), ("bleeding", self.has_cond(cid, "bleeding")),
                                 ("clothes visibly stained", "stained" in self.tags(worn or "x"))) if on]
        tail = f"; {', '.join(marks)}" if marks else ""
        if short:
            return f"{hair}, {outfit}{acc_txt}{tail}"
        tall = {"short": "short", "medium": "of medium height", "tall": "tall"}[lk["height"]]
        return f"{tall}, {hair}, {lk['eyes']}; wearing {outfit}{acc_txt}{tail}"

    def accessory_item(self, cid):
        return f"acc_{cid}" if self.looks(cid).get("accessory") else None

    def wears_accessory(self, cid):
        acc = self.accessory_item(cid)
        return bool(acc) and (self.world.agents.get(cid) or {}).get("inv", {}).get(acc, 0) > 0

    def fibres_of(self, item):
        """The fabric a garment sheds: an outfit's own fibres, or the garment's name."""
        if not item:
            return []
        spec = self.world.item_spec(item)
        if spec.get("fibres"):
            return list(spec["fibres"])
        name = self.world.item_name(item).lower().replace("bloodstained ", "")
        return [f"{name} fibres"]

    def silhouette(self, cid):
        """What a figure in poor light shows: the hair (unless hidden), the garment's shape, the accessory if worn, and height."""
        w = self.world
        worn = self.worn(cid) if cid in w.agents else None
        coat = self.coat_of(cid)
        spec = w.item_spec(worn) if worn else {}
        hidden = "mask" in self.tags(worn or "x") or coat == "sheet_cloak"
        shape = []
        if coat:
            shape += COAT_SHAPE.get(coat, [])
        elif worn:
            shape += spec.get("shape") or []
        lk = self.looks(cid)
        if not hidden:
            shape += [x for x in lk["shape"] if x not in ("hat", "glasses", "scarf")]
        if self.wears_accessory(cid):
            shape += [x for x in lk["shape"] if x in ("hat", "glasses", "scarf")]
        if lk["height"] != "medium":
            shape.append(lk["height"])
        return sorted(set(shape))

    def normal_shape(self, cid):
        """How someone usually looks in silhouette (in their own clothes, with their accessory): what others compare a glimpse against."""
        lk = self.looks(cid)
        return sorted(set(OUTFITS.get(cid, ("", "", [], []))[3] + lk["shape"] + ([lk["height"]] if lk["height"] != "medium" else [])))

    def body_traces(self, case, culprit, victim, room, struggle, close, dark_here):
        """Clues the killer's body and clothes leave: a hair, fibres of what they wore, a lost accessory; and what people in the dark glimpsed."""
        w, s = self.world, self.s
        out = []
        if not culprit or culprit not in w.agents:
            return out
        vn = self.nm(victim)
        worn = self.worn(culprit)
        coat = self.coat_of(culprit)
        masked = "mask" in self.tags(worn or "x") or coat == "sheet_cloak"
        hl, hc = self.looks(culprit)["hair"]
        p_hair = (0.55 if struggle else 0.35 if close else 0.15) * (0.3 if masked else 1.0)
        if self.rng.random() < p_hair:
            hair = f"{hc} hair from someone with locs" if hl == "locs" else f"{hl} {hc} hair"
            out.append({"room": room, "scene": True, "found_by": [], "kind": "hair", "text": f"A single {hair} is caught in {vn}'s fingers.", "hair": [hl, hc]})
        garment = coat or worn
        fib = self.fibres_of(garment)
        if fib and not any(c.get("kind") == "fibres" for c in case.get("clues", [])) and self.rng.random() < (0.45 if struggle or close else 0.25):
            f = self.rng.choice(fib)
            out.append({"room": room, "scene": True, "found_by": [], "kind": "fibres", "text": f"Fibres of {f} are snagged on {vn}'s clothes.", "fibre": f})
        acc = self.accessory_item(culprit)
        if acc and struggle and self.wears_accessory(culprit) and self.rng.random() < 0.25:
            w.drop(culprit, acc, 1)
            out.append({"room": room, "scene": True, "found_by": [], "kind": "accessory", "text": f"A {self.looks(culprit)['accessory'][0]} lies near the body.", "item": acc})
        for o in dark_here:
            shape = self.silhouette(culprit)
            if shape:
                feat = self.rng.choice(shape)
                case.setdefault("glimpses", []).append({"by": o, "feature": feat})
                w.remember(o, f"In the dark you glimpsed the attacker's shape: {feat}.")
        return out

    def look_facts(self, case, ids):
        """Trial facts from hair, fibres, a lost accessory and glimpses, matched by eye against how everyone looks."""
        out = []
        victim = case.get("victim")
        people = [p for p in ids if p != victim]

        def spread(by, fits, total, kind, text_fit, text_not, base=3.0, clear=-0.4):
            n = max(1, len(fits))
            for p in people:
                if p in fits:
                    out.append({"by": by, "about": p, "kind": "look", "look": kind, "fits": True, "w": min(2.5, base / n), "text": text_fit(p), "true": True})
                elif clear:
                    out.append({"by": by, "about": p, "kind": "look", "look": kind, "fits": False, "w": clear, "text": text_not(p), "true": True})

        for c in case.get("clues", []):
            by = next((f for f in c.get("found_by") or [] if f in ids), None)
            if not by or not self.clue_on_table(c):
                continue
            if c["kind"] == "hair" and c.get("hair"):
                hl, hc = c["hair"]
                fits = [p for p in people if tuple(self.looks(p)["hair"]) == (hl, hc)]
                spread(by, fits, len(people), "hair", lambda p: f"{self.nm(p)}'s hair matches.", lambda p: f"Not {self.nm(p)}'s hair.")
            elif c["kind"] == "fibres" and c.get("fibre"):
                fits = [p for p in people if c["fibre"] in OUTFITS.get(p, ("", "", [], []))[2] or c["fibre"] == (self.looks(p).get("accessory") or (None, None))[1]]
                spread(by, fits, len(people), "fibres", lambda p: f"Those fibres match what {self.nm(p)} wears.", None, clear=0)
            elif c["kind"] == "accessory" and c.get("item"):
                owner = self.owner_of(c["item"])
                if owner in people:
                    missing = not self.wears_accessory(owner)
                    out.append({"by": by, "about": owner, "kind": "look", "look": "accessory", "fits": True, "w": 3.0 if missing else 1.5,
                                "text": f"That's {self.nm(owner)}'s {self.looks(owner)['accessory'][0]}." + (f" {self.nm(owner)} hasn't been wearing it since." if missing else ""), "true": True})
        for g in case.get("glimpses") or []:
            if g["by"] not in ids:
                continue
            fits = [p for p in people if g["feature"] in self.normal_shape(p)]
            spread(g["by"], fits, len(people), "glimpse", lambda p, f=g["feature"]: f"I saw a figure in the dark: {f}. That fits {self.nm(p)}.", None, base=2.5, clear=0)
        return out
