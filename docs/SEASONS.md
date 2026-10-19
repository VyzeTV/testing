# Whole mock seasons

40 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (20 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 15 (38%), bittersweet 13 (32%), bad 12 (30%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 9, bittersweet 5, bad 6.
- **NeoVi's fate:** none 7, participant 5, martyr 5, betrayer 3. Romances at the end: 13 in all.
- **Kumiko:** helped the cast 102 times; told someone her real name in 19 seasons; a romance with someone in 16; punished: re-education 5, humiliation 4, participant 1.
- **Minds:** 2438 thoughts shown; 54 beliefs warped by fear, 20 hallucinations, 17 false memories of a crime scene, 10 seen through later; acted on: 1 paranoid plots, 7 hid; 5 plotters overheard muttering; 12 trials heard testimony from a broken mind.
- **Rare turns:** neovi defects 3, raft returned 3, confession 2, killer helps 1.
- **Love life:** 61 nights together, 9 affairs (2 found out), 6 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 2, someone never came out of the house 1, NeoVi gave her life for it 1, TereVi took someone with her 1, one survivor or fewer walked out of the house 1.
- **Killers the show let go:** 10; 1 tried to help from outside (believed 0, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 4 seasons, as a punishment in 1. Seasons that ran the full 28 days: 4.
- **Stories that formed** (story sifting): enemies alone 192, secret held 172, plot 96, near freedom 87, triangle 84, betrayed protector 77, silent witness 50, plot suspected 40, grudge 23, contradiction fear 19, unrequited 9, alliance strain 4, lovers breaking 3.
- **Season length:** median 16.0 days (shortest 5, longest 28).
- **How seasons ended:** THE SHOW SURRENDERS 6, THE LAST BATTLE 4, RESCUE 4, TEREVI IS SHUT DOWN 2, CROWNED BY WHIM 1, THE WINNERS 1, THE RECKONING 1, THE LAST ONE STANDING 1.
- **Deaths per season:** 8.0 on average. Causes: murdered 41, executed after the trial 35, escaped on a raft 23, escaped the island 10, died in the final battle 10, wrongly executed 9, died in the Reckoning 8, killed 7.
- **Trials:** 45 in all, 35 right verdicts.
- **Newcomers:** 3.9 per season on average; 48 of the survivors were newcomers.
- **Rafts launched:** 15 (believed 6, sea 4, returned 3, ashore 1, silenced 1). Rescue countdowns started: 6.
- **Ways out at the end:** the furthest route reached 75% on average (best 100%).
- **Who walked out alive (seasons):** Dario 9, Ilya 9, Mara 9, Chloe 8, Bram 6, Vixen 6, June 4, Noah 4, Teo 4, Ayden 3, Cail 3, Shintaro 3, Kumiko 3, Rosa 3, Seul 3, Szymon 2, Hana 2, Felix 1, Nadia 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 28 | CROWNED BY WHIM: BRAM | bad | Bram | 15 | 7 | 4 (3) |
| 2 | 18 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Dario, Ilya, June, Mara | 5 | 4 | 2 (2) |
| 3 | 14 | THE LAST BATTLE: ILYA STANDS | bad | Ilya | 9 | 2 | 2 (1) |
| 4 | 11 | TEREVI IS SHUT DOWN | good | Cail, Dario, Ilya, Noah, Shintaro, Vixen | 4 | 2 | 1 (1) |
| 5 | 16 | THE LAST BATTLE: TEO STANDS | bad | Teo | 12 | 5 | 3 (2) |
| 6 | 28 | THE LAST BATTLE: KUMIKO STANDS | bad | Kumiko | 15 | 7 | 4 (4) |
| 7 | 28 | THE WINNERS | bittersweet | Bram, Dario, June, Kumiko, Mara, Teo | 10 | 7 | 4 (4) |
| 8 | 17 | RESCUE | bittersweet | Bram, Dario, Ilya, Mara | 8 | 4 | 2 (1) |
| 9 | 14 | THE SHOW SURRENDERS | bittersweet | Ayden, Chloe, Szymon, Vixen | 4 | 0 | 1 (1) |
| 10 | 14 | RESCUE | good | Chloe, Dario, Ilya, Noah, Vixen | 5 | 2 | 1 (1) |
| 11 | 23 | THE SHOW SURRENDERS | good | Bram, Dario, Felix, Hana, June, Mara, Rosa, Teo | 9 | 9 | 3 (3) |
| 12 | 23 | TEREVI IS SHUT DOWN | bittersweet | Bram, Dario, Hana, Ilya, June, Mara, Rosa | 8 | 7 | 3 (2) |
| 13 | 9 | RESCUE | good | Chloe, Dario, Ilya, Mara, Seul, Vixen | 5 | 3 | 1 (1) |
| 14 | 10 | THE LAST BATTLE: CHLOE STANDS | bad | Chloe | 7 | 0 | 2 (1) |
| 15 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 16 | 24 | THE SHOW SURRENDERS | good | Bram, Dario, Kumiko, Mara, Nadia, Rosa | 11 | 8 | 4 (1) |
| 17 | 14 | RESCUE | good | Chloe, Ilya, Mara, Vixen | 6 | 2 | 1 (1) |
| 18 | 28 | THE LAST ONE STANDING | bittersweet | Teo | 14 | 6 | 5 (4) |
| 19 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 20 | 16 | THE SHOW SURRENDERS | good | Chloe, Ilya, Mara, Noah, Seul, Shintaro | 4 | 2 | 2 (2) |

## Violent mock cast

- **Ending tiers:** good 6, bittersweet 8, bad 6.
- **NeoVi's fate:** participant 9, none 7, martyr 3, betrayer 1. Romances at the end: 7 in all.
- **Kumiko:** helped the cast 48 times; told someone her real name in 13 seasons; a romance with someone in 7; punished: participant 1, re-education 1, humiliation 1.
- **Minds:** 1827 thoughts shown; 30 beliefs warped by fear, 9 hallucinations, 11 false memories of a crime scene, 8 seen through later; acted on: 0 paranoid plots, 3 hid; 10 plotters overheard muttering; 9 trials heard testimony from a broken mind.
- **Rare turns:** took blame 6, killer helps 3, confession 3, killer believed 2.
- **Love life:** 43 nights together, 1 affairs (1 found out), 7 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 5, one survivor or fewer walked out of the house 4, NeoVi gave her life for it 2, someone never came out of the house 1.
- **Killers the show let go:** 27; 3 tried to help from outside (believed 2, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 8 seasons, as a punishment in 1. Seasons that ran the full 28 days: 1.
- **Stories that formed** (story sifting): plot 158, secret held 101, triangle 94, near freedom 92, enemies alone 80, silent witness 80, betrayed protector 65, plot suspected 58, contradiction fear 37, grudge 20, unrequited 8, alliance strain 6, lovers breaking 2.
- **Season length:** median 13.0 days (shortest 5, longest 28).
- **How seasons ended:** THE LAST ONE STANDING 4, TEREVI IS SHUT DOWN 3, THE SHOW SURRENDERS 3, RESCUE 3, THE LAST BATTLE 3, CROWNED BY WHIM 2, NOBODY LEFT 1, THE WINNERS 1.
- **Deaths per season:** 9.9 on average. Causes: murdered 63, executed after the trial 43, escaped the island 27, wrongly executed 22, killed 14, escaped on a raft 11, died in an accident 8, died in the final battle 5.
- **Trials:** 70 in all, 43 right verdicts.
- **Newcomers:** 3.8 per season on average; 27 of the survivors were newcomers.
- **Rafts launched:** 6 (believed 3, sea 3). Rescue countdowns started: 5.
- **Ways out at the end:** the furthest route reached 68% on average (best 100%).
- **Who walked out alive (seasons):** Ilya 5, Mara 5, Hana 4, June 4, Kumiko 4, Ayden 3, Vixen 3, Dario 3, Seul 3, Noah 2, Rosa 2, Teo 2, Cail 2, Shintaro 2, Felix 1, Bram 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 13 | TEREVI IS SHUT DOWN | bittersweet | Ayden, Vixen | 8 | 2 | 3 (3) |
| 2 | 11 | THE SHOW SURRENDERS | good | Dario, Ilya, Mara, Noah, Seul, Vixen | 5 | 3 | 1 (0) |
| 3 | 23 | THE LAST ONE STANDING | bittersweet | Rosa | 16 | 8 | 5 (3) |
| 4 | 21 | CROWNED BY WHIM: FELIX | bad | Felix | 17 | 9 | 6 (3) |
| 5 | 26 | RESCUE | good | Hana, June, Kumiko, Teo | 13 | 8 | 4 (2) |
| 6 | 24 | THE LAST BATTLE: AYDEN STANDS | bad | Ayden | 14 | 6 | 5 (4) |
| 7 | 13 | TEREVI IS SHUT DOWN | bittersweet | Cail, Ilya | 7 | 1 | 2 (2) |
| 8 | 10 | THE LAST BATTLE: JUNE STANDS | bad | June | 10 | 3 | 3 (1) |
| 9 | 10 | THE LAST ONE STANDING | bittersweet | Dario | 10 | 3 | 3 (1) |
| 10 | 5 | THE SHOW SURRENDERS | good | Ayden, Seul, Shintaro | 5 | 0 | 2 (1) |
| 11 | 14 | TEREVI IS SHUT DOWN | good | Ilya, June, Mara | 9 | 3 | 4 (3) |
| 12 | 11 | THE LAST ONE STANDING | bittersweet | Vixen | 8 | 1 | 3 (1) |
| 13 | 24 | RESCUE | bittersweet | Bram, Hana, Kumiko, Rosa, Teo | 12 | 8 | 4 (3) |
| 14 | 22 | NOBODY LEFT | bad | none | 13 | 4 | 5 (3) |
| 15 | 12 | RESCUE | good | Hana, Ilya, June, Kumiko, Mara | 9 | 5 | 4 (2) |
| 16 | 13 | THE LAST BATTLE: CAIL STANDS | bad | Cail | 9 | 2 | 3 (1) |
| 17 | 28 | THE WINNERS | bittersweet | Dario, Hana, Ilya, Kumiko | 11 | 6 | 5 (4) |
| 18 | 10 | THE LAST ONE STANDING | bittersweet | Mara | 9 | 2 | 3 (3) |
| 19 | 12 | CROWNED BY WHIM: MARA | bad | Mara | 9 | 2 | 3 (2) |
| 20 | 6 | THE SHOW SURRENDERS | good | Noah, Seul, Shintaro | 5 | 0 | 2 (1) |

## Notes on this run (2026-10-19, phase E: the Woods, the Garden Maze and the raft workshop)

- Tiers: 38% good, 32% bittersweet, 30% bad (the last run: 42/32/25).
- A first run gave 78% good: raft work was sent to the boathouse first, but its door is locked, so raft workers stalled and the group's momentum moved to the ultimatum, which finished in four days. Work now goes to the first work room the person can reach (the beach while the boathouse is locked); the launch still needs the boathouse.
- Except the launch: it stays in the boathouse, as it always was (the boats are there, so getting in is part of the way out). Letting the launch fall back to the beach too made raft escapes in the first week common.

## Notes on an earlier run (2026-10-19, phase C: intrusions and waking)

These notes are written by hand and are not regenerated.

- Tiers: 42% good, 32% bittersweet, 25% bad. With intrusions first on they were 50/32/18: people woken in the night foil some killings (deaths per season 6.5 to 5.9), so more seasons last until the ultimatum works ("THE SHOW SURRENDERS" 8 to 14). The ultimatum's pace (`escape.PACE`) went from 0.7 to 0.55.
- Season verdicts: 16 of 28 and 40 of 64 right (61% in all; the last run 69%). Over 60 mock weeks (seeds 101-130) the share went the other way, from 61% to 72%, so the change is within the noise; a woken owner remembering who was in their room is new evidence for the trial.

## Notes on an earlier run (2026-10-19, phase A and B follow-ups: consistent talk about people, pastimes)

These notes are written by hand and are not regenerated.

- Tiers: 35% good, 40% bittersweet, 25% bad (the last run: 40/35/25).
- Season verdicts: 26 of 34 and 36 of 49 right (76% and 73%; the last run 81% and 78%). Over 60 mock weeks (seeds 101-130) the share of right verdicts fell from about 74% to about 62% with pastimes on; switching parts off one by one put the cause in the pastimes themselves, not the talks or their testimonies: people spend free time together at films, sunsets and talks, so fewer wander the house where they could witness something. Pastimes other than talks count for 0.3 while a death is investigated, and talks then lean to the death and share testimonies.
- End-of-week sanity is higher with pastimes (60.7 and 58.1 against 60.6 and 53.2 over 60 weeks).

## Notes on an earlier run (2026-10-19, phase 8e: the model proposer)

These notes are written by hand and are not regenerated.

- Tiers: 40% good, 35% bittersweet, 25% bad. With proposals off the same seasons give 40/28/32.
- The first version let a proposal wait for the target in any room with a drop or water. That revived stalled plots with the deadliest methods and gave 35/15/50. A proposal must now use a place the plotter has seen the target, as the engine's own planner does.
- A crash was found and fixed: a trial with only one person left (the claim trial looked for a second speaker). It now has no debate and no votes.

## Notes on an earlier run (2026-10-18, phase 8: stories, goals, pauses, reflection)

These notes are written by hand and are not regenerated.

- Tiers: 40% good, 28% bittersweet, 32% bad. Structured reflection first pushed them to 25/28/48 (the engine's own reflections made people distrust, confront and fear too readily); softened, they are back on target.
- A set-order bug was found and fixed (`mind.routine_decision` picked the room to "find some company" from a set, so ties depended on Python's hash seed). Worker processes inherit a random hash seed, so part of the swing between earlier runs of this report came from it; whole seasons now come out the same under any hash seed.

## Notes on an earlier run (2026-10-18, phase 7b final touches)

These notes are written by hand and are not regenerated.

- Tiers: exactly 40% good, 30% bittersweet, 30% bad (counts swing by a few seasons between runs).
- The season now has a fixed run of 28 days: no season went past day 28, and 3 ran the full length. After the fourth trial no newcomers arrive; NeoVi joined the cast that way in 6 seasons (and as a punishment in 2).
- 29 killers were let go by TereVi; 4 tried to help from outside, and 1 was believed, which started a rescue. The rest kept quiet or gave up, for fear of prison or of not being believed.
- To keep the tiers on target with smaller casts late in a season: escape work is a little faster (`escape_rate` 3.3), the bomb threat is slower and less sure (it had grown to 40% of endings), the last stand starts at 63% done, and the endgame fights to the death a bit more often.

## Notes on an earlier run (2026-10-18, phase 7b step 7: balance and epilogues)

These notes are written by hand and are not regenerated.

- Tiers: 38% good, 35% bittersweet, 28% bad, against the 40/30/30 target (counts swing by a few seasons between runs).
- What moved them: work on the ways out is faster (`escape_rate` default 3.0, was 1.0) and finales a little likelier; when only a few are left, they try a way out that is at least 70% done before TereVi ends it her way (`last_stand`); in the endgame TereVi crowns more often and fights to the death less; and a win that cost too much is bittersweet (crowned winners of a killing game, one survivor or fewer, NeoVi dying for it within three days, TereVi's parting shot, or someone the rescue leaves behind).
- No single ending is above a fifth of seasons. Every survivor now gets an epilogue built from their relationships (see the end of this file).

## Notes on an earlier run (2026-10-18, phase 7b step 6: tone, love life and rare turns)

These notes are written by hand and are not regenerated.

- Lovers now spend nights together (113 over 40 seasons, implied and cut away from); two people who feel strongly and click may become lovers that way. 8 affairs, 2 found out; 12 pangs of jealousy.
- Rare turns over 40 seasons: 7 killers confessed at their trial, 7 people took the blame for someone they loved, and NeoVi named the killer once. Death pacts, murder-suicides and a raft coming back are possible but did not happen in this run (they need lovers near breaking point on the right night, or a raft at sea).
- Tiers: 42% good, 5% bittersweet, 52% bad, against 40/30/30. Step 7 balances them.

## Notes on an earlier run (2026-10-18, phase 7b step 5: the inner voice and breaking minds)

These notes are written by hand and are not regenerated.

- Thoughts now show over people's heads and in the feed (about 5,100 over 40 seasons), some muttered out loud; 10 plotters gave themselves away by muttering.
- Below 40 sanity beliefs warp (145), below 25 people hallucinate (106) or, after a body is found, "remember" someone at the scene (37). 25 trials heard testimony from a broken mind. 23 hallucinations were later seen through. Acting on them: 46 people hid, 2 decided to strike first.
- No model calls were added (thought picks use their own random stream). Tiers: 45% good, 8% bittersweet, 48% bad.

## Notes on an earlier run (2026-10-18, phase 7b step 4: NeoVi as Kumiko)

These notes are written by hand and are not regenerated.

- NeoVi now visits one door a night, feelings grow both ways, and she confides once trust is mutual. She told someone her real name in 25 of 40 seasons and fell in love with someone in 17.
- She helped the cast 166 times in all (a part, the locks, a camera, covering for someone). Caught helping, TereVi re-educated her 13 times, humiliated her on air 6 times and made her a contestant 4 times. Kumiko then plays as a participant; she walked out alive in 2 of those 4 seasons, and no newcomers came after her.
- Tiers: 50% good, 8% bittersweet, 42% bad, against 40/30/30. Step 7 (balance) tunes the mix.

## One season, told by its saga (violent seed 4: CROWNED BY WHIM: FELIX, day 21)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 5: The cast voted wrongly: innocent Shintaro was executed and Szymon, the real culprit, escapes the island.
- Day 7: Noah was found guilty and executed.
- Day 7: With only 3 left, they try the build a raft before it is ready.
- Day 7: The cast tried to build a raft: it failed.
- Day 8: Cail's death was announced: no trial, the deadline is lifted.
- Day 11: Teo betrayed Chloe.
- Day 11: NeoVi's arc ended: betrayer.
- Day 13: The cast voted wrongly: innocent Dario was executed and Teo, the real culprit, escapes the island.
- Day 16: Ilya was found guilty and executed.
- Day 16: TereVi made NeoVi a contestant: Kumiko Akimoto. No newcomers will come after her.
- Day 20: Hana was found guilty and executed.
- Day 21: The cast could not agree. June, the culprit, escapes the island.

Deaths in order: day 3 Ayden (murdered); day 5 Shintaro (wrongly executed); day 5 Szymon (escaped the island); day 5 Vixen (murdered); day 7 Noah (executed after the trial); day 7 Cail (died in an accident); day 11 Chloe (murdered); day 13 Dario (wrongly executed); day 13 Teo (escaped the island); day 14 Seul (murdered); day 16 Ilya (executed after the trial); day 19 Omar (murdered); day 20 Hana (executed after the trial); day 20 Kumiko (murdered); day 21 June (escaped the island); day 21 Bram (executed by TereVi's whim); day 21 Mara (executed by TereVi's whim).

## Epilogues from one season (default seed 19: THE SHOW SURRENDERS, good)

- **Szymon**: Szymon sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Szymon and Shintaro have a group chat with one other member. The other member is a picture of the island, with a rude caption. Szymon buys a house with no basement, no pool and no cameras, and is happy in it, mostly.
- **Seul**: Seul is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Seul is godparent to Noah's first child. Nobody at the christening asks why they both flinch at the doorbell. Seul writes a memoir. The publisher cuts the island chapters for being 'too much'. Seul laughs for the first time in months.
- **Vixen**: Vixen walks out into the daylight and, for a long moment, just stands in it. Vixen and Cail meet every year on the day they got out. They mostly talk about anything else. Vixen quits being a hacker altogether and gets a job where nobody films anything.
- **Noah**: Noah gives the officers a full statement, calmly, in order, and then throws up in a bin. Noah never forgives Shintaro, who was in their room in the night on day 1. They see each other once, across a street, and both keep walking. Noah's next project is about the island. It does very well, and Noah hates every minute of it.
- **Ayden**: Ayden walks off the island steadier than anyone expected. Ayden and Seul meet every year on the day they got out. They mostly talk about anything else. Ayden starts a podcast about true crime and quits after one episode, because it turns out it is not entertaining at all.
- **Shintaro**: Shintaro sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Shintaro is always the one who books the table with Szymon, and always the one who leaves first. Shintaro goes back to being a prodigy student, and is better at it, and does not know why that makes them angry.
- **Chloe**: Chloe is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Chloe sues Seul over something said on the island. Both lose. Chloe turns down every interview. The one they finally give is three words long.
- **Cail**: Cail is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Cail is always the one who books the table with Vixen, and always the one who leaves first. Cail gets fan mail from people who thought it was all scripted. Cail answers every single one with the same photo of the island.
- **NeoVi**: Kumiko Akimoto walks out behind the others, out of uniform, and gives the first officer her real name. She gets a small flat, a cat, and a job where nobody tells her what to clean.
