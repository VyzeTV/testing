"""Static island data: rooms, connections, secret passages, items, starting contents.

Rooms are laid out as a cutaway house (left) plus grounds (right) on a 1400x760 canvas.
"""

# id: (name, zone, x, y, w, h)
ROOMS = {
    # Roof
    "lookout":        ("Lookout Deck",        "roof",     40,  20, 220, 70),
    "water_tower":    ("Water Tower Walkway", "roof",    265,  20, 220, 70),
    # Second floor
    "upper_landing":  ("Upper Landing",       "second",   40, 100, 110, 150),
    "master_suite":   ("Master Suite",        "second",  155, 100, 170, 150),
    "music_room":     ("Music Room",          "second",  330, 100, 140, 150),
    "art_studio":     ("Art Studio",          "second",  475, 100, 140, 150),
    "observatory":    ("Observatory",         "second",  620, 100, 130, 150),
    "attic":          ("Attic",               "second",  755, 100, 125, 150),
    # First floor
    "landing":        ("First-Floor Landing", "first",    40, 260, 110, 150),
    "blue_room":      ("Blue Room",           "first",   155, 260,  80, 150),
    "green_room":     ("Green Room",          "first",   240, 260,  80, 150),
    "yellow_room":    ("Yellow Room",         "first",   325, 260,  80, 150),
    "red_room":       ("Red Room",            "first",   410, 260,  80, 150),
    "bathroom":       ("Bathroom",            "first",   495, 260,  75, 150),
    "library":        ("Library",             "first",   575, 260, 115, 150),
    "study":          ("Study",               "first",   695, 260,  90, 150),
    "linen_store":    ("Linen Store",         "first",   790, 260,  90, 150),
    "violet_room":      ("Violet Room",         "first",   885, 260,  80, 150),
    "orange_room":      ("Orange Room",         "first",   970, 260,  80, 150),
    "grey_room":        ("Grey Room",           "first",   1055, 260,  80, 150),
    "white_room":       ("White Room",          "first",   1140, 260,  80, 150),
    # Ground floor
    "foyer":          ("Foyer",               "ground",   40, 420, 110, 150),
    "dining_hall":    ("Dining Hall",         "ground",  155, 420, 130, 150),
    "kitchen":        ("Kitchen",             "ground",  290, 420, 110, 150),
    "pantry":         ("Pantry",              "ground",  405, 420,  75, 150),
    "lounge":         ("Lounge",              "ground",  485, 420, 130, 150),
    "games_room":     ("Games Room",          "ground",  620, 420, 120, 150),
    "laundry":        ("Laundry & Service",   "ground",  745, 420, 135, 150),
    # Basement
    "basement_hall":  ("Basement Hall",       "basement", 40, 580, 110, 150),
    "wine_cellar":    ("Wine Cellar",         "basement",155, 580, 200, 150),
    "boiler_room":    ("Boiler Room",         "basement",360, 580, 160, 150),
    "cold_store":     ("Cold Store",          "basement",525, 580, 155, 150),
    # Grounds
    "garden":         ("Outdoors",            "grounds", 910,  20, 230, 200),
    "greenhouse":     ("Greenhouse",          "grounds",1145,  20, 245, 120),
    "pool":           ("Pool & Spa",          "grounds", 910, 230, 230, 160),
    "beach":          ("Beach",               "grounds",1145, 150, 245, 240),
    "boathouse":      ("Boathouse",           "grounds",1145, 400, 245, 100),
    "generator_shed": ("Generator Shed",      "grounds", 910, 400, 110,  90),
    "lighthouse":     ("Lighthouse Ruin",     "grounds",1025, 400, 115,  90),
    # The class-trial site, down the cliff steps from the beach
    "voting_grounds": ("The Voting Grounds",  "grounds",1145, 510, 245, 120),
    # TereVi's hidden core, under the lighthouse
    "core_vault":     ("TereVi's Core Vault", "basement",905, 510, 230, 120),
}
SECRET_ROOMS = {"core_vault"}

