"""Reusable contestants transcribed from the supplied character cards.

A casting slot describes the show's allocation, independently of identity/pronouns.
Ages and private conflicts are writing defaults; the cards specify neither age.
"""

GUEST_ADDITIONS = {
    "ivette": {
        "name": "Ivette Blanchett", "short": "Ivette", "role": "Bartender", "gender": "female", "pron": "she",
        "age": 29, "origin": "France", "birthday": "October 10", "height_cm": 177, "weight_kg": 64,
        "home": "red_room", "color": "#9b2846", "card": "",
        "persona": "A well-known French bartender whose flair cocktail performances made her hometown bar a destination. She learned service from the unglamorous end: closing shifts, cleaning spills and noticing who needed water rather than another drink. Regulars returned for her good humor and knack for listening without making every confession about herself. Confident, sociable and flirtatious, she enjoys conversation and playful chemistry, but professional friendliness is not a promise of romance. She remembers preferences, makes room for quiet people and can turn a tense table into a conversation. Dishonesty and customers harassing staff end her patience quickly. She has physically removed troublemakers and drunken patrons; she prefers a clear warning and a safe exit before force. Her weakness is deciding she can manage everyone's emotions while hiding her own. On the island she wants to create somewhere people can decompress, but must learn when listening becomes accepting responsibility for choices she cannot control.",
        "secret": "A regular once trusted her with a confession that put another friend in an awkward position. Keeping that confidence cost her the friendship; she still struggles to decide when discretion becomes complicity.",
        "likes": "conversation, flirting, flair cocktail making, making people feel welcome",
        "dislikes": "troublemakers, dishonesty, harassment, people ignoring a clear refusal",
        "speech": "Relaxed, attentive and lightly teasing. Asks useful follow-up questions. Her voice turns short and firm when setting a boundary. 'You can tell me about it. You can't take it out on them.'",
        "candor": "Warm and confident, enjoys reciprocal flirting without assuming attraction. Keeps confidences, challenges lies and gives troublemakers a clear boundary before escalating.",
        "goals": "Build trust, offer people a place to talk, protect others from harassment, and decide which confidences are safe to keep.",
        "start": {"hp": 100, "sanity": 88}, "inv": {"water_bottle": 2, "notebook": 1, "pen": 1},
        "aff": {}, "diary": [],
        "mock_lines": ["Tell me the version you haven't rehearsed.", "Water first. Then we talk.", "That was charming. Was it also true?", "They asked you to stop."],
        "facets": {"anger": 42, "vengefulness": 35, "trust": 55, "gregariousness": 88, "altruism": 72, "assertiveness": 78, "courage": 70, "cruelty": 18, "impulsiveness": 38, "stress_vulnerability": 40, "vanity": 48, "ambition": 62, "curiosity": 72, "orderliness": 75, "humour": 82, "romantic": 68},
        "values": {"truth": 85, "friendship": 85, "cooperation": 80, "self_control": 75, "loyalty": 75},
    },
    "reiko": {
        "name": "Reiko Reyrbart", "short": "Reiko", "role": "Disc Jockey", "gender": "female", "pron": "she",
        "casting_slot": "male", "traits": ["blind"],
        "age": 24, "origin": "Norway", "birthday": "December 4", "height_cm": 167, "weight_kg": 62,
        "home": "green_room", "color": "#9dce48", "card": "",
        "persona": "A cheerful, energetic Norwegian DJ who is blind. She began playing small clubs and local events, uploading music and remixes until an audience grew beyond the people who could attend. Major-label contracts followed, then international music festivals where her bass-heavy sets and infectious enthusiasm became her signature. Her success rests on practice, accessible equipment, tactile controls and preparation, not supernatural hearing. She loves deep bass, dancing crowds and parties that make strangers feel included. She dislikes drawn-out discussions and arguments, often reaching for a joke or a new track instead of staying with an uncomfortable disagreement. Stairs are an annoying access obstacle; she asks for directions or an arm when useful and expects people to ask before touching or guiding her. Uses a white cane to explore unfamiliar places and learns routes through ordinary practice. She can listen to voices and descriptions, but cannot see faces, gestures, written clues or footage. She wants equal participation rather than people deciding what she can do for her. Under stress her relentless cheer can become avoidance; with trust she admits when something is difficult and stays for conversations she cannot remix away.",
        "secret": "She has been avoiding a difficult conversation with a collaborator about taking too much of the credit for a successful remix. Her cheerful replies have postponed an apology she knows she owes.",
        "likes": "deep bass, partying, remixing music, an enthusiastic crowd",
        "dislikes": "drawn-out discussions, stairs, unsolicited grabbing or guiding, being underestimated",
        "speech": "Upbeat, rhythmic and quick to joke; asks direct practical questions about unfamiliar spaces. 'Great speech. Does it have a bass drop?' When serious, slows down and lets the silence remain.",
        "candor": "Cheerful and independent, sometimes deflects conflict with humor. Ask before helping. Blindness does not remove her agency or grant extraordinary senses; describe audible and tactile information rather than visual observations.",
        "goals": "Keep people connected through music, learn safe routes around the island, contribute what she actually hears, and stop dodging a necessary apology.",
        "start": {"hp": 100, "sanity": 90}, "inv": {"white_cane": 1, "notebook": 1, "water_bottle": 1},
        "aff": {}, "diary": [],
        "mock_lines": ["Okay, this room needs a better soundtrack.", "Tell me where the step is, please.", "You can ask before taking my arm.", "Fine. No jokes for a minute. I'm listening."],
        "facets": {"anger": 30, "vengefulness": 22, "trust": 65, "gregariousness": 92, "altruism": 65, "assertiveness": 68, "courage": 70, "cruelty": 12, "impulsiveness": 65, "stress_vulnerability": 45, "vanity": 48, "ambition": 80, "curiosity": 78, "orderliness": 62, "humour": 90, "romantic": 58},
        "values": {"independence": 90, "friendship": 88, "cooperation": 78, "ambition": 75, "tranquility": 35},
    },
}
