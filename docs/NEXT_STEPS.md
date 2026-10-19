# Next steps (after the real Day 3, 2026-10-19)

Where the work stands, what the real-model days showed, and the agreed plan. Phases A, B and C are done (A and B with their follow-ups); Phase D steps 1-4 are done, its real-model check next. Ask the user before starting each phase; commit each step with tests passing (`python tests/smoke.py`, `python tests/baseline.py` at or below about 91.7 calls a day, `python tests/balance.py`).

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
**Steps 1-4 done** (2026-10-19, `neoviday.py`; see `docs/GAME_DESIGN.md`, "NeoVi's day"). On mock days she speaks about two or three times a day, mostly at the table. Mock calls 86.4 a day.
1. She can join live conversations: speaks when addressed, on duty, or with a confidence to share; voiced from her own sheet.
2. Visible chores at set times (serving meals, cleaning rooms, laundry rounds), shown on Who's where, putting her among people.
3. A decision that wants a word with NeoVi sends the person to find her.
4. Punishments and footage sharing play as short scenes where they happen.
5. Check: a mock day with her in conversations and chores; a real day where she speaks several times.

### Phase E: Map areas
1. Split the outdoors: a new room "Outdoors" (lawns, paths, coast) and the "Garden Maze" (hedge maze and its items, joined only to Outdoors). Update room connections, window ladders, hiding spots, free-time places, escape steps and the "indoors only" rule; older saves get a one-time fix by tile position.
2. The Woods (north) as their own room: dense trees that block sight and muffle sound; the hammock moves there. What else is there is the user's call (an old camp from a previous season, a hidden cellar hatch, a forgotten grave).
3. A purpose for the boathouse, the user's call (the raft route's workshop with visible progress, a locked motorboat as a harder way out, flares for the signal route).
4. Check: map validator, routes between every pair of rooms, labels in the browser.

### Phase F: A fully live engine (later, larger; ask first)
1. Each person decides when their own plan runs out (building on the brain setting's intentions), not everyone at minute 0.
2. The once-per-block systems (hazards, dread, the rule referee, wake checks) become timeline events at their minute.
3. Positions only ever laid forward in time (today `sim_talk` and `sim_finish` lay walks back in time within a turn), so blocks can stream to the viewer in 15 to 30 minute pieces.
4. Check: determinism, the full test suite, a real day with no waits after the start of the day.
