"""Putting words to what the engine decided.

A conversation reaches the voice as beats: who does what to whom (comfort, probe, a lie, a threat...), whether it worked, how loud it was. The voice writes one short line
per beat, in the speaker's own voice, and changes nothing: outcomes were settled before any text existed. Two backends: the language model (one call per conversation,
checked: every beat gets a line from its own speaker, or the template line stands in), and the template voice below, which is the zero-model mode and the test backend.
"""

# move or reply -> outcome ("ok", "fail", "backfire", or "*") -> lines. {t} the other person, {x} who it is about, {item}, {claim}. "*" lines are actions.
T = {
    "chat": {"*": ["So. How are you actually doing, {t}?", "Did you sleep at all last night?", "I keep thinking about home.", "This place is too quiet when nobody's talking.",
                   "Have you eaten? You should eat something.", "Weird day. Even for this place."]},
    "joke": {"*": ["You know what this island needs? A gift shop.", "If I die here, tell TereVi her lighting is terrible.", "I've been on worse holidays. Not many, but some.",
                   "Rate this kidnapping out of ten. I'm saying four."]},
    "comfort": {"ok": ["Hey. Come here. You're not on your own with this.", "Breathe. I've got you, {t}.", "It's okay to not be okay in here."],
                "*": ["You look like you need someone to sit with.", "Talk to me, {t}. What's going on?"]},
    "confide": {"*": ["Can I tell you something I haven't told anyone?", "I'm more scared than I let on. A lot more.", "I don't know who I am in here anymore, {t}."]},
    "flirt": {"*": ["You're the only good thing about this place, you know that?", "Sit closer. For warmth. Obviously.", "If we get out of here, I'm buying you dinner."]},
    "gift": {"*": ["Here. I saved this for you. Take the {item}.", "I want you to have the {item}. Don't argue."]},
    "boast": {"*": ["Honestly, I'd have figured this place out by now if anyone listened to me.", "Back home people queue to talk to me. Just saying.",
                    "I'm the only one here keeping a cool head."]},
    "mock": {"*": ["Wow, {t}, bold choice. Everything you do is a bold choice.", "Did you practise that face, or does it come naturally?", "Careful, {t}, someone might mistake that for an idea."]},
    "putdown": {"*": ["Nobody wants you here, {t}. Nobody.", "You're useless. You know that, right?", "Do us all a favour and shut up for once."]},
    "probe": {"*": ["Where were you when it happened, {t}?", "Walk me through your day. All of it.", "Who did you see on your way back?"]},
    "gossip": {"*": ["Between us? {claim}", "Don't repeat this, but... {claim}", "Have you noticed {x}? {claim}"]},
    "warn": {"*": ["Keep an eye on {x}. I mean it.", "I don't trust {x}, and neither should you.", "Stay away from {x} for a while, {t}."]},
    "reveal": {"*": ["You didn't hear it from me. {x} has been hiding something.", "Want to know what {x} is really like? Come here."]},
    "accuse": {"*": ["It was you, wasn't it, {t}?", "Stop lying. I know you did it, {t}.", "Everything points at you, {t}. Everything."]},
    "threaten": {"*": ["Cross me again and you'll regret it.", "Watch yourself, {t}. I mean that.", "One more word and I swear..."]},
    "confront": {"*": ["We need to talk about what you did, {t}.", "Did you really think I wouldn't find out?", "You owe me an explanation, {t}."]},
    "pact": {"*": ["We watch each other's backs from now on. Deal?", "You and me. Whatever happens, we stick together.", "I need someone I can trust in here. Is that you?"]},
    "recruit": {"*": ["I need a favour, {t}. A big one. No questions.", "If anyone asks, I was with you tonight. Okay?"]},
    "teamwork": {"*": ["If we rewire this properly, it might actually work.", "Hold that end. No, the other end.", "We're close. I can feel it."]},
    "incite": {"*": ["{x} is going to come for you. Better you move first.", "Think about it, {t}. {x} would do it to you without blinking."]},
    "feign": {"*": ["I'm really glad we're getting on, {t}.", "You're one of the few people I like here, honestly.", "Let me know if you need anything. Anything at all."]},
    "side": {"*": ["{t} has a point.", "Leave {t} alone.", "I'm with {t} on this one.", "Don't drag me into it. But {t}'s right."]},
    # replies
    "warm": {"*": ["Yeah. Thanks, {t}.", "That's... actually nice to hear.", "I'm glad it's you I'm stuck with."]},
    "agree": {"*": ["Okay. Yeah.", "I was thinking the same thing.", "Fine. I'm in."]},
    "laugh": {"*": ["Ha! Okay, that was good.", "Stop, I can't. Ha.", "Four is generous."]},
    "shrug": {"*": ["Mm.", "Sure. If you say so.", "I don't really want to talk about it.", "Okay."]},
    "accept": {"*": ["Okay. Thank you, {t}.", "Deal.", "...Yeah. I needed that."]},
    "refuse": {"*": ["No. Don't ask me that.", "I can't, {t}. I'm sorry.", "Absolutely not."]},
    "rebuff": {"*": ["I'm fine. Leave it.", "Not now, {t}.", "Why would I tell you that?"]},
    "snap": {"*": ["Back off, {t}!", "Oh, that's rich, coming from you.", "Don't you dare."]},
    "back_down": {"*": ["...Fine. Whatever.", "Okay, okay. I get it.", "I didn't mean anything by it."]},
    "stand_up": {"*": ["Say that again. I dare you.", "You don't scare me, {t}.", "I'm not one of your fans. Try that on someone else."]},
    "testify": {"*": ["{claim}", "Honestly? {claim}"]},
    "lie": {"*": ["{claim}", "Me? {claim} Ask anyone."]},
    "deflect": {"*": ["Why are you asking me? Ask {t} where they were.", "That's none of your business.", "I don't remember. It's all a blur."]},
    "deny": {"*": ["That's insane. I didn't do anything!", "You've got no proof, {t}.", "I would never. Never."]},
    "counter": {"*": ["Funny, I was about to say the same about you.", "Look who's talking.", "You're pointing at me so nobody looks at you."]},
    "freeze": {"*": ["...", "I... I don't...", "That's not... I can't..."]},
}
ACTS = {"comfort": "puts a hand on {t}'s shoulder", "gift": "presses the {item} into {t}'s hands", "threaten": "steps right up to {t}", "putdown": "turns away from {t}",
        "pact": "holds out a hand to {t}", "teamwork": "hands {t} a screwdriver", "flirt": "nudges {t} with an elbow", "snap": "jabs a finger at {t}",
        "laugh": "bursts out laughing", "confide": "lowers their voice and leans in"}
