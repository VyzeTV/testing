"""Adult tone: flirtation between people who are into each other, and friendly trash talk and crude jokes between people who are comfortable.

It is flavour, not a rule: it appears only where the relationship and the personalities make it plausible, scaled by two dials in the tuning panel, and the writers are told never to force it,
never to make everyone do it, to keep it between consenting adults and to cut away before anything explicit. ToneMixin is mixed into DayRunner (engine.py).
"""
import zlib

FLIRT = {
    1: "Where two people clearly have chemistry, light flirtation is welcome: lingering looks, a suggestive tease, a charged silence.",
    2: "Where two adults have chemistry, allow bold innuendo, double meanings, suggestive invitations, teasing about attraction and a welcome kiss. Let a flirt land, get teased back or be declined.",
    3: "Where two adults have chemistry, the dialogue can be sensual and cheekily dirty: sexual innuendo, provocative teasing, double entendres, daring invitations and a welcome kiss. Build tension through words, pauses and mutual reactions. Implied sex fades to black before sexual activity. Never graphic.",
}
BANTER = {
    1: "Friends tease each other lightly.",
    2: "Friends trade affectionate insults, sarcastic comebacks, gallows humour and occasional crude jokes. Let someone answer a roast and get the last word. Swearing can be playful as well as angry. Keep warmth underneath and leave room for sincere conversation.",
    3: "Friends can be relentless when both enjoy it: sharp comebacks, affectionate trash talk and crude or dark jokes. Vary the rhythm; do not turn every line into a punchline. Stop when someone is hurt or asks them to quit.",
}
GORE = {
    0: "Deaths and wounds are never described: cut away before the blow lands and after the body is found.",
    1: "Violence is clear but restrained: blood and a wound, no lingering on the detail.",
    2: "Violence is vivid and brutal: wounds, blood and broken bodies are described plainly and with weight, and nobody dies prettily.",
    3: ("Violence is graphic and visceral, horror-film explicit: name the wound and what it does to the body (the blade grating on bone, the skull giving way, "
        "the eyes reddening as a throat is crushed), the blood and how it moves, the sounds and smells, how long dying takes, and what the body looks like after. "
        "Executions are described step by step, the device and the body's response, with no cutaway. Never sexual violence, never cruelty played for laughs."),
}
TONE_GUIDE = ("TONE: mature, darkly funny and brutal at once. TereVi runs it as a game show: punishments are 'segments' with sound cues, fake sponsors "
              "('this execution is brought to you by...'), ratings jokes and a studio audience that is not there. The cast's gallows humour, petty feuds and absurd "
              "mishaps sit right next to the horror, and grief and fear are played straight when they hit. ")
SPEECH = ("DIALOGUE: characters may swear naturally and uncensored, including 'fuck', 'shit' and 'bastard', for surprise, frustration, emphasis or affectionate banter. "
          "Match each person's vocabulary: some swear freely, some rarely, some get awkward or deadpan. No asterisk censorship, compulsory profanity or identical voices. "
          "Let jokes get a comeback, a laugh, an eye-roll or an awkward silence; friends can enjoy each other without every exchange becoming an insult. ")
SEX = ("Sexual themes are only for consenting characters explicitly aged 18 or older. Desire, awkward attraction, sexual humour, jealousy, affairs, "
       "private invitations and morning-after embarrassment can be mature without erotic detail. Show mutual interest; a refusal or hesitation ends the advance. "
       "Friendship, flirting and clothing never establish consent or a romance by themselves. Keep childhood memories nonsexual. "
       "An intimate night may be implied, then fade to black before sexual activity; no sexual anatomy, arousal descriptions or descriptions of sex acts. Never explicit.")
BANTER_EX = ["'You're a pain in the arse.' 'And yet you saved me a seat.'", "'That was your plan?' 'It sounded less shit in my head.'", "'Keep talking. I nearly mistook you for the sensible one.'"]
FLIRT_EX = ["'Is that an invitation?' 'Depends. Are you going to make me regret it?'", "'You're trouble.' 'You keep sitting closer.'", "'Behave.' 'Give me a good reason.'"]
# Mock/fallback lines use the same register without inventing physical intimacy.
BANTER_LINES = ["Your plan sounds like a fucking terrible idea. Naturally, I'm listening.", "You're a pain in the arse, {t}. Good thing I like you.",
                "Five-star hospitality. Absolute shit room service.", "That sounded much less stupid before you said it out loud."]
FLIRT_LINES = ["You're making it very difficult to behave, {t}.", "Careful with that invitation. I might take you seriously.",
               "Keep teasing me like that and I'll start thinking you mean it."]
EDGY_WORDS = ("profanity", "sarcas", "contempt", "insult", "cold", "dry", "scorn", "venom")


class ToneMixin:
    def tone_guide(self):
        """Post-reveal game-show horror, separate from the dialogue register."""
        g = max(0, min(3, int(self.tune("gore"))))
        return "\n" + TONE_GUIDE + "VIOLENCE: " + GORE[g]

    def dialogue_guide(self):
        """The same writing register before and after the reveal, using saved dials."""
        fl, bn = int(self.tune("flirt_level")), int(self.tune("banter_level"))
        bits = [SPEECH, BANTER[min(3, bn)] if bn > 0 else "Keep the banter civil; no crude jokes."]
        bits.append(FLIRT[min(3, fl)] + " " + SEX if fl > 0 else "Do not add sexual innuendo, sexual jokes or new romantic advances; preserve existing relationship facts.")
        bits.append("Ordinary conversation, friendship, grief and investigation still need space. Match the moment; do not force chemistry or turn teasing into a new relationship or event.")
        return "\n" + " ".join(bits)

    def chemistry(self, a, b):
        """A stable 0..1 figure for how well two particular people click, so the same pairs keep finding each other."""
        return (zlib.crc32("|".join(sorted((a, b))).encode()) % 100) / 100.0

    def attraction(self, a, b):
        """How plausible flirtation is between these two right now (0 = not at all)."""
        w, s = self.world, self.s
        if a not in w.agents or b not in w.agents:
            return 0.0
        if any(w.cast[p].get("age", 0) < 18 for p in (a, b)):
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
                "do not force it and do not make everyone do it. Sexual themes require consensual interest between characters explicitly aged 18 or older. "
                "A person who is not receptive can decline plainly; respect that and move on. Keep childhood memories nonsexual. Nothing explicit.\n")

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
            friends = [o for o in group if o != pid and o in w.agents and min(a["aff"].get(o, 0), w.agents[o]["aff"].get(pid, 0)) >= 2 and o not in flirt]
            if friends:
                edgy = any(k in (w.cast[pid].get("candor", "") + w.cast[pid].get("speech", "")).lower() for k in EDGY_WORDS)
                bits.append(("trades " + ("rude, affectionate jokes" if edgy or bn >= 3 else "light teasing") + " with " + ", ".join(self.nm(o) for o in friends[:2])))
        k = self.worn(pid) if hasattr(self, "worn") else None
        if k is None and a["room"] not in ("voting_grounds",):
            bits.append("is in their underwear (they are comfortable, embarrassed or defiant about it, as suits them)")
        elif k and "swimwear" in self.tags(k):
            bits.append("is in swimwear")
        return (" Tone here: " + "; ".join(bits) + ".") if bits else ""
