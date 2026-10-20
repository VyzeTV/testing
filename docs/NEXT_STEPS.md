# Next steps (after the real Day 3, 2026-10-19)

Where the work stands, what the real-model days showed, and the agreed plan. Phases A, B and C are done (A and B with their follow-ups); Phases D and E are done; Phase F (a fully live engine) is next and needs the user's go-ahead. Ask the user before starting each phase; commit each step with tests passing (`python tests/smoke.py`, `python tests/baseline.py` at or below about 91.7 calls a day, `python tests/balance.py`).

## Already done (commits 96ad566 and after)

- Map: deselect by clicking the person again, clicking empty map or Esc.
- NeoVi walks on the live map (`sim.sim_neovi`, laid down when the turn closes; she reaches each offender before punishing them).
- The outdoor room `garden` is named "Outdoors" (to be split properly in Phase E).
- Default pace 120 real seconds per game hour (old saved 50/90 migrated once).
- Chats wait for both people to reach their seat before the first exchange (14 of 25 mock chats used to part in silence); joiners speak from the next exchange (fixed a "speaks from another room" bug).
- The feed groups each conversation into one card (`feedTalk`, setting "Group conversations"); clicking a card follows it (`followConv`, panel `#convPanel`, other bubbles fade).
- Generation runs two blocks ahead (`session.BUFFER = 2`); the waiting line shows seconds and model calls.
- Free-time picks are spread up to `freetime.PICK_SPREAD` minutes into each daytime slice (not at night: that raised exhaustion).

The user confirmed on Day 3: movement is easier to follow, simultaneous conversations feel better, deselecting works, NeoVi is visible.

## What Day 3 showed (`runs/day_03` on the user's PC)

