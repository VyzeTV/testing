# Murder Channel: Live Edition — Design Document

**For what the game is and how it works today, read `docs/GAME_DESIGN.md`.** This file is the original proposal and roadmap, kept for its reasoning (Dwarf Fortress lessons, phases, risks).

Status: proposal, nothing implemented. Written 2026-10-15 in the fork `E:\MC\murder-channel\app_live` (port 8766, fresh `state/` and `runs/`).
The original `E:\MC\murder-channel\app` (port 8765) stays the stable turn-based edition.

---

## 1. Purpose

Turn the simulation from a turn-based, model-driven day into an always-live, tile-based world in the spirit of Dwarf Fortress:

* characters walk a tile map, act on things they can actually reach, see, hear and break;
* routine behaviour is driven by a deterministic engine (personality, needs, stress, plots); the language model writes speech and settles real dilemmas;
* the same house, the same hidden entrances and connection points as today;
* the world runs continuously, and important moments pause it with a message dialog.

### Non-goals
* Fortress logistics (stockpiles, labours, trade, farming, 3D digging, z-level fluid physics).
* Photographic art. The look is schematic tiles plus the existing portrait tokens.
* Copying anything from Dwarf Fortress code or data. DF's AI is closed source. Only its published data model and general design ideas informed this document.

---

## 2. Why: what the last real week showed

Facts from the seven-day real run (days 1-7):

| Observation | Root cause in the turn-based design |
|---|---|
| Cail and Vixen plotted for 3 days, had 6 same-room tick ends, but only one real attack opportunity; 3 attacks logged "target was not there". | Decisions are made in parallel from a start-of-turn snapshot; attackers and targets swap rooms; a model-chosen `attack` against someone elsewhere is simply dropped. |
| Vixen's death was unclear and had no trial. | Spree rule fired on sanity alone, waived the trial when Cail killed her, and broadcast "the frenzy took her". No readable chronicle of who did what. |
| Characters seem to talk from different rooms. | Reaction "bolts" and NeoVi punishments are recorded in the same tick as the dialogue, so the viewer moves people before they speak. |
| Median sanity about 25 by Day 5; most survivors below 20 by Day 6. | One scalar `sanity` with big fixed costs (taser -40, detention -32 in one day) and recovery only from fixed events. |
| Offensive body actions (knockout, carry, rob, stage) never used; one attack in a week. | Utility of those actions is decided by the model's prose, not by scored opportunity. |
| About 100 model calls and $3-4 per day. | Every agent is asked what to do every two hours. |

A continuous, tile-based simulation fixes the first three structurally: contact, line of sight, noise and conversation are computed from positions each tick, so there is no stale snapshot and no remote talk.

---

## 3. Lessons borrowed from Dwarf Fortress

Read from the install (raws, Lua generators, token names inside the exe). Behaviour of the closed-source AI is inferred.

1. **Characters are numeric bundles.** About 50 personality facets (0-100), about 25 values, about 20 needs, 50-odd emotions. Behaviour comes from small rules over those numbers, not from scripts.
2. **Needs -> thoughts -> stress -> named breakdown** (tantrum, melancholy, berserk, catatonic, insane). Recovery comes from meeting needs (socialise, rest, drink, pray), which gives people reasons to go places.
3. **Everything that happens is a typed event** with participants and a location (about 150 history event kinds; activity events such as conversation, harassment, conflict, performance). "Legends" is just a view over that log.
4. **Crime pipeline:** witnesses report, suspects are interrogated, someone is convicted; interrogation outcomes depend on the subject's personality and values (trusting, loner, stubborn, values truth/law/harmony).
5. **Plots are first-class objects:** assassination, abduction, framing, sabotage, infiltration, corruption, bribery, embezzlement, with plotter and agents, and they can be foiled or revealed.
6. **Procedural generation by composition:** weighted random parts under difficulty budgets (creatures, curses, secrets, entities).
7. **Data-driven definitions:** positions, duties and behaviours live in plain text raws.

---

## 4. Target architecture

```
                 +-----------------------------------------------+
                 |                  Browser viewer               |
                 |  tile canvas | overlays | panels | dialogs     |
                 +----------------------^------------------------+
                                        | SSE/WebSocket: state diffs, events
                 +----------------------+------------------------+
                 |                  Sim server (Python)          |
                 |  clock -> world tick -> event bus -> pause    |
                 |                                               |
                 |  Brain tiers per agent:                       |
                 |   1 Reflex   (every tick)  movement, hazards  |
                 |   2 Utility  (when idle / interrupted)       |
                 |   3 Deliberation (LLM)  rare, queued, async   |
                 |                                               |
                 |  Systems: perception, conversation, plots,    |
                 |  crime/evidence, body (conditions), doors,    |
                 |  fire/water/smoke/light, noise, rules         |
                 |  Event log (single source of truth)           |
                 +-----------------------------------------------+
```

