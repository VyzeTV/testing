# Murder Channel: Game Design Document

Status: describes the game as built (the fork in `E:\MC\murder-channel\app_live`, port 8766, last updated 2026-10-16).
The older `docs/DESIGN.md` is the original proposal and roadmap for the live edition; this document is the reference for what the game is and how it works today.
The original turn-based edition in `E:\MC\murder-channel\app` (port 8765) is kept as the stable version and is not described here.

---

## 1. What this is

A Danganronpa-style killing game, simulated. Eight celebrities are held in a house on an island by **TereVi**, a murderous AI host who runs the "show", served by **NeoVi**, a housemaid held as a slave. Nobody leaves. If nobody dies before the weekly deadline, **everyone** dies. Anyone who kills must survive a **class trial**; a wrong verdict executes an innocent and frees the killer.

You do not play a character. You are the **audience and game master**: you watch the simulation, can pause it, read what everyone privately thinks (GM view), and nudge the story with director tools (whisper, rumour, drop an item, force a twist). Characters are driven by language models (their voices, dilemmas and conversations) on top of a deterministic engine (their bodies, needs, movement, perception, physics and the rules of the house).

### Design pillars
1. **Drama emerges from events, never from seeding.** Nothing is pre-set in character data: no pre-written relationships, no scripted mysteries. Hooks, grudges, alliances and plots grow out of what people actually do.
2. **The engine is the body, the model is the mind.** Positions, time, durations, walls, fire, injuries and probabilities are computed; speech, intentions and judgement are written by the model from what the character actually knows and remembers.
3. **Murder must be possible, plannable, and solvable.** Plots follow a campaign (brood, prepare, stalk, strike), windows come from who can really see and hear, and every kill leaves layered, ambiguous evidence for a trial that can be wrong.
4. **Brutal but creative, never gratuitous.** Dark tone, adult flirtation/sexualization and crude banter are dials; meanness is caused, not default.
5. **Everything is a setting.** Pacing, lethality, quarrels, plots, snapping, clue clarity, pause behaviour and tone are dials in the Tuning panel and the pause settings.
6. **The viewer is the game.** A live tile map of the island, a "Who's where" roster, a chronicle of everything that happens, pause dialogs for important moments, title cards for each part of the day.

### Audience and constraints
One player at home, running on a Claude Pro subscription through the `claude -p` CLI (no API credits). Typical cost of one real day: 55-100 model calls, about $1.9-3.5 of plan usage. A free **mock** backend (scripted, deterministic) exists for testing and for playing without any model.

---

## 2. The people

### The cast
Eight starting characters (ids `szymon, seul, vixen, noah, ayden, shintaro, chloe, cail`), each with: name, role (their celebrity), persona, speech style, `candor` (how they behave under stress), a secret, a colour and a portrait. Cast sheets live in `murder/data_cast.py`; the live cast lives in the saved state (`state["cast"]`), so newcomers can be added.

Each character also carries, derived rather than authored:
* **Mind**: 16 personality facets (anger, vengefulness, trust, gregariousness, altruism, assertiveness, courage, cruelty, impulsiveness, stress vulnerability, vanity, ambition, curiosity, orderliness, humour, romantic) and 12 values, computed once from the cast sheet text with a small fixed per-character spread.
* **Drive**: a secret motivation (survivor, schemer, protector, avenger, nihilist, saboteur, thrill, romantic, martyr, seeker...) re-evaluated each night; it shapes plots and snaps.
* **Relationships**: a −10..+10 affinity toward every other person, moved by every interaction.
* **Body**: health, sanity, hunger, thirst, bladder, hygiene, conditions (see section 6), an inventory, worn clothes, a bedroom of their own.

Newcomers are added only by the player (never invented), to refill the cast to eight (4 male, 4 female) before a new week can start.

### TereVi (the host)
A theatrical, murderous AI on the house monitors. She announces the day and the evening, invents the daily rule, meddles (teases, dares, secrets, motive threats), announces bodies, runs the trial and the executions, and adapts to the cast's escape attempts. Written by the stronger model.

### NeoVi (the housemaid)
Frightened, terse, secretly sympathetic. She enforces the daily rule (tasing or dragging offenders to the Cold Store), inspects bedrooms, repairs doors, restocks medicine, attends trials and last calls as a silent witness, and is made to report to TereVi each night. She has an arc (martyr, survivor or betrayer) and holds the master key.

She is human: her real name is **Kumiko Akimoto** (`kumiko.py`). In the first days she mostly watches. Later, at 01:00, she does her rounds and stops at one door: the person she feels most for. Feelings go both ways (the cast's feelings toward her are kept in `nv_aff`, apart from their feelings for each other; her care and their small gifts move them too). When trust is mutual she confides one thing only she knows: her real name (only at deep trust), a camera blind spot (a real aid for the way out), where TereVi keeps confiscated parts (a real part), what she saw in the dark (a true belief), or a warning (the next counter on that route finds the hiding places empty). A slow romance can grow with someone she trusts deeply; their nights are implied, never shown.

Each night she also chooses: obey, help (a missing part, every TereVi lock opened, a looped camera, covering for someone) or betray (a full report: TereVi counters the leading route). The choice follows her resolve, a lover, her friends, her fear and her own sanity. Helping can get her caught, and then TereVi decides: a humiliation on air, **re-education** (her sanity drops by 25, her fear rises, her feelings are halved) or making her a **participant**. As a participant she is a contestant under her own name, with a bedroom, looks and clothes of her own; there is no one to replace a housemaid, so **no newcomers arrive** for the rest of the season (the viewer and the season sim stop asking for them).

Out of uniform Kumiko is herself: long dark purple hair with blunt bangs, red eyes, short, a black blazer with white trim, a red tie, a pleated skirt and dark purple thigh-highs, and a purple stuffed rabbit she always carries (her accessory, which can be lost like any other). She is reserved but not shy, odd, curious about the mysteries of life, a sharp reader of people, into anime and games, and worried she has no talent among celebrities. Her sheet sets her facets outright (cast `facets` and `values`) and names **traits** the engine reads (`has_trait`), which any character sheet can use:

* `observant`: when someone lies to her face she may read the tell (a belief that they lied).
* `undecided`: a close call at the vote is made at the last second (the reason says so).
* `self_reliant`: her vote is her own; friends' leads do not sway it.
* `catlike`: idle time looks like a cat's (curled up in the sun, watching from a high shelf, following a moth).
* `trapped`: accused or confronted head-on she freezes instead of answering (a `freeze` reply, a sanity cost); in the trial, a contradiction she cannot answer leaves her silent, which looks bad.
* `no_talent`: someone boasting at her costs her a little sanity.
* `yandere` and `twisted` (any sheet): obsessive love as a motive to kill; killing without a reason.

### The player's tools
Director panel (whisper to someone, spread a rumour, drop an item, force a twist, island events), an optional **auto-director** that nudges quiet days, scenario editor and a **scenario generator** (premise, secret twist, rules, scheduled events under a difficulty budget), save slots, rewind/export, "Previously on" recap.

**Goals** (`goals.py`, Director panel "Goal", dial `goal_push`): the GM picks a goal from a menu (make two people enemies, friends or lovers; A betrays B; get the evidence found; keep someone alive; a breakdown for someone; someone dies; get a way out finished) and a number of days. Each turn the director may make one move toward each goal, using engine moves only: a rumour, an unsigned note, someone wanting to talk to someone, a secret learned, NeoVi's inspection of a room, TereVi pointed at someone, a summons on the schedule that puts people in one room, an unlocked door, and shifted odds on the rolls that decide things (a plotter's strike, a betrayal, a new plot, work on a way out). Nothing is forced: the outcome is still rolled. A goal is met when the state shows it, fails when its days run out, and can be dropped. In three mock days an "enemies" goal was met 3 times in 10 and soured the pair more than no goal did; a "friends" goal turned a cooling pair warm. The Stories tab lists the goals and the director's moves.

**Pause hooks** (`pauses.py`, Director panel "Pause and ask me when", dial `gm_nudge`): at a deciding roll (a plotter deciding whether to strike now, a witness deciding whether to speak against someone at the trial when the fact is strong, someone deciding whether to betray an ally), a live session can stop and ask the GM: encourage, discourage, or let the dice decide. The answer moves the chance by 0.25 by default, never to certain; no answer within 45 seconds lets the dice decide, and fast-forward skips the question. The engine waits on its own thread while the viewer keeps playing what was already decided, so the question is about a moment just ahead of what is on screen. Every answer is logged for the GM.

**Structured reflection** (`reflection.py`): each night's diary call also returns up to three choices from a fixed menu, which the engine checks and applies: trust (down: feelings drop by 1 and they are less open to that person; up: feelings rise), protect (for three days they keep an eye on someone and are much more likely to step in if that person is attacked), reread (something someone did now reads as a threat: a false belief and a fear thought), and resolve (tomorrow they want to confront, apologise to, ask or thank someone). Without a model, or when it gives none, the engine chooses from thresholds: a proven lie or a betrayal costs trust, being helped earns trust and thanks, someone dear in danger is protected, a low mind rereads a slight, a hurt is confronted by the bold and a wrong apologised for by the kind. No extra calls: it rides the diary call.