- No engine errors, no voicing fallbacks, no impossible walks; 69 model calls; 0 to 12 calls per block, so generation is no longer the bottleneck.
- **Still feels turn-based and slow.** The 08:00, 12:00 and 18:00 meal-turn blocks are mostly empty: 10, 13 and 12 of their 24 five-minute stretches have no walking, talk or events (free-time blocks have 2 to 6). Most blocks are also dead from minute 95 to 120. Block starts freeze the map for the title card and TereVi's broadcasts. Answer to "is it turns or live?": it is a turn-based simulation played back continuously. Positions, walks, conversations and events are minute by minute, but the model decides once per 2-hour block for everyone at minute 0, the engine finishes a whole block before it can be shown, and several systems run once per block at fixed minutes (hazards 40/90, dread 60, meal-block talk 56, the rule referee at the end, night wake checks at block starts).
- **Voicing does not know the time of day** (`voice.voice_prompt` gives day and room only): "Morning, Shintaro!" at 16:00.
- **Looks compliments and catchphrases**: looks are on every voice card, so openers praise hair and hats; "babe" is in 29 of 174 lines.
- **People answer their own lines.** A conversation is made of exchanges (an opening move and the other's reply, every 3 to 7 minutes) and the next opener can be whoever spoke last. The voice prompt lists the beats as one run and says "react to the line before", so a second line by the same person is written as a reply to themselves. Example (Day 3, 23:22, landing#1): Noah confide, Cail rebuff, Cail joke ("Relax? Babe, I'm dressed as a sailor..."), Noah laugh, Noah chat, Cail warm, Cail boast ("Of course I noticed..."). Also: Cail (in a romance with Noah) rebuffs his "big deal" and it is never followed up; Noah calls Cail both "amigo" and "amiga" (no genders in the prompt).
- **NeoVi says nothing.** `convo.start_convo` keeps only `world.agents` as members, so she is dropped from every live conversation, even when a decision's `talk_to` names her. Her daytime systems are passive (noticing weapons and sneaking; care items only for liked, badly hurt people).
- **Nobody reacts to intruders.** Szymon (plot: stalking Cail, "Cail must pay", a candelabra) woke at 01:00 with "a plan that will not wait", stood in Cail's room from 01:15 until 05:00 while she slept, then went back to bed. The plot never moved from stalking to striking, and Cail never had a chance to wake. Sleepers only wake at the start of a night block (`night.wake_reason`); a night snooper wakes the person searched 15 to 40% of the time however careful they are (`nightlife.py`).
- **Outdoors**: the user wants the Garden Maze to stay a separate area named "Garden Maze", with the rest of the grounds as "Outdoors", and later the Woods as their own area. Today every outdoor tile is the one room `garden` (zone `N`); the hedge maze is drawn by `mapgen.py` (x 12-32, y 48-63) and tree tiles already exist in the north.

## The plan

### Phase A: Dialogue
**Phase A is done** (2026-10-19). Steps 1 to 4: turns, the voice prompt, confidences, looks and catchphrases (see `docs/GAME_DESIGN.md`, Conversations). Also fixed: a staged scene gave lines to someone never walked there (`claimtrial.stage_trial_live`). Step 5: two real evenings (`tests/real_evening.py`, 67 calls) had no one answering their own line, no "morning" after noon, no repeated pet names or looks remarks; Noah's sheet and the pronouns of people mentioned but absent were fixed after the first (`docs/REAL_RUN.md`). Mock calls a day 91.8.
1. Speakers alternate between exchanges (`convo.py`, `social.py`): the next exchange opens with someone other than the last speaker unless they are alone or holding the floor; if one person speaks twice in a row, the voice prompt marks it as going on, not a reply.
2. The voice prompt (`voice.py`) shows the time of day, a marker between exchanges ("a few minutes later"), whom each beat is said to, and each person's gender and pronouns.
3. Confidences pay off: a partner or close friend rarely rebuffs "a big deal"; an accepted confide carries its content (the secret or worry) into the beat; a rebuffed one is remembered and may come back.
4. Looks only when new or notable (fresh clothes, blood, a missing accessory); a catchphrase at most once per scene.
5. Check: a real-model evening; nobody answers their own line, no "morning" after noon.

**Follow-up, done (2026-10-19): speaking of people consistently.** (See `docs/GAME_DESIGN.md`, Conversations, "Speaking of people".) People spoke ill of someone they liked, sometimes in front of them, then complimented them or talked normally about them again. Likely causes: `social.move_options` lets someone gossip about whoever a rumour they heard is about, and warn about anyone on their suspect list (for example someone known to keep a weapon), with no check of their own feelings toward that person or whether that person is in the conversation; nothing keeps a later line in the same scene consistent with an earlier one. Plan: gossip, warnings, mocking and reveals about a third person need cool or hostile feelings toward them (or a strong reason: a lie caught, a weapon seen, real fear), and are not said in front of them unless it is a confrontation; once someone has spoken against a person in a scene, they do not turn warm about them in the same scene; the voice prompt says how each speaker feels about everyone a beat mentions, so the wording matches. Check: a mock week counting moves against a liked person (aff 3+) and remarks about someone present; a real evening.

### Phase B: Pacing
**Phase B is done** (2026-10-19). Steps 1 and 2 (2026-10-19): every daytime block is free time with the meal inside, talk happens live (chats and one gathering a block), picks run to the end, shared games have moments. Dead five-minute stretches (`tests/pacing.py`, 8 seeds): meal blocks 4.0 (were about 11), free blocks 4.5 (were about 6). Mock calls 91.8 a day. Verdicts over 60 extra weeks unchanged (43/23 against 44/24).
Steps 3 and 4 done: the quick clock for dead air (pause settings, 4x by default; 54% of daytime minutes have nobody walking or talking, so a Normal-pace daytime drops from about 28 to about 17 minutes) and block starts that do not stop the clock (title card over the running map, broadcasts inside the block; `tests/pace_check.js` measures the map standing still about 0.1 s at a block start, against the 08:00 rule roulette's 11 s, kept as a staged moment).
1. Free time in every daytime block: 08:00, 12:00 and 18:00 become free-time blocks with the meal inside (no extra model calls).
2. No dead block endings: free-time picks run to the end of the block; the gathering joins the conversations instead of replacing them.
3. Viewer: a quick clock through dead air (nobody moving, talking or acting: the clock runs several times faster until something happens), switchable in the pause settings.
4. Block starts do not freeze: the title card overlays a running clock; TereVi's broadcasts get a minute inside the block.
5. Check: dead five-minute stretches per meal block from 10-13 down to 4 or fewer; a Normal-pace day takes noticeably less real time.

**Follow-up, done (2026-10-19): shared activities without voicing** (`pastimes.py`, see `docs/GAME_DESIGN.md` section 7; verdicts in mock weeks drop from about 74% to about 62% with pastimes on, season verdicts 76%/73% against 81%/78%, tiers 35/40/25; notes in `docs/SEASONS.md`). More things people do together that the engine resolves without a model call, each with small relationship and sanity changes: gaming (pool, chess and darts already have a winner and a moment, step 2), watching a film, watching the sunset, taking pictures together, cooking a meal for others, karaoke, and talking about a subject, a person or something that happened on the island (an outcome and a feed line, not voiced lines: who agreed, who argued, who left feeling closer or hurt). How it goes depends on feelings, mood and nature (a shy person dreads karaoke, a grieving one gets through a sunset, a rival can spoil a film night); good times restore sanity, a sour one costs it. They fill free time between voiced conversations, which stay the only ones that cost a call. Check: a mock week with these activities, their effects on affinity and sanity in `docs/BALANCE.md`, mock calls a day unchanged.

### Phase C: Intrusions and waking
**Phase C is done** (2026-10-19, `intrusion.py`; see `docs/GAME_DESIGN.md`, "Intrusions and waking"). Verdicts over 60 mock weeks 72% right (61% before); deaths about the same; seasons 42/32/25 after slowing the ultimatum (`escape.PACE` 0.7 to 0.55). Mock calls 91.0 a day.
1. Night wake checks every few minutes (`night.py`), from the noise made at that minute, instead of once per block.
2. Arrival reactions (new module): when someone arrives where a person is asleep, bathing or alone in their own bedroom. Awake owner: a friend, partner or invited visitor is welcome; anyone else gets a short confrontation ("What are you doing in my room?") with an excuse or a lie, shaped by feelings and temperament (distrust, a grievance tie, or a fight). Asleep owner: a wake chance from how they came in (door, lock, sneaking), what they do (careless search, rummaging, touching them), noise, and sleep depth (exhaustion, pills, drink).
3. Careful or careless searching: snooping and searching pick a level of care from temperament and skill; careful is slower and quieter, careless is faster and wakes people.
4. A woken person confronts, screams (neighbours may wake), pretends to sleep and watches, or fights back, and remembers who it was.
5. A stalker who finds the target asleep and alone moves to striking, or makes a recorded choice not to (`planner.py`).
6. Check: forced mock tests (intruder with the owner awake, snooper by a sleeper, stalker by a sleeper); balance deaths and snoopers caught.

### Phase D: NeoVi
**Phase D is done** (2026-10-19). Steps 1-4 (2026-10-19, `neoviday.py`; see `docs/GAME_DESIGN.md`, "NeoVi's day"). On mock days she speaks about two or three times a day, mostly at the table. Mock calls 86.4 a day. Step 5: a real afternoon and evening (`tests/real_neovi_day.py`, 43 calls): she was spoken to at both meals and answered in character (`docs/REAL_RUN.md`).
1. She can join live conversations: speaks when addressed, on duty, or with a confidence to share; voiced from her own sheet.
2. Visible chores at set times (serving meals, cleaning rooms, laundry rounds), shown on Who's where, putting her among people.
3. A decision that wants a word with NeoVi sends the person to find her.
4. Punishments and footage sharing play as short scenes where they happen.
5. Check: a mock day with her in conversations and chores; a real day where she speaks several times.

### Phase E: Map areas
**Phase E is done** (2026-10-19). The user chose a hidden cellar hatch and an old camp for the Woods, and the raft workshop and flares for the boathouse. See `docs/GAME_DESIGN.md`, section 9, "The outdoor rooms" and "The boathouse". The plan edit was a one-time script (`murder/maps/split_outdoors.py`, refuses to run twice).
1. Split the outdoors: a new room "Outdoors" (lawns, paths, coast) and the "Garden Maze" (hedge maze and its items, joined only to Outdoors). Update room connections, window ladders, hiding spots, free-time places, escape steps and the "indoors only" rule; older saves get a one-time fix by tile position.
2. The Woods (north) as their own room: dense trees that block sight and muffle sound; the hammock moves there. What else is there is the user's call (an old camp from a previous season, a hidden cellar hatch, a forgotten grave).
3. A purpose for the boathouse, the user's call (the raft route's workshop with visible progress, a locked motorboat as a harder way out, flares for the signal route).
4. Check: map validator, routes between every pair of rooms, labels in the browser.

### Phase G: Habits, investigation focus and electricity (agreed 2026-10-19, before F)
1. **Done.** Logical sequences and light routines (`habits.py`): follow-ups (cook then eat, a swim or a workout then a shower, a meal then washing up), dirt that shows and pulls people to wash (a sink for the light kinds, a shower for mud, grease and soot; blood scrubbed off at a sink is seen), a morning and a bedtime wash, and one signature habit per person.
2. **Done.** Investigation focus (`inquiry.py`): free time gets investigation activities (examine the scene, search a room tied to the case, question someone, compare notes); everything but real needs is cut back while a death is investigated, except for the very unstable and a killer acting calm.
3. **Done.** Electrocution as a murder method in the planner (`electric.py`) (an appliance in an occupied bath, a live cable in a flooded room, a door handle wired to the generator), with its own marks for the trial (burns on the hands, a scorched socket, a tripped fuse at an odd hour) and the risk of killing the wrong person or causing a blackout.

**Done (2026-10-19, `neovi_life.py`; see `docs/GAME_DESIGN.md`, "Her own body and mind"):** NeoVi's health and sanity, fights (she can be killed, with a trial; her own kills as the housemaid have none, but a witness raises them at the next trial), the master key taken from her, low-sanity behaviours and the climb back, a grudge against TereVi, no newcomers after her death, and the carry-over when she joins the cast. The user chose no replacement maid. Diaries are now asked for during the last night block (`night.diary_ahead`), so dawn no longer waits for them. Was: give NeoVi HP and sanity of her own (hurt, tired and worn down like the cast), and make sure her stats and her relationships (`nv["aff"]` and the cast's `nv_aff`, her lover, what she has told whom) carry over when she becomes the participant `kumiko` (`kumiko.py`). Build it after phase F.

