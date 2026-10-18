"""Adult tone: flirtation between people who are into each other, and friendly trash talk and crude jokes between people who are comfortable.

It is flavour, not a rule: it appears only where the relationship and the personalities make it plausible, scaled by two dials in the tuning panel, and the writers are told never to force it,
never to make everyone do it, to keep it between consenting adults and to cut away before anything explicit. ToneMixin is mixed into DayRunner (engine.py).
"""
import zlib

FLIRT = {
    1: "Where two people clearly have chemistry, light flirtation is welcome: lingering looks, a suggestive tease, a charged silence.",
    2: "Where two people have chemistry, flirtation is frequent and bold: innuendo, obvious sexual tension, touching, kissing; a night together may be shown suggestively and cut away before anything explicit.",
    3: "Where two people have chemistry, it is openly sensual and heated: sexual banter, kissing, undressing each other, implied sex that fades to black. Never graphic.",
}
BANTER = {
    1: "Friends tease each other lightly.",
    2: "Friends roast each other, trash-talk affectionately and trade the odd nasty or crude joke (about bodies, habits, love lives, the situation, themselves); people with a sarcastic or edgy streak go further. It is banter between people who are comfortable, not cruelty.",
    3: "Friends are relentless: constant roasting, crude and dark humour, innuendo flying about. Still affection underneath, never cruelty.",
}
GORE = {
    0: "Deaths and wounds are never described: cut away before the blow lands and after the body is found.",
    1: "Violence is clear but restrained: blood and a wound, no lingering on the detail.",
    2: "Violence is vivid and brutal: wounds, blood and broken bodies are described plainly and with weight, and nobody dies prettily.",
    3: "Violence is graphic and visceral: the full horror of wounds, bodies and executions, described unflinchingly.",
}
TONE_GUIDE = ("TONE: mature, darkly funny and brutal at once. TereVi runs it as a game show: punishments are 'segments' with sound cues, fake sponsors "
              "('this execution is brought to you by...'), ratings jokes and a studio audience that is not there. The cast's gallows humour, petty feuds and absurd "
              "mishaps sit right next to the horror, and grief and fear are played straight when they hit. ")
SEX = ("Sex happens between consenting adults whose feelings got there: desire, flirting, the night together implied and cut away from, the morning after, "
       "jealousy, affairs and rumours. Never explicit.")
BANTER_EX = ["'Nice hair. Did you lose a fight with the wardrobe?'", "'You snore like a dying walrus and I say that with love.'", "'Tell me you're not wearing that on purpose. Oh god, you are.'"]
FLIRT_EX = ["'You're staring.' 'I'm admiring.'", "'If you wanted me out of this shirt you only had to ask.'", "'Don't look at me like that unless you mean it.'"]
EDGY_WORDS = ("profanity", "sarcas", "contempt", "insult", "cold", "dry", "scorn", "venom")


class ToneMixin:
    def tone_guide(self):
        """One paragraph every voice call reads (through the bible): comedy, the gore dial, and how sex is handled."""
        g = max(0, min(3, int(self.tune("gore"))))
        return "\n" + TONE_GUIDE + "VIOLENCE: " + GORE[g] + " " + (SEX if int(self.tune("flirt_level")) > 0 else "Nobody here is interested in romance.")

    def chemistry(self, a, b):
        """A stable 0..1 figure for how well two particular people click, so the same pairs keep finding each other."""
        return (zlib.crc32("|".join(sorted((a, b))).encode()) % 100) / 100.0

    def attraction(self, a, b):
        """How plausible flirtation is between these two right now (0 = not at all)."""
        w, s = self.world, self.s
        if a not in w.agents or b not in w.agents:
            return 0.0
        if any(bd["kind"] == "romance" and {bd["a"], bd["b"]} == {a, b} for bd in s.get("bonds", [])):
            return 1.0
        ab, ba = w.agents[a]["aff"].get(b, 0), w.agents[b]["aff"].get(a, 0)
        if min(ab, ba) < 4:
            return 0.0
        base = 0.35 + 0.08 * (min(ab, ba) - 4)
        for x in (a, b):
            if w.agents[x]["drive"]["id"] in ("romantic", "thrill"):
                base += 0.15
            elif w.agents[x]["drive"]["id"] in ("protector", "martyr", "nihilist"):
                base -= 0.1
        return max(0.0, min(0.95, base))

    def flirty_pairs(self, group):
        lvl = int(self.tune("flirt_level"))
        out = []
        if lvl <= 0:
            return out
        thr = {1: 0.45, 2: 0.3, 3: 0.2}[min(3, lvl)]
        hs = [p for p in group if p in self.world.agents]
        for i, x in enumerate(hs):
            for y in hs[i + 1:]:
                if self.attraction(x, y) * (0.5 + self.chemistry(x, y)) >= thr:
                    out.append((x, y))
        return out

    def tone_paragraph(self, group):
        """The global instruction appended to every conversation prompt, from the two dials."""
        fl, bn = int(self.tune("flirt_level")), int(self.tune("banter_level"))
        bits = []
        if bn > 0:
            bits.append(BANTER[min(3, bn)])
        if fl > 0:
            bits.append(FLIRT[min(3, fl)])
        if not bits:
            return ""
        if bn >= 2:
            bits.append("Register examples for banter (do not copy them): " + " ".join(BANTER_EX) + ".")
        if fl >= 2:
            bits.append("Register examples for flirtation (do not copy them): " + " ".join(FLIRT_EX) + ".")
        return ("ADULT TONE (flavour, not a rule): " + " ".join(bits) + " Use it only where it suits those people and the moment (their personalities, how they feel about each other, how tense or safe the scene is); "
                "do not force it and do not make everyone do it. Everyone is an adult and everything is consensual: a person who is not receptive deflects or laughs it off. Nothing explicit.\n")

    def card_tone(self, pid, group):
        """A short, per-person note for a conversation card: who they might flirt with here, who they trade friendly insults with, and what their clothes make of the moment."""
        w = self.world
        a = w.agents.get(pid)
        if not a:
            return ""
        bits = []
        flirt = [y if x == pid else x for x, y in self.flirty_pairs(group) if pid in (x, y)]
        if flirt:
            lover = any(bd["kind"] == "romance" and pid in (bd["a"], bd["b"]) and (bd["b"] if bd["a"] == pid else bd["a"]) in flirt for bd in self.s.get("bonds", []))
            lvl = int(self.tune("flirt_level"))
            bits.append(("is openly flirtatious and touchy with " if lover and lvl >= 2 else "may flirt with ") + ", ".join(self.nm(o) for o in flirt[:2]) + ("" if lover and lvl >= 2 else " if it feels right"))
        bn = int(self.tune("banter_level"))
        if bn >= 1:
            friends = [o for o in group if o != pid and o in w.agents and 2 <= a["aff"].get(o, 0) < 9 and o not in flirt]
            if friends:
                edgy = any(k in (w.cast[pid].get("candor", "") + w.cast[pid].get("speech", "")).lower() for k in EDGY_WORDS)
                bits.append(("trades " + ("rude, affectionate jokes" if edgy or bn >= 3 else "light teasing") + " with " + ", ".join(self.nm(o) for o in friends[:2])))
        k = self.worn(pid) if hasattr(self, "worn") else None
        if k is None and a["room"] not in ("voting_grounds",):
            bits.append("is in their underwear (they are comfortable, embarrassed or defiant about it, as suits them)")
        elif k and "swimwear" in self.tags(k):
            bits.append("is in swimwear")
        return (" Tone here: " + "; ".join(bits) + ".") if bits else ""
