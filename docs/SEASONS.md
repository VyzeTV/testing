# Whole mock seasons

80 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (40 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 23 (29%), bittersweet 33 (41%), bad 24 (30%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 11, bittersweet 16, bad 13.
- **NeoVi's fate:** none 17, participant 12, martyr 6, betrayer 4, survivor 1. Romances at the end: 27 in all.
- **Kumiko:** helped the cast 164 times; told someone her real name in 33 seasons; a romance with someone in 20; punished: re-education 13, humiliation 8, participant 7.
- **Minds:** 4407 thoughts shown; 76 beliefs warped by fear, 44 hallucinations, 17 false memories of a crime scene, 5 seen through later; acted on: 0 paranoid plots, 23 hid; 9 plotters overheard muttering; 14 trials heard testimony from a broken mind.
- **Rare turns:** neovi defects 4, confession 3, took blame 2, killer helps 1.
- **Love life:** 105 nights together, 8 affairs (3 found out), 10 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 5, someone never came out of the house 4, TereVi took someone with her 3, one survivor or fewer walked out of the house 3, NeoVi gave her life for it 2.
- **Killers the show let go:** 23; 1 tried to help from outside (believed 0, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 5 seasons, as a punishment in 7. Seasons that ran the full 28 days: 5.
- **Stories that formed** (story sifting): enemies alone 338, secret held 294, triangle 180, plot 173, near freedom 165, betrayed protector 118, silent witness 93, plot suspected 87, contradiction fear 66, grudge 51, unrequited 10, alliance strain 8, lovers breaking 7.
- **Season length:** median 14.0 days (shortest 4, longest 28).
- **How seasons ended:** RESCUE 8, THE LAST BATTLE 7, THE SHOW SURRENDERS 7, TEREVI IS SHUT DOWN 5, THE RECKONING 4, THE LAST ONE STANDING 3, THE WINNERS 2, ONLY THE RAFT GOT AWAY 2, NOBODY LEFT 1, CROWNED BY WHIM 1.
- **Deaths per season:** 7.9 on average. Causes: murdered 65, executed after the trial 52, escaped on a raft 49, died in the Reckoning 29, escaped the island 23, wrongly executed 22, died in an accident 21, died in the final battle 20.
- **Trials:** 75 in all, 52 right verdicts.
- **Newcomers:** 2.8 per season on average; 59 of the survivors were newcomers.
- **Rafts launched:** 23 (believed 11, sea 9, ashore 2, dismissed 1). Rescue countdowns started: 11.
- **Ways out at the end:** the furthest route reached 72% on average (best 100%).
- **Who walked out alive (seasons):** Dario 14, Chloe 11, Seul 11, Vixen 11, Ilya 10, Mara 8, Bram 7, Hana 7, Cail 7, Noah 7, Kumiko 6, Ayden 6, Shintaro 5, June 3, Teo 3, Szymon 3, Nadia 2, Rosa 2, Felix 2, Omar 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 26 | TEREVI IS SHUT DOWN | good | Dario, Ilya, Kumiko, Nadia, Rosa | 14 | 10 | 5 (4) |
| 2 | 28 | THE WINNERS | bittersweet | Bram, Dario, Hana, Mara | 11 | 7 | 3 (2) |
| 3 | 11 | NOBODY LEFT | bad | none | 8 | 0 | 2 (1) |
| 4 | 24 | TEREVI IS SHUT DOWN | good | Bram, Chloe, Dario, Hana, Kumiko, Mara, Shintaro | 8 | 6 | 4 (4) |
| 5 | 7 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 7 | 0 | 1 (0) |
| 6 | 28 | THE WINNERS | bittersweet | Felix, June, Nadia, Omar, Teo | 14 | 11 | 3 (1) |
| 7 | 14 | THE SHOW SURRENDERS | good | Cail, Chloe, Dario, Ilya, Seul, Vixen | 4 | 2 | 1 (1) |
| 8 | 17 | RESCUE | good | Bram, Dario, Ilya, June, Mara | 8 | 5 | 2 (2) |
| 9 | 14 | ONLY THE RAFT GOT AWAY | bittersweet | none | 8 | 0 | 2 (1) |
| 10 | 27 | TEREVI IS SHUT DOWN | bittersweet | Dario, Hana, Kumiko | 11 | 5 | 4 (2) |
| 11 | 4 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 12 | 14 | THE SHOW SURRENDERS | bittersweet | Cail, Chloe, Noah, Vixen | 4 | 0 | 2 (2) |
| 13 | 19 | CROWNED BY WHIM: HANA | bad | Hana | 10 | 3 | 2 (1) |
| 14 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 15 | 6 | THE SHOW SURRENDERS | bittersweet | Ayden, Cail, Chloe, Seul, Vixen | 3 | 0 | 1 (1) |
| 16 | 28 | THE LAST BATTLE: TEO STANDS | bad | Teo | 16 | 8 | 3 (2) |
| 17 | 27 | RESCUE | bittersweet | Bram, Dario, Hana, Ilya, June, Kumiko | 10 | 7 | 3 (3) |
| 18 | 14 | RESCUE | bittersweet | Ayden, Bram, Dario, Ilya, Kumiko, Mara, Vixen | 6 | 4 | 1 (1) |
| 19 | 14 | RESCUE | bittersweet | Chloe, Dario, Ilya, Shintaro, Vixen | 5 | 2 | 1 (1) |
| 20 | 13 | THE LAST ONE STANDING | bittersweet | Ayden | 7 | 0 | 2 (1) |
| 21 | 28 | THE LAST BATTLE: DARIO STANDS | bad | Dario | 14 | 6 | 3 (3) |
| 22 | 11 | THE LAST BATTLE: VIXEN STANDS | bad | Vixen | 7 | 0 | 2 (1) |
| 23 | 14 | THE RECKONING | bad | none | 10 | 2 | 1 (1) |
| 24 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 25 | 28 | THE SHOW SURRENDERS | good | Felix, Hana, Kumiko, Rosa | 14 | 9 | 5 (4) |
| 26 | 21 | THE LAST BATTLE: MARA STANDS | bad | Mara | 10 | 3 | 1 (1) |
| 27 | 16 | RESCUE | good | Bram, Chloe, Dario, Ilya, Mara | 7 | 4 | 2 (1) |
| 28 | 4 | THE SHOW SURRENDERS | bittersweet | Ayden, Cail, Chloe, Noah, Seul, Szymon, Vixen | 1 | 0 | 0 (0) |
| 29 | 12 | RESCUE | bittersweet | Dario, Ilya, Seul | 7 | 2 | 1 (0) |
| 30 | 4 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 31 | 11 | THE SHOW SURRENDERS | good | Cail, Chloe, Ilya, Mara, Seul | 5 | 2 | 1 (1) |
| 32 | 14 | THE RECKONING | bad | none | 9 | 0 | 1 (1) |
| 33 | 17 | ONLY THE RAFT GOT AWAY | bittersweet | none | 9 | 0 | 3 (2) |
| 34 | 23 | TEREVI IS SHUT DOWN | good | Dario, Hana, Teo | 14 | 8 | 4 (2) |
| 35 | 9 | THE LAST BATTLE: NOAH STANDS | bad | Noah | 7 | 0 | 1 (0) |
| 36 | 11 | RESCUE | good | Noah, Seul, Shintaro, Vixen | 4 | 0 | 1 (1) |
| 37 | 11 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 8 | 1 | 1 (0) |
| 38 | 14 | THE LAST ONE STANDING | bittersweet | Chloe | 7 | 0 | 2 (1) |
| 39 | 18 | THE LAST ONE STANDING | bittersweet | Noah | 8 | 0 | 3 (2) |
| 40 | 10 | RESCUE | bittersweet | Bram, Dario, Ilya, Mara, Seul, Vixen | 6 | 4 | 1 (1) |

## Violent mock cast

- **Ending tiers:** good 12, bittersweet 17, bad 11.
- **NeoVi's fate:** none 18, participant 11, betrayer 9, martyr 2. Romances at the end: 16 in all.
- **Kumiko:** helped the cast 66 times; told someone her real name in 20 seasons; a romance with someone in 13; punished: humiliation 2, re-education 1.
- **Minds:** 3308 thoughts shown; 21 beliefs warped by fear, 10 hallucinations, 9 false memories of a crime scene, 8 seen through later; acted on: 0 paranoid plots, 2 hid; 8 plotters overheard muttering; 7 trials heard testimony from a broken mind.
- **Rare turns:** took blame 9, confession 9, killer helps 3, raft returned 2, neovi defects 2.
- **Love life:** 49 nights together, 1 affairs (1 found out), 2 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 13, one survivor or fewer walked out of the house 8, NeoVi gave her life for it 2, TereVi took someone with her 1.
- **Killers the show let go:** 34; 3 tried to help from outside (believed 0, dismissed 1), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 11 seasons, as a punishment in 0. Seasons that ran the full 28 days: 0.
- **Stories that formed** (story sifting): plot 289, secret held 196, silent witness 148, triangle 135, enemies alone 132, near freedom 114, plot suspected 105, betrayed protector 94, contradiction fear 62, grudge 32, unrequited 9, alliance strain 3, lovers breaking 1.
- **Season length:** median 13.0 days (shortest 4, longest 26).
- **How seasons ended:** THE SHOW SURRENDERS 11, THE LAST BATTLE 9, THE LAST ONE STANDING 8, THE WINNERS 5, TEREVI IS SHUT DOWN 2, RESCUE 2, ONLY THE RAFT GOT AWAY 1, NOBODY LEFT 1, CROWNED BY WHIM 1.
- **Deaths per season:** 8.8 on average. Causes: murdered 111, executed after the trial 86, escaped the island 34, wrongly executed 32, escaped on a raft 30, killed 26, died in the final battle 16, died in an accident 8.
- **Trials:** 120 in all, 86 right verdicts.
- **Newcomers:** 3.3 per season on average; 58 of the survivors were newcomers.
- **Rafts launched:** 18 (sea 11, believed 3, ashore 2, returned 2). Rescue countdowns started: 3.
- **Ways out at the end:** the furthest route reached 64% on average (best 100%).
- **Who walked out alive (seasons):** Ilya 13, Mara 12, Dario 10, Vixen 9, June 8, Ayden 7, Cail 6, Chloe 6, Shintaro 6, Bram 6, Szymon 6, Noah 5, Seul 4, Kumiko 3, Teo 3, Hana 2, Rosa 2, Elsa 1, Nadia 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Seul, Shintaro | 3 | 0 | 0 (0) |
| 2 | 19 | THE WINNERS | bittersweet | Ayden, Bram, Dario | 12 | 7 | 3 (3) |
| 3 | 12 | THE LAST BATTLE: MARA STANDS | bad | Mara | 9 | 2 | 3 (2) |
| 4 | 6 | THE LAST ONE STANDING | bittersweet | Chloe | 7 | 0 | 2 (1) |
| 5 | 15 | THE WINNERS | bittersweet | June, Kumiko | 11 | 4 | 5 (5) |
| 6 | 13 | THE SHOW SURRENDERS | good | Ilya, Mara, Noah | 7 | 2 | 3 (2) |
| 7 | 6 | THE LAST BATTLE: VIXEN STANDS | bad | Vixen | 7 | 0 | 2 (1) |
| 8 | 12 | THE LAST ONE STANDING | bittersweet | Ilya | 9 | 2 | 3 (2) |
| 9 | 16 | ONLY THE RAFT GOT AWAY | bittersweet | none | 13 | 4 | 5 (3) |
| 10 | 14 | TEREVI IS SHUT DOWN | bittersweet | Cail, Dario, Mara | 9 | 4 | 4 (3) |
| 11 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 12 | 22 | THE LAST BATTLE: NOAH STANDS | bad | Noah | 14 | 6 | 6 (5) |
| 13 | 10 | THE LAST ONE STANDING | bittersweet | Dario | 10 | 3 | 3 (1) |
| 14 | 21 | THE LAST ONE STANDING | bittersweet | Szymon | 12 | 4 | 5 (3) |
| 15 | 10 | THE WINNERS | bittersweet | Ilya, Mara, Szymon | 7 | 2 | 2 (1) |
| 16 | 19 | THE SHOW SURRENDERS | good | Bram, Ilya, Mara, Teo, Vixen | 8 | 5 | 3 (1) |
| 17 | 13 | RESCUE | good | Ilya, Mara, Szymon | 7 | 2 | 2 (1) |
| 18 | 26 | THE LAST ONE STANDING | bittersweet | Dario | 12 | 4 | 5 (4) |
| 19 | 21 | THE LAST BATTLE: AYDEN STANDS | bad | Ayden | 14 | 6 | 5 (3) |
| 20 | 12 | THE WINNERS | bittersweet | Ilya, Mara, Vixen | 7 | 2 | 3 (2) |
| 21 | 11 | THE SHOW SURRENDERS | good | Dario, Ilya, June, Kumiko | 9 | 4 | 4 (3) |
| 22 | 13 | THE LAST BATTLE: VIXEN STANDS | bad | Vixen | 9 | 2 | 3 (2) |
| 23 | 14 | THE SHOW SURRENDERS | bittersweet | Chloe, Ilya, June, Mara, Seul, Shintaro | 6 | 4 | 3 (3) |
| 24 | 16 | THE SHOW SURRENDERS | good | Dario, Elsa, Hana, Ilya, Nadia, Rosa | 11 | 9 | 3 (2) |
| 25 | 14 | TEREVI IS SHUT DOWN | bittersweet | Shintaro, Szymon, Vixen | 7 | 2 | 3 (3) |
| 26 | 11 | THE SHOW SURRENDERS | good | Bram, Dario, Ilya, June, Mara, Vixen | 7 | 5 | 2 (2) |
| 27 | 6 | THE LAST BATTLE: VIXEN STANDS | bad | Vixen | 7 | 0 | 2 (1) |
| 28 | 4 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 29 | 10 | NOBODY LEFT | bad | none | 8 | 0 | 2 (1) |
| 30 | 17 | THE WINNERS | bittersweet | Ayden, Rosa | 11 | 4 | 5 (4) |
| 31 | 14 | THE LAST BATTLE: KUMIKO STANDS | bad | Kumiko | 10 | 2 | 4 (4) |
| 32 | 18 | RESCUE | good | Bram, Dario, June, Mara, Teo | 9 | 6 | 3 (2) |
| 33 | 14 | CROWNED BY WHIM: DARIO | bad | Dario | 12 | 4 | 4 (4) |
| 34 | 10 | THE LAST ONE STANDING | bittersweet | June | 11 | 4 | 1 (1) |
| 35 | 7 | THE LAST ONE STANDING | bittersweet | Cail | 7 | 0 | 2 (1) |
| 36 | 22 | THE LAST BATTLE: DARIO STANDS | bad | Dario | 14 | 6 | 5 (4) |
| 37 | 20 | THE LAST BATTLE: BRAM STANDS | bad | Bram | 13 | 6 | 3 (1) |
| 38 | 16 | THE SHOW SURRENDERS | good | Bram, Chloe, Ilya, June, Mara, Teo | 8 | 6 | 3 (3) |
| 39 | 13 | THE LAST ONE STANDING | bittersweet | Ilya | 11 | 4 | 2 (0) |
| 40 | 8 | THE SHOW SURRENDERS | good | Ayden, Cail, Hana, Ilya, June, Mara, Noah, Shintaro | 4 | 4 | 2 (2) |

## Notes on this run (2026-10-19, phase G: habits, investigation focus, electricity)

- 40 seeds per configuration this time (80 seasons), because 20-seed runs swung by ten points or more between runs (38/22/40, then 25/52/22, on the same code).
- Tiers: 29% good, 41% bittersweet, 30% bad. The same 80 seasons on the code at the end of phase E: 35% good, 41% bittersweet, 24% bad. The earlier 38/32/30 from 20 seeds was partly luck.
- Phase G costs about five good endings in 80. Likely causes: investigations now take people's free time (work on a way out is kept, leisure is cut), and electrocution adds a way to kill.

## Notes on an earlier run (2026-10-19, phase E: the Woods, the Garden Maze and the raft workshop)

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

## One season, told by its saga (violent seed 12: THE LAST BATTLE: NOAH STANDS, day 22)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 4: Ayden was found guilty and executed.
- Day 7: Szymon was found guilty and executed.
- Day 12: NeoVi's arc ended: betrayer.
- Day 13: Vixen betrayed Chloe.
- Day 13: Chloe was found guilty and executed.
- Day 15: Dario was found guilty and executed.
- Day 15: TereVi made NeoVi a contestant: Kumiko Akimoto. No newcomers will come after her.
- Day 15: Noah betrayed Kumiko.
- Day 18: Noah betrayed Hana.
- Day 18: Kumiko was found guilty and executed.
- Day 22: Mara betrayed Ilya.
- Day 22: The cast could not agree. Ilya, the culprit, escapes the island. Bram was exposed as the killer's alibi, but TereVi tries only one culprit: whoever struck the blow.
- Day 22: With only 3 left, they try the build a raft before it is ready.
- Day 22: The cast tried to build a raft: it failed.

Deaths in order: day 2 Cail (murdered); day 4 Ayden (executed after the trial); day 6 Shintaro (murdered); day 7 Szymon (executed after the trial); day 11 Seul (killed); day 13 Chloe (executed after the trial); day 13 Vixen (murdered); day 15 Dario (executed after the trial); day 17 June (murdered); day 18 Kumiko (executed after the trial); day 20 Hana (murdered); day 22 Ilya (escaped the island); day 22 Mara (died in the final battle); day 22 Bram (died in the final battle).

## Epilogues from one season (violent seed 40: THE SHOW SURRENDERS, good)

- **Noah**: Noah sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Noah and Ayden stay together. The tabloids call them 'the couple who survived Murder Channel'; they call it something else, and only to each other. Noah turns down every interview. The one they finally give is three words long.
- **Ayden**: Ayden walks out into the daylight and, for a long moment, just stands in it. Ayden still keeps a spare key to Noah's door, and uses it. Ayden's next project is about the island. It does very well, and Ayden hates every minute of it.
- **Shintaro**: Shintaro walks off the island steadier than anyone expected. Shintaro and Cail move in together within a month, which everyone says is too fast, and which is the only thing about the last year that has felt right. Shintaro writes a memoir. The publisher cuts the island chapters for being 'too much'. Shintaro laughs for the first time in months.
- **Cail**: Cail gives the officers a full statement, calmly, in order, and then throws up in a bin. Cail still keeps a spare key to Shintaro's door, and uses it. Cail gets fan mail from people who thought it was all scripted. Cail answers every single one with the same photo of the island.
- **Ilya**: Ilya is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Ilya quits being a chess grandmaster altogether and gets a job where nobody films anything.
- **Mara**: Mara gives the officers a full statement, calmly, in order, and then throws up in a bin. Mara buys a house with no basement, no pool and no cameras, and is happy in it, mostly.
- **June**: June sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. June starts a podcast about true crime and quits after one episode, because it turns out it is not entertaining at all.
- **Hana**: Hana walks off the island steadier than anyone expected. Hana goes back to being a detective novelist, and is better at it, and does not know why that makes them angry.
- **NeoVi**: Kumiko Akimoto walks out behind the others, out of uniform, and gives the first officer her real name. She gets a small flat, a cat, and a job where nobody tells her what to clean.

