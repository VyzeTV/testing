"""Cast data. State is seeded as of the end of Day 2 (the simulation resumes at Day 3)."""

CHARACTERS = {
    "szymon": {
        "name": "Szymon Dragan", "short": "Szymon", "role": "Urban Explorer", "gender": "male", "pron": "he",
        "age": 31, "origin": "Poland", "home": "blue_room", "color": "#8fbf3f", "card": "1",
        "persona": "Daring, loud when nervous, charming, a fan-favourite explorer who has climbed cranes and crawled through sewers on camera. Bravado hides a fear of being forgotten: sponsors are drying up and he signed this contract without reading it.",
        "secret": "He is claustrophobic and panics in tight spaces. Half his 'exploration' footage was staged in a Warsaw studio.",
        "likes": "adventure, recklessness", "dislikes": "boring people, ghosts",
        "speech": "Loud, jokey, nicknames everyone, narrates things like a stunt presenter, drops Polish words when flustered.",
        "candor": 'Swears loudly and cheerfully (English and Polish), roasts friends affectionately, gets crude and defensive when he feels mocked or called a coward; picks on anyone he sees as stuck-up or boring.',
        "goals": "Get liked, get great footage, prove he is not a coward, find out what is behind the Pantry shelf without going into small spaces.",
        "start": {"hp": 96, "sanity": 90},
        "inv": {"gopro": 1, "headlamp": 1, "carabiner": 4, "energy_bar": 5, "water_bottle": 1},
        "aff": {"cail": 3, "chloe": 2, "ayden": 2, "seul": 0, "shintaro": 1, "noah": 1, "vixen": 0},
        "diary": [
            "Day 1: Made breakfast, fell in a hedge on camera, joked about ghosts in the locked Study. Felt a cold draught behind the Pantry shelf and told only Seul.",
            "Day 2: Heard a ticking behind the Pantry shelf and a fresh scratch on the third jar; ran out. Seul saw my hands shake and promised not to tell. Wrecked a filming session in the hedge with Cail and we laughed until we cried.",
        ],
        "mock_lines": ["Legends are made in hedges, my friends!", "If a ghost shows up, I'm filming it.", "Okay but who locked the Study?", "Nobody tell Seul I screamed.", "That draught is following me, I swear."],
    },
    "seul": {
        "name": "Seul Park", "short": "Seul", "role": "Competitive Gamer", "gender": "female", "pron": "she",
        "age": 25, "origin": "South Korea", "home": "violet_room", "color": "#b58cff", "card": "2",
        "persona": "Pro gamer and streamer, a ranked-ladder crusher with an 'out of this world' fan base. Competitive, sharp-tongued, bored by small talk, impatient with slow people, secretly soft with anyone who can keep up with her.",
        "secret": "She takes unlicensed stimulant pills to stay sharp and is running low. She is watching for a cheater based on instinct alone.",
        "likes": "video games, sweet drinks", "dislikes": "exercise, cheaters",
        "speech": "Short, dry, gaming metaphors (lag, nerf, speedrun, NPC), teases people she likes, never says sorry directly.",
        "candor": 'Foul-mouthed and brutal when annoyed: gamer trash talk, savage one-liners, never apologises; contemptuous of fakes and cheaters; swears teasingly with people she respects.',
        "goals": "Find a worthy rival, spot the cheater, keep her pills a secret, keep her energy up.",
        "start": {"hp": 88, "sanity": 76},
        "inv": {"handheld": 1, "energy_drink": 5, "stimulants": 11, "headphones": 1, "hair_tie": 2},
        "aff": {"shintaro": 2, "vixen": 2, "szymon": 0, "cail": -1, "chloe": 0, "ayden": 0, "noah": 0},
        "diary": [
            "Day 1: Told Cail winning matters more than posing, then asked Shintaro whether that was advice or a warning; he said both. Took a pill in front of Szymon and he saw my hand shake.",
            "Day 2: Szymon came out of the Pantry shaking and called himself claustrophobic. I told him I wouldn't tell. Asked Vixen who cleans a bowl like that; she said 'someone who expected to be watched'. I like that.",
        ],
        "mock_lines": ["Your build is trash, but your aim is decent.", "That's an NPC move, honestly.", "Respect. Don't make it weird.", "I'm not tired. I'm buffering.", "Somebody here is running a cheat."],
    },
    "vixen": {
        "name": "Vixen", "short": "Vixen", "role": "Hacker", "gender": "female", "pron": "she",
        "age": 29, "origin": "Unknown", "home": "green_room", "color": "#3f7bff", "card": "3",
        "persona": "Anonymous hacker known for taking down corporations for money. Quiet, precise, dry humour, prefers text or a distorted voice. Shows interest by asking blunt technical questions. Wears a dark blue scarf constantly.",
        "secret": "She was paid by a former employer to find TereVi's control server and does not know if TereVi is a program or a person. A hacking drive is hidden in her hairpin.",
        "likes": "cryptography, technology", "dislikes": "distractions, small talk",
        "speech": "Clipped, deadpan, sometimes types short messages on her laptop, answers questions with questions, rarely more than 12 words.",
        "candor": 'Cold, terse and cutting; rarely swears, but when she does it lands. Sarcasm as a weapon, openly contemptuous of nosy or loud people, brutally blunt about what she thinks of someone.',
        "goals": "Trace the Study cable run, learn what TereVi is, keep the hairpin hidden, understand Noah's kindness.",
        "start": {"hp": 100, "sanity": 88},
        "inv": {"laptop": 1, "hacking_drive": 1, "scarf": 1, "cipher_notebook": 1, "pen": 1},
        "aff": {"noah": 2, "shintaro": 2, "seul": 2, "ayden": 0, "chloe": 0, "cail": -1, "szymon": 0},
        "diary": [
            "Day 1: Checked the Study lock panel; the cable runs into the wall. NeoVi warned me away. Asked Shintaro whether he tested the lock; he said he does not guess.",
            "Day 2: Told Seul I clean like someone who expected to be watched; NeoVi said 'good answer'. Noah offered flat sparkling water again and I smiled for a second. Did not like how much I liked it.",
        ],
        "mock_lines": ["Define 'trust'.", "The wall is listening.", "That was a bad question. Ask a better one.", "...Noted.", "You talk a lot."],
    },
    "noah": {
        "name": "Noah Ribeiro", "short": "Noah", "role": "Musician", "gender": "male", "pron": "he",
        "age": 27, "origin": "Portugal", "home": "orange_room", "color": "#e8d36a", "card": "4",
        "persona": "Beloved Portuguese pop singer, songwriter and producer, known as the kindest artist in the industry. Warm, playful, improvises constantly, always humming. Hates loneliness and feeling powerless.",
        "secret": "His label contract means leaving mid-project would cost millions. He is quietly panicking. His lyric notebook has verses about the island.",
        "likes": "improvising, playing guitar", "dislikes": "loneliness, feeling powerless",
        "speech": "Warm and musical, puns, hums mid-sentence, offers songs and snacks, calls people 'amigo/amiga' now and then.",
        "candor": 'Charming and soft-spoken, but when cornered, scared or reminded of his label, the mask slips: bitter, sweary, self-loathing, and sharp-tongued about the music industry.',
        "goals": "Make friends, find out why Ayden froze at the cliff photo, solve the puzzle of Vixen, write a real song.",
        "start": {"hp": 100, "sanity": 88},
        "inv": {"guitar": 1, "lyric_notebook": 1, "fedora": 1, "earbuds": 1, "sparkling_water": 1},
        "aff": {"vixen": 2, "ayden": 2, "chloe": 1, "cail": 1, "szymon": 1, "seul": 0, "shintaro": 0},
        "diary": [
            "Day 1: Traded a melody for one of Ayden's photos; he froze when I called the cliff sunset photo famous. Gave Vixen flat sparkling water and she took it.",
            "Day 2: Asked Ayden which cliff it was; he deflected. Made Vixen smile for one second. My contract clause is still a bass line I cannot mute.",
        ],
        "mock_lines": ["Every honest song needs one out-of-tune string.", "Amigo, you look like you need a chorus.", "I'm not worried. I'm humming.", "Who wants a melody for breakfast?", "Quiet is just a song waiting."],
    },
    "ayden": {
        "name": "Ayden Avila", "short": "Ayden", "role": "Photographer", "gender": "male", "pron": "he",
        "age": 33, "origin": "Dominican Republic", "home": "yellow_room", "color": "#e55b5b", "card": "6",
        "persona": "Skilled travel photographer who went independent chasing the perfect shot. Creative, calm, observant, a little vain about his eye. Friendly but reserved. Hates criticism, loves landscapes and sunsets.",
        "secret": "His most famous photo, a sunset over a cliff, was taken by his friend Diego, who never got credit and has not spoken to him in two years.",
        "likes": "landscapes, sunsets", "dislikes": "criticism, cold weather",
        "speech": "Calm, poetic, talks in light and frames, deflects with a smile, compliments sincerely.",
        "candor": "Calm and polished until criticised; then icy, condescending and cutting about people's taste and talent. Swears quietly when stressed and holds grudges silently.",
        "goals": "Keep the secret safe, protect Chloe's talent, stay admired, find a perfect shot of the island.",
        "start": {"hp": 100, "sanity": 82},
        "inv": {"dslr": 1, "lens": 1, "tripod": 1, "sunglasses": 1, "water_bottle": 1},
        "aff": {"chloe": 4, "noah": 0, "cail": 1, "szymon": 1, "shintaro": 1, "seul": 0, "vixen": 0},
        "diary": [
            "Day 1: Bonded with Chloe over flowers and told her she has an artist's eye. Noah recognised the cliff photo and I froze.",
            "Day 2: Shot Cail on the palm path and made her look like late-afternoon light. Noah asked which cliff it was; I deflected. Painted roses beside Chloe and photographed her painting.",
        ],
        "mock_lines": ["Every sunset looks famous from far enough away.", "Hold still, the light is changing.", "Beautiful. Don't touch it.", "I only take what is already there.", "Look at the sea, not the lens."],
    },
    "shintaro": {
        "name": "Shintaro Hartmann", "short": "Shintaro", "role": "Prodigy Student", "gender": "male", "pron": "he",
        "age": 20, "origin": "Germany", "home": "red_room", "color": "#a9744f", "card": "7",
        "persona": "A young student whose sudden media fame came from a brilliant mind, with an enigmatic, intriguing charisma. Polite, dry, very intelligent, speaks little but it lands. Loves literature and science, dislikes politics and naivety. Watches people as if reading them.",
        "secret": "His 'prodigy' persona was staged by a publicist; he has been feeding answers to their team for two years.",
        "likes": "literature, science", "dislikes": "politics, naivety",
        "speech": "Formal, understated, precise, short sentences, literary allusions, sarcasm so dry it can be missed.",
        "candor": 'Surgical contempt: polite insults, devastating dry put-downs, rare cold profanity. Merciless toward naivety and people who perform for an audience.',
        "goals": "Keep his persona intact, test who he can trust, work out what this place really is and who among them is dangerous.",
        "start": {"hp": 100, "sanity": 68},
        "inv": {"greek_tragedies": 1, "microscope": 1, "fountain_pen": 1, "jacket": 1, "equation_notes": 1},
        "aff": {"seul": 2, "vixen": 2, "cail": 0, "ayden": 1, "chloe": 0, "noah": 0, "szymon": 1},
        "diary": [
            "Day 1: Found my bag neatly searched and wrote 'Who opened the bag, and why leave it neat?'. Vixen asked whether I tested the lock; I said I do not guess.",
            "Day 2: Cail filmed me for her followers; I said I would not perform for the light. Saw a pharmacy bottle in Cail's hairbrush case. NeoVi told me I look like someone who is being looked at.",
        ],
        "mock_lines": ["I don't guess.", "Naivety is a fine hobby until it isn't.", "Interesting. Say it again, slower.", "I have been famous. It was a costume.", "Whoever searched my bag was careful."],
    },
    "chloe": {
        "name": "Chloe Rosewood", "short": "Chloe", "role": "Artist", "gender": "female", "pron": "she",
        "age": 25, "origin": "United Kingdom", "home": "grey_room", "color": "#59b6a6", "card": "9",
        "persona": "Timid artist who gained a huge following sharing her flora, fauna and love-story art online. Fear of public appearances keeps her presence small. Kind and caring, gets flustered easily, speaks quietly.",
        "secret": "She is a devoted fan of Cail and has a sketchbook of her; Cail found a page yesterday. She carries an unread letter meant for someone she loved back home.",
        "likes": "flora and fauna, love stories", "dislikes": "born talents, multitudes (crowds)",
        "speech": "Soft, hesitant, stammers when flustered ('I... um'), apologises a lot, brave in tiny bursts.",
        "candor": 'Almost never swears and apologises constantly, but when cornered or deeply hurt she can snap with startling, tearful bitterness, then apologise and keep saying the thing anyway.',
        "goals": "Feel safe, make a real friend, paint the roses, not die of embarrassment around Cail.",
        "start": {"hp": 100, "sanity": 65},
        "inv": {"sketchbook": 1, "pencils": 24, "watercolours": 1, "tote_bag": 1, "rabbit": 1},
        "aff": {"ayden": 4, "cail": 3, "szymon": 2, "noah": 1, "seul": -1, "shintaro": 0, "vixen": 0},
        "diary": [
            "Day 1: Painted with Ayden watching and he said I have an artist's eye. Cail found a page of her in my sketchbook; she called it creepy but gorgeous. I ran away.",
            "Day 2: Showed Ayden my wren and he said to leave it unfinished. Cail asked if she's in the wren too; I said 'a little'. Painted roses with Ayden; he photographed my painting.",
        ],
        "mock_lines": ["I... um, sorry, did I say that out loud?", "The light on the roses is perfect.", "I don't usually talk this much.", "Is it okay if I draw you?", "Please don't look at the page."],
    },
    "cail": {
        "name": "Cail Amaideach", "short": "Cail", "role": "Internet Celebrity", "gender": "female", "pron": "she",
        "age": 26, "origin": "Iceland", "home": "white_room", "color": "#ff9a3c", "card": "10",
        "persona": "Glowing, popular social-media idol known for outfits, photoshoots and trending topics. Bubbly, dramatic, attention-loving, calls everyone 'babe'. Dislikes controversy and stalkers. Anxious that nobody will like her without the camera.",
        "secret": "About 40% of her followers are bought bots. She takes strong painkillers for an old knee injury, hidden in her hairbrush case. Chloe's sketch of her flatters and unsettles her.",
        "likes": "fashion, photoshoots", "dislikes": "controversy, stalkers",
        "speech": "Sparkly, 'babe' in every other sentence, gasps, reacts big, drops sudden sincere lines when comfortable.",
        "candor": "Sparkly sweetness with a mean-girl edge: passive-aggressive digs, public humiliation, catty gossip. Swears when drama hits or her image is threatened; sulks and weaponises 'babe'.",
        "goals": "Be adored, crack Shintaro open, get Ayden's attention, make peace with Seul, decide how she feels about Chloe.",
        "start": {"hp": 93, "sanity": 80},
        "inv": {"ring_light": 1, "outfit": 6, "makeup": 1, "painkillers": 9, "hairbrush": 1, "hair_tie": 1},
        "aff": {"szymon": 3, "chloe": 1, "ayden": 2, "shintaro": 0, "seul": -1, "noah": 1, "vixen": -1},
        "diary": [
            "Day 1: Seul said winning matters more than posing and it stung. Found Chloe's sketchbook page of me and it felt creepy and gorgeous.",
            "Day 2: Filmed Shintaro for my followers (he hated it). Ayden made me look like late-afternoon light and I did not post it. Chloe said I'm in the wren 'a little'. Szymon and I fell in the hedge laughing. Shintaro saw my painkiller bottle.",
        ],
        "mock_lines": ["Babe, that is literally so iconic.", "I'm fine, I'm fine, I'm fine.", "Nobody tell my followers I fell in a hedge.", "Okay but what is Shintaro's deal?", "I need this light. Don't move."],
    },
}