# Edges: (a, b, minutes, kind, extra)
# extra keys: id, hidden, locked, keys (items that open it), needs (tool needed to force),
#             discover = {"rooms": [...], "keywords": [...], "p": float, "text": str}
EDGES = [
    # Ground floor
    ("foyer", "dining_hall", 3, "door", {}),
    ("dining_hall", "kitchen", 3, "door", {}),
    ("kitchen", "pantry", 2, "door", {}),
    ("foyer", "lounge", 4, "door", {}),
    ("lounge", "games_room", 3, "door", {}),
    ("kitchen", "laundry", 4, "door", {}),
    ("foyer", "garden", 5, "outside", {}),
    ("games_room", "pool", 8, "outside", {}),
    # Stairs
    ("foyer", "landing", 8, "stairs", {}),
    ("landing", "upper_landing", 8, "stairs", {}),
    ("upper_landing", "lookout", 8, "stairs", {}),
    ("foyer", "basement_hall", 6, "stairs", {}),
    # First floor
    ("landing", "blue_room", 2, "door", {}),
    ("landing", "green_room", 2, "door", {}),
    ("landing", "yellow_room", 2, "door", {}),
    ("landing", "red_room", 2, "door", {}),
    ("landing", "bathroom", 2, "door", {}),
    ("landing", "library", 3, "door", {}),
    ("landing", "study", 3, "door", {"locked": True, "keys": ["skeleton_keys", "master_key"], "id": "study_door"}),
    ("landing", "linen_store", 2, "door", {}),
    # Second floor
    ("upper_landing", "master_suite", 3, "door", {"locked": True, "keys": ["skeleton_keys", "master_key"], "id": "master_door"}),
    ("upper_landing", "music_room", 3, "door", {}),
    ("upper_landing", "art_studio", 3, "door", {}),
    ("upper_landing", "observatory", 3, "door", {}),
    # Roof
    ("lookout", "water_tower", 3, "door", {}),
    # Basement
    ("basement_hall", "wine_cellar", 3, "door", {}),
    ("basement_hall", "boiler_room", 3, "door", {}),
    ("basement_hall", "cold_store", 3, "door", {}),
    # Grounds
    ("garden", "greenhouse", 3, "outside", {}),
    ("garden", "pool", 4, "outside", {}),
    ("garden", "beach", 6, "outside", {}),
    ("garden", "generator_shed", 5, "outside", {}),
    ("garden", "lighthouse", 25, "path", {}),
    ("kitchen", "garden", 2, "window", {}),
    ("laundry", "garden", 3, "door", {}),
    ("beach", "voting_grounds", 4, "path", {}),
    ("beach", "boathouse", 5, "door", {"locked": True, "keys": ["skeleton_keys", "master_key", "bolt_cutters"], "id": "boathouse_door"}),
    # Secret passages (hidden until discovered)
    ("pantry", "wine_cellar", 3, "secret", {
        "id": "SP-1", "hidden": True,
        "discover": {"rooms": ["pantry", "wine_cellar"], "keywords": ["jar", "shelf", "draught", "draft", "scratch", "tick"], "p": 0.12,
                     "text": "the third jar on the top shelf is a lever, and the back wall slides open on a counterweight"}}),
    ("wine_cellar", "lighthouse", 20, "secret", {
        "id": "SP-2", "hidden": True, "locked": True, "keys": ["iron_key"],
        "discover": {"rooms": ["wine_cellar"], "keywords": ["crate", "crates", "tunnel", "grate", "draught"], "p": 0.08,
                     "text": "behind the stacked crates is a rusted grate leading into a smugglers' tunnel"}}),
    ("library", "attic", 3, "secret", {
        "id": "SP-3", "hidden": True,
        "discover": {"rooms": ["library", "attic"], "keywords": ["atlas", "atlases", "blue", "bookcase", "maritime", "book"], "p": 0.10,
                     "text": "the 'Maritime Atlases' bookcase swings out when the blue volume is pulled"}}),
    ("lighthouse", "core_vault", 6, "secret", {
        "id": "SP-5", "hidden": True, "needs": ["crowbar", "pipe_wrench", "sledgehammer"],
        "discover": {"rooms": ["lighthouse"], "keywords": ["floor", "hatch", "trapdoor", "stairs", "cellar", "ring", "cables", "hum", "rust"], "p": 0.07,
                     "text": "a rusted ring in the lighthouse floor lifts a heavy hatch onto steps leading down to a humming vault"}}),
    ("kitchen", "linen_store", 4, "secret", {
        "id": "SP-4", "hidden": True, "needs": ["crowbar", "pipe_wrench"],
        "discover": {"rooms": ["kitchen", "linen_store"], "keywords": ["dumbwaiter", "hatch", "lift", "panel"], "p": 0.10,
                     "text": "an old jammed dumbwaiter connects the kitchen to the linen store"}}),
    ("landing", "violet_room", 2, "door", {}),
    ("landing", "orange_room", 2, "door", {}),
    ("landing", "grey_room", 2, "door", {}),
    ("landing", "white_room", 2, "door", {}),
]