### 4.1 Time model
* One sim tick = one game minute. A game day is 1,440 ticks.
* Real-time scale at speed x1: 1 game minute per 0.5 s (a day in 12 minutes); x2, x4, x8, x16 and "fast-forward until something important happens". A headless mode runs as fast as the CPU allows (a week in seconds with the mock backend) for balance tuning.
* The existing daily structure (Day 1 intros then reveal at 20:00, deadline, rules, night turn, trials) becomes scheduled world events on the clock, not loop structure.
* The sim runs on its own thread; the model is only called through a queue (4.5).

### 4.2 Agent state
Extends today's `world.agents[cid]`.

| Group | Contents |
|---|---|
| Identity | existing cast data (persona, speech, candor, secret, home). Static text stays text. |
| Facets | 0-100 each. Proposed set of about 16: anger, vengefulness, trust, gregariousness, altruism, assertiveness, courage, cruelty, impulsiveness, stress vulnerability, vanity, ambition, curiosity, orderliness, humour, romantic. Derived once from the persona (by the model at game start, then frozen; user-editable in the Director panel). |
| Values | about 12: loyalty, law, truth, cooperation, cunning, friendship, independence, self-control, competition, romance, knowledge, tranquility. Used for conflict, interrogation, trial and plot motives. |
| Needs | about 10 with a level 0-100 and a decay rate: social, intimacy, rest, food, water, safety, purpose (escape work), creativity, privacy, possessions. |
| Mind | list of active thoughts (cause, valence, weight, expiry). Stress = decayed sum. Replaces the scalar `sanity`; sanity shown to the user is derived (100 - stress). Breakdown states reuse today's ladder: panic, snap, deranged, spree. |
| Body | existing conditions, injuries, unconsciousness (`conds`, `out`), hunger/thirst. Unchanged. |
| Relationships | existing `aff`, `ties`, bonds, alliances, hooks; now built from the event log. |
| Task | current task (go, use, talk, hide, search, craft, treat, attack...) with a target, path and duration; plus a queue. |
| Memory | references to event-log entries the agent witnessed or heard about, with decay and distortion (existing imperfect-memory rules). |

### 4.3 Brain tiers
1. **Reflex (every tick, no model):** follow path, open doors, avoid fire and deep water, flee smoke, step aside, pick up what they are carrying, fall, faint, bleed. Always interrupts the current task when a hazard or an attack happens.
2. **Utility (whenever a task ends or is interrupted):** every candidate action is scored from needs, facets, values, current stress, relationships, active plot step, rules in force, opportunity (see 4.6) and risk (witnesses). The best (with noise from the impulsiveness facet) becomes the next task. Candidates include everything that exists today: eat, rest, socialise, search, craft, treat someone, lock/pick/barricade, experiment, sneak, spy, knock out, carry, rob, frame, attack.
3. **Deliberation (LLM, asynchronous):** called only when
   * utility scores are within a margin and the stakes are high (accuse, forgive, start or abandon a plot, betray, confess);
   * writing dialogue for a conversation scene (4.5);
   * designing a plot or a cover story (plot stage change);
   * trial speeches, TereVi announcements, nightly reflection.
   The model returns an *intention* (target, method, tone), never tile moves. The engine converts it to a task.

### 4.4 Event log (single source of truth)
Every change emits a typed event:
`{id, tick, kind, actors[], targets[], place (room + tile), visibility, witnesses[], text, data}`.

* Kinds start from today's `log_event` types and grow toward a DF-like taxonomy: move, door_open/close/lock/pick/break, take/drop/give/steal, use, craft, speak (conversation scene), friction, plot_stage, attack, wound, faint, treat, carry, frame, body_found, case_open, clue_found, testimony, vote, execution, fire_start, flood, blackout, rule_broken, punishment, newcomer, etc.
* **Witnesses are computed from the grid** (4.6), not guessed.
* Derived views: the live feed, the *Chronicle* panel (Legends-style, filterable by person/place/day, includes private knowledge in GM view), clues and notebooks, ties and hooks, the trial case file, Stats, "Previously on".
* The turn-based code that today writes `ties`, `hooks`, `disturbances` and `clues` becomes a set of subscribers to this log.
* Event sourcing also gives replay: seed + commands + log reproduce a run.

