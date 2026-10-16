# Murder Channel: Live Edition (fork)

Fork of the turn-based app in `../app` (started 2026-10-15): the same cast, engine and AI backends, plus a tile-based live world. Port 8766, its own `state/` and `runs/`.
Start it with `start.bat` and open `http://localhost:8766`: it is the original viewer, now with a **Tile map** mode (the default; the selector next to the speed box switches back to the old Schematic). Press **Start a day** as usual. Game design: `docs/GAME_DESIGN.md` (what the game is and how it works today); original proposal: `docs/DESIGN.md` (all eight phases are built as a first slice; its section 5.2.x lists what each does and does not do yet).

What is new in this fork
* **Chronicle** (`murder/chronicle.py`): a typed, persistent log of everything that happens, with a Chronicle tab and `/api/chronicle`.
* **Tile map** (`murder/gridmap.py`, `static/tilemap.js`): the house and grounds as tiles on five levels, hidden entrances in the GM view, furniture, cameras, and a map editor (Layers > Edit map: paint floors and walls, place furniture; validated and saved). The scenario editor has a "Generate a season" row.
* **Live play** (`murder/gridnav.py`, `murder/livetimeline.py`, `static/tilemap.js`): each engine turn is played out as portrait tokens walking real routes, paced by the original viewer's playback (speed box, pause, fast-forward), with pause dialogs for important events (Pause settings button; per-class and per-kind settings).
* **World systems**: sight, hearing, light and cameras (`perception.py`); fire, water, smoke, breakage, marks and items on tiles (`environment.py`, `envsys.py`); needs, facets, thoughts and stress with engine-made routine turns (`mind.py`); pursuit, witnesses and facet-driven interrogation (`crime.py`); procedural scenarios with scheduled events (`scengen.py`).
* **Tuning dials** (World group in the Tuning panel): Sight and hearing, Fire/water/smoke/breakage, Needs/thoughts/stress, Engine-made routine turns, Stress strength, Pursuit/witnesses/interrogation. Each switches its layer off at 0.

* **Free time** (`murder/freetime.py`, dial `free_time`): the day alternates turns (08:00 morning, 12:00 midday, 18:00 evening) with free-time blocks (10:00, 14:00, 16:00, 20:00). In a block the model still makes one decision (the start of the block); then it is played out in 15-minute slices where everybody eats, drinks, uses the bathroom, washes, plays, swims, reads, makes music or art, strolls, naps, tinkers (crafts) or looks around, walking there and spending real time on it (a drink 15 minutes, a meal 30, a game 45, an experiment 90). The last half hour is the gathering and the conversation. The viewer plays a block over real time (**Pace** box: 12 minutes per day by default), things happen at their minute, and the **Who's where** panel (default on in Schematic mode) lists each person's room, activity and last words.
* **Plots in real time**: a stalking or striking plotter follows the target room to room and strikes the moment they are alone, in a blind spot, in the dark or asleep; each missed chance makes them less patient. After a long wait the Director may steer the target somewhere quiet (dial `director_nudge`: an opportunity, never the kill itself).
* **Snapping** (dial `snap_rate`): someone with almost no sanity left, or pushed past their limit beside someone they hate, may attack with no plan; a kill is recorded as unplanned in the case.
* **Embarrassment** (dial `modesty`): modesty comes from a person's nature; being seen in their underwear costs the modest sanity and makes them cover up.
* **Experiments** now succeed more often and a success lifts health and sanity; a failure costs at most a bruise. Free-time slices, the take-before-walking fix and the spy fix remove the GM errors seen in the last session ("could not take ...", "cannot watch from here").

* **Round two of the fork** (fire, scale, furniture, purpose): fire, heat and smoke now hurt people every five minutes where they actually stand; people wake, run for a safe room and the unlucky (sleepers, the unconscious, the badly hurt) can die (dial `fire_lethality`, 1.0 by default: awake people usually get out, sleepers often do not). The map is tighter (`murder/scale.py`: `MAP_SCALE` 0.8, grounds a little smaller still; sound, sight, walking speed and the big-room threshold all follow it; regenerate with `python -m murder.gridmap`), with about 25% more furniture in 40% less floor and new things to use (armchairs, a chess table, a dartboard, a fireplace, a jukebox, a fridge, a hammock, a firepit, mirrors). Free time is done at pieces of furniture (cook at the stove, relax on a sofa, play chess, listen to the radio, tend the plants...) with capacities, and driven by intentions: what they wanted from their last decision, who they want a word with, hostility, loose ends (hooks), looking for a weapon, rooms they have not been in today, work on a way out, plus their needs and nature; nobody repeats the same activity three times running. Conversations start where two people meet (a sofa, a bench, a corner), at their own minute, instead of at the middle of the room at the end of the block, and the viewer plays them there with the clock standing still; **Pause settings > Conversations in free time** can pause at every conversation, only when it matters (a plot, a feud; the default) or never. Badly hurt, loaded-down and dragging people walk more slowly (`move_factor`), in the engine and on the map.

* **The brain** (`murder/brain.py`, dial `brain`, off by default): the engine is the body, the chat models are the mind. Characters keep a real memory (timestamped, scored, about people; walking about is not kept; trimmed nightly), and a prompt gets the most relevant memories (recent, important, about the people involved) instead of the last few lines. In a decision the model also writes up to three intentions (talk, go, work, search, avoid, wait); the free-time engine carries them out, ticks them off and only asks again when the plan is used up (4 hours), stale (6) or something big happens, so routine blocks stop costing a call. Conversations get what each person remembers about the other and the reason from their plan; the diary and arc become memories at night. In GM view the cast card shows the plan and what is on their mind. First real run (one day, brain on): 60 calls and $2.07 against 68 / $2.35 and 82 / $3.18 for earlier real days; scenes carried secrets and promises between each other across the day.