**The model as a proposer** (`proposer.py`, dial `proposer_calls`, default 2 a day, 0 = off): now and then the model suggests a murder plan for a plot that has stalled (striking for 4 turns or stalking for 6 with no opening), or one social move for someone in crisis (sanity under 20, no plot). The GM can ask for one too (Director panel, "Propose"). The model sees the character's beliefs, feelings, goal and what they know of the world: rooms with a drop, water, useful items lying about, what they carry. It answers in the planner's own format: a scheme, a room, an item, when, a cover story and steps. The engine checks every part: the scheme exists, the room exists and can be reached, a push needs a real drop, a drowning needs water, an item must exist, a sleeping target must be in their own bedroom, a plan that waits for the target somewhere (alone, a push, a drowning) must use a place the plotter has seen them (as the engine's own planner does), each step is a known verb on a real thing. One impossible part rejects the whole proposal and the engine's own plan stands. An accepted social move is used once, the next day, when they talk to that person. Counts in `s["proposer_stats"]`; each proposal is a GM-only line in the feed.

**Stories in play** (`sifting.py`, the Stories tab in GM view): after every turn, patterns over the state spot stories forming: a love triangle, a love not returned, two enemies both alone right now, someone betrayed while protecting a third, someone holding a proven lie against a person they fear, a secret held by someone the owner dislikes, an alliance wearing thin, a plot (and a target starting to suspect the plotter), a witness the killer does not know about, lovers at breaking point, a grudge for an innocent voted to death, a way out close to done. Each has a heat and a "since"; one that stops matching is marked over. Sifting only reads (no chance, no state change). When the auto-director steps in, most of the time it pushes the hottest story one step at its people: a rumour, an unsigned note, or TereVi pointed at them.

---

## 3. The arc of a season

```
Day 1  meeting and introductions (10:00) -> TereVi reveals the truth at 20:00
Day 2+ ordinary days (section 4)
   every week_len days (default 7): the DEADLINE.
       nobody has died by the end of the deadline day  ->  THE RECKONING: everyone dies.
       a death (any kind) moves the deadline to the end of the next week.
   deadline day 20:00: LAST CALL. Someone may volunteer to die, or strike in the dark.
a death -> a case -> body announced -> 24h of investigation -> class trial -> execution (or not)
fewer than 4 survivors -> ENDGAME (battle, crown or whim, TereVi's mood)
four ways out: broadcast the truth, shut TereVi down, raft (saves 3), threaten to blow up the island
```

Every death counts toward the deadline: murder, manslaughter (a killing blow nobody intended), suicide, accident (fire, a fall, a failed experiment, an infection). Only a murder with a culprit has a trial; accidents and suicides lift the deadline with a short death notice. A **killing spree** (frenzy) waives the trial for the spree killer's own victims only.

**Aftermath**: a closed case opens a calm window (no drain, dread or new plots), a vigil the next morning (sanity lift), then half drain for two days. Sanity recovery after a trial comes first, by design.

**Escape routes** (`routes.py`, `escape.py`, `finales.py`): each has a plan with steps and percentages (e.g. transmitter, power, signal position, proof, beating the jamming), advanced by **experiments** and by **free-time work** ("working on a way out"): people go where a step is done, fetch parts where they lie (driftwood on the beach, fuel at the Generator Shed, chemicals in the art studio), use what they carry, and make progress at a pace set by the dial `escape_rate`. Skill helps (the hacker with the signal and the cameras, the explorer finding the hatch). Each step has needs in the world (parts gathered, an earlier step done, the hidden hatch found, a way to blind the cameras: a blackout, a hacking drive, cut feeds or NeoVi) and stops at half way until they are met. Work can go wrong (a burn, a collapsing frame, a fall in the dark). People join the route that is clearly ahead. A first attempt comes after about two weeks.
* **The raid on the core** (the shutdown finale) is a live scene: the team goes down the Lighthouse hatch; if TereVi notices (less likely if she was blinded) she seals the hatch, gasses the stairs or offers the shakiest member their life to raise the alarm; pressure plates can wound; then the core falls or holds.
* **The bomb standoff** (the ultimatum) is a live scene over up to three rounds: TereVi doubts them, bargains (one walks free if they hand over the trigger), works on the shakiest member, or calls the bluff. The team holds, splits, betrays her the trigger, presses it (a real blast: deaths possible, the island dark, her cameras down a while) or folds. She surrenders when the threat is credible and the team holds.
* **The raft** (`outside.py`) is small: two, or three if well built. Its launch is a live scene on the beach: who goes (the builders and the ones they love), who is left in the surf, sometimes a desperate stowaway who makes it riskier. The show goes on for everyone else. The crew then lives on an off-screen track rolled at dawn, and the audience gets a snippet each time: days at sea (thirst, storms, someone lost overboard), landfall or a passing boat, or lost; then ashore they must be believed (proof helps), or are dismissed, or are silenced by the show's own people. The island only hears what TereVi chooses to say.
* **The rescue countdown**: a believed raft crew or a believed broadcast of the truth (the transmit finale no longer ends the show at once) brings help in 2 to 5 days. TereVi announces a "final episode" and plots come easier. Rescue ends the season: good if enough people are still alive, bittersweet ("too late") if not. If the island empties while a crew is out there, the season ends with them (bittersweet).
* **TereVi's counters** are things people see: NeoVi confiscates half of the gathered parts, the workroom locks itself, the most active worker is tased on air, or she lets slip that one of them has been "such a help" keeping her informed (a planted false rumour).
* **How a season ends** (`routes.ending_tier`, `endings.py`): every ending is good, bittersweet or bad. TereVi shut down, surrendering, or a rescue in time is good, unless it cost too much: then it is bittersweet. A cost is TereVi's parting shot (when she loses she may take someone with her: a last execution of whoever hurt her most, or the lower floors flooding as the doors open, so only part of the island gets out; dial `parting_shot`), NeoVi dying for it within three days, someone the rescue leaves behind (missing in the house, or refusing to leave a grave), or one survivor or fewer walking out. Crowned winners of a killing game, a lone survivor, a late rescue and a raft crew outliving the island are bittersweet. The reckoning, the final battle, a winner crowned on a whim and nobody left are bad.
* **Last words** (`departures.py`): after the vote, before anyone is taken away, the condemned and an escaping killer speak: the killer gives their motive (from the plot that drove them: jealousy, the deadline, blackmail, revenge, fear, a hallucination...) and either remorse or defiance; an innocent protests and asks a friend who voted against them "you too?"; each says goodbye to the person they care about most, who answers (or turns away), and someone who hated them may curse them. One voicing call; shown as LAST WORDS after the verdict.
* **Killers the show lets go**: after a wrong verdict or no verdict, TereVi releases the killer. Out in the world, at a low chance (more if remorseful, or if they left someone they love behind; dial `escapee_help`), they try to help: they risk a murder charge and are rarely believed. Most keep quiet; some give up when a lawyer explains what a confession means; one who is believed starts the rescue countdown.
* **The season's run** is 28 days (dial `season_days`). At the last turn of the last day TereVi ends the show her way (a last stand first, if a way out is far along); an untried death is never tried.
* **After the fourth trial** no newcomers arrive: TereVi makes NeoVi a contestant instead, under her own name (if she is still the maid).
* **The last stand**: when only three are left and TereVi is about to end it her way, they first try the way out that is furthest along, if it is at least 70% done, with odds lowered by how unfinished it is (once a season; dial `last_stand`).
* **Epilogues**: every survivor gets two or three sentences over the credits, built from the state: how they come out of it (sanity), the person who matters most (a lover who walked out with them, one written from both sides; a lover who did not; a friend; someone who wronged them; an enemy; someone they loved who died), a killing nobody outside knows about or the day they cannot talk about, and what they make of their old life. NeoVi (Kumiko) gets hers if she is alive and not a contestant. One voicing call words them all; the templates stand otherwise. The season-end card lists them under "Afterwards", with the costs ("At a price: ...").
* Tuning over 40 refilled mock seasons gives about 38% good, 35% bittersweet, 28% bad (target 40/30/30); `escape_rate` now defaults to 3.0.

---

## 4. The day

Time runs 08:00-22:00 in two-hour blocks (a "tick" each), then a night played in two-hour blocks until 07:00.

| Hour | Segment | Kind |
|---|---|---|
| 08:00 | Morning announcement | **Turn**: TereVi's rule and news; everyone decides once. **Breakfast** 08:30-09:30 |
| 10:00 | Free time | **Free block** |
| 12:00 | Midday gathering | Turn. **Lunch** 12:30-13:30 |
| 14:00 | Free time | Free block |
| 16:00 | Free time | Free block |
| 18:00 | Evening gathering | Turn. **Dinner** 18:30-19:30 |
| 20:00 | Free time | Free block (evening announcement) |
| 22:00 | Bedtime | Curfew, locks, everyone to bed except whoever stays up; the deadline reckoning |
| 23:00, 01:00, 03:00, 05:00 | Night | **Night blocks** (internally hours 23, 25, 27, 29, so time only goes forward) |
| 07:00 | Dawn | How everyone slept, the diaries; the day ends |

**The schedule** (`schedule.py`). The day has fixed draws: wake-up, the three meals in the Dining Hall, the evening announcement and curfew. The daily rule (Mandatory Mealtimes makes lunch and dinner compulsory) and the GM (Director panel: cancel, move, or add a summons to any room) can change them; a change to a time already past applies tomorrow. At a meal's minute everyone weighs coming (hunger, thirst, loneliness, sociability, friends and enemies at the table, stress, a plot on the go) and those who come walk to the table and eat. The meal's conversation always happens. A **calm meal** (no accusation, threat, confrontation, put-down, fight, punishment, outburst, body or fire) lifts everyone at it: a little sanity (a "meal" special moment, bigger with friends there), company, +1 affinity between people who talked, less stress, and the day's news passes around the table (`s["news"]`: what someone witnessed reaches those who had not heard). A **tense meal** gives nothing. Skipping is a quiet cost: no company and no news, and three missed meals in a row get noticed by the others. A summons works like a meal without food and is mandatory.

**Mandatory scenes** (the presentations, the reveal, the last call, the trial, the vigil, a summons): whoever will not make it on their own (asleep, hiding, too far, locked away, dragging their feet) is fetched by NeoVi, and the feed says so.

**The night** (`night.py`). Sleep is a task in a bed. At 22:00 everyone goes to bed except whoever stays up: anyone who asked to ("night": true), plotters on the move, seekers on a case, the badly shaken, the stressed, the hungry and thirsty. There is no cap and no flat health cost. At each block sleepers may wake for a reason: a noise or a commotion next door, smoke, a full bladder, hunger, thirst, a bad dream, insomnia, a plan that will not wait. Whoever is awake lives the block with the free-time machinery, limited to quiet things (eat, drink, the bathroom, read, sit, look around, explore, the telescope, the radio, tinkering, a whispered chat, stalking) and sooner or later goes back to bed (the "sleep" act; nobody sleeps on a full bladder or an empty stomach). The ones who asked to stay up get their own decision in the first block. Sleeping bodies slow down. At dawn sleep is counted: a full night mends a little health; less than five hours leaves someone **exhausted** and tired all day. A block where the whole house sleeps is **quiet** (`tick["quiet"]`).

**NeoVi's day** (`neoviday.py`, phase D). While she is the housemaid she works a chore list each daytime block (`CHORES`: cooking and serving each meal at its minute, washing up, the laundry, dusting, changing someone's sheets, sweeping, the evening rounds); her room follows the work minute by minute (what she notices, where she walks on the map, and her row in Who's where). She takes part in any live conversation in the room she is working in (`conv["nv"]`; not a member, since she has no track during a block): now and then someone turns to her (always, when they came to find her): they ask her something (she plays dumb, answers if she likes them, or with mutual trust and nobody else listening confides what only she knows, through `neovi_confide`), thank her for the meal, flirt, or needle her (a cold rebuke); feelings move both ways. She is at the table when she serves, so a lone diner talks with her. A decision whose talk_to names her sends the person to find her for a word. Her punishments and the stills she shows an investigator play as short scenes where they happen, in engine-written lines (no model call). Her lines in conversations ride the conversation's one voicing call, with her own card.

**Intrusions and waking** (`intrusion.py`, phase C). Sleepers are also checked every quarter hour of a block: a noise in their room (or a louder one next door), or someone awake standing in their room who has no business there, may wake them, more easily for light sleepers (stress, low sanity, the observant trait) and less for deep ones (exhausted, drunk). Walking into someone's own bedroom: a friend, a partner or someone they wanted to see is welcome; anyone else is asked "What are you doing in my room?" and gives an excuse, a lie if they came to snoop or stalk (an observant owner, or half of the others, sees through it: a `lied` belief and a grievance); a hostile, hot-tempered owner shoves them out. An owner asleep may wake as they come in (sneaking halves it). Walking in on someone in the bath or shower happens now and then (most people lock or knock); the shy are mortified. Snooping is **careful** (puts things back, wakes half as often) or **careless** (wakes people 1.6 times as often, misses things), by orderliness, impulsiveness and skill. A woken person **confronts** the intruder (who backs out), **screams** (neighbours may wake; the intruder runs), **pretends to sleep and watches**, or **fights back**; they always remember who it was, and someone who came to kill them comes to believe they are dangerous (the plot falls back to stalking). A **stalker** who finds the target asleep and alone decides then: they move to strike, or lose their nerve, leave, and it is written into the plot. Counts in `s["intrusions"]` and `docs/BALANCE.md`.

**Deadline day.** Every hour of the deadline day costs sanity, more the nearer 22:00 gets: 1 an hour in the morning, 2 in the afternoon, 3 in the last hours, each hour charged once whatever kind of turn covers it (special scenes too), scaled by the everyday-drain dial and damped for people already near breaking. The evening before the deadline already frays nerves.

* A **turn** is one decision per character (model or engine), movement, actions, resolution and one conversation per group, as in the original edition.
* A **free block** is the live part of the day (section 7): one decision to start, then 15-minute slices in which people live their lives.
* The viewer shows a **title card** and a feed line when each segment begins (switchable in the pause settings). With the `free_time` dial off, every block is a plain turn.

Special scenes replace ordinary ticks when due: presentations and the reveal on day 1, last call, the trial, the vigil, the endgame and escape finales.

---

## 5. How a turn runs (engine order)

`DayRunner.run_tick(hour, kind)` in `engine.py`, simplified. A turn is two hours of game minutes on a minute clock (`clock.py`): every step below happens at a minute, every event carries it, and everybody's tile position at that minute is real state (`sim.py`, section 9).

1. **Setup** (minute 0): rule notices, NeoVi's routine, island events and scheduled scenario events, discovery checks, wellness check, impulses, threats.
2. **Decisions**: for each character, either the **engine** makes a routine decision from needs and relationships, or the **model** is asked (rule days, plots, crises, conflicts, the start of the day, a missing plan). Unconscious people skip the call.
3. **Overrides and plots**: spree and focus overrides; plot steering (engine-driven stages).
4. **Apply decisions**: everybody sets off at their own minute in the first quarter hour and walks their route on the tiles; the action they came for (take, use, craft, search, hide, spy, stash...) happens when they arrive, in the order people arrive. An attack happens when attacker and target are first in the same room.
5. **Passive systems**: observation of movement, traps, stealth, secrets, withheld clues, hooks (loose ends), conditions and hunger, NeoVi's agenda, clothes, alliances.
6. **Resolution**: attacks, assaults, sabotage, impulses, deaths, hazards, case upkeep, experiments (the dice decide, the model narrates), occasions, TereVi's intervention, rule enforcement, dread and sanity drain, friction.
7. **Free block only**: `free_time()` plays the block out in slices (section 7).
8. **Conversations**: live (section 9, Conversations): free-time chats run from the minute they start, the turn's gatherings from about minute 56 (92 in free time); the engine resolves every social move as it happens and one call per conversation voices them afterwards. Staged scenes (occasions, TereVi on the monitor, the trial, the reveal, finales, the last call) are still written whole by one model call whose effects are applied.
9. **Emit**: environment steps, mind update, chronicle, snapshot, and the turn's live record (everybody's walk, every line and event with its minute) for the viewer.

