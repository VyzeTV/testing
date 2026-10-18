"""The wider item pool: weapons, useful items and special items for every room, the unlimited common supplies each room has, and the crafting recipes.

Nothing exists unless it is lying in a room, carried by someone, a common supply of the room the character stands in, or crafted from those.
Crafted items are "special" items (tag "crafted"); common supplies are unlimited but only in the rooms where they would plausibly be found.
"""

W = "weapon"


def _i(name, *tags, use=None):
    d = {"name": name, "tags": list(tags)}
    if use:
        d["use"] = use
    return d


NEW_ITEMS = {
    # ---- common supplies (unlimited in the rooms listed in COMMON_ITEMS)
    "matches": _i("Box of matches", "common", "fire"),
    "string": _i("Ball of string", "common"),
    "rags": _i("Rags", "common", "flammable"),
    "nails": _i("Handful of nails", "common"),
    "paper": _i("Sheets of paper", "common"),
    "pencil": _i("Pencil", "common"),
    "cooking_oil": _i("Cooking oil", "common", "flammable"),
    "salt": _i("Salt", "common"),
    "bread": _i("Loaf of bread", "common", "food", use={"hp": 1}),
    "tinned_food": _i("Tin of food", "common", "food", use={"hp": 1}),
    "soap": _i("Bar of soap", "common"),
    "charcoal": _i("Stick of charcoal", "common"),
    "guitar_string": _i("Guitar string", "common"),
    "chalk": _i("Chalk", "common"),
    "coal": _i("Lump of coal", "common", "flammable"),
    "ice": _i("Block of ice", "common"),
    "oleander_leaves": _i("Oleander leaves", "common", "plant"),
    "stones": _i("Beach stones", "common"),
    "sand": _i("Sand", "common"),
    "stick": _i("Stout stick", "common"),
    # ---- weapons, sharp
    "carving_fork": _i("Carving fork", W, "sharp"),
    "skewers": _i("Metal skewers", W, "sharp"),
    "ice_pick": _i("Ice pick", W, "sharp"),
    "meat_hook": _i("Meat hook", W, "sharp"),
    "craft_knife": _i("Craft knife", W, "sharp"),
    "sewing_needles": _i("Sewing needles", W, "sharp"),
    "corkscrew": _i("Corkscrew", W, "sharp", "tool"),
    "hatchet": _i("Hatchet", W, "sharp", "tool"),
    "fire_axe": _i("Fire axe", W, "sharp", "tool"),
    "screwdriver": _i("Screwdriver", W, "sharp", "tool"),
    "hacksaw": _i("Hacksaw", W, "sharp", "tool"),
    "boat_hook": _i("Boat hook", W, "sharp"),
    "rusty_saw": _i("Rusty saw", W, "sharp"),
    "garden_fork": _i("Garden fork", W, "sharp"),
    # ---- weapons, blunt
    "frying_pan": _i("Cast-iron frying pan", W, "blunt"),
    "rolling_pin": _i("Rolling pin", W, "blunt"),
    "serving_tray": _i("Silver serving tray", W, "blunt"),
    "decanter": _i("Crystal decanter", W, "blunt", "glass"),
    "crystal_ashtray": _i("Crystal ashtray", W, "blunt"),
    "pool_cue": _i("Billiard cue", W, "blunt"),
    "billiard_balls": _i("Billiard balls", W, "blunt"),
    "flat_iron": _i("Clothes iron", W, "blunt"),
    "bookends": _i("Marble bookends", W, "blunt"),
    "heavy_atlas": _i("Heavy atlas", W, "blunt"),
    "paperweight": _i("Brass paperweight", W, "blunt"),
    "bedside_lamp": _i("Bedside lamp", W, "blunt"),
    "walking_cane": _i("Walking cane", W, "blunt"),
    "drumsticks": _i("Drumsticks", W, "blunt"),
    "pipe_section": _i("Length of iron pipe", W, "blunt"),
    "mop": _i("Mop", W, "blunt"),
    "spade": _i("Spade", W, "blunt", "tool"),
    "oars": _i("Boat oars", W, "blunt"),
    "rusty_anchor": _i("Rusty anchor", W, "blunt"),
    "fire_extinguisher": _i("Fire extinguisher", W, "blunt", "tool"),
    # ---- useful items
    "flashlight": _i("Flashlight", "gear", "light"),
    "oil_lantern": _i("Oil lantern", "gear", "light", "fire"),
    "towels": _i("Towels", "gear"),
    "bed_sheets": _i("Bed sheets", "gear"),
    "pillow": _i("Pillow", "gear", "comfort"),
    "mirror": _i("Hand mirror", "gear", "glass"),
    "binoculars": _i("Binoculars", "gear"),
    "magnifying_glass": _i("Magnifying glass", "gear"),
    "tin_opener": _i("Tin opener", "tool"),
    "oven_gloves": _i("Oven gloves", "gear"),
    "work_gloves": _i("Work gloves", "gear"),
    "bucket": _i("Metal bucket", "gear"),
    "hose": _i("Garden hose", "tool"),
    "pliers": _i("Pliers", "tool"),
    "jump_leads": _i("Jump leads", "tool", "power"),
    "extension_cord": _i("Extension cord", "tool", "power"),
    "duct_tape": _i("Duct tape", "tool"),
    "fertiliser": _i("Bag of fertiliser", "flammable"),
    "lamp_oil": _i("Lamp oil", "flammable"),
    "spare_fuses": _i("Spare fuses", "gear", "power"),
    "hot_water_bottle": _i("Hot-water bottle", "comfort", use={"sanity": 1}),
    "life_ring": _i("Life ring", "gear"),
    "snorkel": _i("Snorkel and mask", "gear"),
    "fishing_net": _i("Fishing net", "gear"),
    "buoy": _i("Cork buoy", "gear"),
    "fishing_line": _i("Fishing line", "tool"),
    "clothes_line": _i("Washing line", "tool"),
    "spray_paint": _i("Can of spray paint", "flammable"),
    "mothballs": _i("Mothballs", "poison"),
    "drain_cleaner": _i("Drain cleaner", "poison"),
    "detergent": _i("Strong detergent", "poison"),
    "sack_of_flour": _i("Sack of flour", "food"),
    "mouse_traps": _i("Mouse traps", "gear", "trap"),
    "herb_bundle": _i("Bundle of dried chamomile", "food", use={"sanity": 1}),
    "terracotta_pots": _i("Terracotta pots", "gear"),
    "perfume": _i("Bottle of perfume", "comfort"),
    "sheet_music": _i("Sheet music", "comfort"),
    # ---- special items (rare, one-offs, keys, documents)
    "old_map": _i("Old map of the island", "special", "document"),
    "star_charts": _i("Star charts", "special", "document"),
    "sextant": _i("Brass sextant", "special", "gadget"),
    "signal_mirror": _i("Signalling mirror", "special", "gadget", "glass"),
    "radio_manual": _i("Radio service manual", "special", "document"),
    "piano_wire": _i("Piano wire", "special", "tool"),
    "handcuffs": _i("Handcuffs", "special", "restraint"),
    "tape_recorder": _i("Tape recorder", "special", "gadget"),
    "logbook": _i("Lighthouse logbook", "special", "document"),
    "visitor_book": _i("Visitors' book", "special", "document"),
    "hidden_letter": _i("Unsent letter", "special", "mystery"),
    "message_bottle": _i("Message in a bottle", "special", "mystery"),
    "key_blue_room": _i("Spare key: Blue Room", "special", "key"),
    "key_green_room": _i("Spare key: Green Room", "special", "key"),
    "key_yellow_room": _i("Spare key: Yellow Room", "special", "key"),
    "key_red_room": _i("Spare key: Red Room", "special", "key"),
    "key_violet_room": _i("Spare key: Violet Room", "special", "key"),
    "key_orange_room": _i("Spare key: Orange Room", "special", "key"),
    "key_grey_room": _i("Spare key: Grey Room", "special", "key"),
    "key_white_room": _i("Spare key: White Room", "special", "key"),
    # ---- crafted items (special by definition: they exist only because someone made them)
    "bottle_shiv": _i("Broken-bottle shiv", W, "sharp", "special", "crafted"),
    "garrote": _i("Garrote", W, "sharp", "special", "crafted"),
    "nail_board": _i("Nail-studded board", W, "blunt", "special", "crafted"),
    "molotov": _i("Petrol bomb", W, "fire", "flammable", "special", "crafted"),
    "oleander_extract": _i("Oleander extract", "poison", "special", "crafted"),
    "drugged_drink": _i("Drugged drink", "poison", "drink", "special", "crafted"),
    "lockpicks": _i("Improvised lockpicks", "tool", "special", "crafted"),
    "torch": _i("Oil-soaked torch", W, "blunt", "fire", "light", "special", "crafted"),
    "sock_cosh": _i("Stone-weighted cosh", W, "blunt", "special", "crafted"),
    "spear": _i("Improvised spear", W, "sharp", "special", "crafted"),
    "rigged_radio": _i("Rigged radio", "gadget", "power", "special", "crafted"),
    # ---- clothes and costumes (everyone's own clothes and swimsuit are generated per character)
    "bathrobe": _i("Bathrobe", "clothing"),
    "raincoat": _i("Yellow raincoat", "clothing"),
    "overalls": _i("Work overalls", "clothing"),
    "formal_dress": _i("Evening dress", "clothing"),
    "tuxedo": _i("Dinner jacket and trousers", "clothing", "costume"),
    "swim_trunks": _i("Swim trunks", "clothing", "swimwear"),
    "bikini": _i("Bikini", "clothing", "swimwear"),
    "party_costume": _i("Glittering party costume", "clothing", "costume"),
    "trench_coat": _i("Long trench coat", "clothing"),
    "wetsuit": _i("Wetsuit", "clothing", "swimwear"),
    "old_robes": _i("Old ceremonial robes", "clothing", "costume"),
    "smock": _i("Paint-stained smock", "clothing"),
    "pyjamas": _i("Pyjamas", "clothing"),
    "sheet_cloak": _i("Bedsheet cloak", "clothing", "costume", "disguise", "special", "crafted"),
    "splint": _i("Makeshift splint", "medical", "special", "crafted"),
    "antibiotics": _i("Antibiotics", "medical", "special", use={"hp": 1}),
    "smelling_salts": _i("Smelling salts", "medical", "special"),
    "paper_mask": _i("Paper mask", "clothing", "costume", "disguise", "mask", "special", "crafted"),
    # ---- gear (gear.py): a holster hides one weapon and it draws at once, a bag hides a few, rubber gloves leave no prints
    "holster": _i("Leather holster", "gear"),
    "duffel_bag": _i("Canvas duffel bag", "gear"),
    "rubber_gloves": _i("Rubber gloves", "gear"),
}