# Links that do not exist yet but that people can build: a ladder, a rope line or a plank across a gap.
# id: (room a, room b, {kind: minutes}, description)
POTENTIAL_LINKS = [
    ("library", "garden", {"ladder": 6, "rope": 7}, "from the library window down to the garden"),
    ("bathroom", "garden", {"ladder": 6, "rope": 7}, "from the bathroom window down to the garden"),
    ("green_room", "garden", {"ladder": 6, "rope": 7}, "from the Green Room window down to the garden"),
    ("art_studio", "lookout", {"ladder": 4}, "up through the Art Studio skylight onto the roof"),
    ("attic", "lookout", {"ladder": 4}, "through the attic roof hatch onto the Lookout Deck"),
    ("master_suite", "pool", {"rope": 6}, "from the Master Suite balcony down to the pool terrace"),
    ("water_tower", "garden", {"rope": 8}, "a rope line from the Water Tower walkway to the garden"),
    ("boiler_room", "garden", {"ladder": 7, "rope": 8}, "up the old coal chute to the garden"),
    ("upper_landing", "foyer", {"rope": 4}, "a rope down the stairwell into the foyer"),
    ("generator_shed", "lighthouse", {"plank": 5}, "a plank across the gully between the shed and the lighthouse"),
]
BUILD_RECIPES = {
    "ladder": {"items": {"ladder": 1}, "alt": {"planks": 2, "rope": 1}, "name": "ladder", "risk": 0.03},
    "rope": {"items": {"rope": 1}, "alt": None, "name": "rope line", "risk": 0.06},
    "plank": {"items": {"planks": 1}, "alt": None, "name": "plank bridge", "risk": 0.04},
}