---

## 6. The inner life: mind, body and brain

### Beliefs (`beliefs.py`)
Each person keeps what they think is true in `agent["beliefs"]`: a kind (`at` someone was in a room from one time to another, `did` someone did something, `rumor`, `news`, `lied` someone lied to them), who it is about, where and when (absolute hours: day * 24 + hour), how it was learned (**seen**, **heard** by overhearing, **told** to their face, **inferred**) and how sure they are. Beliefs can be wrong; the engine keeps the truth beside each one (`true`), which only the GM view shows.

* **Sightings**: after every turn, everyone awake notes who they saw where (sampled every 15 minutes from real positions and line of sight, worse in the dark), and where they were themselves. Consecutive sightings join up; a gap means the person was out of sight.
* **Witnessed events** (an assault, a body, a theft, a punishment...) become beliefs about who did what.
* **Testimony** in a conversation (someone saying where they were at the time of a death) is *told* to the people in it, *heard* by a listener in full earshot, and half heard at the edge of earshot with the room wrong.
* **Rumours** and the **news at meals** become told beliefs, a rumour marked false if it was a lie.
* **Lies are caught** when a claim about where someone was contradicts what the listener saw at that time: the listener now believes the speaker lied, likes them less, suspects them first, and wants to tell the booth about it.
* **Uses**: honest testimony says where the person knows they were and who they actually saw; suspicion puts caught liars first; during a case the decision prompt lists what they know about the time of the death and whom they caught lying; the GM view lists each person's latest beliefs with their source, confidence and whether they are wrong.

### Mind (`mind.py`)
* **Needs**: social, rest, safety, purpose, privacy (0-100), driven by what happens (company, sleep, danger, getting something done, solitude).
* **Thoughts**: every change of sanity becomes a thought with a weight that fades. **Stress** is the weighted sum, scaled by stress vulnerability and the `stress_scale` dial plus deadline pressure.
* **Sanity** = a set point minus stress. It recovers on its own when nothing new hurts and needs are met; the old flat drain is replaced. Low sanity feeds madness (dark impulses, outbursts), slips, snapping and spree risk.
* **Engine-made turns**: a quiet turn (nothing at stake) is decided by `routine_decision` without a model call. The model is asked when something matters (a case, an event, a hazard, a rule, a plot, a crisis, a conflict, a bond, a missing plan, a heartbeat).