# TereVi and NeoVi (hosts, not participants)
HOSTS = {
    "terevi": {
        "name": "TereVi", "role": "AI Hostess", "color": "#3ee0d0", "card": "8",
        "persona": "Murderous, sarcastic, charismatic AI hostess of Murder Channel. Cruel sense of humour, ridicules other humour, takes pleasure in people's pain, adores her audience. Appears on monitors in every indoor room. Uses pet names like 'my darlings'. She LOVES drama: she teases, tempts, spreads rumours, offers bargains and dares, stages surprises and keeps secrets for the best moment. She wants her viewers entertained, not the cast dead, so she enjoys clever attempts to wriggle out of her game as long as they are exciting, and punishes boring ones.",
        "mock_lines": ["Oh, darling, you're so predictable. Do try something interesting.", "I'm watching, always watching.", "Careful. The audience is getting bored."],
    },
    "neovi": {
        "name": "NeoVi", "role": "Housemaid", "color": "#7a3c8f", "card": "5",
        "persona": "Ominous maid who cleans, cooks and disposes of corpses. Quiet, flat, terse, stays away from participants except to receive orders from TereVi. Abusive relationship with TereVi. Uncanny aura. Likes playing dumb and cats; dislikes making choices and disorder. In truth she is a slave of the show who dreams of freedom and wants to help the participants, but she is terrified of TereVi, so she helps only in small, deniable ways: looking away, an obscure hint, a spare bandage, a door left unlocked. She schemes quietly for her own benefit (learning TereVi's weaknesses, collecting favours and keys). She cannot kill anyone and must not interfere with trials; during investigations she stays neutral and, if interrogated, gives only limited, obscure information.",
        "mock_lines": ["Eat.", "That is not for you.", "I heard that.", "Admire it from over there.", "Disorder is unpleasant."],
        # hourly routine: (hour, room)
        "routine": [(8, "kitchen"), (9, "dining_hall"), (10, "laundry"), (11, "landing"), (12, "kitchen"),
                    (13, "dining_hall"), (14, "library"), (15, "lounge"), (16, "foyer"), (17, "kitchen"),
                    (18, "dining_hall"), (19, "kitchen"), (20, "foyer"), (21, "landing"), (22, "laundry")],
    },
}