CLOTHES_BY_ROOM = {
    "bathroom": {"bathrobe": 2}, "garden": {"raincoat": 1}, "generator_shed": {"overalls": 1}, "pool": {"swim_trunks": 2, "bikini": 1},
    "games_room": {"party_costume": 1}, "foyer": {"trench_coat": 1}, "boathouse": {"wetsuit": 1}, "attic": {"old_robes": 1}, "art_studio": {"smock": 1},
    "linen_store": {"pyjamas": 2}, "master_suite": {"formal_dress": 1, "tuxedo": 1},
}
# existing items that are clothes
CLOTHING_TAGS = {"outfit": ["clothing"], "jacket": ["clothing"], "maid_uniform": ["clothing", "costume"], "apron": ["clothing", "costume"]}

# What each room adds to its lying-around stock: weapons, useful items and special items that make sense to find there.
ROOM_ADDITIONS = {
    "master_suite": {"bedside_lamp": 2, "mirror": 1, "pillow": 4, "perfume": 2, "paperweight": 1, "walking_cane": 1},
    "foyer": {"walking_cane": 1, "visitor_book": 1, "umbrella": 1},
    "dining_hall": {"carving_fork": 1, "serving_tray": 2, "decanter": 1},
    "kitchen": {"frying_pan": 2, "rolling_pin": 1, "skewers": 1, "oven_gloves": 2, "tin_opener": 1, "fire_extinguisher": 1, "corkscrew": 1, "rubber_gloves": 2},
    "pantry": {"sack_of_flour": 2, "mouse_traps": 3, "tinned_food": 0, "herb_bundle": 2},
    "lounge": {"decanter": 1, "crystal_ashtray": 1, "pillow": 4, "perfume": 1},
    "games_room": {"pool_cue": 2, "billiard_balls": 3},
    "laundry": {"flat_iron": 2, "clothes_line": 2, "detergent": 2, "towels": 4, "bed_sheets": 2, "sewing_needles": 1, "key_yellow_room": 1, "key_red_room": 1, "key_violet_room": 1, "key_orange_room": 1, "rubber_gloves": 2},
    "blue_room": {"bedside_lamp": 1, "mirror": 1, "pillow": 2, "perfume": 1},
    "green_room": {"bedside_lamp": 1, "hot_water_bottle": 1, "mirror": 1, "pillow": 2},
    "yellow_room": {"mirror": 1, "pillow": 2, "paperweight": 1},
    "red_room": {"mirror": 1, "pillow": 2, "bookends": 1},
    "violet_room": {"mirror": 1, "pillow": 2, "perfume": 1},
    "orange_room": {"bedside_lamp": 1, "pillow": 2, "hot_water_bottle": 1},
    "grey_room": {"mirror": 1, "pillow": 2, "paperweight": 1},
    "white_room": {"bedside_lamp": 1, "pillow": 2, "bookends": 1},
    "bathroom": {"drain_cleaner": 1, "towels": 3, "mothballs": 0, "antibiotics": 1, "smelling_salts": 1},
    "library": {"bookends": 1, "heavy_atlas": 2, "magnifying_glass": 1, "old_map": 1},
    "study": {"paperweight": 1, "tape_recorder": 1, "handcuffs": 0},
    "linen_store": {"bed_sheets": 10, "towels": 6, "mothballs": 2, "sewing_needles": 1, "key_blue_room": 1, "key_green_room": 1, "key_grey_room": 1, "key_white_room": 1, "pillow": 4},
    "music_room": {"drumsticks": 2, "piano_wire": 1, "sheet_music": 3},
    "art_studio": {"craft_knife": 2, "spray_paint": 2},
    "observatory": {"star_charts": 1, "binoculars": 1, "tripod": 1},
    "attic": {"rusty_saw": 1, "oil_lantern": 1, "mothballs": 2},
    "lookout": {"binoculars": 1},
    "water_tower": {"pipe_section": 2, "bucket": 1},
    "basement_hall": {"mop": 1, "bucket": 1, "flashlight": 2, "spare_fuses": 3},
    "wine_cellar": {"corkscrew": 1, "oil_lantern": 1},
    "boiler_room": {"hatchet": 1, "work_gloves": 2, "pipe_section": 1},
    "cold_store": {"meat_hook": 2, "ice_pick": 1},
    "garden": {"garden_fork": 1, "spade": 1, "hose": 1, "terracotta_pots": 4},
    "greenhouse": {"fertiliser": 2, "herb_bundle": 3, "terracotta_pots": 6},
    "pool": {"life_ring": 2, "snorkel": 2, "towels": 4},
    "beach": {"rusty_anchor": 1, "fishing_net": 1, "buoy": 2},
    "boathouse": {"oars": 2, "boat_hook": 1, "fishing_line": 2, "buoy": 2, "duffel_bag": 1, "holster": 1},
    "generator_shed": {"screwdriver": 2, "pliers": 1, "jump_leads": 1, "extension_cord": 1, "duct_tape": 2, "hacksaw": 1, "work_gloves": 2},
    "lighthouse": {"lamp_oil": 3, "logbook": 1},
}