HEDGES = {"nervous": ("I... ", ""), "wry": ("", " Honestly."), "blunt": ("", ""), "warm": ("", "")}


def manner(eng, cid):
    """A speaker's manner for the template voice, from their nature and state."""
    a = eng.world.agents.get(cid)
    if not a:
        return "blunt"
    f = (lambda n: eng.facet(cid, n)) if eng.mind_on() else (lambda n: 50)
    if a["sanity"] < 40 or f("stress_vulnerability") >= 70:
        return "nervous"
    if f("humour") >= 65:
        return "wry"
    if f("altruism") >= 65:
        return "warm"
    return "blunt"


def template_line(eng, beat, rng):
    """One line for a beat in the template voice."""
    mv = beat["move"]
    pool = T.get(mv) or T["chat"]
    lines = pool.get(beat.get("outcome")) or pool.get("*") or T["chat"]["*"]
    t = eng.nm(beat.get("to")) if beat.get("to") else "you"
    x = eng.nm(beat["about"]) if beat.get("about") else "them"
    item = eng.world.item_name(beat["item"]) if beat.get("item") else "this"
    claim = beat.get("claim") or "I don't know anything."
    if mv in ACTS and beat.get("outcome") in ("ok", "backfire") and rng.random() < 0.35:
        return {"speaker": beat["who"], "kind": "act", "text": ACTS[mv].format(t=t, x=x, item=item)}
    if mv == "chat":
        own = (eng.world.char(beat["who"]) or {}).get("mock_lines") or []
        if own and rng.random() < 0.5:
            lines = own
    text = rng.choice(lines).format(t=t, x=x, item=item, claim=claim)
    pre, post = HEDGES[manner(eng, beat["who"])]
    if pre and rng.random() < 0.4 and not text.startswith("I... "):
        first = text.split(" ", 1)[0]
        text = pre + (text if first in ("I", "I'm", "I've", "I'd", "I'll") or first.startswith("I'") else text[0].lower() + text[1:])
    if post and rng.random() < 0.25 and text.endswith("."):
        text = text + post
    return {"speaker": beat["who"], "kind": "say", "text": text}