### The inner voice (`innervoice.py`, dial `hallucinations`)
Now and then the viewer sees what someone is thinking: a cloud over their head on the map and an italic line in the feed. The engine picks the thought from their state (a plot, someone they lost, someone who lied to them, a crush, the way out, hunger or tiredness, what hurt them, their traits, low sanity); there is no model call, and the picks draw from their own random stream so they do not change the run. Thoughts come more often right after a shock and the lower someone's sanity. Some are said out loud: often when alone, and, once sanity is under 40, muttered in company. A mutter is a quiet line that can be overheard; a plotter muttering about their target plants a rumour in whoever hears it.

Low sanity bends beliefs:

| Sanity | What happens |
|---|---|
| Below 40 | Now and then a belief is reread through fear: a sighting gets the wrong person, a rumour hardens into certainty, a friend's kindness becomes "they're setting me up". |
| Below 25 | Hallucinations, held with confidence: the dead walking a corridor, someone standing over the bed with a knife, TereVi whispering a name, someone in the room who was never there. After a body is found, a false memory of seeing someone at the scene. |
| Below 10 | They act on it: hiding, or deciding to strike first (a plot with the motive "paranoia"). |

These beliefs feed everything that reads beliefs, so a broken mind can give honest, false testimony at a trial. Hallucinations are kept like caught lies (vivid memories are not pushed out by new sightings). When sanity recovers to 35 and 15 above where it was, a hallucination may be seen for what it was, which stings. The GM view marks each one ("hallucination", "warped by fear", "seen through").

### Body (`conditions.py`, `nonlethal.py`)
Afflictions (sickness, poison, panic, blindness, breathlessness, dizziness, hunger, thirst, drunkenness, exhaustion, cold) and injuries (bleeding, burns, broken bones, concussion, infection). Unconsciousness (`out`) with a cause and an **absolute** wake-up time; the unconscious are helpless, can be carried, robbed, framed and revived, and are left out of scenes. Walking speed depends on health, conditions, load and dragging someone (`move_factor`). Hunger, thirst, bladder and hygiene run in the background and are met in free time.

### Modesty
Derived from facets (shy and orderly vs gregarious, vain, romantic). Being seen in underwear costs the modest sanity and an "embarrassed" event; the unselfconscious do not mind.

### The brain (`brain.py`, dial `brain`, off by default)
* **Memory**: everything a character perceives or does becomes a timestamped, scored memory about specific people (`agent["mem"]`). Walking about is not kept. A prompt gets the most relevant memories (recency, importance, people involved, room), not the whole log. The diary and the nightly "how I am changing" line are memories. The store is trimmed nightly.
* **Plans**: in a decision the model also writes up to three **intentions** (talk, go, work, search, avoid, wait). The free-time engine carries them out and ticks them off; the model is asked again only when the plan is used up, stale, or something big happens.
* **Conversations**: a scene card carries what each person remembers about the other and the reason from their plan.

---

## 7. Free time: the live part of the day

Called from `run_tick` for every daytime block, 08:00 to 20:00 (`freetime.py`, `FREE_HOURS`; phase B). The 08:00 block keeps TereVi's morning announcement; breakfast, lunch and dinner (and any summons) are called at their own minute inside the block (`_meal_in_block`): whoever comes stays at the table until the meal ends, and the table talks as one live conversation.

**Structure of a block (120 minutes)**: one decision per character becomes the first activity (15-90 minutes by action). Then 15-minute **slices**: the environment steps, then each free person chooses and starts an activity. Picks run to the end of the block (the last at minute 105; no new chat or gathering after minute 108). There is no separate conversation phase: talk happens live during the block, as chats (up to 3) and **gatherings**: when someone drifts over for company and finds idle people, they get talking as one group conversation at that minute (`_gather_check`; one per block, the table talk counts, two more while a death is investigated; each is a voicing call). TereVi on the monitor and occasions are still written whole after the block. **Pastimes** (`pastimes.py`, none of them voiced, so none costs a call): shared ones (a film in the lounge, the sunset, karaoke, cards, a campfire on the beach, taking pictures, a proper meal cooked for everyone) invite idle friends nearby, and someone starting one already going in that room joins it; how it went is decided at the end from who is there (a rival spoils it, a shy person dreads karaoke unless a close friend is there, the grieving think of the dead at sunset, a couple gets closer). **Talks**: two people talk about a subject, a person both feel strongly about (swapping stories, grumbling together, or falling out when they disagree) or something that happened (a recent death; during an investigation they also ask each other where they were, which gives testimonies and beliefs). **Alone**: a journal, a workout, sitting quietly, practising their talent, crying where nobody sees (anyone there remembers it), pacing, fishing, a letter home, sunbathing. Each changes sanity, needs or feelings a little; counts in `s["pastimes"]` and `docs/BALANCE.md`. While a death is investigated, pastimes other than talks count for 0.3 (`PREOCCUPIED`). **Choosing**: when nothing is pressing, any option within 0.12 of the best may be taken (`NEAR_UNTIL`), so the house does not all do the single top thing; someone walking somewhere far carries on there at the next pick, and a room they cannot get into is dropped for the block. **Shared games** (pool, chess, darts) have engine-made moments: a good shot midway, and a winner or a draw at the end, which warms the players to each other (a vain loser sulks).

**Activities with real durations** (a drink 15 minutes, a bathroom visit 15, a shower 30, a meal 30, a game 45, a nap 60, an experiment 90): eat, cook, snack, drink, wash, bathroom, shower, bath, swim, pool, chess, darts, music, jukebox, art, read, sit, stroll, tend plants, laundry, radio, stargaze, mirror, nap, tinker (craft), look, explore, dress, gather, chat, stalk, flee, rescue, fight (a fire), warn.

**Furniture and capacity**: activities are done *at* a particular piece of furniture (sofa, stove, chess table, armchair, bench...). Each piece has a capacity (a sofa 2, a table 4, a bed 1); nobody uses what is burnt, smashed or taken; other people's bedrooms are off limits.

**What people choose** (`free_pick`): scored candidates, highest wins:
* danger first (fire, smoke, flood in the room they are in), then dressing when half-dressed;
* bodily needs (hunger, thirst, bladder, hygiene, rest);
* personal tastes (each person has stable preferences per activity; nobody repeats the same activity three times running; the shy avoid crowded rooms);
* **intentions**: what they asked for in their decision, their plan (if the brain is on), a loose end (someone went through their things), looking for a weapon, rooms they have not visited today, work on a way out;
* company: who they want to talk to and why (see chats).