# Unlimited common supplies, only in the rooms where they would plausibly be found (taking one never runs the room out).
COMMON_ITEMS = {
    "kitchen": ["water_bottle", "bread", "matches", "cooking_oil", "salt", "string", "rags"],
    "pantry": ["tinned_food", "bread", "water_bottle", "salt"],
    "dining_hall": ["water_bottle", "salt"],
    "lounge": ["matches", "paper", "pencil"],
    "laundry": ["rags", "string", "soap"],
    "bathroom": ["soap", "rags", "water_bottle"],
    "library": ["paper", "pencil"],
    "study": ["paper", "pencil", "string"],
    "art_studio": ["paper", "charcoal", "string", "rags"],
    "music_room": ["guitar_string", "paper"],
    "games_room": ["chalk"],
    "generator_shed": ["nails", "rags", "string"],
    "boiler_room": ["coal", "rags", "matches"],
    "cold_store": ["ice"],
    "garden": ["stones", "stick", "oleander_leaves"],
    "greenhouse": ["oleander_leaves", "stick"],
    "beach": ["stones", "sand", "stick"],
    "boathouse": ["rags", "string"],
    "attic": ["nails", "string"],
    "lighthouse": ["matches"],
}

HIDDEN_ADDITIONS = {
    "library": [{"items": {"hidden_letter": 1}, "keywords": ["atlas", "atlases", "book", "letter", "behind", "shelf"], "p": 0.12, "text": "an unsent letter tucked behind the atlases"}],
    "study": [{"items": {"radio_manual": 1}, "keywords": ["desk", "drawer", "manual", "radio", "under"], "p": 0.12, "text": "a radio service manual taped under a desk drawer"}],
    "art_studio": [{"items": {"craft_knife": 1}, "keywords": ["tin", "paint", "pots", "knife"], "p": 0.12, "text": "a craft knife hidden in an empty paint tin"}],
    "boiler_room": [{"items": {"fire_axe": 1}, "keywords": ["wall", "behind", "boiler", "axe", "glass", "case"], "p": 0.10, "text": "a fire axe in a sealed glass case behind the boiler"}],
    "attic": [{"items": {"handcuffs": 1}, "keywords": ["trunk", "trunks", "chest", "locked"], "p": 0.12, "text": "a pair of handcuffs at the bottom of an old trunk"}],
    "beach": [{"items": {"message_bottle": 1}, "keywords": ["sand", "bottle", "shore", "tide", "wash"], "p": 0.10, "text": "a corked bottle with a note, half buried in the sand"}],
    "lookout": [{"items": {"signal_mirror": 1}, "keywords": ["rail", "railing", "mirror", "glint", "locker"], "p": 0.12, "text": "a signalling mirror in a rusty locker"}],
    "observatory": [{"items": {"sextant": 1}, "keywords": ["cabinet", "drawer", "brass", "case"], "p": 0.12, "text": "a brass sextant in a cabinet drawer"}],
}