**Done at the phase F gate:** `escape_rate` 3.3 to 4.6 brought 80 seasons to 38/34/29 (see `docs/SEASONS.md`). Was: **To do later (the user asked, 2026-10-19):** re-tune the ending tiers back towards 40/30/30. Over 80 seasons phase G gives 29% good, 41% bittersweet, 30% bad (the end of phase E gave 35/41/24). Too few good endings and too many bittersweet ones; judge with `python tests/season.py --seeds 40` (20-seed runs swing by ten points). Dials to try: `escape_rate`, `escape.PACE`, `endings.ending_costs`, `inquiry.FOCUS`.

### Phase F: A fully live engine (planned 2026-10-19; ask before starting)
**Why.** Today a two-hour block is worked out whole and only then played. With the real model that means a wait at the start of each block: everyone's decision is asked at minute 0 (one batch of calls), every conversation is voiced after the block (one call each), and the walks to conversations are laid back in time (`sim_talk`, `sim_finish`), so nothing in a block is final until all of it is. The aim: the engine produces the day in 15 to 30 minute pieces, each final when made, and the viewer plays each piece as soon as it exists.

**How `run_tick` works today** (engine.py): decisions at minute 0 (`decide_many`), arrivals on a Timeline, then systems at fixed minutes in sequence (`clock_to(15)` passive systems, attacks at the meet minute, 20 assaults, the meal, free time at 15-minute slices, 40 hazards and discovery, 60 dread and drains, 56/92 conversations), then voicing (`voice_convos`), `sim_talk`, reactions, the booth, the inner voice, the evening broadcast, the director, goals and the proposer; `emit` then finishes the tick (environment, minds, sifting, positions via `sim_finish`) and the session writes it whole.