def spoken_line(eng, beat, rng):
    """A template line that is speech, never an action."""
    for _ in range(6):
        ln = template_line(eng, beat, rng)
        if ln["kind"] == "say":
            return ln
    return {"speaker": beat["who"], "kind": "say", "text": "Mm."}


MOVE_WORDS = {"chat": "makes small talk with", "joke": "jokes with", "comfort": "comforts", "confide": "confides in", "flirt": "flirts with", "gift": "gives a gift to",
              "boast": "boasts to", "mock": "mocks", "putdown": "insults", "probe": "questions", "gossip": "gossips with", "warn": "warns", "reveal": "lets a secret slip to",
              "accuse": "accuses", "threaten": "threatens", "confront": "confronts", "pact": "proposes a pact to", "recruit": "quietly asks for help from",
              "teamwork": "works on the way out with", "incite": "tries to turn against someone:", "feign": "fakes friendliness toward", "side": "sides with",
              "warm": "responds warmly to", "agree": "agrees with", "laugh": "laughs with", "shrug": "shrugs off", "accept": "accepts from", "refuse": "refuses",
              "rebuff": "brushes off", "snap": "snaps at", "back_down": "backs down before", "stand_up": "stands up to", "testify": "answers", "lie": "lies to",
              "deflect": "deflects", "deny": "denies it to", "counter": "turns it back on",
              "freeze": "freezes, trapped, in front of"}


def beat_text(eng, i, b):
    """A beat in plain words for the model."""
    who, to = eng.nm(b["who"]), eng.nm(b.get("to")) if b.get("to") else ""
    s = f"{i}. {who} ({b['who']}) {MOVE_WORDS.get(b['move'], b['move'])} {to}".rstrip()
    if b.get("about"):
        s += f" (about {eng.nm(b['about'])})"
    if b.get("item"):
        s += f" (the {eng.world.item_name(b['item'])})"
    if b["move"] in MOVE_WORDS and b.get("reply_to") is None and b["move"] not in ("side",):
        s += {"ok": " - it lands", "fail": " - it falls flat", "backfire": " - it backfires"}.get(b.get("outcome"), "")
    if b.get("cont"):
        s += " - they go on from their own last line; this is not a reply to themselves"
    if b.get("shares"):
        s += f"; what they open up about: {b['shares']}"
    if b.get("claim"):
        s += f'; they say, in substance: "{b["claim"]}"' + (" (a LIE)" if b["move"] == "lie" else "")
    if b.get("loud") in ("whisper", "heated"):
        s += f" [{'whispered' if b['loud'] == 'whisper' else 'raised voice'}]"
    return s


PRONOUNS = {"he": "he/him", "she": "she/her", "they": "they/them"}


def part_of_day(h):
    h = h % 24
    return "early morning" if 5 <= h < 9 else "morning" if h < 12 else "afternoon" if h < 17 else "evening" if h < 21 else "night"