### 4.5 Conversation and the language model
* A conversation is an activity event with participants and a place. It starts when two or more agents are within talking range (same room or within 3 tiles with a clear path for hearing) and at least one wants to talk (social need, plot, rule, reaction to an event).
* Dialogue is produced per *scene* (3-8 lines) by a single model call, queued asynchronously. While waiting, participants show a "..." marker and keep their current task; the world does not block.
* Volume matters: normal, whisper, shout. Noise travels through the grid with attenuation (4.6). Whispering in a room is overheard by nobody outside. Shouting through a door is heard. **Remote speech is impossible without a radio, intercom or similar item**, fixing the cross-room bug. TereVi speaks through monitors (tiles) and the PA.
* Budget: a per-game-hour cap on model calls (setting). When exhausted, scenes use a template fallback driven by facets and needs, so the sim never stalls. The mock backend is the same fallback.
* Expected load: about 40-60 calls per game day (versus about 100 today), dominated by scenes and the daily TereVi/NeoVi/night material.

### 4.6 Perception on the grid
* **Line of sight** (Bresenham or shadowcasting on the 2D plane; walls, closed doors, smoke and darkness block or reduce it).
* **Hearing:** noise events with a loudness spread by flood fill with attenuation through doors, walls and distance.
* **Light:** each tile has a light level from daylight, lamps, candles, flashlights, fire, power state (blackouts darken the house). Dark tiles raise stealth and reduce sight.
* **Cameras (TereVi):** a set of tiles covered by cameras (and a list of blind spots); the "camera archive" clue is now literally what cameras saw.
* **Opportunity** for a plotter = target in reach and path, number of agents who could see or hear, camera coverage, light, time since last seen. This replaces today's `len(humans) <= 2` check.
* **Witness set** of any event = agents who could see or hear it, with confidence by distance and light.

### 4.7 Rules and enforcement
Daily rules (roulette, user-typed, presets) become predicates over the event log and zone flags: in-zone, outdoors/indoors, speech volume of conversation events, clothing worn, item carried. The AI referee is only needed for text rules that cannot be coded; coded checks stay deterministic. This removes the class of mis-enforcement seen on Day 2.

### 4.8 What stays model-driven
TereVi (announcements, mischief, verdicts), NeoVi's flavour, dialogue, trial speeches, newcomer development, rule roulette text, diaries. These are authored text, not decisions.

---

## 5. The grid map

### 5.1 What exists today (measured)
* 37 rooms in six zones: roof 2, second floor 6, first floor 9, ground 7, basement 5, grounds 8. Each room is a rectangle on a 1390 x 730 schematic.
* 42 connections: 24 doors, 6 outside, 5 secret, 4 stairs, 2 paths, 1 window. 3 are locked (key), 5 are hidden (4 hidden, 1 hidden and locked), 2 need an item.
* Total floor area about 761,000 px^2, which is **about 7,600 tiles at 10 px per tile** (1,900 at 20 px). Rooms are 11-22 tiles wide at 10 px. Tiny by DF standards.
* 252 item types, 54 common (unlimited) supplies, 6 hazard rooms, rooftop and tower walkways, a pool, beach, lighthouse, tunnels, a vault.

### 5.2 Conversion rules (same layout, same secrets)
The current room list is the source of truth; a one-off generator produces the tile map and a checked-in JSON; an editor can adjust it later.

1. Each room rectangle becomes a block of floor tiles at 1 tile = 10 px; outer edges become walls.
2. Each connection becomes a door tile (or tiles) on the shared wall segment, with the same state fields as today: `closed/open/locked/barred/broken/hidden/jammed`, `keys`, `needs`. Hidden connections render as plain wall until discovered, then as a door (existing `discover` text and keywords stay).
3. Stairs: stair tile pairs that link z-levels; each floor is its own 2D plane (zones roof / second / first / ground / basement). Grounds is an outdoor plane at ground level with grass, sand, rock, water.
4. Windows: window tiles (see-through, climbable or breakable). The kitchen window to the garden is one.
5. Rooms that are not adjacent on the schematic but are connected (wine cellar -> lighthouse tunnel, pantry -> wine cellar lever, library -> attic, kitchen -> linen store dumbwaiter, lighthouse -> core vault): v1 uses short corridor tiles hidden behind the secret door, drawn in free space beside the rooms, with travel time preserved (the `cost` field becomes tile length). Fallback: portal tiles with a delay.
6. Travel costs: tile moves replace the `cost` minutes; the 40-minute per-hour budget disappears. Existing `move_factor` (injuries) becomes ticks per tile.
7. Rooms keep their ids and become **zones**. Locks, rules, ownership (bedrooms), camera coverage and hazard flags attach to zones; `occupants(room)` = agents standing on the room's tiles. This lets almost all existing systems keep working through a compatibility layer.