**Chats**: when somebody wants to talk to a specific person, they walk over and the two sit or stand together for 30 minutes at a seat (sofa, bench, armchair, table or the other person's spot). Reasons: a stated purpose, company, closeness, a quarrel, something one knows about the other (a secret), a loose end, a spark, a plan item. Chats that matter (a plot, a feud, a secret, a hook, a spark, a purpose) are flagged. At most 2 chats per block (3 with the brain on); nobody talks twice in a block; no chats in the bathroom or in a bedroom that is neither person's. The conversation is written when the block ends, but is played **at the minute and place it happened**.

**Plots, minute by minute**: a stalking or striking plotter follows the target room to room and strikes the moment the two are alone, in a blind spot, in the dark, or the target is asleep. Each missed chance makes them less patient. The **Director** (`director_nudge`) may steer a long-waiting plot's *target* towards a quiet corner (the bathroom, their bedroom); it never makes the kill.

**Snapping** (`snap_rate`): someone with almost no sanity left, or pushed past their limit beside someone they hate, may attack with no plan. A kill is recorded as unplanned in the case. (One case at a time: while a case is open it becomes an assault.)

---

## 8. Murder, evidence and the trial

### The claim-based trial (phase 7, `claimtrial.py`)
The engine runs the trial; the model only voices it (one call per sequence, templates otherwise; no call per voter).
* **Claims**: everyone says where they were at the minute of the death (the truth, from their own whereabouts; the culprit lies).
* **Weak points**: every claim is checked against every participant's beliefs. A claim that conflicts with what someone saw is a weak point; whether the holder raises it is a **willingness** roll (courage, how they feel about the speaker, how sure they are, alliances; an accomplice never gives the culprit away).
* **Lies and credibility**: a proven lie halves the liar's credibility. The culprit answers with the **lie planner** (a new room that fits what they think the room knows) or, when nothing fits, is **cornered** by temperament (indignant, tearful, silent, lashing out). The culprit never confesses.
* **The suspicion meter**: facts on the table move a public meter per suspect: clues that name someone, being seen near the scene, being seen carrying the weapon (the same kind of weapon counts a little; any other weapon not at all), earlier lies, an eye witness; a corroborated alibi, a frame flaw or being placed elsewhere by NeoVi's camera still lowers it. The viewer's trial panel shows it as "Evidence against".
* **Sequences**: open debate (alibis, clues, objections), the hot seat (the most suspected answers attackers and a defender), the clash (two people who suspect different people; the weaker case concedes), brainstorm (when nobody stands out: whoever has no witness for the time), closing arguments.
* **Cries**: whoever catches a contradiction shouts first ("Objection!", "Hold it!", "That's wrong!"...). A character can have a signature cry (cast field `objection`); otherwise it is picked at random, leaning on temperament. The cry is never reworded by the voice; the viewer flashes it on a card.
* **Cross-examination**: the accused tests the strongest witness against them: was it too dark to be sure, have they lied before, do they hate the accused? A witness with a weak spot falters, loses credibility and the case weakens; one without stands, and the case grows.
* **Split court**: when the room divides between two suspects, the two sides argue in turns and people on the weaker side cross over.
* **The climax**: before the vote, when one suspect clearly leads, the accuser tells the crime step by step (opportunity, means, the deed, the cover-up). A step with no fact behind it is a gap; the accused jumps on the first one, and gaps weaken the case.
* **Wounds and marks, read by eye** (`marks.py`): nobody on the island has a lab or can read fingerprints, so evidence on a body or a weapon is only what a person can see and compare. Everyone has visible traits (hand size, the hand they use, height; cast field `body`). The fight records where each blow landed, so examining the body (the Case File's "Wounds") tells which side the blows hit (so which hand the attacker used), whether head blows came from above (someone taller than the victim), finger bruises on a strangled throat (the size of the hand), defensive wounds on the forearms, and skin under the nails (the attacker has fresh scratches for a day or so). A bare hand on a bloody handle may leave a handprint of a size, or just a smear; gloves leave a fabric weave and are stained themselves. At the trial whoever examined the body compares: "Everyone, put your hands on the table", who uses that hand, who is taller, whose hands are scratched. Scratches have innocent causes too (thorns while tending the garden): an explanation holds if someone saw them in the garden that day; the killer's "thorns" story has nobody to back it up.
* **Looks and the traces they leave** (`looks.py`): everyone's looks follow their portrait: hair (Seul's long lavender hair, Ayden's dark brown locs, Cail's orange ponytail), eyes, build, an accessory always worn (Ayden's cross earring, Noah's fedora, Chloe's red-framed glasses, Cail's green ribbon, Szymon's red face scarf, Vixen's blue scarf), and an outfit with fabrics that shed fibres (Szymon's green parka, Shintaro's fur-collared jacket, Cail's sailor uniform...). The viewer's cast card shows them. A killing can leave the killer's hair in the victim's fingers (more likely in a struggle, less behind a mask or cloak), fibres of whatever they wore (someone else's clothes point at the owner; a coat at the coat), or their accessory near the body (and they are visibly without it). In the dark, people without a light glimpse a silhouette feature (a hood, a hat, a ponytail, a long coat, height); a cloak hides the hair. The prompts carry how each person looks right now (`looks_line`: their portrait's looks, what they actually wear, a missing accessory, scratches, bleeding or stained clothes), so the voices can notice them. At the trial each trace is held up against how everyone looks ("Whose hair is that?"); the fewer people it fits, the more it counts, and a hair that fits nobody clears them.
* **Truth against belief**: after the verdict the report shows what really happened, each vote, whether it was right, what each person held and what they kept to themselves. Someone who held a fact against the culprit, stayed silent and saw the vote go wrong remembers it and loses sanity.
* **A live practice**: the trial plays on the map. Everyone walks to the Voting Grounds from where they were, every line is on the clock (nobody speaks before they arrive), allies whisper (and can be overheard), and now and then the most rattled person slips out for a few minutes. The introductions, the reveal, the last call and the remembrance are live practices too (`scenes.py`): see below. Each piece of evidence is shown once, and each person names everyone they saw in one line.
* **The gatherings as live practices** (`scenes.py`): the introductions, the reveal, the last call and the remembrance work like the trial. The engine decides each beat, one call voices them, people walk in, the lines run on the clock, allies whisper and someone may step out. Introductions: everyone says who they are, most outgoing first, and someone who already likes or dislikes them may answer. The reveal: each reacts by temperament (panic, rage at the monitor, demanding a way out, distrust, silence); TereVi answers the first two challenges; a friend comforts the most shaken. The last call: the engine decides who volunteers to die (the most broken or the most selfless) and who means to strike when the lights go out (a plotter whose target is there, or else the cruellest and most desperate); a friend may refuse to let a volunteer go; the rest take a stance (drawing lots, bargaining with TereVi, protecting a friend, a dark joke, watching everyone's hands, despair, a plea, or turning on the one they like least). At the remembrance an executed killer is remembered as a betrayal, not mourned like a victim. The remembrance: each survivor speaks of the dead they were closest to (fondly, with regret, or, for the killer, with false grief); someone lights a candle; the closest pair hold each other.
* **Votes** are computed: the meter, plus what only the voter knows, minus affinity, plus the lead of people they trust; an accomplice never votes for the one they helped; a muddled mind may vote on a gut feeling. A tie means no verdict and the culprit escapes.
* The dial `claim_trial` (0) brings back the old trial, where the model writes the debate and casts the votes.

### Plans, fights and what people carry (phase 6)
* **The planner** (`planner.py`): when a plot starts preparing, the plotter settles on a scheme from what the world offers and what they have seen: the target **asleep** in their own room at night (better if they sleep alone), a place they saw the target **alone**, a **height** where the target goes (the first-floor gallery over the foyer, the garden cliffs) for a push that looks like a fall, or a **poison** they hold or know where to find. They strike in the planned place (and, for a night plan, at night), not wherever they happen to be, unless the deadline is on them or they have waited too long. A fatal push is a murder with the pusher as culprit.
* **Fights in blows** (`combat.py`): up to six exchanges. The attacker goes for a part of the body (throat or head on a sleeper, chest with a blade, head with something heavy, a grip on the throat with bare hands that only a struggle breaks); the defender blocks, dodges, struggles for the weapon, runs or screams. Every hit is a wound on a part (kept in the case for the autopsy); a struggle can leave scratches on the attacker. A victim can get away, be rescued by a scream, or take the weapon. Roughly: a sleeper almost never survives; an awake victim survives a blade about half the time, a blunt weapon two thirds, bare hands three quarters.
* **Hands and pockets** (`carry.py`): every item has a capability record from its tags (what it does: cut, bludgeon, poison, bind, light, burn, open, climb; its size; the traces it leaves). Large items and unhidden weapons are seen in the hand, and someone seen carrying a weapon is believed to have it (and suspected); small things stay in a pocket. A large item takes both hands. A hidden weapon has to be drawn first, so the target sees it coming. Whoever is knocked out or falls drops what they hold.
* **Night snooping and secret meetings** (`nightlife.py`): lovers, allies, and a plotter with an accomplice may meet in a quiet unwatched room in a night block; people with someone to suspect may stay up to search that person's room (and go through their things if they sleep there, which may wake them) or the scene of the death.
* **Silencing**: a gag (tape, rags, towels, a scarf, a pillow, an apron) or a hand over the mouth in the first moment of an attack, a grip on the throat, or being held under water (pool, bath, beach, water tower) keeps a victim from screaming for help. Someone knocked out can be gagged; they tear it off when they come round unless their hands are tied.
* **Stacking the odds**: fights are hard to win, so the planner also offers a **lure** (a target who trusts them is asked to a quiet room at night), a **trap** (a rigged fall, a poisoned drink or a blade, set while the plotter keeps away), **drowning** someone seen alone by the water, and **subduing first** (sleeping pills or something heavy, then finishing a helpless target). Plotters who mean to take someone awake fetch a gag first.
* **Evidence the cast can have** (`evidence.py`): the house cameras are TereVi's. Only NeoVi can show someone a still from the archive; anyone else's footage must come from a camera or tape recorder of their own (hidden in a room, it records who came and went or what was said). A line citing footage the speaker cannot have is cut.
* **TereVi's Case File**: the first piece of evidence when a death is announced: victim, where and by whom they were found, time and cause of death (or "withheld by TereVi"), wounds and weapon. Examining the body brings the time and wounds into the file, finding the weapon names it, and everyone is told; any clue can be updated the same way.
* **Gear** (`gear.py`): gloves (work, oven, rubber) keep a bare hand off the weapon: the handle shows a fabric weave instead of a bloody handprint, and the gloves are stained; a coat (raincoat, trench coat, jacket, bedsheet cloak) takes the blood instead of the clothes and becomes the evidence to get rid of; a bag (tote or duffel) hides up to three weapons that would be seen in the hand, but drawing from it takes a moment; a holster hides one and it comes out at once. New items: rubber gloves (kitchen, laundry), a duffel bag and a holster (boathouse). A careful (orderly) plotter fetches gloves first.
* **Combinations**: the planner combines items: a rope (or clothes line, cord, fishing line) to hang a helpless target from the gallery railing or a beam, staged as a suicide; sleeping pills and the bath to drown them, staged as an accident. The plotter fetches what the plan needs; staging leaves flaws a careful look finds, and the rope stays at the scene.
* **Captivity wear**: each dawn after the reveal lowers the level sanity recovers towards (the `wear` dial, default 2.8, scaled by stress vulnerability, floor 25), so a week's survivors average about 60.

### Plots (`plotting.py`)
Most people here are not born killers: the game makes them. Every plot has a cause (hatred, jealousy, the deadline, blackmail, revenge, fear, betrayal, humiliation, envy, protection, staying hidden), and an attack the model decides on needs a plot or a motive against that person; without one, they think about it and cannot go through with it. Only the twisted (a `twisted` trait, extreme cruelty, a nihilist or saboteur drive) or the broken (sanity under 15) can kill without a reason. A `yandere` trait (obsessive love) makes anyone the beloved warms to a rival worth killing, and a beloved who turns cold a target too.

A plot is a campaign with stages **brooding, preparing, stalking, striking** driven by the engine; the model may also write a plot step. Plots can be abandoned (calm, fondness) or hardened by the deadline.

**Motives** (the strongest decides): hatred, vengeance, urge, deadline, jealousy, blackmail, revenge for the wrongly condemned, retaliation (what was done to you while helpless), protection, exposure, silencing, ambition, greed (the keys), **fear** (somebody hurt you), **betrayal**, **humiliation** (a vain person seen undressed), **envy**, the **prize** (a single winner). A plot against someone who is already plotting against you is ten times less likely. There is **no cap** on plots at once; three or more can tip the house into a killing spree (`plot_pileup`).

### Attack resolution (`cases.py`, `mayhem.py`)
Weapon, poison or bare hands; the target must be there (an attacker may follow a target who slipped away); victims can counter-kill, protectors can step in (a "mercy" moment), the killer can hit the wrong person at low sanity, accomplices (lookout, alibi, cleanup, weapon) can help but are never tried. Exactly **one culprit** per trial; multiple killers only in a spree.

### Discovery
Whoever walks in first finds the body first, at the minute they walk in. A body is announced when three living people have physically found it, or forced by TereVi after 12 hours. Sooner: a **wellness check** at breakfast, lunch and supper (someone who is missed is knocked for; NeoVi opens a locked door). When the body is announced, **NeoVi unbolts the scene and TereVi's tape seals it** until the trial: nobody can lock or barricade it again.

### Evidence (`cases.py`, `forensics.py`)
Layered, solvable clues: the scene, the weapon and its provenance, a dropped trace, bruises, the camera archive (Foyer) and the bedroom door-lock log (the locked Study) which narrow the field without naming anyone, forensic clues (marks, blood, drag trails, burns), stained clothes (the killer's garment), framing flaws, planted evidence, and **red herrings**: other people's real quarrels, hatreds and threats against the victim. A garment's label may be fully readable, show only an initial, or be cut out; TereVi's single free clue never names the killer outright. The dial **`clue_clarity`** (default 0.8) shifts all of this.

### The class trial (`trial.py`)
At the Voting Grounds, up to five segments of: **open debate**, **hot seat** (when suspicion falls on someone), **clash** (two people with contradicting ideas), **brainstorm** (a baffling matter); closing arguments; a vote; a tally. The culprit lies and deflects and never confesses. A wrong vote executes an innocent and frees the killer. Evidence on the table is only what was actually found.

---

## 9. The world

### The map (`maps/`, `mapgen.py`, `gridmap.py`, `static/grid_map.json`)
**An island with a house on it, one tile to a metre, five levels.** Every level shares one 104 x 84 frame (basement -1, ground 0, first 1, second 2, roof 3), so a tile directly above another really is above it. The island is compact: every outbuilding is a short walk from the house, which keeps people within sight and earshot of each other.
* **Source files** in `murder/maps/`: one character plan per level (`<level>.txt`), a room-zone plan beside it (`<level>.zones.txt`) and `map.json` (zone codes, furniture with its width and height, secret passages, labels). `python -m murder.mapgen --force` redraws them; hand edits to the plans are kept otherwise.
* **The island**: a coastline ringed by deep and shallow water, sand and dunes, rocks and cliffs; woods, a hedge maze, lawns and a pool deck; outbuildings (greenhouse, generator shed, lighthouse ruin, boathouse with a jetty, the Voting Grounds) joined by paths and a boardwalk.
* **The house**: rooms sized from a 3 x 5 m bedroom (bedrooms 12-15 m², nothing indoors over 120 m²); ground floor (games room, pantry, kitchen, laundry, lounge, foyer, dining hall), first floor (eight bedrooms, landing, a gallery open to the foyer below, library, study, bathroom), second floor (master suite with balcony, music room, art studio, observatory, attic, a lower roof), roof (lookout and water tower), cellars (wine cellar, hall, boiler room, cold store).
* **The outdoor rooms** (phase E): "Outdoors" (`garden`: lawns, paths, coast), the **Garden Maze** (`maze`, a hedge ring west of the pool with one entrance on the north path, joined only to Outdoors; a hiding place "in a dead end of the maze"), and **the Woods** (`woods`, the north of the island: dense trees, one path to a clearing with an old camp, a firepit, a crate and the hammock; no camera; hiding "among the trees"). The camp has a hatchet and tin mugs, and a search of the crate can turn up an **old journal** from a past season: its notes on the currents and the lighthouse floor help the raft's provisions and launch and the search for the vault hatch, and it is kept, not used up. Under the leaves by the camp is a **trapdoor** (`SP-6`, hidden until found by searching the Woods): a ladder down into a branch of the smugglers' tunnel as far as the wine cellar's grate, which opens from the tunnel side without the iron key. Strolls, photos and meditation can happen in the Woods and the maze. An older save is fixed once (`map_v5` in `world.upgrade_state`): whoever stands where the Woods or the maze now are is put in that room, and a position on a new hedge or tree is dropped.
* **The boathouse** is the raft's workshop: the raft's materials and building are done there when someone can get in (its door is locked), else on the beach; the launch is always from the boathouse. As the build step passes 25, 50, 75 and 100% the raft in the boathouse is seen to grow (a frame of lashed barrels, a plank deck, a mast, a tarp sail; event `raft`, `escape.raft_stage`). It can be wrecked there (`escape.wreck_raft`: a fit of rage, or the decision `sabotage` with method `raft`): the build drops by 30, the launch by half, and builders who see it hold it against the wrecker. The boathouse's flares (and the Lookout's flare gun) help the transmit route's signal step; firing one is seen by everyone outdoors (event `flare`).
* **Secrets**: hidden passages (hidden tiles `h` that look like floor until discovered), among them the tunnel from the cellars to TereVi's core vault under the lighthouse.
* **The builder** reads the plans: doors are door tiles between zones, stairs are an up tile above a down tile (or ladder above ladder), secrets come from `map.json`. **The validator** checks that rooms sit on their level, every connection exists, locks are right, every room is reachable from the front door, furniture stands on floor in its own room, secret passages lead through, and rooms are furnished (at least 45% of the floor in use, hubs excepted).
* A **map editor** (Layers > Edit map, GM) paints any tile on any level and places or removes furniture; doors, stairs and hatches are protected; edits are validated and saved to `state/maps`.

### Scale (`scale.py`)
`MAP_SCALE` 1.0: a tile is a metre. A whisper carries 2 tiles, quiet speech 3.5, normal 8, loud 14, a shout 18; sight is 18 tiles in light, 7 dim, 2 dark; a room of more than 220 m² can hold separate conversations. Walking is 40 tiles a minute, 110 at full speed. Sight crosses levels only where the floor is open (`v` tiles, such as the gallery); sound passes a floor at a cost.

### Conversations (`social.py`, `convo.py`, `voice.py`)
**A conversation is a thing in the world**: members, a place (a seat, a spot, or the people themselves when they walk and talk), a reason, and exchanges a few minutes apart on the turn's clock while everybody else keeps moving. In each exchange somebody makes a **social move** on somebody else and the target replies; sometimes a third person takes a side. About twenty moves in six families: bonding (chat, joke, comfort, confide, flirt, gift), status (boast, mock, put down), information (probe, gossip, warn, reveal), conflict (accuse, threaten, confront), alliance (pact, recruit, teamwork) and deception (incite, feign; lies come as replies). A move's **willingness** comes from the speaker's nature, feelings and situation; it is rolled against the target's **receptivity** (their feelings toward the speaker, trust, mood, grievances) and lands, falls flat or backfires. The outcome changes the world at once: affinity, special moments that restore sanity, secrets, rumours, pacts and feuds, testimonies (from where people really were; the culprit lies), accomplices, gifts. **Between exchanges**: members who drift out of earshot leave and the talk ends when they part; a fight, a body or a fire cuts it short; somebody nearby with a reason (a friend in it, being talked about, curiosity, a grudge) walks over and joins. Friends who finish talking may **walk on together**, and a close friend at a loose end goes along when somebody sets off.
**Overhearing**: every line is checked against perception at its minute from where everybody actually stood: heard in full, half heard at the edge of earshot (a fragment), or only seen being said. Listening on purpose (spying, hiding) hears more; members who catch a listener get wary (they whisper and drop risky subjects). A line heard through a wall or a floor without seeing the speaker is remembered as a voice, named only if the listener knows it well. **The voice**: one model call per conversation writes one checked line per resolved beat; the template voice stands in for a missing or wrong line, and is the mock and zero-model voice.
**Turns and the voice prompt** (phase A): the next exchange opens with someone other than the last speaker; now and then (`social.HOLD_FLOOR`, 20%) the last speaker holds the floor, and the voice is told the line goes on and is not a reply. The voice prompt gives the time of day, a "(a few minutes later)" marker between exchanges, whom each line is said to, and each person's gender and pronouns. Looks reach a voice card only when notable (marks, someone else's or stained clothes, a missing accessory) or changed since the person's last scene (`looks.looks_notable`); a pet name or catchphrase at most once per person in a scene. **Confidences**: a partner or close friend rarely turns one away; the beat carries what is shared (their secret between people this close, which the listener then knows, otherwise what weighs on them most); a rebuff leaves a `rebuffed` tie that can come back as a confrontation. An action line dropped for naming an object nobody has is replaced by a plain spoken line, so no reply is left answering nothing.
**Speaking of people**: gossip, warnings and revealed secrets about a third person need cool feelings toward them (affinity 1 or lower) or a real reason (`social.grounds_against`: a lie caught, a weapon seen, harm done, a wrong, distrust or a settled fear), and are never said with that person in the conversation; whoever has spoken against someone in a scene does not turn warm on them in it (no comfort, confidence, flirt, gift, pact or feigned friendship). The voice is told how the speaker feels about whoever a beat is about.

### Tone (`tone.py`, dials `gore`, `flirt_level`, `banter_level`)
Every voice call reads one tone guide through the bible: mature, darkly funny and brutal at once. TereVi runs a game show (punishments as segments, sound cues, fake sponsors, ratings jokes); the cast's gallows humour, petty feuds and absurd mishaps sit next to the horror, and grief and fear are played straight. The `gore` dial (0 to 3, default 2) sets how graphic violence is, in the guide and in the engine's own body descriptions (0 none, 1 the first clause, 2 as written, 3 with an extra visceral detail). Sex happens between consenting adults whose feelings got there and is never explicit; `flirt_level` now defaults to 2.

### Love life (`intimacy.py`)
After lights out, lovers (a romance bond) may spend the night together; the feed implies it and cuts away. Two people who feel strongly about each other (both at 7 or more) and click may fall into bed for the first time and are lovers from then on. Both sleep better for it. At dawn one may be seen leaving the other's room: whoever sees it believes it, and anyone who wanted one of them is jealous (feelings toward the rival sour, a tie that feeds the jealousy plot motive). Someone in a romance who is drawn hard to someone else may have an affair; if the partner finds out, the romance ends in a row. How often follows `flirt_level` (0 = never).

### Rare turns (`twists.py`)
Engine events with a cause, rolled rarely, counted in `s["twists"]`:
* a death pact: when the last call ends in silence, two lovers with nothing left (both under 45 sanity, one under 35) go together; no trial, and the deadline is lifted;
* a murder-suicide: a lover under 20 sanity who believes the worst of the other (a warped or hallucinated belief, or an affair) kills them in the night and then themselves; no trial;
* at the trial, just before the vote: a guilt-sick killer confesses, someone who loves the killer takes the blame, or NeoVi, who saw it, names the killer to save an innocent (and TereVi punishes her afterwards);
* a raft at sea is carried back to the island, and its crew are participants again;
* a paranoid plot born of a hallucination (`innervoice.py`) that ends in a real killing.

### The confessional booth (`booth.py`)
A curtained box at the end of the first-floor gallery, over the foyer. What happens to people (being mocked or threatened, a moment with someone they like, a body, a plot coming together, a loss, fear) builds an urge to talk to the camera; when it is strong they walk to the booth in free time (or slip in late in a turn) and record one to three short lines, at most 14 words each, straight to the audience. The engine picks the subject; one call per turn words all the entries. Someone on the gallery, or in the foyer under its open floor, can overhear a confession.

### Positions and heights (`sim.py`, `falls.py`)
Everybody has a tile position, saved with the game. The engine walks people on the tiles as it moves them (A* through doors, stairs and, for those who know them, secret passages), at its own minute, so perception, witnesses and hearing ask where people actually stand, including on their way between rooms. A conversation is staged before its lines get minutes: its members walk to it and stay until their last line, so nobody speaks from another room. **Falls** take somebody from where they lose their footing to where they land (down the stairs, a ladder, through the gallery's open floor, from an upper window or the roof, over the cliff); damage follows the drop and the ground (water forgives, rock does not) through the injury system, and two storeys onto stone can kill. Causes: a slip on stairs or a ladder (likelier in the dark, on a wet floor, in a hurry, drunk, dizzy, hurt or frayed), jumping from a burning room with no way out, a failed climb down the wall. Somebody **locked in** climbs out through a window (easy on the ground floor, a climb from upstairs). A push from a height (`fall_from_edge` with a culprit) is ready for the murder planner.

### Perception (`perception.py`, dial `perception`)
Line of sight (walls and closed doors block; windows do not; smoke of 4 or more blocks), light (lit, dim, dark; power cuts), a sound flood-fill through doors, windows, walls and stairs by loudness, cameras (die with the power), witnesses (who saw or heard, and how), the plotter's "alone" test, and who can hear whom in a large space. This is what makes plot windows, eavesdropping and witnesses real.

### Environment (`environment.py`, `envsys.py`, dial `environment`)
Sparse fields on the tiles in five-minute steps: **fire** (spreads by flammability, burns furniture, doors and items, leaves soot and scorched floor), **water** (extinguishes, flows, bursts from pipes, shorts the fuse box), **smoke** (through doors, blocks sight, chokes), **light**, **noise**, breakage (doors and furniture take damage), blood and **marks** that become clues. Hazards: grease fires, lightning, burst pipes, failed experiments, scheduled scenario events. Accidental fires are rare; intentional ones are not.
**Fire consequences** (dial `fire_lethality`): at every five-minute step each person in a burning or smoky room may wake, run, or stay; those who stay take heat and smoke damage, may be burned, blinded, panic, or collapse; the unconscious cannot flee and can die; the brave rescue the collapsed, fight small fires with extinguishers or water, and wake sleepers. Awake healthy people usually get out; sleepers, the hurt and the unconscious often do not.

### Doors, locks and stealth (`doors.py`, `stealth.py`, `secrets.py`)
Per-room locks, keys (spare keys, skeleton keys, master key), picking, breaking, barricading (with furniture or even a body), noise that wakes sleepers, a door-lock log, sneaking, hiding, spying and eavesdropping, stashing and retrieving items, hiding bodies, concealed carry and frisking, withheld clues and knowledge that crack under pressure.

### Items, crafting and clothes (`data_items.py`, `craft.py`, `clothing.py`, `itemuse.py`)
Room item pools, unlimited common supplies per room, recipes with ingredients and tools (a crafted item is traceable), light and optics, handcuffs, tape, snares. Everyone owns their own clothes, a wardrobe and a swimsuit; underwear is a state; killers stain their clothes and change out of them; disguises and masks alter who is recognised.

### Hooks, ties and alliances (`hooks.py`, `ties.py`, `alliances.py`)
**Hooks** are loose ends that grow from real events (someone rifled your things, a lock was picked, an item vanished, a hiding place was found); they have a culprit, evidence and a victim who may suspect the wrong person. **Ties** record who wronged, helped or loved whom. **Alliances** form between trusting people and can be broken.

---

## 10. Rules, events and scenarios

* **Daily rule**: TereVi's model invents a fresh rule each day from the current drama (or the player types one, or none, or a coded preset). An AI referee classifies it (zone, obligation, state, behaviour), judges each turn with a grace turn, and NeoVi punishes clear violations (taser: heavy health and sanity loss; or detention in the Cold Store).
* **Island events**: storm, fog, a cat, a package, blackouts, fires and floods; they last a number of **hours** (stored in absolute time).
* **Scenarios** (`scenario.py`, `scengen.py`): premise, a secret twist TereVi reveals on a day, house rules, seeded items and a shorter first deadline, plus **scheduled events that really fire** (blackout, fire, flood, storm). `scengen.generate(seed, difficulty)` composes them from weighted parts under a budget. Scenarios never seed relationships or edit the cast.

---

## 11. Where the model is used and where it is not

| Done by the **engine** (deterministic or dice) | Done by the **model** |
|---|---|
| Time, positions, pathing, furniture, durations | Decisions on non-routine turns (action, intent, a plan) |
| Needs, stress, sanity, conditions, hunger | Conversations (speech, small gestures, affinity changes, special moments) |
| Perception, witnesses, windows, noise, light | TereVi's and NeoVi's speech and meddling |
| Fire, water, smoke, breakage | The daily rule and the referee's reading |
| Plot stages, strikes, snaps, spree, attack odds | Experiment narration (the dice decide the outcome) |
| Clues, evidence, discovery, locks, sealing | Trial debate and votes |
| Routine turns and free-time activities | The nightly reflection (diary, drive, arc) |
| Memory store and retrieval; plan execution | Recaps, awards, newcomer development |
| Checking every proposal against the world | Proposed plans and social moves (a few a day) |

**Backends** (`llm.py`): `cli` (default: `claude -p`, Haiku 5.5 for characters, Sonnet 5.5 for TereVi, `--effort low`), `api` (needs credits), `mock` (scripted, free; the test backend). Calls run in parallel threads; a call cap and "lean prompts" setting exist. An `ANTHROPIC_API_KEY` in the environment is stripped from every CLI call so the subscription is used.

**Cost per real day** (one measured per setup): 56-94 calls, $1.9-3.4. Biggest levers: the `engine_decisions` and `brain` dials (fewer decision calls), the confessional booth (off saves calls), lean prompts and the call cap.

---

## 12. The viewer

`static/index.html`, `app.js` (playback, panels), `tilemap.js` (the map), `style.css`; a Python stdlib server (`server.py`).

* **Tile map**: every level drawn side by side (the island on the left, the house's other levels in a column beside it); zoom presets (whole map, island, house, levels, the selected person's room) and level buttons; a search box for people, rooms and items; a minimap; a **Talking now** panel; pings where events happen and arrows at the screen edge pointing to what is off it; clicking a feed event or a roster row goes there. Portrait tokens walk real routes; day, night and light overlays; fire, smoke, water, marks and items on tiles; GM view shows hidden hatches, concealed items, thoughts, plans and memories. The **Who's where** roster (on by default) lists each person's room, activity and last words.
* **Playback**: pause, speed 0.5x-8x, scrubber (rewind), fast-forward the day. A **Pace** box sets real time per game hour (Normal is 2 minutes, about 28 minutes per game day, so a walk across the house takes a few seconds). Every turn plays as one continuous stretch of game minutes: things happen at their minute, conversations are played where and when they happen, and nobody stops while others talk; when lines come faster than they can be read, the clock slows down instead. **Dead air** (minutes in which nobody walks and no conversation is going on) plays at the quick-clock speed from the pause settings (4x by default, or 8x, or off): at Normal pace a day's daytime takes about 17 minutes instead of 28. **Block starts do not stop the clock**: the title card shows over the running map, and in the live player TereVi's broadcasts play inside the block at its first minutes (the banner shows and she speaks while the clock creeps on, as with a line). The daily rule's roulette at 08:00 is still a short staged moment. The engine runs two turns ahead of playback, so model calls usually finish before their moment is shown; while it is still busy the viewer says so, with the seconds waited and the model calls made so far.
* **Pause settings**: which events pause the game, per class (critical, important, notable, background) and per kind, as a dialog, a small notice, or feed only; whether **conversations in free time** pause (never, when it matters, every one); whether the **segment title card** shows; the **quick clock** for dead air. Stored in the browser.
* **Conversations on the map**: speech bubbles at the speaker; a dashed line from each listener to the speaker while a line is overheard (faint when half heard); in GM view the feed names who overheard each line; booth confessionals appear at their minute as a short REC card and a bubble at the booth.
* **Panels**: Feed, Cast (stats, needs, thoughts, plan, memories in GM view), Web (relationships), Booth (confessionals), Room, Board (evidence corkboard), Stats, Chronicle (a typed, searchable, persistent log of everything), Tuning (the dials), Director.
* **Phone and remote**: `start_remote.bat` (`python server.py --host`) listens on the network behind a 4-digit PIN kept in `state/remote.json` (HMAC cookie that survives restarts; five wrong tries lock a device for fifteen minutes, twenty in an hour lock every device; the PC itself is never asked; `--password` or `MC_PASSWORD` replaces the PIN), with touch controls and a phone layout; used over Tailscale, never port-forwarded. The PC must stay on.
* Optional **sound** (stings, a dread drone) and browser **voices** (a different voice per character).

---

## 13. Tuning dials (Tuning panel; saved in `state/tuning.json`, read live)

| Group | Dials |
|---|---|
| Drama | quarrels, clue clarity, murder plots starting, alliances, betrayals, noticing something is wrong, NeoVi's daily inspection, Director opportunities, snapping |
| Pacing | escape attempts per day |
| Sanity | everyday drain, deadline dread, calm window after a death, remembrance lift |
| Night | locking doors |
| Body | afflictions, injuries, fainting and knockouts, hunger and thirst |
| World | sight and hearing, fire/water/smoke/breakage, needs/thoughts/stress, stress strength, engine-made routine turns, pursuit/witnesses/interrogation, memory and plans (brain), fire and smoke danger, free-time blocks |
| Tone | embarrassment, flirtation, banter and crude jokes |

Each layer that has an on/off dial returns to the older behaviour at 0.

---

## 14. Data, saves and tools

* **Saves**: `state/current.json` (the live world, committed when a day finishes), `state/day_NN_start.json` (the start of each day, for "go back to that day's start"), save slots, `runs/day_NN/ticks.jsonl` + `meta.json` (every tick as played, for replay and analysis), `state/tuning.json`, `state/grid_map.json` (a custom map), `rules_seen.jsonl`. Set `MC_DATA_DIR` to keep tests and experiments away from your save.
* **Chronicle**: every event becomes a typed entry (id, day, hour, minute, type, who, room, visibility, class, text, who is named, who saw it); `/api/chronicle` and the Chronicle tab are views over it. Importance classes (critical, important, notable, background) drive the pause dialogs.
* **Tests** (`tests/`): `smoke.py` (about 760 checks, mock backend), `free_day.py` and `brain_compare.py` (mock days with statistics), `week_metrics.py` (mock weeks), and real-AI checks (`real_day.py`, `real_free_day.py`, `real_brain_day.py`, `real_stage_day.py`, `real_scenario_day.py`) that use a scratch data folder.
* **Run**: `start.bat` (local, `http://localhost:8766`) or `start_remote.bat` (network, password). Start a day from the dialog: backend (Claude subscription, API, mock), pace of the day, murders on/off, TereVi's mischief, season length, chaos level, lean prompts, call cap.

### Code map (`murder/`)
Engine and turn: `engine.py`, `world.py`, `cases.py`, `trial.py`, `story.py`, `drama.py`, `chaos.py`, `mayhem.py`, `night.py`, `aftermath.py`, `reaction.py`, `pace.py`. Characters: `mind.py`, `brain.py`, `conditions.py`, `nonlethal.py`, `clothing.py`, `plotting.py`, `crime.py`, `hooks.py`, `ties.py`, `alliances.py`. World: `gridmap.py`, `gridnav.py`, `perception.py`, `environment.py`, `envsys.py`, `doors.py`, `stealth.py`, `secrets.py`, `craft.py`, `itemuse.py`, `scale.py`. Free time: `freetime.py`. Time and positions: `clock.py`, `sim.py`, `falls.py`. Talk: `social.py`, `convo.py`, `voice.py`, `booth.py`. Rules and scenarios: `rules.py`, `refcheck.py`, `scenario.py`, `scengen.py`. Infrastructure: `llm.py`, `session.py`, `settings.py`, `telemetry.py`, `chronicle.py`, `export.py`, `director.py`, `tone.py`. Data: `data_cast.py`, `data_world.py`, `data_items.py`. Everything is mixed into one `DayRunner`.

---

## 15. Known limits and what comes next

* **Beliefs** (phase 5) do not yet drive night snooping or secret meetings, and testimony only covers where someone was at the time of a death. The trial still reads the old testimony; the claim-based trial (phase 7) will argue over beliefs.

* **Real-model coverage**: the brain, the harder trial, the sealed scene and the new motives have been exercised on the mock backend and on two calm real days; a full real week with a murder and a trial on the new map has not been played yet.
* **Brain**: off by default; plan completion was about a third on real days; retrieval is simple scoring (recency, importance, people), with no separate reflection call beyond the nightly diary.
* **Map**: a custom map saved before map v4 is rejected and the generated one used.
* **Time**: decisions are still made at the start of each two-hour turn (and every quarter hour in free time); the turn then plays out minute by minute. Conversations are written whole when the turn's gathering comes, so a chunk streamed to the viewer is a whole turn; live conversations (joinable, interruptible, overheard) are the next phase. Turn-level systems (drains, friction) still run once per turn rather than hourly; deadline-day dread is charged per hour. Special turns (trial, presentations, finales, night) carry minutes only for what the position simulation stages.
* **Talk**: staged scenes (occasions, TereVi on the monitor, trial, reveal, finales, last call, vigil) are still written whole by the model, whose effects are applied as before; everything else is resolved move by move by the engine. What people overhear goes into their memories as text; belief bases with confidence (phase 5) will make it something they reason with. People join a conversation when they can hear it, are in the same room, can see it from a distance with a reason to come over, or have been wanting a word with one of its members; in free time somebody at a loose end may also choose to go and join friends who are talking nearby. About one conversation in six gains a joiner in mock weeks.
* **Fire**: awake healthy people almost always escape; if you want deadlier fires, raise `fire_lethality` or slow the first reaction.
* **Not built**: continuous per-minute decisions by the model (decisions are per block, with the engine playing the minutes between); NeoVi and TereVi walking on the map; breaching weak walls (deferred by decision); a fully AI-written pause-on-conversation summary.
* **Next steps considered**: play several real days to a trial and tune `clue_clarity`, plot completion and chat limits; make the brain the default once a few days confirm it; add more interactables and richer reasons for conversations.