def scene_time(conv, beats):
    t = conv.get("hour", 12) + (beats[0]["m"] if beats else conv.get("m0", 0)) / 60
    return f"{int(t % 24):02d}:{int(t * 60) % 60:02d}, {part_of_day(t)}"


def beats_block(eng, beats):
    """The beats, numbered, with a marker where minutes pass between exchanges."""
    out, prev = [], None
    for i, b in enumerate(beats):
        if prev is not None and b.get("ex") != prev.get("ex") and b["m"] - prev["m"] >= 2.5:
            out.append("   (a few minutes later)")
        out.append(beat_text(eng, i, b))
        prev = b
    return "\n".join(out)


def voice_prompt(eng, conv, beats):
    """(system, user) for one model call that voices a whole conversation."""
    w = eng.world
    cards = []
    for p in conv["members"]:
        if p not in w.agents:
            continue
        c, a = w.cast[p], w.agents[p]
        rel = "; ".join(f"{eng.nm(o)} {a['aff'].get(o, 0):+d}" for o in conv["members"] if o != p and o in w.agents)
        pron = PRONOUNS.get(c.get("pron"), "they/them")
        lk = eng.looks_notable(p)
        cards.append(f"- {p} = {c['name']} ({c.get('gender', 'person')}, {pron}), {c['role']}." + (f" Notable right now: {lk}." if lk else "")
                     + f" Speech: {c['speech']} Mood: {eng.mood_text(a)}. Feelings: {rel or 'n/a'}.")
    sysm = (eng.bible() + " You voice a scene the game has already decided: you write the words, never the outcomes. Plain, natural, short spoken lines, each in the speaker's own voice. "
            "Reply with a single JSON object and nothing else.")
    rule = (eng.s.get("rule") or {}).get("text")
    user = (f"SCENE: Day {eng.day}, {scene_time(conv, beats)}, {w.room_name(conv['room'])}. Why they are talking: {conv.get('why') or 'they happen to be together'}.\n"
            + (f"TODAY'S RULE (they know it): {rule}\n" if rule else "")
            + "PEOPLE:\n" + "\n".join(cards) + "\nBEATS (in order; each already happened exactly as stated):\n" + beats_block(eng, beats) + "\n"
            "Write exactly one line per beat, spoken (or done) by that beat's person to the person named in it: max 20 words, plain speech. A reply answers the other person's line "
            "before it; a new move after a pause starts something new; nobody ever answers their own line. Greetings and talk of the time must fit the time of day. Use the right "
            "pronouns and gendered words for each person. A pet name, catchphrase or verbal tic at most once per person in the whole scene; do not comment on anyone's looks unless "
            "it is listed as notable right now. A beat whose person mostly acts may be an "
            "action line instead (kind \"act\", starts with a verb, no name, max 14 words). Never add events, never change who wins or loses, never reveal anything not in the beats. "
            'Reply as JSON: {"lines": [{"beat": 0, "speaker": "<id>", "kind": "say|act", "text": "..."}]}')
    return sysm, user


def check_lines(eng, beats, res, rng):
    """The model's lines, beat by beat, with the template voice standing in for any beat that is missing or spoken by the wrong person."""
    got = {}
    for ln in (res or {}).get("lines") or []:
        try:
            i = int(ln.get("beat"))
        except Exception:
            continue
        if 0 <= i < len(beats) and ln.get("speaker") == beats[i]["who"] and str(ln.get("text") or "").strip() and i not in got:
            got[i] = {"speaker": beats[i]["who"], "kind": "act" if ln.get("kind") == "act" else "say", "text": str(ln["text"]).strip()[:200]}
    out, fixed = [], 0
    for i, b in enumerate(beats):
        if i in got:
            out.append(got[i])
        else:
            out.append(template_line(eng, b, rng))
            fixed += 1
    return out, fixed