#### 5.2.1 As built in Phase 1
* 144 x 70 tiles per level; the house is one row per floor (same footprint on every level, so stairs line up) and the grounds sit east of the ground floor on the same plane.
* Far connections: each floor hub (foyer, landing, upper landing, basement hall) opens onto a corridor strip that serves all its distant rooms; the one other far door (kitchen to laundry) is a private lane; outdoor connections are doors in the building wall facing the open zone, with path tiles drawn for the "path" edges.
* Open zones (garden, pool, beach) have no walls; the field around them is open, so outdoor movement is free between them. Hidden connections are one hidden stair or hatch tile at each end (shown only in the GM view). The far tunnel (wine cellar to lighthouse) is a hatch pair with its travel cost kept (portal).
* `static/grid_map.json` is GM data: it lists the hidden entrances, so the live server must strip them for any player-facing view.

#### 5.2.2 As built in Phase 2 (what is live and what is not yet)
* The engine still decides every two game hours; between decisions the world is played out on the tile map (walking routes, settling, wandering, gathering for talk). Decisions are therefore not yet continuous: that arrives with Phase 5 (utility AI), and perception, noise and per-tick attacks with Phases 3-4.
* The plan is a pure, deterministic function of the tick, so it adds no randomness to the game and can be recomputed for replays. The engine runs one turn ahead of the viewer (existing `BUFFER`); if the next turn is not ready the clock waits.
* NeoVi and TereVi do not walk yet (their positions are not in the tick snapshot). Dead people stay where they fell, shown greyed.
* Pause settings live in the browser (localStorage): class defaults critical = dialog, important = dialog, notable = toast, background = log; any event kind can override its class.

#### 5.2.3 As built in Phase 3
* Perception is pure geometry (`Perception`) plus a mixin of engine hooks. Daylight lets people see across a whole garden (18 tiles); darkness (a blackout) cuts sight to 2 tiles and hearing decides. A whisper carries about 2 tiles, normal speech 8 (a wall costs 5, a door 2, a window 3), a shout 18, and sound climbs stairs only when loud.
* Positions: the engine uses the live planner's tile when it matches the person's room, otherwise a fixed per-person pick in the room (`GridNav.nominal`), the same pick the planner starts from.
* Not yet: smoke occlusion, flashlight cones, cameras as a clue source (the existing camera ledger is unchanged), radio items for remote speech (until then nobody can talk across rooms; TereVi speaks through her monitors), noise from actions that wakes sleepers (the door-noise code is unchanged).
* Debug overlay in the live view: show what the followed person sees (blue) and hears at normal volume (orange dots), for lit, dim or dark rooms; the Cameras toggle tints covered rooms and darkens blind spots.