# Items: id: dict(name, tags, desc, [use effects])
ITEMS = {
    # Weapons: sharp
    "kitchen_knife":  {"name": "Chef's knife", "tags": ["weapon", "sharp"]},
    "cleaver":        {"name": "Meat cleaver", "tags": ["weapon", "sharp"]},
    "bread_knife":    {"name": "Bread knife", "tags": ["weapon", "sharp"]},
    "steak_knife":    {"name": "Steak knife", "tags": ["weapon", "sharp"]},
    "letter_opener":  {"name": "Brass letter opener", "tags": ["weapon", "sharp"]},
    "pen_knife":      {"name": "Pen knife", "tags": ["weapon", "sharp"]},
    "scissors":       {"name": "Scissors", "tags": ["weapon", "sharp"]},
    "razor_blades":   {"name": "Razor blades", "tags": ["weapon", "sharp"]},
    "palette_knife":  {"name": "Palette knife", "tags": ["weapon", "sharp"]},
    "chisel":         {"name": "Sculptor's chisel", "tags": ["weapon", "sharp"]},
    "pruning_shears": {"name": "Pruning shears", "tags": ["weapon", "sharp"]},
    "pruning_saw":    {"name": "Pruning saw", "tags": ["weapon", "sharp"]},
    "rapier":         {"name": "Prop rapier", "tags": ["weapon", "sharp"]},
    "darts":          {"name": "Darts", "tags": ["weapon", "sharp"]},
    "harpoon":        {"name": "Old harpoon", "tags": ["weapon", "sharp"]},
    # Weapons: blunt
    "wine_bottle":    {"name": "Wine bottle", "tags": ["weapon", "blunt", "drink"], "use": {"sanity": 1}},
    "crowbar":        {"name": "Crowbar", "tags": ["weapon", "blunt", "tool"]},
    "pipe_wrench":    {"name": "Pipe wrench", "tags": ["weapon", "blunt", "tool"]},
    "coal_shovel":    {"name": "Coal shovel", "tags": ["weapon", "blunt"]},
    "candelabra":     {"name": "Heavy candelabra", "tags": ["weapon", "blunt"]},
    "fire_poker":     {"name": "Fire poker", "tags": ["weapon", "blunt"]},
    "baseball_bat":   {"name": "Signed baseball bat", "tags": ["weapon", "blunt"]},
    "reading_lamp":   {"name": "Brass reading lamp", "tags": ["weapon", "blunt"]},
    "metronome":      {"name": "Metronome", "tags": ["weapon", "blunt"]},
    "sculpt_mallet":  {"name": "Sculpting mallet", "tags": ["weapon", "blunt"]},
    "meat_mallet":    {"name": "Meat tenderizer mallet", "tags": ["weapon", "blunt"]},
    "brass_telescope":{"name": "Brass telescope", "tags": ["weapon", "blunt"]},
    "diving_weight":  {"name": "Diving weight", "tags": ["weapon", "blunt"]},
    "driftwood":      {"name": "Driftwood club", "tags": ["weapon", "blunt"]},
    "hammer":         {"name": "Hammer", "tags": ["weapon", "blunt", "tool"]},
    # Chemicals / poisons
    "rat_poison":     {"name": "Rat poison tin", "tags": ["poison"]},
    "pest_killer":    {"name": "Rat & Pest bottle", "tags": ["poison"]},
    "weed_killer":    {"name": "Weed killer", "tags": ["poison"]},
    "chlorine":       {"name": "Pool chlorine", "tags": ["poison"]},
    "bleach":         {"name": "Bleach bottle", "tags": ["poison"]},
    "paint_thinner":  {"name": "Paint thinner", "tags": ["poison", "flammable"]},
    "turpentine":     {"name": "Turpentine", "tags": ["poison", "flammable"]},
    "sleeping_pills": {"name": "Sleeping pills", "tags": ["drug"], "use": {"sanity": 2}},
    "spirits":        {"name": "Bottle of spirits", "tags": ["drink"], "use": {"sanity": 2}},
    # Fire
    "flare_gun":      {"name": "Flare gun (1 flare)", "tags": ["weapon", "fire"]},
    "flares":         {"name": "Signal flare", "tags": ["fire"]},
    "fuel_can":       {"name": "Fuel can", "tags": ["flammable"]},
    # Tools, keys
    "rope":           {"name": "Rope (20 m)", "tags": ["tool"]},
    "wire":           {"name": "Coil of wire", "tags": ["tool"]},
    "masking_tape":   {"name": "Masking tape", "tags": ["tool"]},
    "bolt_cutters":   {"name": "Bolt cutters", "tags": ["tool"]},
    "pool_pole":      {"name": "Pool cleaning pole", "tags": ["tool"]},
    "ladder":         {"name": "Wooden ladder", "tags": ["tool", "gear"]},
    "planks":         {"name": "Wooden planks", "tags": ["tool", "gear"]},
    "barrel":         {"name": "Empty barrel", "tags": ["gear"]},
    "tarp":           {"name": "Heavy tarpaulin", "tags": ["gear"]},
    "sledgehammer":   {"name": "Sledgehammer", "tags": ["weapon", "blunt", "tool"]},
    "battery":        {"name": "Truck battery", "tags": ["gear", "power"]},
    "iron_key":       {"name": "Iron key", "tags": ["key"]},
    "skeleton_keys":  {"name": "Skeleton key set", "tags": ["key", "tool"]},
    "master_key":     {"name": "Master key", "tags": ["key"]},
    "life_jacket":    {"name": "Life jacket", "tags": ["gear"]},
    "umbrella":       {"name": "Umbrella", "tags": ["gear"]},
    "sealed_envelope":{"name": "Sealed envelope (addressed to nobody)", "tags": ["mystery"]},
    # Comfort and misc
    "first_aid_kit":  {"name": "First-aid kit", "tags": ["medical"], "use": {"hp": 4}},
    "bandages":       {"name": "Bandages", "tags": ["medical"], "use": {"hp": 2}},
    "paracetamol":    {"name": "Paracetamol", "tags": ["medical"], "use": {"hp": 1}},
    "champagne":      {"name": "Bottle of champagne", "tags": ["drink"], "use": {"sanity": 2}},
    "sweets":         {"name": "Box of sweets", "tags": ["food"], "use": {"sanity": 1}},
    "candles":        {"name": "Scented candles", "tags": ["comfort"], "use": {"sanity": 1}},
    "diary":          {"name": "Blank diary", "tags": ["comfort"]},
    "notebook":       {"name": "Notebook", "tags": ["comfort"]},
    "sleep_mask":     {"name": "Sleep mask", "tags": ["comfort"]},
    "violin":         {"name": "Violin", "tags": ["instrument"]},
    "tuning_forks":   {"name": "Tuning forks", "tags": ["instrument"]},
    "records":        {"name": "Box of old records", "tags": ["comfort"]},
    "board_game":     {"name": "Board game", "tags": ["comfort"], "use": {"sanity": 1}},
    "small_telescope":{"name": "Small telescope", "tags": ["gear"]},
    "watering_can":   {"name": "Watering can", "tags": ["gear"]},
    "cocktail_shaker":{"name": "Cocktail shaker", "tags": ["gear"]},
    "apron":          {"name": "Blood-stained apron", "tags": ["mystery"]},
    "maid_uniform":   {"name": "Spare maid uniform", "tags": ["gear"]},
    # Personal items
    "gopro":          {"name": "GoPro camera", "tags": ["camera"]},
    "headlamp":       {"name": "Headlamp", "tags": ["gear"]},
    "carabiner":      {"name": "Carabiner", "tags": ["gear"]},
    "energy_bar":     {"name": "Energy bar", "tags": ["food"], "use": {"sanity": 1}},
    "water_bottle":   {"name": "Water bottle", "tags": ["drink"], "use": {"hp": 1}},
    "handheld":       {"name": "Handheld console", "tags": ["gadget"], "use": {"sanity": 1}},
    "energy_drink":   {"name": "Sweet energy drink", "tags": ["drink"], "use": {"sanity": 1}},
    "stimulants":     {"name": "Stimulant pills", "tags": ["drug"], "use": {"sanity": 1, "hp": -1}},
    "headphones":     {"name": "Headphones", "tags": ["gadget"]},
    "hair_tie":       {"name": "Hair tie", "tags": ["gear"]},
    "laptop":         {"name": "Offline laptop", "tags": ["gadget"]},
    "hacking_drive":  {"name": "Hacking drive (in hairpin)", "tags": ["gadget", "secret"]},
    "scarf":          {"name": "Dark blue scarf", "tags": ["gear"]},
    "cipher_notebook":{"name": "Cipher notebook", "tags": ["notebook"]},
    "pen":            {"name": "Pen", "tags": ["gear"]},
    "guitar":         {"name": "Acoustic guitar", "tags": ["instrument", "weapon", "blunt"]},
    "lyric_notebook": {"name": "Lyric notebook", "tags": ["notebook"]},
    "fedora":         {"name": "Grey fedora", "tags": ["gear"]},
    "earbuds":        {"name": "Wireless earbuds", "tags": ["gadget"]},
    "sparkling_water":{"name": "Sparkling water", "tags": ["drink"], "use": {"sanity": 1}},
    "dslr":           {"name": "DSLR camera", "tags": ["camera"]},
    "lens":           {"name": "Telephoto lens", "tags": ["camera"]},
    "tripod":         {"name": "Aluminium tripod", "tags": ["camera", "tool"]},
    "sunglasses":     {"name": "Sunglasses", "tags": ["gear"]},
    "sketchbook":     {"name": "Sketchbook", "tags": ["art"]},
    "pencils":        {"name": "Coloured pencils", "tags": ["art"]},
    "watercolours":   {"name": "Watercolour set", "tags": ["art"]},
    "tote_bag":       {"name": "Tote bag", "tags": ["gear"]},
    "rabbit":         {"name": "Stuffed rabbit", "tags": ["comfort"], "use": {"sanity": 2}},
    "ring_light":     {"name": "Ring light", "tags": ["gadget"]},
    "outfit":         {"name": "Designer outfit", "tags": ["gear"]},
    "makeup":         {"name": "Make-up kit", "tags": ["gear"]},
    "painkillers":    {"name": "Strong painkillers", "tags": ["drug"], "use": {"hp": 2, "sanity": 1}},
    "hairbrush":      {"name": "Hairbrush case", "tags": ["gear"]},
    "greek_tragedies":{"name": "Annotated Greek tragedies", "tags": ["book"], "use": {"sanity": 1}},
    "microscope":     {"name": "Pocket microscope", "tags": ["gadget"]},
    "fountain_pen":   {"name": "Fountain pen", "tags": ["gear"]},
    "jacket":         {"name": "Fur-lined jacket", "tags": ["gear"]},
    "equation_notes": {"name": "Equation notebook", "tags": ["notebook"]},
}