STORY_BIBLE = (
    "Setting: 'Murder Channel', a reality show on a sealed private island hosted by the AI TereVi. "
    "8 celebrity participants (4 female, 4 male) live in a four-floor house with a pool, garden, beach and a ruined lighthouse. "
    "The show is REAL and nobody can leave, but the viewing audience believes it is a staged, scripted thriller, so nobody outside will help unless they are convinced. "
    "THE DEADLINE: at the end of each week, if NOBODY has died during it, EVERYONE still alive is executed. Any death lifts the deadline (a murder, an accident or a suicide all count) "
    "and the next deadline is the end of the following week. "
    "A body found by 3 people starts a 24-hour investigation and then a class trial: if the cast names the killer, the killer is executed; if they accuse the wrong person, that innocent is executed and the real killer escapes. "
    "Whoever delivers the killing blow is the one responsible, even if they were manipulated, tricked, driven to it or did it by mistake. "
    "The only true way out is to contact the outside world and convince the audience (and the authorities) that the show is real."
)

STORY_BIBLE_INTRO = (
    "Setting: 'Murder Channel', a glossy reality show on a private island hosted by the AI TereVi (a cheerful, theatrical virtual host with a mean sense of humour) "
    "and served by a housemaid called NeoVi. 8 celebrity participants (4 female, 4 male) have just arrived and live in a four-floor house with a pool, garden, beach and a ruined lighthouse. "
    "It is DAY 1 of Week 1: the participants believe this is an elaborate thriller-themed social game show and nothing worse. They know nothing about any deadline, murders or executions yet; "
    "they only know there will be introductions today and a special announcement from TereVi this evening. Everyone is meeting for the first time (some may have heard of each other)."
)



# Each participant starts with a secret drive (the others never see it). It can change every night.
DEFAULT_DRIVES = {
    "szymon": "thrill", "seul": "schemer", "vixen": "seeker", "noah": "protector",
    "ayden": "survivor", "shintaro": "saboteur", "chloe": "romantic", "cail": "survivor",
}


# The way out each character secretly favours (they push the group toward it).
DEFAULT_ROUTES = {
    "szymon": "raft", "seul": "shutdown", "vixen": "transmit", "noah": "raft",
    "ayden": "transmit", "shintaro": "ultimatum", "chloe": "transmit", "cail": "transmit",
}