**Steps** (each committed with tests passing):
1. **Done.** **F1 One timeline per block** (F1a: `run_tick` split into phase methods with byte-identical output; F1b: the phases on one Timeline at their minutes. In free blocks the minute-40 systems now really run at minute 90 among the slices, and free time starts at 15 instead of 20; 60 mock weeks: deaths and verdicts as before, mock calls 88.3 a day). Was: Put every system of `run_tick` on one Timeline at the minute it already runs (pure refactor: same minutes, same order). Check: a mock week gives the same ticks as before (same seed, same output), plus the hash-seed check.
2. **Done.** **F2 Forward-only positions** (`sim.py` forward mode: the frontier follows the engine's clock and nothing is laid before it, counted in `live["late"]`, two in two mock days, from conversation joiners; staged conversations are walked to when they are written; the idle wander on a 22-minute cadence; NeoVi walks to each chore as it starts and to each punishment as it happens, which then takes place when she arrives; smoke checks 25,200 positions do not change once passed, and fails when the clamp is off). Was: Walks to a conversation are laid when the conversation starts; idle wandering and whoever a system moved are laid as the clock passes, not at the end (`sim_finish` only closes the books). A "frontier" check: once the clock is past minute m, nothing before m changes (a test that snapshots tracks as the block runs).
3. **Done.** **F3 Voicing as you go** (`convo.voice_submit` asks for a conversation's lines on a worker thread the moment it ends; `voice_collect(tick, hour, upto)` takes them in, waiting if need be, in the order the conversations ended, so a seeded run stays the same. The rule referee stays one call at the end of the block: judging each conversation would add calls, and at the end of the block it already only acts forward. The booth and the inner voice also stay at the end; F5 decides how lines for earlier minutes reach the viewer). Was: **F3 Voicing and judging as you go.** A conversation is voiced when it ends, on a worker thread, while the engine carries on; its lines are attached when they arrive. The rule referee judges each conversation when it ends; reactions, the booth and the inner voice run at their minute. Same number of calls.
4. **Done (after F5, as "decide ahead", the user's choice).** `ahead.py`: at minute 107 of a day block the next block's decision prompts are built without leaving a trace (`decide_prepare_dry`) and the calls sent off; at the next block's start an early answer is used for anyone whose situation has not changed (`ahead_sig`: out cold or asleep, badly hurt, a death announced or tried, the rule, who is alive), else they are asked again. Only when someone watches live and has caught up (`viewer_close`, the session's `viewer_pos`), with the dial `decide_ahead` on; never before a trial, the last call, a vigil, a finale, the endgame, the evening or under the leader rule. Mock days with every block asked ahead: about 3.6 extra calls a day from people whose situation changed (so it is off when nobody watches; tests and baselines are unchanged at 89.6). Slow-mock browser run: 24 early answers used, none wasted; the first block of the day still waits for its decisions (it follows the night and TereVi's morning announcement). Earlier note: **Moved after F5, and to be decided at F6.** In this engine every activity ends at the block's edge, so "when a plan runs out" is minute 0 for everyone; spreading the decisions would change the game for little gain. What is left of the wait at a block start is the decisions themselves (they come before any piece); F6 measures it and then decides whether to ask for decisions ahead (during the previous block). Was: **F4 Decisions when a plan runs out.** Each person's one model decision per block is asked when their current activity is about to end (prefetched a few game minutes early on worker threads), not all at minute 0. Same number of calls, spread across the block. Something sudden (a scream, a body) is still handled by the engine at once, with no extra call.
5. **Done.** **F5 Streaming pieces** (`engine.block_piece` every quarter hour of a day block: ended conversations are taken in, then the block so far, up to the start of any conversation still going on, goes to `on_part` (`sim.sim_partial`); the session keeps the latest piece (`sess["partial"]`, versioned `pv`) and `/api/ticks` hands it out once the viewer has caught up; the viewer's `playStream` plays pieces as they come and carries on into the finished block (`playWindow` with a `st` state; `?nostream` turns it off). `tests/stream_check.js` with a slow mock (`MC_MOCK_LATENCY`): the wait at the start of the day went from about 18 to 12.5 seconds; later blocks were already ready. Smoke checks that every piece agrees with the finished block). Was: **F5 Streaming pieces.** The engine hands the session each finished piece (`tick["parts"]`: minutes m0 to m1 with their tracks, lines and events); the viewer plays a block piece by piece and extends it as pieces arrive; the buffer is counted in game minutes, not blocks. The finished block is still saved whole, and saves and resume stay per block. Special scenes (trial, finales, vigil, last call) stay whole for now.
6. **Done.** **F6 Gate** (2026-10-19): the full suite (1144), mock calls 86.4 a day, balance and 80 seasons with the re-tune (`escape_rate` 4.6: 38/34/29), a crash found and fixed (a joiner dying on the way), the browser checks, and a real day watched live (`docs/REAL_RUN.md`: 92 calls; waits only before the first block, 34 s, and before dawn, 35 s, for the diaries). **Phase F is done.** Possible follow-up: the wait before dawn could go by writing the diaries during the night blocks. Was: **F6 Gate.** Determinism, the full suite, balance, 80 seasons (and the pending re-tune of the ending tiers, since balance will move anyway), `pace_check.js` (how long the map stands still at a block start), `viewer_check.js`, and a real-model day with no waits after the start of the day (uses the user's subscription: ask first).

**Risks.** The core loop changes, so many tests will need updating; F1's same-output check is the safety net for the rest. Faster reactions (F4) may shift balance. Night blocks use the same machinery and come along with each step.


## Future features (planned 2026-10-19; ask before starting any of them)

The user listed these for later. Suggested order: H1 (it is the frame the modes need), then H2, H3, H4, H5, H6, H7. Each step is committed with tests passing.

### H1: Game modes
A `s["game_mode"]` chosen on the start screen: **Classic** (today's rules), **Danganronpa**, **Battle Royale**. TereVi's bible, the morning broadcast, the endings and the season report read it. Check: a mock season in each mode reaches an ending.

### H2: Danganronpa mode
* A **wrong verdict executes everyone except the culprit**, who "graduates" and leaves (a new ending, THE BLACKENED GRADUATES, tier bad). A right verdict executes the culprit, as now.
* The cast knows the stakes: a killer's plan now includes surviving the trial to win, and everyone's willingness to speak at the trial goes up (`claimtrial` willingness).
* TereVi announces the rule on Day 1 (the reveal) and at every trial opening.
* Open choices for the user: keep the weekly deadline (or use motives only, as in the games); keep the ways out.
* Check: forced wrong verdicts end the season with the culprit alone; 80 seasons for the tiers.

### H3: Battle Royale mode
* **No trials, no investigation**: a death is announced at once with the killer's name kept secret (or shown: user's choice); the last one standing wins.
* Pressure instead of the deadline: rooms close day by day (doors locked by TereVi, a shrinking map), supply drops in the open, and a collar countdown if nobody has died for a set number of hours.
* Plots and alliances matter more: alliances last until only the allies are left, then break.
* Endings: the last one standing (bittersweet), nobody left (bad); the ways out stay possible (good) unless the user turns them off.
* Check: mock seasons end with one survivor or nobody, and no trial ever opens.

### H4: TereVi's torments for participants
**Done (2026-10-19), as option 1** (`torments.py`): dares are checkable tasks (go to a room, talk with someone, give up an item, confess a secret) with a deadline; a willing person is pulled toward theirs in free time; a dare done gives +3 sanity; a failed one is only listed for the GM (Director > Torment, "ignored a dare") and the auto-director may torment that person (at most once a day). Torments happen only from the GM or the auto-director: humiliation, secret on every screen, a treasure taken, a shock collar, a friend turned. No boredom or favourite-target triggers and no `torment_rate` dial (the user's choice). No model calls.
**Possible today?** Only partly. The Director's "Twist" asks TereVi's model to tease, and a tease can be a whisper, a **dare**, a gift, a motive video, an announcement or a blackout. But nothing checks whether a dare was done and nothing happens if it was not, and there is no torment aimed at one participant (the nearest is the rule's punishment, and NeoVi's torment, which is hers alone).
The plan (`torments.py`, reusing NeoVi's `nv_torment` pattern):
* **Challenges the engine can judge**: TereVi's dares become structured tasks with a deadline (go somewhere, spend the night somewhere, eat or drink something, tell a secret, insult or kiss someone, hand over an item). The engine checks them from the world state.
* **Torments** for failing a challenge, or because TereVi is bored (no death or drama for some hours), or for her favourite target (the hottest story from story sifting): public humiliation, a secret played on every screen, a night locked out, an item taken, a shock collar for a day, a fake motive aimed at a friend. Sanity costs, and people who like the victim are hurt watching.
* A GM action **"Torment"** (target and kind), and a dial `torment_rate`.
* Check: failed dares are tormented, done ones rewarded; mock calls stay under the ceiling.

### H5: Bigger pool of preset characters
* About 24 to 30 presets (today: the default eight plus the newcomer sketches), each a full sheet: persona, backstory, secret, speech, facets, values, traits, looks, objection cry.
* The start screen draws a cast from the pool (random, or picked), and weekly newcomers come from the same pool.
* Portraits: the user supplies them, or a plain placeholder until then.

### H6: Cast editor with a helper
* A viewer page to make or edit a character: name, role, gender, age, persona, **backstory**, secret, likes and dislikes, speech, the 16 facets and 7 values as sliders, **traits** as chips (today's traits plus new ones), drive, looks (hair, eyes, outfit, accessory), objection cry, and starting ties to the rest of the cast.
* **The helper** (one model call, optional): fills in what is blank, suggests traits from the persona and backstory, flags contradictions (a gentle persona with cruelty 90), and offers three variations. Without a model, the facets are derived from the persona's words (`derive_mind`, which exists).
* Casts are saved as files (a library), and can be exported and imported.

### H7: Cast size and newcomers
* A cast of 6 to 16. Above 8: **shared bedrooms** (two beds per room: roommates see and hear each other at night, which changes alibis, intimacy and bedside strikes) or **a new dorm wing** (new rooms on the map, through the map plan files and the validator).
* A start-screen toggle: **weekly newcomers on or off** (today they are on until NeoVi joins or dies).
* What scales with size: the deadline, meal seating, trial voting, ending thresholds (a "lone survivor" with 16), and model calls (about 11 a day per person: 16 people is about 180 calls a day).
* Check: balance and 80 seasons at 6, 8, 12 and 16.

## After the real five-day season (2026-10-19)

A real-model season with a 5-day week, played by the user. It ended in the Reckoning on Day 5: nobody was killed, two rafts left with four people, and the four left on the island were executed. No engine errors.

### Fixed (commit 3a12ace)
1. **The clothes-swap rule could not be obeyed** (NeoVi punished 15 times in one day). "Use" on clothing now wears it, and the rule referee is told what each person wears and whose it is (`clothing.wearing_desc`).
2. **Romances and pacts overwrote each other** (the same romance announced three times). A pair can hold both; a betrayal ends both (`drama.apply_bonds`).
3. **The Reckoning ignored raft crews at sea.** They are now settled (`outside.crews_coda`); a surviving crew makes the ending bittersweet.
4. **Someone lost at sea was listed as "escaped".** Now dead (`outside.lost_at_sea`).

### Open (suggested order: 1-4, then 5-6 with one season check, then 7, then 8)
1. **Events stamped past the end of a block** (minute 146 of 120, some meal and pastime sanity events): the viewer may never show them. Clamp them to the block.
2. **NeoVi's conversations do not wait for people to arrive** (Day 4, 08:00: Ayden spoke to her in the Kitchen while still outside). Other conversations wait for both people to reach the seat; hers should too.
3. **The rule referee mixes up who said what, and where** (Day 5: Ayden tased for "addressing Szymon in the Kitchen while in the Bathroom"). Check what `refcheck.referee_turn` is given about speakers and rooms.
4. **Rule punishments all land at the end of a block**, and one bad day can leave people at about 50 HP for the week (Szymon, Noah). Punish at the minute of the breach, and cap the health a rule can take in a day. Check that the grace turn is long enough for rules that need setup (a swap).
5. **No murder in a 5-day week.** Sanity stayed at 76-96 until Day 5 (then 37-58); one plotter; the last call had no volunteers or strikers. Dread and plot pressure should ramp from the middle of the week, scaled to the week's length, not a fixed two days before the deadline.
6. **The raft is too easy with the real model**: all 8 helped and it was built twice in 5 days, taking 4 people off the island. Options: fewer helpers, a cooldown after a launch, TereVi countering it after the first escape. Rafts hold up the good endings in the mock seasons, so re-tune the tiers after (`tests/season.py --seeds 40`).
7. **Pet names and pet topics dominate across a day** (Cail "babe" 24 times and "followers" 8; Ayden "light" 20 and "frame" 5, even at the last call; Noah "amiga/amigo" 21). The Phase A cap is once per scene. Add a daily cap per person, and ease off a character's theme once used that day.
8. **Usage**: about 13k input tokens per call, 0.8-1.3M a day on the user's subscription. Trim the shared prompt context (rules text, cast list, memories); measure on a real day.

### What worked
Dialogue (nobody answers their own line; no "morning" after noon in 527 lines), NeoVi (spoke 33 times, served, thanked, flirted with, helped people break the rule), intrusions (caught going through things, walked in on in the shower, a confrontation), a full plot chain (Chloe plotted, watched, chose a method, struck on Day 5, was fought off), specific diaries that remember the raft crew, decide-ahead (44 early decisions used, 3 wasted; 55-92 calls a day), and the outside snippets and experiments.

### Found while voicing seed 28 (2026-10-20)
9. **Verdicts ignore the strongest evidence.** Seed 28, Day 8: a blue hair and a small hand pointed at Vixen, yet six of seven votes followed a herring clue ("Seul could not stand Cail"). Day 13: Shintaro's alibi (Cold Store) and Szymon's (Bathroom, with Shintaro) contradict each other and nobody raised it. Check the weights in `claimtrial` (suspicion meter vs. herrings; contradiction between two people's alibis).
10. **People present evidence against themselves** at the trial (Seul: "plenty of people know Seul could not stand Cail"; Ayden presenting a clue naming Ayden). A clue that names the presenter should not be presented by them, or should be framed as a defence.
11. **TereVi torments NeoVi almost every night**, and the same torment repeats ("taser herself" several times in one season). Lower `nv_torment`'s odds and avoid the last one used.
12. **A repeated feed line**: in seed 27, "Cail shoves Ayden back out of the door" six times in one day (an intrusion repeating).

### Found in the themed seed hunt (2026-10-20)
13. **Romances form and re-form far too easily.** Seed 13 (default): Szymon is in a romance with about seven people over 27 days; "Cail and Szymon are now in a romance" is announced three times in seed 11. A romance should need time and mutual feeling, and a breakup should cool things for days.
14. **The same madness line repeats** ("Mara has snapped" three times in one afternoon, seed 13). Announce a snap once.

### Also open from H4
After H4, 80 mock seasons gave 29/36/35 (36/29/35 before). Possibly noise (runs swing by about 5 points), possibly the "hand something over" dare taking escape parts. Check with dares off; if it is the dares, keep escape parts and keys out of that dare.