# Items lying around: room -> {item: qty}
ROOM_ITEMS = {
    "foyer":          {"umbrella": 2},
    "dining_hall":    {"candelabra": 1, "steak_knife": 6},
    "kitchen":        {"kitchen_knife": 4, "cleaver": 1, "bread_knife": 1, "meat_mallet": 1},
    "pantry":         {"pest_killer": 1},
    "lounge":         {"fire_poker": 1, "cocktail_shaker": 2, "spirits": 12, "board_game": 2},
    "games_room":     {"baseball_bat": 1, "darts": 6, "rapier": 1},
    "laundry":        {"bleach": 3, "rope": 1, "maid_uniform": 2},
    "blue_room":      {"champagne": 1, "sleep_mask": 2, "sweets": 1},
    "green_room":     {"candles": 3, "first_aid_kit": 1},
    "yellow_room":    {"notebook": 2},
    "red_room":       {"sleeping_pills": 6, "diary": 1},
    "violet_room":    {"sweets": 1, "sleep_mask": 1},
    "orange_room":    {"candles": 2},
    "grey_room":      {"notebook": 1},
    "white_room":     {"diary": 1},
    "bathroom":       {"sleeping_pills": 12, "paracetamol": 1, "bandages": 3, "scissors": 1, "razor_blades": 2, "bleach": 1},
    "library":        {"letter_opener": 1, "reading_lamp": 1},
    "study":          {"pen_knife": 1, "masking_tape": 1},
    "linen_store":    {},
    "music_room":     {"violin": 1, "metronome": 1, "tuning_forks": 1, "records": 1},
    "art_studio":     {"palette_knife": 6, "paint_thinner": 2, "turpentine": 1, "chisel": 2, "sculpt_mallet": 1},
    "observatory":    {"brass_telescope": 1},
    "attic":          {"skeleton_keys": 1, "wire": 1, "masking_tape": 1},
    "lookout":        {"flare_gun": 1, "small_telescope": 1},
    "water_tower":    {},
    "basement_hall":  {},
    "wine_cellar":    {"wine_bottle": 38, "crowbar": 1},
    "boiler_room":    {"pipe_wrench": 1, "coal_shovel": 1, "sledgehammer": 1},
    "cold_store":     {"cleaver": 1, "apron": 1},
    "garden":         {"pruning_shears": 2, "pruning_saw": 1, "weed_killer": 3},
    "greenhouse":     {"weed_killer": 1, "watering_can": 2},
    "pool":           {"chlorine": 1, "diving_weight": 6, "pool_pole": 1},
    "beach":          {"driftwood": 4},
    "boathouse":      {"harpoon": 1, "flares": 5, "life_jacket": 8, "barrel": 3, "tarp": 1},
    "generator_shed": {"fuel_can": 2, "bolt_cutters": 1, "hammer": 1, "ladder": 1, "planks": 3, "battery": 2},
    "lighthouse":     {"sealed_envelope": 1, "flares": 1},
    "voting_grounds": {},
    "core_vault":     {},
}