# Recipes. "needs": list of (acceptable items, quantity); "tools": list of acceptable-item groups that are required but not used up;
# "where": rooms in which it can be made (None = anywhere you have the ingredients); "risk": what a botched attempt does.
RECIPES = {
    "bottle_shiv": {"name": "broken-bottle shiv", "out": "bottle_shiv", "needs": [(["wine_bottle", "decanter", "champagne", "spirits"], 1), (["rags"], 1)],
                    "tools": [], "where": None, "p": 0.8, "risk": "cut"},
    "garrote": {"name": "garrote", "out": "garrote", "needs": [(["guitar_string", "piano_wire", "wire"], 1), (["pencil", "drumsticks", "stick"], 2)],
                "tools": [], "where": None, "p": 0.85, "risk": "cut"},
    "nail_board": {"name": "nail-studded board", "out": "nail_board", "needs": [(["planks"], 1), (["nails"], 4)],
                   "tools": [["hammer", "sledgehammer", "pipe_wrench"]], "where": ["generator_shed", "boathouse", "boiler_room", "attic"], "p": 0.85, "risk": "cut"},
    "molotov": {"name": "petrol bomb", "out": "molotov", "needs": [(["wine_bottle", "spirits", "champagne"], 1), (["rags"], 1),
                                                               (["fuel_can", "paint_thinner", "turpentine", "cooking_oil", "lamp_oil", "spray_paint"], 1), (["matches"], 1)],
                "tools": [], "where": None, "p": 0.75, "risk": "burn"},
    "oleander_extract": {"name": "oleander extract", "out": "oleander_extract", "needs": [(["oleander_leaves"], 4), (["water_bottle"], 1)],
                         "tools": [["cocktail_shaker", "watering_can", "frying_pan", "bucket"]], "where": ["kitchen", "greenhouse"], "p": 0.8, "risk": None},
    "drugged_drink": {"name": "drugged drink", "out": "drugged_drink", "needs": [(["sleeping_pills"], 3), (["spirits", "champagne", "wine_bottle", "energy_drink", "sparkling_water"], 1)],
                      "tools": [], "where": ["kitchen", "bathroom", "lounge", "dining_hall", "blue_room", "green_room", "yellow_room", "red_room", "violet_room", "orange_room", "grey_room", "white_room"], "p": 0.9, "risk": None},
    "lockpicks": {"name": "improvised lockpicks", "out": "lockpicks", "needs": [(["wire", "piano_wire"], 1), (["pen", "pencil", "hair_tie"], 1)],
                  "tools": [], "where": ["study", "library", "attic", "generator_shed", "art_studio"], "p": 0.8, "risk": None},
    "torch": {"name": "oil-soaked torch", "out": "torch", "needs": [(["stick"], 1), (["rags"], 1), (["cooking_oil", "lamp_oil", "spirits", "fuel_can"], 1), (["matches"], 1)],
              "tools": [], "where": None, "p": 0.9, "risk": "burn"},
    "sock_cosh": {"name": "stone-weighted cosh", "out": "sock_cosh", "needs": [(["stones", "billiard_balls"], 2), (["rags", "bed_sheets", "towels", "scarf"], 1)],
                  "tools": [], "where": None, "p": 0.9, "risk": None},
    "spear": {"name": "improvised spear", "out": "spear", "needs": [(["kitchen_knife", "steak_knife", "cleaver", "chisel", "carving_fork"], 1), (["stick", "pool_pole", "mop"], 1),
                                                                    (["string", "masking_tape", "duct_tape", "wire"], 1)],
              "tools": [], "where": None, "p": 0.8, "risk": "cut"},
    "sheet_cloak": {"name": "bedsheet cloak", "out": "sheet_cloak", "needs": [(["bed_sheets"], 1), (["string", "clothes_line", "masking_tape", "duct_tape"], 1)],
                    "tools": [], "where": None, "p": 0.9, "risk": None},
    "paper_mask": {"name": "paper mask", "out": "paper_mask", "needs": [(["paper"], 2), (["string"], 1), (["charcoal", "pencil"], 1)],
                   "tools": [], "where": None, "p": 0.9, "risk": None},
    "splint": {"name": "splint", "out": "splint", "needs": [(["planks", "stick", "pool_pole", "mop"], 1), (["bandages", "rags", "towels", "string", "duct_tape"], 1)],
               "tools": [], "where": None, "p": 0.9, "risk": None},
    "rigged_radio": {"name": "rigged radio", "out": "rigged_radio", "needs": [(["handheld"], 1), (["wire"], 1), (["battery"], 1)],
                     "tools": [["pliers", "screwdriver", "pipe_wrench"]], "where": ["generator_shed", "study"], "p": 0.6, "risk": None},
}


def apply_item_pool(items, room_items, hidden_items):
    """Merge the wider pool into the base data (called once by data_world)."""
    for k, v in NEW_ITEMS.items():
        items.setdefault(k, v)
    for k, tags in CLOTHING_TAGS.items():
        if k in items:
            items[k]["tags"] = sorted(set(items[k].get("tags", [])) | set(tags))
    for room, add in CLOTHES_BY_ROOM.items():
        pool = room_items.setdefault(room, {})
        for k, q in add.items():
            pool.setdefault(k, q)
    for room, add in ROOM_ADDITIONS.items():
        pool = room_items.setdefault(room, {})
        for k, q in add.items():
            if q > 0:
                pool[k] = pool.get(k, 0) + q
    for room, lst in HIDDEN_ADDITIONS.items():
        hidden_items.setdefault(room, []).extend(dict(x) for x in lst)