#### 5.2.4 As built in Phase 4
* Fields are sparse dicts in `state["env"]` (saved with the game); the engine advances them in five-minute steps over each turn (using the engine's seeded RNG) and attaches half-hourly frames so the viewer shows fires growing. Fire spreads by tile flammability (carpet and wood burn, stone and tile do not, furniture burns longest), makes smoke, wrecks furniture and burns doors; water extinguishes, flows downhill in small amounts and dries; smoke crosses doors and windows and thins outdoors, and blocks sight when thick.
* Marks (blood, drag, soot, splinters, glass) are evidence: `env_clues` turns blood that is not the victim's, drag marks, forced entry and scorching into case clues without naming anyone.
* Items on tiles are a view of the room-level stacks (a fixed tile per stack); fire on a tile burns flammable items there. Moving the item model fully onto tiles is later work.
* Not yet: weak-wall breaching (deferred by decision), floods that carry items, noise that wakes sleepers through the tile field (the old door-noise code is unchanged), rain.

#### 5.2.5 As built in Phase 5 (and what it does not yet do)
* Every change of sanity made anywhere in the engine (`stat()` or a direct assignment) is absorbed as a thought with a weight that fades linearly (bigger shocks last longer, up to about three and a half days); good news is a short uplift. Stress adds unmet needs and the looming deadline, scaled by stress vulnerability and the `stress_scale` dial; the displayed sanity is set point minus stress, so it recovers when nothing new hurts and needs are met (sleep, company, safety, meaningful work, time alone).
* Facets and values shape stress, plot motives (vengefulness, anger, cruelty, altruism) and the prompt (YOUR NATURE, YOU VALUE, YOU FEEL lines); the live Cast panel shows stress, need bars and the strongest thoughts.
* The model is still asked on: cases, plots in the stalking or striking stage, daily rules, hazards, mornings and evenings, crises (stress 50+, a need nearly empty, low sense of purpose), injuries, conflicts and bonds in the room, and a one-in-five heartbeat. Everything else is decided by the engine. It is conservative on purpose: a real run will tell how far the share can grow.
* Not yet: interrogation and trial tactics from facets and values, utility-scored plot design, and model calls only for scenes (conversations are still model-written, though people whose need for company is met chat less).

#### 5.2.6 As built in Phase 6 (and what it does not yet do)
* Pursuit is a post-decision rule in attack resolution (path cost up to 30 minutes, 50-75% to catch up, higher with assertiveness), so the model still only says whom to attack.
* Witness material comes from the chronicle (`seen` lists computed from the grid in Phase 3). Interrogation produces testimonies and chronicle entries (`interrogation`, GM view); killers resist (a quarter of the usual chance).
* Not yet: utility-scored plot design (plots are still model-proposed and engine-steered), witness reports to NeoVi or TereVi, cover stories checked against the chronicle, and interrogation tactics chosen by the model rather than the engine.

### 5.3 Tile layers
| Layer | Content | Notes |
|---|---|---|
| Terrain | floor, grass, sand, rock, water (shallow/deep), tile material | sets walk cost, flammability, sound absorption |
| Structure | wall, door, window, stairs, rubble, hole | each with material, HP, state |
| Furniture | bed, table, shelf, workbench, barrel, cabinet, wardrobe, desk, monitor, camera, switch, fuse box | each is an interactable with a task type |
| Items | stacks on tiles (existing 252 types) | search reveals hidden items |
| Liquids | depth 0-7 | flows to lower neighbours; pool, bathroom, flooding, burst pipes |
| Fire | intensity 0-3 | spreads to flammable neighbours; consumes wood and cloth; makes light and smoke |
| Gas / smoke | concentration 0-9 | diffuses through open doors; blocks sight; damages (breathless) |
| Light | level 0-15 computed per tick | daylight, lamps, fire, power |
| Temperature | per zone (cold store, boiler room) | drives chilled/burned |
| Marks | blood, footprints, drag marks, soot | evidence for the case file |
| Noise | transient events | loudness and source for hearing |

All fields are sparse (only active tiles are simulated). A pure-Python prototype measured about 2.4 ms for a whole-map diffusion step and about 5 ms for a full-map A* query; numpy is available for fields. With 8 agents at 1 tick per game minute, the sim is tiny relative to any reasonable budget.

### 5.4 Interactables (rendered and actionable)
Doors (open, close, lock, unlock, pick, break, barricade with prop), beds (sleep; sleeping agents are defenceless), shelves and wardrobes (search, take), workbenches (craft, with recipe-required stations), sinks and taps (water, wash, fill), stoves and ovens (cook, burn), fuse box and generator (blackout, power), switches, monitors and cameras (TereVi), the radio in the study, boats, ladders and rope (climb), the lever and bookcase secrets, traps, beds and chairs as cover, corpses (a body is an item-like entity: discover, drag, hide, burn).

### 5.5 Destructible environment
Scope for v1 is deliberately modest:
* **Doors and windows:** HP by material; break actions already exist; NeoVi repairs weekly (existing).
* **Furniture:** can be smashed for planks (crafting input), used as barricades, burn.
* **Walls:** only designated *weak* walls (plaster, panelling) can be broken through, with a tool and noise; stone and load-bearing walls are indestructible. Explosions (generator shed) breach weak walls and leave rubble tiles.
* **Fire:** spreads on flammable materials; fire doors, water and sand extinguish; burns clothing and items; produces smoke.
* **Water:** burst pipes, a flooded cellar or pool overflow; liquids can short the fuse box.
* No structural collapse and no 3D digging in v1; holes through floors are scripted events only (attic floor, lookout railing).

### 5.6 Rendering
* **Look: light tileset (decided).** Flat 2D tiles with simple texture and drawn objects: brick-pattern walls, plank-line floors, rippled water, grass and sand textures, flame shapes, doors with handles, furniture as small drawn sprites. Tiles are generated in code (an atlas built at load time from small drawing routines, no external art) so the look can be swapped or refined later without engine changes. Light overlays darken or tint tiles; smoke and fire are translucent layers on top.
* Canvas 2D tile renderer using that atlas. Z-level selector (roof / second / first / ground / basement / grounds), zoom and pan, overlay toggles (fire, water, smoke, light, noise, cameras, blood, zones, hidden doors in GM view).
* **Characters are the actual characters, shown as their portrait tokens** (the existing `static/portraits/*.png`: the eight cast members plus TereVi's monitor presence and NeoVi), drawn as round tokens with a coloured ring, walking tile to tile with smooth interpolation, one token per tile. A name tag appears on hover or selection; state icons sit on the token (unconscious, bleeding, carrying, hiding, speaking "...", plotting in GM view). Tokens are scaled to the tile size, with a zoom level where the portrait is clearly recognisable. Selecting a token opens the existing Cast detail (Body row, relationships, current task and thought).
* Existing panels (Cast, Web, Booth, Room, Board, Stats, Tuning, Director) are reused; add Chronicle, Tasks/Thinking, Overlay toggles, and a Speed control.
* Rendering cost: 7,600 tiles and a few dozen sprites, trivial for a canvas at 60 fps.

### 5.7 Movement and interaction rules
* Agents occupy one tile; two agents may share a tile only in doorways when passing (swap) or when one is carried or unconscious.
* A* on the tile graph (cost by terrain, doors, crowding), cached by room-graph hierarchy for long trips.
* Reach: interact with adjacent tiles; ranged actions (throw, spy through a keyhole, shout) use line of sight.
* Attacks resolve per tick between adjacent agents with initiative; the target's movement does not cancel the attack, the attacker simply follows (this removes "target was not there").
* Carrying and dragging: one agent moves a helpless one at half speed, leaving drag marks.

---

## 6. Pause and announcement system

Event classes with a default response; each class is configurable (pause + dialog, toast only, log only), plus "do not show again this game".

| Class | Examples | Default |
|---|---|---|
| Critical | any death, body found, case opened, trial starts/ends, execution, deadline 24 h / 1 h / strike, the reveal, spree start, endgame, newcomer needed, game over | pause + dialog |
| Important | plot stage becomes striking, first fire or flood, blackout, someone starts a breakdown (snap, berserk), knockout, someone locked in, NeoVi punishes, escape attempt resolves, new rule announced | pause + dialog (toggle) |
| Notable | alliance, betrayal, hook noticed, quarrels, treatment | toast, no pause |
| Background | movement, meals, routine chatter | feed only |

Dialog contents: title, a one-paragraph plain statement written from the event (who, what, where, when), a "who saw it" line (GM view), buttons *Continue*, *Show me* (centre and zoom on the tile, open the chronicle entry), *Slow down*, *Mute this kind*. Trial and newcomer decisions open their existing modal flows and return to live play afterwards. A **"Clear death"** message always states cause and, where it is knowable, who did it in the GM view. Pause also triggers when the user leaves the tab if "pause when away" is on.

---

## 7. Migration strategy: keep what works

The fork reuses almost all current Python systems through a compatibility layer.

1. **Strangler approach:** build the grid world and live loop first, expose a *room view* (`occupants(room)`, `agent.room`, `reachable`) so conditions, items, crafting, plots, forensics, trial, tuning and tests keep running.
2. Replace the turn loop (`run_tick`, parallel decisions, reaction pass, night turn) by the live loop plus task execution.
3. Replace sanity by stress/needs only after the grid works (flag-controlled so the two can be compared headlessly).
4. Move `ties`, `hooks`, `clues` onto the event log, then add the Chronicle panel.
5. Models are called through the same `LLM` wrapper (CLI backend and mock); prompts are re-used with a new perception block (what the agent can see and hear now).

Code reuse estimate: conditions, nonlethal, doors (state logic), craft, items, clothing, cases, trial, forensics, plotting (as utility inputs), tuning, telemetry. Rewritten: engine loop, world movement/occupancy, stealth/spying (grid-based), reaction pass, night turn, conversation grouping, viewer map layer.

---

## 8. Phased roadmap

Each phase ends with a headless test and a playable build.

| Phase | Deliverable | Acceptance |
|---|---|---|
| 0 | **Done 2026-10-15.** Fork done. Event log (`murder/chronicle.py`) added to the engine without behaviour change; Chronicle tab in the viewer; `/api/chronicle`. | Same smoke suite (541 checks); every death has a public statement and a GM-view truth entry. |
| 1 | **Done 2026-10-15.** `murder/gridmap.py` builds `static/grid_map.json` from `ROOMS` + `build_edges`; static light-tileset viewer `static/grid.html` with five levels, GM toggle for hidden entrances, furniture, cameras and a token preview. | All 37 rooms and 42 connections present with the same hidden/locked/key/needs state; every room reachable on the tiles; hidden entrances render as floor until the GM view is on. |
| 2 | **Done 2026-10-15 (first slice).** `murder/gridnav.py` (A* on the tiles, stairs, hidden hatches only when the engine used them), `murder/livetimeline.py` (each engine turn becomes minute-by-minute tile tracks, scheduled events and speech bubbles, attached to every tick as `tick["live"]`), `static/live.js` (game clock, speed x0.5-x16, skip-to-next-event, portrait tokens walking, follow a character, feed and cast panels, per-class and per-kind pause settings with a message dialog, pause when the tab is hidden). | A mock week plans without errors; every track tile is walkable and every alive person ends in the engine's room; the clock never runs backwards; the dialog pauses on every Critical event by default. |
| 3 | **Done 2026-10-15 (first slice).** `murder/perception.py`: line of sight (walls and closed doors block, windows do not), light levels (lit 18 / dim 7 / dark 2 tiles), sound that spreads through doors, walls and stairs by loudness (whisper to shout), camera coverage from the map, witnesses, plot windows. Engine hooks (behind the `perception` dial): witnesses of public events, a plotter's window, and conversations in very large rooms. The live planner keeps every speaker in the room they speak in. | Property over many mock turns: no speech bubble comes from someone outside the room being talked in (0 of 151+); the old room-level behaviour returns with the dial at 0. |
| 4 | **Done 2026-10-15 (first slice).** `murder/environment.py` (pure fire, water, smoke, light, noise, structure damage, marks, items on tiles) and `murder/envsys.py` (engine side: kitchen grease fires, lightning in storms, burst pipes, failed experiments, generator blast; effects on people; reflex extinguishing; blood, drag and forced-entry marks that become clues; room warnings in prompts; per-turn snapshot `tick["env"]`). Live viewer draws flames, smoke, water, wrecks, marks, items, darkness and noise ripples. Dial `environment`. | Scripted scenarios behave (fire spreads on carpet and wood, water puts fires out, smoke crosses doors, pipes flood, water at the fuse box blacks the house out); a mock week runs with no environment errors. |
| 5 | **Done 2026-10-15 (first slice).** `murder/mind.py`: 16 facets and 12 values derived from each cast sheet, five needs (social, rest, safety, purpose, privacy), thoughts that fade, stress, and sanity as the projection of the character's set point minus stress; engine-made routine turns from needs and relationships (`routine_decision`) with a gate (`needs_model`) that sends anything at stake to the model. Dials: `mind`, `engine_decisions`, `stress_scale`. `tests/week_metrics.py` compares configurations. | Measured on mock weeks (4 seeds x 7 days): the old scalar sanity collapses (median 4-12 from day 5, 90% of survivors under 20); with the mind layer the median stays 66-82 with no one under 20 and breakdowns still occur (about 30 madness events per 4 weeks, against about 145 for the old spiral); model calls per day fall from about 55-70 to about 50 (decisions: about 25% decided by the engine on mock weeks, more on quiet days). |
| 6 | **Done 2026-10-15 (first slice).** `murder/crime.py`: attackers follow a target who slipped away and strike on arrival (the swap-and-miss problem); a spree waives the trial only for the spree killer's own victims, so killing a "frenzied" person who never killed is an ordinary murder with an ordinary trial; interrogation picks the approach (friendship, pressure, reason) that suits the facets and values of both people; questioning a witness brings out what they saw near the scene (from the chronicle, never naming a culprit); the trial prompt gets a digest of who the cast saw near the scene and the killer is told what was seen of them. Dial `crime_pipeline`. | A scripted Cail/Vixen duel (target in the next room, the frenzied one with no kills) ends in a recorded killing and a trial that closes the case; interrogation and digest are covered by tests. |
| 7 | **Done 2026-10-15 (first slice).** `murder/scengen.py`: seeded scenarios composed from weighted parts (premise, one twist, house rules, scheduled blackout/fire/flood/storm that really happen on their day, gear, a shorter first deadline, optional secrets; never relationships) under a difficulty budget; preview and apply in the live start dialog and at `/api/scenario/generate`. Map editor in the grid view (paint floors and walls, place and remove furniture, undo, validate, save, reset) backed by `gridmap.validate_edit`; the engine uses the saved map on the next day. | Generation is deterministic and never overspends its budget; scheduled events fire once on their day; invalid edits (a walled-up door, a lost staircase, furniture in a wall, a resized room, rooms cut off) are refused. |

Rough effort (in sessions of the kind used so far): phase 0: 1-2, phase 1: 2-3, phase 2: 3-4, phase 3: 3-4, phase 4: 3-4, phase 5: 4-6, phase 6: 3-4, phase 7: 2-3. Total roughly 20-30 sessions; phases 0-3 already give a playable, much more coherent game.

---

## 8a. Where things stand (2026-10-15)

Update: the separate live page was merged into the main viewer (`static/tilemap.js` is a map mode of `index.html`; playback, start dialog, trials and panels are the original ones). References below to `grid.html`, `live.js` and a 12-minute game day describe the earlier separate page; the day length now follows the original playback pacing.

Update (round four): single-plane map with 4x4 rooms and portals for stairs (`gridmap.LAYOUT`), eight bedrooms, absolute-time knock-outs, sealed crime scenes with a wellness check, ambiguous labels and red herrings, more murder motives, spree from three or more plots, segment title cards. Smoke suite: 760 checks.

Update (round two): fire damage per 5-minute step with fleeing (`envsys.env_advance`, `env_step_effects`, `fire_flee`); `murder/scale.py` holds every tile-size-dependent constant; free time at furniture with intentions and chats (`freetime.py`: `chat_options`, `_start_chat`, `free_chat_groups`; conversation groups can be keyed `room#n`); viewer plays chats in the timeline (`playChat`) with a pause setting. Not done yet: the model-as-brain split (memory retrieval, plan calls, conversation-on-meet written by the model with retrieved memory), which is to be tested aside. Smoke suite: 703 checks.

Update (free time): the day is now turns plus free-time blocks (`murder/freetime.py`): one model decision per block, then 15-minute slices decided by needs and nature with real durations, plot windows and snap checks per slice, the Director's quiet-corner opportunities, modesty, and a viewer that plays blocks over real time (Pace box, Who's where roster). This is the first step toward continuous play: the decisions are still per block, but the world inside a block is minute-resolved. Smoke suite: 681 checks. Not yet run with the real model.

All eight phases exist as a first slice and share one smoke suite (650 checks at the time). Honest limits:
* Nothing from phases 2-7 has been run with the real model yet; the numbers in the roadmap table come from mock weeks. The first real week will show what to tune (dials: perception, environment, mind, engine decisions, stress strength, crime pipeline).
* The engine still decides every two game hours and the world is played out between decisions. Continuous per-tick decisions (utility scoring each minute, per-tick attack resolution, conversations as proximity-triggered scenes) are the next big step, together with NeoVi and TereVi moving on the map.
* The editor changes tiles and furniture only; rooms and connections stay those of the game data. Weak-wall breaching was deferred by decision.

## 9. Technical choices

* **Language:** keep Python for the sim (fast enough, reuses 14,000 lines). Use numpy for fields if profiling asks for it.
* **Server:** the stdlib HTTP server stays for static files and commands; add Server-Sent Events (or a small WebSocket library) for state diffs so the viewer updates smoothly. The sim thread owns the world; the HTTP thread only enqueues commands.
* **State and saves:** JSON snapshots plus the event log; autosave every game hour; checkpoint on every pause. The fork starts a fresh world (old saves are not migrated).
* **Determinism:** one seeded RNG per subsystem; commands and model outputs recorded, so any run can be replayed and bugs reproduced.
* **Tests:** keep the smoke harness (mock backend, temp `MC_DATA_DIR`), add property tests (no remote speech, opportunities consistent with line of sight, round-trip of the map), and a headless week simulator with metrics (attacks, trials, faints, calls, sanity distribution).
* **LLM:** same CLI backend (Claude plan, no API credits). Queue with priorities (trial and plot design first, scenes next, flavour last), a call cap per game hour, a template fallback.

---

## 10. Risks and open questions

| Risk | Mitigation |
|---|---|
| Real-time and model latency (seconds per call) makes dialogue feel slow. | Asynchronous scenes with "..." markers; agents continue tasks; prefetch likely scenes; slower default speed. |
| Emergent behaviour from scoring may be dull or erratic. | Headless week metrics, tuning panel, per-agent facet editing, model tie-breaks for high-stakes choices. |
| Scope: a DF-style world is a very large project. | Phased roadmap; phases 0-3 deliver value alone; keep the original app as the fallback. |
| Pause fatigue. | Class-based pause settings, "mute this kind", summary toasts. |
| Hidden connections that are far apart on the schematic. | Corridor tiles or portals (5.2.5). |
| Python performance with many agents. | Measured headroom is large; sparse fields; hierarchical pathfinding. |

Decisions (answered 2026-10-15):
1. **Look:** light tileset (textured flat tiles with drawn objects), with the characters shown as their portrait tokens walking around the map.
2. **Speed:** default one game day = 12 real minutes at x1; adjustable at runtime (speed control plus a settings value for the base rate). Whether the sim runs with the tab hidden is a setting; default is pause when away.
3. **Control:** GM/Director tools only. No direct control of a character.
4. **Pauses:** every event class is a setting (pause with dialog, toast only, log only), per kind, with sensible defaults (section 6) and a Tuning-panel group "Pauses".
5. **Destruction:** weak-wall breaching is deferred (not in v1). v1 keeps doors, windows, furniture, fire and water.
6. **Old edition:** not frozen. `app` stays maintained in parallel; because the live edition can pause, the two editions never need to be run at the same time.

---

## 11. Appendix: current data inventory

* Rooms by zone: roof 2, second 6, first 9, ground 7, basement 5, grounds 8 (37 total).
* Connection kinds: door 24, outside 6, secret 5, stairs 4, path 2, window 1 (42 total).
* Items: 252 types, 54 unlimited common supplies, plus crafted special items.
* Python modules: 43 in `murder/`, about 14,700 lines; smoke suite 529 checks.
* Cast: 8 characters (two hosts: TereVi, NeoVi), with personas, speech styles, candor, secrets.

### Proposed pause class table (summary)
Critical: death, body found, case, trial, execution, deadline, reveal, spree, endgame, newcomer, game over. Important: plot strike, fire, flood, blackout, breakdown, knockout, imprisonment, punishment, escape result, new rule. Notable: alliance, betrayal, hook, quarrel, treatment. Background: movement, meals, chatter.
