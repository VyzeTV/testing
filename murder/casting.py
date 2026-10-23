"""Select a season's participants from the reusable character roster."""
import random

from .data_cast import CHARACTERS

SLOTS = {"female": 4, "male": 4}


def slot_for(profile):
    """The show allocation; identity and pronouns remain independent."""
    slot = profile.get("casting_slot", profile.get("gender"))
    if slot not in SLOTS:
        raise ValueError("Choose a female or male casting slot.")
    return slot


def select_cast(rng=None):
    rng = rng if rng is not None else random.Random()
    selected = set()
    for gender, count in SLOTS.items():
        pool = sorted(cid for cid, c in CHARACTERS.items() if slot_for(c) == gender)
        if len(pool) < count:
            raise ValueError(f"The roster needs at least {count} {gender} characters")
        selected.update(rng.sample(pool, count))
    # Stable roster order keeps later simulation randomness independent of set order.
    return [cid for cid in CHARACTERS if cid in selected]


FRESH_GOALS = {
    "szymon": "Get liked, explore the island, get great footage, and prove he is brave while facing his fear of tight spaces.",
    "seul": "Find a worthy rival, spot cheating when there is evidence, protect her secret and keep her energy up.",
    "vixen": "Trace the island's systems, learn what the hosts are hiding, keep her commission secret, and find a way out.",
    "noah": "Make friends, write a real song, and decide whom he can trust with his private worries.",
    "ayden": "Keep his secret safe, encourage talent he encounters, stay admired, and find a perfect shot of the island.",
    "shintaro": "Keep his persona intact, test whom he can trust, and work out what this place really is.",
    "chloe": "Find something worth drawing, form genuine friendships, and grow confident enough to share her art.",
    "cail": "Be liked beyond her public image, keep her followers and painkillers secret, and form real relationships.",
}

FRESH_SECRETS = {
    "cail": "About 40% of her followers are bought bots. She takes strong painkillers for an old knee injury, hidden in her hairbrush case.",
    "chloe": "She is a devoted fan of Cail and has a private sketchbook based on her public photos. She carries an unread letter meant for someone she loved back home.",
}

FRESH_LINES = {
    "szymon": ["Legends are made in hedges, my friends!", "If a ghost shows up, I'm filming it.", "Okay but who locked the Study?", "Nobody tell anyone I screamed.", "That draught is following me, I swear."],
}