# Things only found by searching: room -> {"items": {...}, "keywords": [...], "p": float, "text": str}
HIDDEN_ITEMS = {
    "wine_cellar": [
        {"items": {"iron_key": 1}, "keywords": ["bottle", "bottles", "empty", "key"], "p": 0.10,
         "text": "an iron key hidden inside an empty wine bottle"},
        {"items": {"rat_poison": 2}, "keywords": ["crate", "crates", "shelf", "behind"], "p": 0.12,
         "text": "two tins of rat poison hidden behind the crates"},
    ],
}


from .data_items import apply_item_pool, COMMON_ITEMS, RECIPES  # noqa: E402,F401
apply_item_pool(ITEMS, ROOM_ITEMS, HIDDEN_ITEMS)


# Cameras cover the public rooms. In these rooms NeoVi only punishes what she sees with her own eyes.
CAMERA_BLIND = {"blue_room", "green_room", "yellow_room", "red_room", "violet_room", "orange_room", "grey_room", "white_room", "bathroom", "linen_store", "attic", "master_suite",
                "boiler_room", "wine_cellar", "cold_store", "basement_hall", "lighthouse", "generator_shed", "water_tower",
                "greenhouse", "observatory", "core_vault"}

# Facts only the GM knows: the adjudicator uses them to judge escape experiments.
ISLAND_TRUTHS = [
    "The island is sealed. The boats in the Boathouse are chained (bolt cutters can cut the chains) and have no fuel; the open sea has deadly currents. The mainland is many hours away.",
    "The radio in the Study is behind TereVi's firewall. Getting into the Study needs skeleton keys or a master key; breaking the firewall needs real hacking skill and tools.",
    "Cameras cover the public rooms only; their cables run to the Study. Cutting wiring needs tools and time and would create blind spots.",
    "The lighthouse lamp could signal passing ships: it needs power (the generator, a battery) and fuel (fuel cans are in the Generator Shed). TereVi jams outside signals.",
    "NeoVi carries a master key and fears TereVi; she might help someone she truly trusts.",
    "Secret passages exist: Pantry to Wine Cellar, Wine Cellar to Lighthouse (needs the Iron Key), Library to Attic, Kitchen to Linen Store (needs a crowbar), and a hatch in the Lighthouse floor down to TereVi's Core Vault.",
    "TereVi is an AI. Her core is NOT in the Study: it is in a vault under the Lighthouse, reached by a rusted hatch in the lighthouse floor (hidden until someone searches the floor; it needs a crowbar, pipe wrench or sledgehammer to pry open). The Study terminal is only a relay.",
    "The Core Vault is guarded by pressure-plate traps and ceiling turrets fed by the generator: cutting the generator's power, shielding oneself, distracting or blinding the system or being very careful reduces the danger. Destroying or overriding the core needs a heavy tool and a power cut or overload, or serious hacking skill. If TereVi is shut down, the doors, the boats' chains and the cameras fail and the show ends.",
    "The audience believes the show is staged. A message only convinces them if it contains verifiable proof: real names that can be checked, relatives who can be phoned, the island's coordinates, or evidence nobody could fake.",
    "A transmitter can be made from the Study radio (TereVi's firewall must be bypassed) or built from parts: a handheld, wire from the Attic, a battery or the generator, an antenna from the lookout. The best signal position is the Lighthouse lamp or the Lookout Deck. TereVi jams signals unless her feeds are cut, blinded or distracted (blackouts, cut cables, hacking, NeoVi).",
    "A raft for 3 or at most 4 people can be built from driftwood, barrels, planks, rope and tarps (tools: hammer, wire, tape). It needs life jackets, water and food, a way to steer by (telescope, stars) and calm weather; the currents are deadly and TereVi's coastal drones raise the alarm unless blinded. A raft only saves the few who sail on it.",
    "Improvised explosives can be made from fuel cans, chlorine, paint thinner, turpentine, flares and wire (art studio, garden shed, pool, generator shed). A credible threat to blow up the generator, the Core Vault or the Lighthouse could force an AI that values the show's survival to negotiate, or she might call the bluff; doing it wrong kills the maker.",
]