* **Round four** (the saved game's problems): a knock-out, a pair of handcuffs or a storm is now measured in absolute game time (it used to be a per-day tick counter, so a tasing late in the evening kept someone out for most of the next day); the unconscious are no longer marched to the reveal, the introductions, the vigil or to bed; when a body is announced NeoVi unbolts the scene with her master key and TereVi's tape stops anyone locking it again until the trial, and somebody who misses breakfast, lunch or supper is checked on (a friend knocks, NeoVi opens a locked door), so a body is found within hours instead of after a day. Trials are harder (dial `clue_clarity`): a garment's label may be readable, only an initial, or cut out; TereVi's free clue never names the killer outright; and other people's quarrels, hatreds and threats with the victim become true red herrings. Everyone has a bedroom of their own (eight: violet, orange, grey and white were added; an older save with roommates is fixed when the day starts). Murder motives now include fear (somebody hurt you), betrayal, humiliation, envy and a single prize on top of hatred, jealousy, blackmail, exposure, silencing, revenge and the rest; a plot against somebody who is plotting against you is ten times less likely; there is no cap on how many plots are going at once, but three or more can tip the house into a killing spree. A title card and a feed line mark each part of the day (free time, the gatherings, night; switchable in the pause settings).
* **The map is one section**: no floors to switch between. Every room is 4x4 tiles (5x5 counting a shared wall) in a small blueprint (upper floors, first floor, ground floor and cellars as blocks on one plane; the stairs are U/D tile pairs that carry you to the other block; the secret passages are hidden tiles); the island is 74x67 tiles. Everything that depends on tile size follows `murder/scale.py` (`MAP_SCALE` 0.35): a whisper carries 1.5 tiles, normal speech 2.8, a shout 6; sight is 6 tiles in light and 2 in the dark; walls cost sound in the same scaled tiles. People walk 4 tiles a minute (12 when hurrying) and a stair takes a moment.

Phone and remote use: run `start_remote.bat` (same as `python server.py --host`). It listens on your network and asks for a password on every device except the PC itself; it prints the addresses and a password made up for that run (set your own with `--password` or the `MC_PASSWORD` variable). Use it only on your own Wi-Fi or over a private network such as Tailscale (install it on the PC and the phone, then open `http://<the PC's Tailscale address>:8766`); never forward the port on your router. The PC must stay on, because the game and the Claude CLI run there. The map supports touch (drag to pan, pinch to zoom, tap to select) and the page has a phone layout.

Checks: `python tests/smoke.py` (about 760 checks, mock backend, never touches your saves; a check marked KNOWN is a failure that is expected until a later rebuild phase fixes it), `python tests/baseline.py --write` (mock weeks measured against `docs/BASELINE.md`: model calls per day, chats, deaths, verdicts, sanity), `python tests/week_metrics.py` (mock weeks: sanity and calls per day), `python tests/real_body.py` / `real_day.py` / `real_smoke.py` (real AI, a few cents to a few dollars of plan usage).

---


# Murder Channel: island viewer

A local app that simulates one in-game day at a time and shows the cast moving through the house, talking, and handling items.

## Run it

Double-click `start.bat` (or run `python server.py` in this folder). It opens http://localhost:8765.

Requirements: Python 3.10+, the `claude` command (Claude Code) logged in to your Pro plan, and `pip install anthropic pillow` (the SDK is only needed for the optional API backend).

## Using it

1. Click **Start a day**.
2. Pick **Play live** (simulates the next day while you watch) or **Replay** (any recorded day).
3. Pick a backend and a pace, then **Start**.

While a day is running:
- **Fast-forward day** skips the rest of the day. In live mode the engine stops waiting for you and finishes the day at full speed.
- **Pause**, **speed** (0.5x to 8x) and the turn slider control playback. Dragging the slider rewinds the view.
- **GM view** shows secret passages, hidden items, and each character's private thought. The map click panels (character, room) show inventory, health, sanity and relationships.
- **Stop** abandons a live day; nothing from it is saved.

A live day is only saved once it finishes. Live generation stays one turn ahead of what you are watching, so closing the tab pauses the spending.

## Backends

| Backend | Cost | Notes |
|---|---|---|
| Claude subscription (CLI) | Your plan's usage allowance | Runs `claude -p` headless. Haiku 5.5 for characters, Sonnet 5.5 for TereVi's broadcasts. The app removes `ANTHROPIC_API_KEY` from these calls so they never bill the API. |
| Anthropic API | API credits | Same models, direct calls. |
| Mock | Free | Scripted wandering, for testing the viewer. |

A 2-hour-pace day is about 90 short calls (8 characters x 7 turns, plus conversations, diaries and two broadcasts). The 1-hour pace roughly doubles that. If your plan's limit is hit mid-day the run stops and that unfinished day is not saved.

## Where things live

- `murder/data_world.py`: rooms, doors, secret passages, items and where they lie.
- `murder/data_cast.py`: character personas, starting stats, relationships, diaries (seeded to the end of Day 2).
- `murder/engine.py`: one day: decisions, movement, conversations, broadcasts, night and diaries.
- `state/current.json`: the world as of the next morning. `runs/day_NN/`: each recorded day (`ticks.jsonl` plays in the viewer).
- Story notes from the chat: `../map.md`, `../cast/`, `../logs/`.

## Daily rules (the roulette)

The start dialog has a **Rule of the day** selector:

- **Roulette (default):** TereVi's model invents a fresh rule each day from the current drama (who is stressed, recent events, how close the deadline is), avoiding recent rules. You can type an optional theme or constraint, for example "something about silence".
- **My own rule:** type any rule in plain words ("Nobody may say the word babe today").
- **None.**
- **Presets**, checked directly by the game code with no AI judge: Follow the Leader (the leader moves first and everyone is told where), Buddy System, Never Alone, Ground Floor Only, Mandatory Mealtimes, Weapons Ban.

TereVi announces the rule in the morning broadcast, the viewer plays a roulette spin, and the header shows a gold rule chip. Everyone's prompts (both what they do and what they say) include the rule, so they obey, or bend and defy it knowingly.

**Enforcement.** Prompt-based rules (roulette and your own) have no code check. After each turn a referee model reads a log of where everyone was, what they carried, what they did and what they said, and flags only clear violations with a short reason (about 7 extra short calls per day). Presets are checked in code. NeoVi walks to each violator and tases them (-12 health and -6 sanity, harsher on the 2nd and 3rd strike, never below 5 health) or drags them to the Cold Store. More presets can be added in `murder/rules.py`. The old free-text field is now an announce-only "extra announcement or motive".

## Tone and relationships

Characters talk like people, not villains: most exchanges are ordinary, curious, funny or warm, and meanness needs a cause. The tone toward each person in a conversation comes from three things, written into each character's prompt as a per-person hint:

- the **relationship points** (-10 to +10: hated, hostile, cold, wary, neutral, friendly, fond, close, devoted),
- the speaker's **sanity** (frayed minds snap more, even at friends; calm ones are generous),
- the speaker's **health** (hurt people are short-tempered or clingy).

Each character's `candor` text in `murder/data_cast.py` describes how they react under stress or provocation, not their default. Swearing is allowed when it fits; slurs and hate speech about protected groups are excluded.

**Relationships move every time people interact.** Conversations report a shift of -3 to +3 for each pair that interacted (a kind word +1, a shared laugh +1 or +2, real support +2 or +3, a jab -1, an insult -2, cruelty -3). If the model leaves a pair out, listeners still drift by one point (warmer, or colder if the exchange hurt).

## Health and sanity

Sanity is meant to fall and to be hard to get back:

- **Baseline drain:** every turn costs each person 1 sanity (2 if their health is under 40). Hurtful interactions cost more: every negative relationship shift takes that many points from *both* people, and scenes can report extra losses.
- **The deadline wears everyone down:** dread grows as it approaches (4 days out -1 each morning, then -2, -3, -4, -5 on deadline day, plus -1 per turn on deadline day and the evening before). Blackouts cost 2.
- **No automatic recovery:** sleep mends health (+3) but not sanity, ordinary friendly chat restores nothing, and `rest` only helps health.
- **Special moments restore sanity**, capped at 8 per person per day: a heartfelt comfort or confession (+3), a romantic spark (+3), helpless laughter (+3), real teamwork (+3), a gift (+2), a shared meal (+4), a movie night (+4), a party (+5), a game night (+3), a successful prank (+2 for the pranksters). The scene writer flags these in `effects.special`; occasions grant them automatically. Consumable items (sweets, champagne, a stuffed rabbit...) still give their small boosts.
- Low sanity and health change how people talk and act, and tasers, detention, fights, experiments gone wrong and murders hit the stats directly.

Set `MC_DATA_DIR` to a scratch folder to run the server against a copy of your saves when testing.

## The drama layer

**Action lines.** Scenes mix speech with short action lines (the viewer shows them in italics, with dashed bubbles). They are physical things people do to each other or the surroundings: a shove, a hug, jamming a door, turning up the music. Actions can have consequences: health or sanity changes, items changing hands, and **forced moves** (a shove, a drag or a lure can put someone into an adjacent room, for example into a forbidden one).

**Survival, curiosity, experiments.** The shared goal is to survive, or to help others survive depending on personality and bonds. Murder is a last resort in the prompts; people are pushed to probe the radio, boats, cameras and rules, bargain with TereVi, win NeoVi over and look for loopholes. The `experiment` action sends an idea to a judge (a model that knows the GM's island truths: chained boats, the firewalled radio, camera wiring, the lighthouse lamp, NeoVi's master key, the secret passages). Outcomes are partial, can hurt, may teach the experimenter a fact, and add to a hidden **escape progress** meter (shown in GM view, with clues). Crossing 30, 60, 90 and 100 makes TereVi react. Nobody actually escapes automatically; at 100 it is up to you how the story answers.

**Breaking rules.** Characters are told punishment is real but uncertain. Cameras cover only the public rooms (blind spots: bedrooms, bathroom, basement and remote rooms, greenhouse, observatory, water tower). A violation in a blind spot is only caught about a third of the time unless NeoVi is in the room (attendance rules like the leader, buddy and mealtime rules are always visible), and during a TereVi blackout nothing is caught. NeoVi may also look away from someone she likes. People can lure, dare or shove rivals into breaking the rule.

**TereVi meddles.** Occasionally (selectable: quiet, occasional, often; more often as the deadline nears) she makes one move from the monitors: **whisper** a rumour or secret to one person, **announce** a house-wide game or bounty, **dare** someone, trigger a **blackout** of cameras and lights for a turn, or send a **gift** (champagne, spirits, sweets, a board game, candles, rope...). Her announcements stay in people's prompts for the day. Anyone can address her by adding `terevi` to who they want to talk to; she then joins that room's scene through the monitor. She knows every secret and uses them.

**NeoVi has an agenda.** She is a slave of the show who wants to help but is terrified. She holds her own feelings toward each participant, a fear level, a pocketful of small helpful items (first-aid kit, bandages, sweets; the master key only for someone she trusts at +8 or more), and a private scheme she revises every night. She helps in small, deniable ways: looking away from violations, hints, a spare bandage. She can never kill or touch a trial. During an investigation she stays neutral: if interrogated she shares only a little, obscurely (for example "silver does not walk"), based on a few facts she really saw. Her scheme and feelings are visible in GM view.

**Occasions.** Anyone can host a meal, movie night, game night, beach or pool party, concert, prank or ritual for the next turn (the `host` field). The invitation reaches the cast (a secret prank only reaches the pranksters), people choose whether to come, and if the host and at least one guest are at the venue a special scene plays with a bonus to sanity and a point of warmth between host and guests. Occasions pull everyone around the island, which is also when rules get bent and murders get easier.

**Bonds.** When two people are both strongly warm (+5 or more) a **romance** can form; when both are strongly hostile (-4 or less) a **feud**. Bonds show on the cast panel and in prompts, and fade if the feelings cool.

**Confessional booth.** Now and then (selectable on or off) a character speaks candidly to the camera about what they really feel, fear or plan. It plays as a sepia card over the map and is collected in the **Booth** tab. It costs about one extra call per turn when it fires.

**Dread.** As the deadline nears the map darkens at the edges and pulses red, the header shows the dread level, TereVi's broadcasts get more ominous and sanity drains faster.

Extra calls per game day: the referee for prompt rules (about 7), TereVi's meddling (about 2), experiments (a few), the confessional booth (a few) and NeoVi's nightly plan (1). Expect roughly 100 to 110 short calls in total at the 2-hour pace.

## Surprise, madness and chaos

The point of this layer is that nobody is a fixed character: people change, break, scheme and sometimes do something nobody saw coming. You choose the **Chaos level** in the start dialog (calm, normal, wild); it scales surprises, impulses, island events and how often minds snap.

**Secret drives.** Every participant holds a hidden drive: Survivor, Protector, Saboteur, Schemer, Avenger, Thrill-seeker, Romantic, Seeker, Nihilist or Martyr. Not all of them care about surviving. A drive tells the character what they actually want and outweighs generic caution, and they are nudged to act against type now and then (about one turn in five at normal chaos) if the drive, their sanity, a grudge or an opportunity justifies it. Your existing cast got drives matching their personalities (for instance Shintaro starts as a Saboteur and Chloe as a Romantic). **Every night each character reflects** (this replaces the plain diary, same number of calls) and may change drive and target, with a one-sentence arc about how they are changing. Drives and arcs are visible in GM view.

**The madness ladder.** Sanity maps to steady (55+), frayed (35-54), unraveling (20-34), breaking down (10-19) and snapped (under 10). Crossing into unraveling or worse is announced in the feed. At unraveling and below, characters get **dark impulses** (hurt someone, lash out at their most disliked person, smash something, blurt out a secret, cut the lights, lock themselves away). The prompt lets them resist or give in; if they do not act on it themselves it can boil over anyway (an outburst scene). Nihilists, avengers and saboteurs are more prone. A character who ends the night snapped (under 10) turns into an Avenger of their worst enemy or a Nihilist about half the time.

**Violence short of murder.** With murders enabled characters can also `assault` (a real beating, 8-25 damage depending on the weapon, health never below 5) or `sabotage` (cut the lights for a turn, ruin an announced occasion, steal an item). Attacking, killing, exposing a secret or voting against a bonded partner triggers a **betrayal**: the bond shatters, the victim's feelings of the betrayer crash and they lose sanity.

**Secrets and leaks.** Characters start knowing only their own secret. People can learn others' secrets (overheard, whispered by TereVi, leaked) and then use, trade or leak them: a leak in conversation (`effects.reveals`) only works if the leaker actually knows the secret. The exposed person loses sanity and trust. TereVi's new **motive video** threatens one person with exposure at a set time unless they meet a demand; when it comes due she judges whether they complied and, if not, broadcasts the secret to everyone.

**Pacts.** Two people who both trust each other (+3) can swear a pact; a betrayal dissolves it.

**Island events.** At random (more often at higher chaos) the island itself intervenes: a **storm** (outdoors hurts, cameras glitch), a **kitchen fire** (people present get hurt; two or more put it out together for a sanity boost, otherwise the kitchen burns), a **power cut** (dark, cameras dead), **fog and whispers** (sanity chip), a **stray cat** (whoever finds it feels warmth; NeoVi softens) and a **mystery package** in the foyer (rope, champagne, a flare gun or a board game). The viewer shows weather, a fire glow, a cat and darkness.

**Making it watchable.**
- **Relationship web** (Web tab): live graph of who loves or hates whom, with romance, feud and pact markers and sanity rings.
- **Mood auras** on the map tokens as people fray, and a **tension meter** in the header.
- **Camera effects:** screen shake on violence and outbursts, red flashes on betrayals and leaks, hearts for tender moments, confetti for parties, weather overlays.
- **Episode recap** at the end of each day: TereVi's title, a gleeful recap and awards (MVP, Villain of the Day, Heartthrob, Biggest Betrayal...), shown as a card and saved in the feed.
- **Optional sound** (header toggle, off by default): synthesized stings for violence, betrayals, leaks, parties and executions, plus a low drone that swells with dread.

Extra calls: none per turn for the new mechanics (impulses, island events and secrets are engine rules and prompts); the recap adds 1 per day and TereVi's threats add one only when a motive comes due.

## The story layer (deaths, plots, the Reckoning, Day 1 and the way out)

**Day 1 is introductions; the truth comes out that evening.** A new game started at Day 1 plays a gentler day: the cast believes it is a thriller-themed reality show. TereVi welcomes them, the housemaid NeoVi is introduced, everyone mingles and meets, there is a formal **presentations scene** in the Dining Hall at 10:00, and at 20:00 TereVi **reveals the true purpose**: the show is real, nobody leaves, the audience thinks it is staged, and if nobody dies by the end of Day 7 everyone dies. No murders, rules, experiments or island events happen before the reveal, and sanity takes a big hit when it lands. (Start a new game from the Start dialog and choose Day 1; choosing Day 3 continues the older chat story, where the cast already knows.)

**The Reckoning and the Last Call.** If nobody has died by the deadline, everyone dies and the season ends (a mass execution scene and an end card). Two hours before that, on deadline day at 20:00, TereVi calls a **Last Call**: everyone gathers, the arithmetic is spelled out, and the cast can volunteer to die, refuse, nominate someone, draw lots or fall silent. A real volunteer's sacrifice is a death (a friend may stop them); someone who decides to kill strikes while TereVi cuts the lights, so nobody sees who did it. In the final days the prompts also spell out the math ("the escape plan is only X% done, only a death saves everyone"), and desperate or broken characters get the option `end_life`.

**Every kind of death counts, and the killing blow decides who is responsible.** Deaths can be: a **murder** (an `attack`, optionally `staged` to look like an accident or a suicide), **manslaughter** (an assault that goes too far, e.g. against someone already beaten down, by mistake), a **suicide** or sacrifice, or an **accident** (a storm or fire at low health, a failed experiment, a fall on the roof, a drowning). Whoever lands the killing blow is the culprit, even if they were **manipulated, tricked, blackmailed or lured** into it (the conversation effect `incite`; the manipulator is exposed at the trial but is not the one executed) or hit the wrong person. At the trial the cast votes for a person **or for "nobody"** (an accident or suicide): naming the right culprit executes them, naming nobody when nobody was to blame is correct, and accusing an innocent executes the innocent (even for a death nobody caused) while any real culprit walks free.

**Solvable, but not trivial.** Every case is built from layered clues: TereVi's file (cause, place, time), a **camera and door-lock archive** in the Foyer that places most people elsewhere and leaves three or four unaccounted for (the killer among them, never alone), the **history of the weapon or a dropped item** (who handled it, sometimes with a link missing), what neighbours heard and glimpsed, older bruises if the victim was beaten earlier, a flaw in the staging, a note for a real suicide, a **red herring** that points at an innocent, and, if the cast found fewer than three clues, TereVi hands out the best missing ones at the trial. Everything found is put on the table in the debate and the vote.

**Murder plots you can watch.** A character who is seriously planning a killing declares a **plot** (target, stage brooding, preparing, stalking or striking, method, this turn's step, cover story). The plot shows in the feed in red, in a "Scheming" panel in the Cast tab and a pulsing header chip; the plotter gets confessional entries about it; others sometimes notice odd behaviour and remember it. Plots fade if the character stops pursuing them.

**Slip-ups.** The lower someone's sanity and health, the more **error-prone** they are: they can strike the wrong person, hit harder than they meant, leave a dropped item at the scene, muddle their story or vote on a gut feeling. The prompts tell them so.

**Grief and defining memories.** Any death costs every survivor a lot of sanity (more for friends, much more for a lover) and is **remembered from then on**: the dead appear in the characters' prompts, nightly reflections, confessionals and conversations ("The dead you carry"). Characters also keep a list of **defining moments** (betrayals, attacks, lost loved ones, exposed secrets, being talked down from the edge) that colour what they say and do, and TereVi calls back to the season's story threads.

**The way out is concrete: contact the outside world.** The audience believes the show is staged, so the escape needs five things, each tracked as a percentage in the GM view: a **transmitter**, **power**, a **signal position** (the Lighthouse lamp, the Lookout), **proof the audience cannot dismiss** (real names, relatives to phone, coordinates) and a way past **TereVi's jamming** (blind spots, cutting cables, hacking, blackouts, or NeoVi's help if she trusts someone). Experiments advance one step; when all five are complete a team gathers at the Lighthouse and **broadcasts**. If it works the season ends with "the truth gets out"; if TereVi jams it, the equipment is damaged and progress is set back.

**Variation, factions, rumours.** The **personality drift** slider in the Start dialog gives every character a small, believable change at the start of each day (one extra call per day; 0 = off). People spread **rumours** (true or invented) that move opinions; bonds merge into visible **alliances** (Web tab); a **novelty guard** nudges characters who keep repeating the same gestures.

**The Director.** The Director button lets you whisper an unsigned note to someone, spread a rumour, drop an item in a room, make TereVi announce something, push her to escalate or force an island event. It lands on the next turn (or the next day's start if nothing is running); the characters still choose for themselves.

**Newcomers can be developed by the AI.** In the newcomer form tick "Let the AI develop the rest" (or press "Preview what the AI writes"): it fills only the blanks (backstory, secret, motivation, speech, goals, items, hidden drive) and never changes what you typed. You still choose who joins.

**Safety, cost and export.** The Start dialog has **Rewind the last day** (restores the state from before it), **Export the story** (a Markdown file of any day or the whole season, no AI calls) and shows the season's AI-call total. Extra calls: none per turn for deaths and plots; +1 per day for personality drift; the Last Call adds a couple on deadline day.

Mock knobs for testing: `MC_MOCK_PLOT`, `MC_MOCK_SUICIDE`, `MC_MOCK_INCITE`, `MC_MOCK_LASTCALL_VOL`, `MC_MOCK_LASTCALL_KILL`.

## The living island (map, odds, memory, evidence, the new trial and the ways out)

**A map that makes sense.** Rooms connect only through doors, stairs, outside paths, windows and secret passages. Upper floors and the roof can also be linked by things people **build**: a ladder (a found one, or crafted from 2 planks and a rope plus a hammer, tape or wire), a rope line or a plank (the `build` action, with materials from the Generator Shed, Boathouse and so on; built links show as orange lines and can be taken down). Climbing a built link can end in a fall, much more so for the hurt and the panicked. New places: **The Voting Grounds** (down the cliff steps from the Beach, where trials are held) and **TereVi's Core Vault**, a hidden room under the Lighthouse (secret hatch SP-5, shown in GM view until found).

**Actions can fail.** The chance depends on the context, sanity and health, and there is always plain bad luck (and sometimes plain good luck): fumbling an item, a search that finds nothing, a ladder that slips, a blow that misses or lands too hard. Experiments toward a way out are decided by dice first and narrated afterwards: a failure really fails.

**Seeing people come and go, and imperfect memory.** People notice who leaves or enters their room and who passes through; characters who cross paths pass each other. They remember small details if relevant (carrying a weapon or a ladder, looking hurt or wild-eyed, a killer's shaken look). Memories are **imperfect**: when sanity or health is low, or they were distracted (searching, experimenting), a sighting can come out wrong (wrong time, person or place), and nobody tells them. A wrong memory can be **set straight** when someone who remembers it right talks to them. Only events people witnessed, were told, or heard as rumours exist for them.

**TereVi stays vague.** She no longer recounts what people did: her broadcasts and whispers only hint at moods and tensions. Events that only some people see (a betrayal, a leak, lights cut by someone) are remembered only by those present; everyone else just notices the lights went out.

**Investigation: evidence and testimonies.** Each investigator keeps a **case notebook** of the clues they found and the testimonies they gathered. They can `interrogate` someone (target plus the question); statements are recorded as testimonies (a culprit's may be lies) and shown, with the evidence, on the **Case file** panel in the Cast tab.

**The trial at the Voting Grounds.** Everyone gathers at the Voting Grounds for a **limited-time** argument of up to five segments, chosen by how the suspicion is moving:
- **Open debate:** everyone presents evidence and presses alibis and testimonies.
- **The Hot Seat:** when suspicion falls heavily on one person (at least half the room), they stand in the middle and explain themselves while the others attack and defend, only until the matter is made clear (at most two rounds).
- **The Clash:** when two people hold contradicting ideas, they argue one on one while the rest decide who was more convincing, which moves the suspicion.
- **Brainstorm:** when something baffling remains, people float competing theories and the room picks the most plausible, which becomes the working theory.
Then everyone votes. **There is no "nobody" vote**: a death with a culprit always has someone guilty, and a wrong accusation executes an innocent while the culprit walks free.

**Culprits.** A killer never reveals themselves: they deflect, deny, shift the blame, and can **frame** someone with planted evidence (the `frame` field on an attack). A culprit can also be **unaware**: someone struck in a blackout, or beaten so badly they die in the night of an injury nobody knew was fatal. The unaware culprit does not know they killed anyone, works to solve the case, and may **realise** it during the investigation or at the Hot Seat. **A death with no culprit** (an accident, a suicide or a sacrifice) has no investigation and no trial: TereVi just informs everyone, and the deadline is lifted.

**Several ways out, all of which can fail.** The GM view tracks four routes with their steps:
- **Broadcast the truth** (transmitter, power, signal position, proof, beating the jamming); finale at the Lighthouse.
- **Shut TereVi down:** her AI core is hidden in the Core Vault under the Lighthouse (find the hatch, get past the pressure-plate traps and turrets, get the means to destroy or override the core, blind her meanwhile); finale in the vault.
- **Build a raft** (materials, build, provisions, launch): it saves only the 3 who sail on it, the rest stay, and a wreck can drown someone.
- **Threaten to blow up the island** (explosives, plant them, make the threat credible, keep the trigger safe): TereVi may surrender, or call the bluff and the charge goes off.
When every step of a route is complete a team attempts its finale, whose odds depend on the team, their condition, helpers like NeoVi, blackouts and luck. Success can end the season (the truth gets out, TereVi is shut down, the show surrenders, the last raft) or free a few; failure sets the route back and costs the team dearly.

Extra calls: a trial is about 5 segment calls plus the votes and a few broadcasts; everything else adds none per turn.

## Darkness, balance and polish (latest)

**Harder, cooperative murders.** Besides direct attacks, a killer can **rig a trap** (a loosened railing or ladder, a spiked bottle, a wire-and-blade at a doorway) that kills later while they are elsewhere, and may catch the wrong person. Cases are layered so they can be solved, but not by one person alone: the **camera archive** (Foyer) and the **bedroom door-lock log** (the locked Study, so someone must get a key) are separate clues; there can be two red herrings and a planted frame; **lies can be caught** (a testimony that contradicts the archives is flagged for whoever holds both); hostile people refuse or lie when questioned, and low sanity garbles what an investigator wrote down. In real test trials with a trap murder the cast named the right culprit in both an ordinary and a hostile, low-sanity setting (the hostile one split the vote 4-3).

**Brutal tone.** Attacks, discoveries and executions are written grim and visceral, with no jokes or confetti. Body discoveries get a dark full-screen scene (heartbeat, red vignette, grey portrait, slow text); executions type out slowly under a darker tint.

**Sanity balance.** Besides special moments (now scaled by how close the people are and how deep the moment, cap 12 a day): a night beside someone you trust restores sanity, a vigil together after a death helps, NeoVi's tea helps if she likes you, a plain quiet sleep helps a little, and surviving a trial with a friend gives a small relief. (If everyone still sinks, lower the Chaos level or make the day lean.)

**NeoVi's rebellion.** Her resolve grows with kindness shown to her, deaths and unfair punishments, and shows as stages (servile, doubting, secretly helping, defiant, ready to act). At the climax, with an ally she trusts, she either **sacrifices herself** (every feed goes dark and TereVi ends her), **survives** (defies TereVi, hands over the master key and unlocks the house) or **betrays the cast** if things are out of control.

**Collapse and endgame.** If general sanity is very low and relationships are bad, a character can snap into a **killing spree**: deaths during it have no investigation and no trial, bodies lie where they fall, and it is a fight over who stays alive. When **fewer than 4 survive**, TereVi ends the show according to her mood: a **final battle** (dice and wounds; possibly nobody walks away), **crowns** the survivors as winners, or **crowns one on a whim** and executes the rest. With 4 or more, newcomers arrive as usual (you choose them); everyone can also die. **TereVi adapts**: when a route passes 50% or 80%, or after a failed finale, she reinforces it (guards, jamming, a harder vault) and it sets the route back.

**Trial polish.** A live **suspicion tally** and the **working theory** show during the trial, and the most suspected give **closing arguments** before the vote.

**Voices.** The Voices toggle reads dialogue aloud with the browser's own voices, a different one for each character (TereVi low and slow, NeoVi soft). Quality depends on the voices installed on your computer.

**Budget, balance and housekeeping.** Each favoured way out gives characters a secret subplot. The Start dialog has **Lean prompts** and a **daily call cap** (the day turns lean and calm at 75% of the cap; past it characters idle instead of failing). **Saves:** name and load saves, and go back to the start of any earlier day. A real Day 1 on Normal measured 65 calls, about 4.5 minutes and about 535k tokens. `python tests/smoke.py` runs a minute of mock checks without touching your saves.

## Auto-director, recaps, evidence board and stats

- **Auto-director** (header toggle, also set when you start a day; it can be switched on and off while a day runs). When several turns pass with nothing dramatic, it nudges the story: TereVi is told to stir things up with a dare or a tempting bargain, an anonymous (true or false) rumour starts, an unsigned note reaches the most isolated or fragile character, or an island event is triggered. At most twice a day, never during a case, a spree or the evening. It shows in the feed as "Auto-director".
- **Previously on Murder Channel:** when you start a day (live or replay) a recap card shows the previous episode's title, recap and awards, what happened, who was lost, how many are alive and the deadline. Built from the recordings with no AI calls; "Do not show recaps" turns it off.
- **Board tab:** a corkboard for the open case. The victim sits in the middle, the living around the edge; yellow notes are clues, blue are testimonies, red dashed are lies that were caught, with strings to the people each item names, and a numbered legend below.
- **Stats tab:** per character: health and sanity with a sanity trend line, kills, assaults, plots, sabotage, manipulations, betrayals, leaks, rumours, right and wrong votes, times wrongly accused, way-out steps, experiments and builds, plus their closest friend and rival.

## Plans that go wrong, accomplices, and custom scenarios

**Murder plans do not always work.** At the moment of the strike: a protector who loves the victim can throw themselves in the way and stop it (the plot is exposed and the attacker is hurt); a failed attack can be **turned around** by the victim, who kills the attacker (by the killing-blow rule the survivor is the culprit, though a "signs of a struggle" clue shows who attacked first); an unhinged or bitter plotter whose target is gone can **switch targets**; plots fade if the target dies or becomes a close friend; a killer who is not stopped may **kill a second person** in the same room (one case, two victims, one culprit). Traps can also catch the wrong person.

**Accomplices, but never two killers.** A plotter can recruit a trusted friend who dislikes the victim as a **lookout** (witnesses get led away), **alibi** (a false testimony), **cleanup** (weapon and trace clues vanish) or **weapon** supplier; it happens through conversation, and occasionally on its own. **Only one culprit is ever tried**: whoever struck the blow. Accomplices walk free, but TereVi exposes them after the verdict (everyone's feelings toward them sink). A second killer in the same case is not possible (a second attack is blocked, as is a second lethal blow); the only time several people kill is a killing spree, which has no trials.

**Custom scenarios and house rules.** The Start dialog's "Scenario and house rules..." editor lets you set: a **title** and **premise** (everyone lives under it once the show is revealed, and TereVi plays with it); a **secret twist** TereVi announces on a day you choose (it becomes known to all from then on); the **first deadline**; **house rules** (one per line, enforced by NeoVi's referee every day on top of the daily rule); and seeded **relationships** (exes, rivals, siblings, lovers... with the history), extra **secrets** for characters, and **starting items** in rooms. Templates: Old Wounds, The Informant, Blackout Week. The scenario is saved with your game and kept when you start a new one (you are asked).

## NeoVi at the big scenes

NeoVi now attends the trial, the Last Call, the endgame and the Day 1 introductions and reveal: she walks over (you see her cross the map) and stands silent at the edge of the room. She never accuses or votes. **A hint:** if she saw something about the case, she speaks exactly one short, flat, obscure line in the opening debate (clearer about a place or item if she has become braver; cold and unhelpful if she turns betrayer; silent if she saw nothing or has been lost). **An enforcer:** at executions and the Reckoning TereVi makes her take part, and what she does follows her feelings and her arc: dutiful with her eyes on the floor, shaking and whispering "I'm sorry" if she cares about the condemned (which hardens her resolve), openly refusing to touch them if she has become a survivor who liked them, or doing it coldly if she has turned betrayer. The execution scene weaves her part in.

## Sneaking, hiding and hidden things

Everything rests on two numbers: how well someone conceals (calm, healthy and lucky people do it well; panicked or hurt ones badly) and how **sharp** the people around them are (calm, suspicious, undistracted people, in the light). New options for characters:
- **Sneak** (`"sneak": true` on a move): slower, and each observer rolls to notice; if they miss it they at most hear "someone slipping past". Sneaking also helps against NeoVi's punishments and keeps a secret passage from being revealed to onlookers.
- **Hide** (action `hide`) in a room with cover (wardrobes, curtains, the stacks, behind the boiler...). Hidden people are not counted as present, can't be attacked, and overhear what is said around them; they may be caught, found by a careful search, or noticed by luck. Hidden characters are shown faded on the map.
- **Spy** (action `spy` with the adjacent room) from a doorway or window: overhear part of a conversation, and risk being caught listening (feelings drop). Schemers and seekers also do this on their own now and then.
- **Stash** an item (action `stash`, with where) and **retrieve** it later. Anyone who searches the room can find it: sharp searchers often do, and **badly hidden** things (a careless or panicked hider) can be found by plain luck. A found item shows who handled it. A weapon that has been stashed is missing from the scene, so its clue can't be found until the stash is.
- **Hide a body** (action `hide_body`, only for the culprit, before it is found): a body hidden behind cover isn't discovered by people just walking in, but it leaves **drag marks** as a clue, can be found by a sharp search, and TereVi reveals it anyway after about 14 hours. Killers try covering their tracks on their own too.
The GM view shows stashes in the Room tab.

## Concealed carry, frisking and withheld evidence

**Concealed carry.** A character can keep a small item (not a ladder, plank, rope and the like) out of sight on their person (`"conceal": {"item": id, "on": true|false}`, up to three). Anyone who sees them come or go only notices a concealed weapon if they are sharp and the concealment is poor (twitchy people, hurt or panicked, give themselves away). Killers, plotters and the paranoid tuck weapons away on their own; so does anyone carrying a secret item. The GM view marks concealed items on the Cast tab.

**Frisking** (action `frisk`, with the person): innocent people usually agree, people with something hidden often refuse, and a refusal is itself noted as suspicious (during an investigation it goes in everyone's notebook). A search finds concealed items by the searcher's sharpness against the quality of the concealment; a found weapon costs the carrier sanity and everyone's goodwill.

**Withholding.** A character can sit on a clue they found or something they know (`"keep_back": {"what", "why"}`), and the engine also decides this for them: a culprit who finds their own trail, someone shielding a person they love, the paranoid ("I trust nobody with this"), schemers (leverage) and the frightened. A held clue is **off the shared evidence table** (and off the public evidence board) until it comes out; the GM view lists what is being held back and why (Board tab, purple dashed notes). It comes out when:
- someone **presses** them in an interrogation (easier when they like the asker or are shaky; a culprit or a protector resists most),
- the **reason is gone** (the person they protect died or turned on them),
- they **crack** (very low sanity), the **vote is near** (a few hours before the trial), or at the **closing arguments** (the paranoid and the self-serving reveal; self-incriminating secrets stay hidden),
- they choose to come clean (`"disclose": true`),
- or someone else finds the same clue.
A secret that comes out late is flagged on the table ("kept back until pressed"), those present note it as suspicious and trust them less. If an innocent is wrongly executed while someone still sat on a secret, they carry that guilt (sanity loss, a defining moment). All of this ends with the case.

**Less "experiment" every turn.** The prompts now say experimenting is one of many things to do; after two experiments in the last three turns the character gets a "VARIETY" nudge with context-aware alternatives (sit with a shaky friend, mourn, rest, investigate, listen in); after three in a row they are often forced to take a break instead.

## Pacing, rule enforcement, long plots and the night (latest round)

**Season length.** The Start dialog has a "Season length" setting: a deadline every 4, 5, 7 (default) or 10 days. It is stored in the save (`week_len`), applies from the current day, and a death moves the next deadline one full period away. A custom scenario's first deadline still wins.

**Escape attempts are back.** The earlier "stop experimenting" tuning went too far (a whole week with one experiment). Now each day has a quota (about 1 by 10:00-12:00, 2 by 14:00, 3 by 18:00): the engine picks someone with an escape-minded drive, tells them which step of the plan is next, and if their turn drifted into something idle it becomes the attempt. Idle ruts (the same stay/search/take three turns running) still get a nudge.

**Hostility starts sooner.** Sanity pressure and small frictions (a snub, an accusation, a repeated confidence) rise with the day count and the closeness of the deadline. Frictions are specific events between two people in a room, they sour affinity and are remembered, so tea-party weeks turn into grudges and feuds. No AI call is spent on them.

**Murder plans are campaigns.** A plot (declared by a character, or started by the engine from hatred, an avenger drive, an urge or the deadline) now runs brooding -> preparing -> stalking -> striking across turns and days, with a timeline the plotter sees (`YOUR PLAN`). The engine owns the checklist: it sends the plotter to fetch a weapon, follow and watch the target, and strike when a window opens (alone, a camera blind spot, a blackout, a sleeping victim, or the deadline). Plots persist through the night, can be abandoned by calm and fondness, and a failed attack ends them. A plot no longer dies because the model forgot to mention it.

**The night turn.** On ordinary days a character can choose to stay up after the last turn ("night": true), and plotters, investigators and the sleepless are nudged to. It costs about 8 health and their sleep; it is a normal turn at 23:00 with only the owls awake. Everyone else is asleep in their room: not counted as present, sees and hears nothing, cannot defend themselves (a sleeper is killed with 92%+ certainty) and does not discover a body until morning. Owls do not heal at bedtime. No night turn on the deadline day.

**Reaction pass and conflicts.** Decisions are still made in parallel, but they are applied by initiative (calm, healthy, quick people first) rather than at random, and a person whose action was pre-empted (the item was gone, the person they went to talk to left) is told so. When something dramatic happens in a room during a turn (an attack, an assault, a breakdown, a body, a punishment), up to four people there get a quick reaction: freeze, flee, help, comfort, confront, hide or shout. One small call each, only on those turns.

**Rule enforcement.** Rules are classified when set up and judged in the way that can work: a **zone** rule ("only outdoors") is checked by the engine from where everyone is; an **obligation** ("slap someone before 20:00") is tracked by the referee all day and everyone who has not done it by the deadline is punished; a **state** rule ("be in your underwear") puts the burden of proof on the characters (silence counts against them, and they are told to say how they comply); a **behaviour** rule is read from the record with the last turns' verdicts as memory. The turn a rule is announced is a grace turn. The viewer posts "RULE CHECK: ..." or "NO RULE TODAY: <why>" every morning, so a rule that cannot be enforced no longer fails silently.

**Dialogue.** The conversation prompts now ask for plain, natural speech: short lines about concrete things, answering what the last speaker said, no stacked metaphors, quips, hashtags, pet names or non-sequiturs.

## Sanity and the aftermath of a death

**Why it stalled.** In the finished 7-day season the cast's average sanity fell from 78 to 45 (about -6 per person per day): -1 every turn from the baseline drain (-7/day), -3 a day of deadline dread, plus incidents, against only about +5 to +8 a day back, because sleep gave back almost nothing and restorative moments are capped. A trial costs the survivors 25 to 60 sanity in a day or two (body, announcement, verdict, mourning, execution), so recovery took 4+ days, right into the next deadline.

**What changed.**
- **Calm window.** Once a case is closed (verdict carried out, or a no-culprit death announced), the rest of that day and the whole next day are calm: no baseline drain, no deadline dread, no pressure drain, no new frictions or plots. Then two days of half-strength drain while things settle.
- **The remembrance.** The next morning at 10:00 the survivors hold a real scene together in the Lounge (NeoVi at the door, no TereVi), and everyone gets a guaranteed +6 (+3 if they loved the dead) and +1 toward each other.
- **Reliable recovery.** In the calm window anyone below 70 near someone they trust (+2 or more) leans on them every turn (up to +10 a day), restorative moments count 1.5x with a doubled daily limit, and nights give +4.
- **Always on.** Sleep now restores +2 (it was almost nothing), the daily limit for restorative moments is 14 (was 12), a newcomer's arrival gives everyone a small lift, and the baseline drain is self-limiting ("numbness"): the lower someone is, the less each quiet turn wears them down (at 35-59 it hits 70% of turns, at 15-34 only 40%, below 15 only 20%).
- **Result in the simulator:** a cast at 42 with a death falls to 38 that day, climbs to 56 the next day and is still 49 two days on; the same cast with no aftermath falls to 26.

## Locks, forced doors, barricades and where people sleep

- **Shuffled rooms.** Every new game pairs the starting cast two to a bedroom at random (rooms and pairings). An existing save keeps its pairings; newcomers take the emptiest bedroom.
- **Every indoor room has a lock.** `lock` bolts the room you are in (`"door"`: its room id) or locks an adjacent room you hold a key for; `unlock` undoes it. The people who sleep in a room, whoever locked it, and anyone with the master key or skeleton keys can open it; everyone else is kept out. Leaving a room draws your bolt back (a key-holder leaves it locked behind them). Outdoor places, the roof, the Voting Grounds and the Core Vault have no lock.
- **Picking and breaking.** `pick` (quiet, needs skeleton keys, bolt cutters, wire, a hair tie or a pen; better tools pick more often) opens a lock without a trace; `break` forces it (loud, tiring, a hammer, crowbar or sledgehammer helps a lot) and leaves the door **broken** (it cannot be locked again) until **NeoVi mends every broken door at the turn of the week**.
- **Barricades.** Any ordinary door (or window) can be blocked from your side with `barricade`: heavy furniture (always available indoors), planks, a barrel, a ladder, or a body (which leaves a drag clue and costs sanity). Whoever is on the other side must `break` it down (a few attempts; each success wears it down). Walking out through your own barricade clears it.
- **Noise.** A break-in is loud: it wakes sleepers in the room (usually) and next door (about half the time), who react; picking is nearly silent.
- **Sleeping anywhere.** `"sleep_in": <room id>` from 16:00 on; the default is your own room. Your own room gives a sanity and health bonus; another bedroom or an indoor room is neutral; the open air or a cellar costs health and sanity. You have to be able to get in (a locked door sends you home). Lovers and the frightened sometimes end up in a friend's room on their own.
- **Fear locks doors.** At night people bolt their rooms more the more afraid they are (a body, a spree, plots, low sanity), and the very frightened pile furniture in front of the door. Plotters with a lock between them and their target pick it (if they carry a tool) or break it down.
- **Viewer.** Map labels show a lock, a barricade or a broken door; the Room tab lists the doors of the selected room.

## The item pool, common supplies and crafting

- **A much wider pool.** Every room now holds a mix of potential weapons (sharp and blunt: pans and rolling pins in the kitchen, pool cues and billiard balls in the games room, hatchets in the boiler room, meat hooks and an ice pick in the cold store...), useful items (flashlights, towels, a hose, pliers, jump leads, chamomile, a life ring...) and **special** items (an old map, star charts, a sextant, a signalling mirror, a radio manual, piano wire, handcuffs, a tape recorder, spare bedroom keys, an unsent letter, a message in a bottle). A few more are hidden for sharp searchers (a fire axe behind the boiler, a craft knife in a paint tin...). Older saves get the new items once.
- **Common supplies are unlimited, but only where they belong:** rags, string and soap in the laundry; matches, bread, cooking oil and water in the kitchen; nails in the shed and attic; coal and rags in the boiler room; guitar string in the music room; stones, sand and sticks on the beach; oleander leaves in the garden and greenhouse; ice in the cold store. They can be taken freely (the room never runs out) and are never weapons. Everything else is finite: take it and it is gone.
- **Nothing comes from nowhere.** A character has what they carry; they can take what they see lying in the room and the room's common supplies. Prompts say so, the escape-experiment referee is told so, and the game will not let anyone use, give or make an item they do not have.
- **Crafting** (`craft`, with a recipe id): ingredients come from the inventory, from what lies in the room, or from the room's common supplies; some recipes need a tool and a fitting room (nail-studded board in the shed or boiler room, oleander extract in the kitchen or greenhouse, a rigged radio in the shed or study). A botched attempt wastes half the parts and can cut or burn. Recipes: broken-bottle shiv, garrote, nail-studded board, petrol bomb, oleander extract, drugged drink, improvised lockpicks (which pick doors), oil-soaked torch, stone-weighted cosh, improvised spear, rigged radio. The prompt lists what you could craft right now and what you are partly ready for ("still needs 3 sleeping pills, in the Red Room"), so people have to go and get the parts.
- **Crafted items are special items and are traceable.** Each make is recorded; a homemade weapon at a crime scene says it was made and which kinds of room its parts come from. A plotter with no weapon makes one from whatever is to hand.
- Spare bedroom keys (linen store and laundry) open that bedroom like the people who sleep there.

## Emergent hooks, ties, evidence, alliances, motives and a busier NeoVi

- **Hooks grow out of events; nothing is pre-set.** The old static "someone searched his bag" text is gone, as is the `hook` field. A hook opens when something real happens that someone can notice: going through someone's things (searching a bedroom whose owner is away; people keep a few personal things in their room), a lock picked or a door broken into, a stolen item, a found hiding place, someone at the door in the night, or two people noticing the same odd behaviour. Each has a real culprit, witnesses who saw something, and a victim who may suspect the wrong person (without evidence suspicion falls on whoever they trust least). It is solved by evidence (a witness, the stolen thing found on someone via a frisk, a crack under questioning) or it fades after a few days with a note of closure. The GM view lists open hooks, culprit and evidence on the Board tab.
- **Relationship ties.** Feelings now come with reasons taken from real events (a rescue, a slight, a gift, a refusal to be searched, a theft, a hook solved, an alliance, a betrayal, a wrongful execution). The prompt tells each character why they feel as they do about the people who matter right now, and conversation cards carry the latest tie. New games start with no ties and zero affinity.
- **More evidence at a trial:** damp footprints (the killer came in from outside), a locked room that was not forced and who held a key, scratches on a picked lock, a splintered door, a victim who never woke, fibres from what the killer wears, a chemical smell, a missing spare key, and a prior hook (the victim had been uneasy). None names the killer.
- **More plot motives:** besides hatred, vengeance, urges and the deadline, plots now come from jealousy, blackmail, revenge for a wrongly executed friend, protecting someone being hurt, exposure and silencing (a culprit about to be found out), ambition (few left) and greed (the keys). The motive shows in the plan the plotter sees.
- **Alliances and betrayals.** Two or three people who trust each other under pressure ally (openly or in secret). Allies share what they learn in an investigation, are told when something is wrong, and a killer's loyal ally swears to a false alibi. Strength grows while they stay close and fades when apart. A member can break faith (`"betray": id`, or the engine does it under pressure): leak the ally's secret, or denounce them in public; at a trial an ally can withdraw the alibi and testify against them.
- **A busier NeoVi.** She notices who carries a weapon where she is, inspects one empty bedroom a day (confiscating weapons, poisons and crafted items she finds, leaving a card), looks after people she likes with bandages and sweets, leaves trusted people a folded note about what she saw (with a warning if they are someone's target), reports to TereVi at night, and can be bought off for the day with a small gift (`give` to `neovi`).
- **Rules.** A free-text rule is read by the engine and then checked by a second, independent reading when the engine would enforce it by itself; if they disagree the referee judges it. Speech rules and rules that depend on indoors or outdoors tell the referee where everyone is. A generated rule whose title contradicts its text takes its short line as the title. Every rule is logged to `state/rules_seen.jsonl`; `tests/rule_corpus.json` holds the cases the classifier must read correctly.
- **Reliability of the optional mechanics.** The Stats tab shows today's usage of each optional mechanic, split into "chosen by the model" and "done by the engine"; each day's numbers go into `meta.json`. Each character gets one or two situational suggestions ("that door is locked", "someone here is hiding something") chosen to favour what has been used least, the long explanations of the optional systems appear only on the first turns of a day, and dialogue action lines that conjure objects nobody has are dropped.
- **Mid-day saves.** A checkpoint is written after every turn; if the server dies or you stop mid-day, the Start dialog offers "Resume it" from the last completed turn.
- **Tests.** 350 mock checks (`python tests/smoke.py`), deterministic seeds for the engine and the world, and `python tests/real_smoke.py` for one real-AI turn.

## Tuning panel, clothes, adult tone and items that do things

- **Tuning panel** (the "Tuning" button in the header): sliders for quarrels, plot, alliance and betrayal rates, how quickly people notice something is wrong, NeoVi's daily inspection, escape attempts per day, everyday sanity drain, deadline dread, the length of the calm window after a death, the remembrance lift, the cost and size of the night turn, how readily frightened people lock up, and two tone dials (flirtation 0-3, banter 0-3). Saved in `state/tuning.json`, applied from the next turn, "Defaults" restores the old behaviour. Definitions live in `murder/settings.py`.
- **Clothes.** Everyone has their own clothes on them and two spare copies plus a swimsuit in the bedroom wardrobe (the old 'outfit' and 'jacket' items became these). No clothing in the inventory means underwear. `"wear": <item id>|"none"` changes clothes from what you carry, what lies here or your own wardrobe. People dress in the morning, prefer their own things, put a swimsuit on at the pool, usually sleep in their underwear, and strip when a rule asks for it. Costumes and clothes lie around (bathrobes, a raincoat, an evening dress, a tuxedo, a party costume, old robes...) and a bedsheet cloak or a paper mask can be crafted. Others notice odd outfits.
- **Clothes in the story.** Someone in another person's clothes can be mistaken for them by people who see them pass (more easily by someone who is not thinking straight), a mask hides who it is, a killer's clothes are stained and carry the owner's label (they change and hide them; if the stained clothes turn up the label names whose they were), and a killer in someone else's clothes leaves a clue that points at the owner. A "be in your underwear" rule is now checked in code from what each person is wearing.
- **Adult tone.** Two dials. Flirtation appears only between people who click (a romance bond, or warm feelings plus personality plus a stable pairwise chemistry); banter and crude jokes between friends who are comfortable, edgier for sarcastic characters. Both are told to be flavour only: not forced, consensual, never explicit (it fades to black at the top setting). Clothes and underwear colour a scene.
- **Items that do something.** Lights (flashlight, headlamp, oil lantern with oil, torch that burns down) let you see in a blackout while others cannot, so a murder in the dark is witnessed only by people with a light; binoculars and telescopes let you watch a distant outdoor place; a magnifying glass finds fine clues (fibres, scratches, footprints, smells) others miss; handcuffs restrain (sleepers and the hurt are easy; they hold for a while, others can free you with a key or pick); a tape recorder hidden in a room records what is said there and plays it back as evidence; charts, a sextant, a radio manual or a signalling mirror raise the odds of the escape attempts they fit; mouse traps plus string make a snare that hurts but does not kill; and knocking at a locked door gets it opened by a friend or a reason for being turned away.

## Murders, trials and the deadline

**Murder.** In the start dialog, "Murders" can be Allowed or Peaceful. When allowed, characters get an `attack` action (target plus method: a weapon item, `poison:<item>`, or bare hands) whenever no case is open. Direct attacks resolve right after movement: sharp weapons usually kill, blunt less, bare hands rarely; a failed attack leaves the victim wounded and everyone hostile. Poison is secret and kills during the night. Everyone in the room sees a direct attack and remembers it. Only one case can be open at a time.

**Clues and discovery.** A murder leaves clues: the cause and time of death, the weapon (often left behind), sometimes an item dropped by the killer, an empty poison container. Anyone who finds the body sees the scene clues; `investigate`/`search` reveals clues in a room once the case is announced. When 3 people (not counting the killer) have found the body, TereVi announces it. If nobody finds it for about 14 hours, she announces it herself.

**Investigation and trial.** The announcement starts a 24-hour window. On the next day at the same hour a trial tick runs: everyone gathers in the Dining Hall for a debate, each living person votes (the killer too, lying), and the plurality decides. A unique majority on the killer means the killer is executed. **If the cast votes for the wrong person, that innocent is executed and the real killer escapes the island** (two scenes play, and three seats open up). A split vote with no majority executes nobody and the killer still escapes. The scene plays in the viewer with the votes revealed one by one.

**Weekly deadline (the Reckoning).** Weeks run Day 1-7, 8-14, and so on. If nobody has died by the end of the deadline day, **everyone still alive is executed** at the 22:00 night tick and the season ends. Any death (murder, accident or suicide) lifts the deadline and sets a new one at the end of the following week. The header chip shows the current deadline. See "The story layer" for how this pressure plays out.

**Newcomers.** Every death, execution or escape opens a vacancy of that gender (the show keeps 4 female and 4 male). Add newcomers with the form in the Start dialog (name, gender, role, personality, optional secret, items and portrait). They arrive at the next morning broadcast. Starting the first day of a new week is blocked until all vacancies are filled, so you stay in control of who joins.

**Optional TereVi motive.** The Start dialog has a free-text motive. If filled, TereVi dangles it in that morning's broadcast.

Test knobs for the mock backend: set `MC_MOCK_MURDER` (chance per turn, e.g. 0.3) and `MC_MOCK_VOTE` (chance a voter picks the true killer) before launching the server.

## Afflictions, injuries and unconsciousness

- **Conditions** (`murder/conditions.py`): afflictions (sick, poisoned, deranged, panicking, blinded, breathless, dizzy, hungry, thirsty, drunk, exhausted, chilled) and injuries (bleeding, broken arm/leg, whiplash, concussion, weakness, burns, infection, lost hand/fingers/eye/foot). Each has severity and modifiers for movement, physical success, fighting, perception, carrying and fainting; injuries heal over days, afflictions wear off, bleeding leaves a blood trail.
- **Unconsciousness**: anyone can faint (low HP, fear, hunger, fumes), be knocked out, choked out, drugged or tased. The unconscious take no turn (no model call), are not present for conversation, and wake with possible amnesia.
- **Non-lethal combat** (`murder/nonlethal.py`): actions `knockout`, `carry`, `rob`, `wake`, `treat`, `stage`. Blows, falls, fire and blades cause injuries; a killer can stage a helpless person beside the body (they wake with the murder weapon in hand); people can be locked in (keyed lock, escape by picking or breaking).
- People look after one another (auto-treat, wake the collapsed); plotters sometimes knock a target out first. Tuning "Body" dials: afflictions, injuries, fainting, hunger.

- **Follow-ups**: medical supplies on the shelf (bathroom, green room) are used for treatment, practice improves care, resting in those rooms speeds healing. A victim who remembers their attacker, or was locked in or robbed, gains a "wronged" tie and a *retaliation* plot motive. NeoVi wakes the unconscious she finds, notes drags, and unbolts keyed locks at breakfast. At trial, a framed person is told so, staging leaves flaws (head lump, drag marks), and anyone found unconscious at the time of death gets an alibi. The viewer shows blood spots and a chain icon on rooms with prisoners.
- `python tests/real_body.py` runs one real-AI turn in a staged injury scene.

## Not built yet

Hidden bodies or moving corpses, multiple simultaneous cases, and a hacker/terminal minigame for the Study.
