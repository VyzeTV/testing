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

### The player's tools
Director panel (whisper to someone, spread a rumour, drop an item, force a twist, island events), an optional **auto-director** that nudges quiet days, scenario editor and a **scenario generator** (premise, secret twist, rules, scheduled events under a difficulty budget), save slots, rewind/export, "Previously on" recap.

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

**Escape routes** (`routes.py`): each has a plan with steps and percentages (e.g. transmitter, power, signal position, proof, beating the jamming), advanced by **experiments**; a finale at a site (the Lighthouse, the Core Vault, the beach, the Study) can succeed or fail with consequences. TereVi hears of attempts and counters them.

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

Called from `run_tick` for blocks at 10, 14, 16 and 20 (`freetime.py`).

**Structure of a block (120 minutes)**: one decision per character becomes the first activity (15-90 minutes by action). Then 15-minute **slices**: the environment steps, then each free person chooses and starts an activity. The last half hour leans towards company; at minute 90+ nobody sets out anywhere new, so the conversation phase (about minute 95) finds people where they are.

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
* **Truth against belief**: after the verdict the report shows what really happened, each vote, whether it was right, what each person held and what they kept to themselves. Someone who held a fact against the culprit, stayed silent and saw the vote go wrong remembers it and loses sanity.
* **A live practice**: the trial plays on the map. Everyone walks to the Voting Grounds from where they were, every line is on the clock (nobody speaks before they arrive), allies whisper (and can be overheard), and now and then the most rattled person slips out for a few minutes. The meeting, the reveal, last call and the vigil also start the live map, so people walk in. Each piece of evidence is shown once, and each person names everyone they saw in one line.
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
* **Secrets**: hidden passages (hidden tiles `h` that look like floor until discovered), among them the tunnel from the cellars to TereVi's core vault under the lighthouse.
* **The builder** reads the plans: doors are door tiles between zones, stairs are an up tile above a down tile (or ladder above ladder), secrets come from `map.json`. **The validator** checks that rooms sit on their level, every connection exists, locks are right, every room is reachable from the front door, furniture stands on floor in its own room, secret passages lead through, and rooms are furnished (at least 45% of the floor in use, hubs excepted).
* A **map editor** (Layers > Edit map, GM) paints any tile on any level and places or removes furniture; doors, stairs and hatches are protected; edits are validated and saved to `state/maps`.

### Scale (`scale.py`)
`MAP_SCALE` 1.0: a tile is a metre. A whisper carries 2 tiles, quiet speech 3.5, normal 8, loud 14, a shout 18; sight is 18 tiles in light, 7 dim, 2 dark; a room of more than 220 m² can hold separate conversations. Walking is 40 tiles a minute, 110 at full speed. Sight crosses levels only where the floor is open (`v` tiles, such as the gallery); sound passes a floor at a cost.

### Conversations (`social.py`, `convo.py`, `voice.py`)
**A conversation is a thing in the world**: members, a place (a seat, a spot, or the people themselves when they walk and talk), a reason, and exchanges a few minutes apart on the turn's clock while everybody else keeps moving. In each exchange somebody makes a **social move** on somebody else and the target replies; sometimes a third person takes a side. About twenty moves in six families: bonding (chat, joke, comfort, confide, flirt, gift), status (boast, mock, put down), information (probe, gossip, warn, reveal), conflict (accuse, threaten, confront), alliance (pact, recruit, teamwork) and deception (incite, feign; lies come as replies). A move's **willingness** comes from the speaker's nature, feelings and situation; it is rolled against the target's **receptivity** (their feelings toward the speaker, trust, mood, grievances) and lands, falls flat or backfires. The outcome changes the world at once: affinity, special moments that restore sanity, secrets, rumours, pacts and feuds, testimonies (from where people really were; the culprit lies), accomplices, gifts. **Between exchanges**: members who drift out of earshot leave and the talk ends when they part; a fight, a body or a fire cuts it short; somebody nearby with a reason (a friend in it, being talked about, curiosity, a grudge) walks over and joins. Friends who finish talking may **walk on together**, and a close friend at a loose end goes along when somebody sets off.
**Overhearing**: every line is checked against perception at its minute from where everybody actually stood: heard in full, half heard at the edge of earshot (a fragment), or only seen being said. Listening on purpose (spying, hiding) hears more; members who catch a listener get wary (they whisper and drop risky subjects). A line heard through a wall or a floor without seeing the speaker is remembered as a voice, named only if the listener knows it well. **The voice**: one model call per conversation writes one checked line per resolved beat; the template voice stands in for a missing or wrong line, and is the mock and zero-model voice.

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

**Backends** (`llm.py`): `cli` (default: `claude -p`, Haiku 5.5 for characters, Sonnet 5.5 for TereVi, `--effort low`), `api` (needs credits), `mock` (scripted, free; the test backend). Calls run in parallel threads; a call cap and "lean prompts" setting exist. An `ANTHROPIC_API_KEY` in the environment is stripped from every CLI call so the subscription is used.

**Cost per real day** (one measured per setup): 56-94 calls, $1.9-3.4. Biggest levers: the `engine_decisions` and `brain` dials (fewer decision calls), the confessional booth (off saves calls), lean prompts and the call cap.

---

## 12. The viewer

`static/index.html`, `app.js` (playback, panels), `tilemap.js` (the map), `style.css`; a Python stdlib server (`server.py`).

* **Tile map**: every level drawn side by side (the island on the left, the house's other levels in a column beside it); zoom presets (whole map, island, house, levels, the selected person's room) and level buttons; a search box for people, rooms and items; a minimap; a **Talking now** panel; pings where events happen and arrows at the screen edge pointing to what is off it; clicking a feed event or a roster row goes there. Portrait tokens walk real routes; day, night and light overlays; fire, smoke, water, marks and items on tiles; GM view shows hidden hatches, concealed items, thoughts, plans and memories. The **Who's where** roster (on by default) lists each person's room, activity and last words.
* **Playback**: pause, speed 0.5x-8x, scrubber (rewind), fast-forward the day. A **Pace** box sets real time per game hour (12 minutes per game day by default). Every turn plays as one continuous stretch of game minutes: things happen at their minute, conversations are played where and when they happen, and nobody stops while others talk; when lines come faster than they can be read, the clock slows down instead. The engine runs a turn ahead of playback, so model calls finish before their moment is shown.
* **Pause settings**: which events pause the game, per class (critical, important, notable, background) and per kind, as a dialog, a small notice, or feed only; whether **conversations in free time** pause (never, when it matters, every one); whether the **segment title card** shows. Stored in the browser.
* **Conversations on the map**: speech bubbles at the speaker; a dashed line from each listener to the speaker while a line is overheard (faint when half heard); in GM view the feed names who overheard each line; booth confessionals appear at their minute as a short REC card and a bubble at the booth.
* **Panels**: Feed, Cast (stats, needs, thoughts, plan, memories in GM view), Web (relationships), Booth (confessionals), Room, Board (evidence corkboard), Stats, Chronicle (a typed, searchable, persistent log of everything), Tuning (the dials), Director.
* **Phone and remote**: `start_remote.bat` (`python server.py --host`) listens on the network behind a password (HMAC cookie, lockout after repeated failures; the PC itself is never asked), with touch controls and a phone layout; used over Tailscale, never port-forwarded. The PC must stay on.
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