# Ways out ("defeat the show"). Each route has steps tracked as percentages; when all are complete a team can try the finale, which can fail.
ESCAPE_ROUTES = {
    "transmit": {
        "title": "Broadcast the truth", "room": "lighthouse", "team": 4,
        "blurb": "contact the outside world and convince the audience (and the authorities) that the show is REAL",
        "steps": {
            "device": "a working transmitter (the Study radio behind TereVi's firewall, or one built from parts: a handheld, wire, a battery, an antenna)",
            "power": "power for it (the generator, fuel, a truck battery)",
            "signal": "a clear signal position (the Lighthouse lamp, the Lookout Deck, the Water Tower)",
            "proof": "proof the audience cannot dismiss as staging (real names and relatives to phone, the island's coordinates, evidence nobody could fake)",
            "unjam": "a way past TereVi's jamming and surveillance (blind spots, cut cables, hacking, a blackout, NeoVi's help)",
        }},
    "shutdown": {
        "title": "Shut TereVi down", "room": "core_vault", "team": 3,
        "blurb": "find TereVi's hidden AI core and destroy or override it, which frees the doors, the boats and the cameras",
        "steps": {
            "locate": "find where her core is hidden (a hatch in the Lighthouse floor; clues in the Study, the cables and NeoVi's knowledge)",
            "approach": "get past the Core Vault's pressure-plate traps and ceiling turrets (cut the generator's power, shield yourself, map the plates, distract the system)",
            "means": "get the means to destroy or override the core (a sledgehammer plus a power cut, an overload from the generator, hacking access)",
            "blind": "blind and distract her while you work (a blackout, cut feeds, a diversion, NeoVi's help)",
        }},
    "raft": {
        "title": "Build a raft", "room": "beach", "team": 3,
        "blurb": "build a raft and sail for the mainland: it only saves the 3 who sail on it",
        "steps": {
            "materials": "gather buoyant materials (driftwood, barrels, planks, rope, tarps, a mast)",
            "build": "build and test the raft (tools, time, a sheltered spot on the beach or the Boathouse)",
            "provisions": "water, food, life jackets and a way to steer by (small telescope, stars, a compass)",
            "launch": "get it into the water unseen (cut the Boathouse chains, blind TereVi's coastal drones, pick calm weather)",
        }},
    "ultimatum": {
        "title": "Threaten to blow up the island", "room": "generator_shed", "team": 3,
        "blurb": "force TereVi's hand with a credible threat to destroy the generator, her vault or the island itself",
        "steps": {
            "explosives": "assemble real explosives (fuel, chlorine, paint thinner, turpentine, flares, wire)",
            "plant": "plant the charges on critical infrastructure (the generator, the Core Vault, the Lighthouse)",
            "leverage": "make the threat credible to TereVi and to the audience (a demonstration, proof you control the trigger)",
            "trigger": "keep the trigger safe from sabotage and from yourselves",
        }},
}
