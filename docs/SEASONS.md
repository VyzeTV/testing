# Whole mock seasons

80 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (40 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 30 (38%), bittersweet 27 (34%), bad 23 (29%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 13, bittersweet 17, bad 10.
- **NeoVi's fate:** none 23, participant 7, martyr 7, betrayer 2, survivor 1. Romances at the end: 25 in all.
- **Kumiko:** helped the cast 112 times; told someone her real name in 27 seasons; a romance with someone in 18; punished: humiliation 8, re-education 6, participant 5.
- **Minds:** 3465 thoughts shown; 44 beliefs warped by fear, 47 hallucinations, 17 false memories of a crime scene, 11 seen through later; acted on: 3 paranoid plots, 22 hid; 5 plotters overheard muttering; 10 trials heard testimony from a broken mind.
- **Rare turns:** killer helps 7, took blame 6, killer believed 3, confession 2, neovi defects 1.
- **Love life:** 102 nights together, 4 affairs (1 found out), 14 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 7, someone never came out of the house 5, one survivor or fewer walked out of the house 5, NeoVi gave her life for it 2, TereVi took someone with her 2.
- **Killers the show let go:** 25; 7 tried to help from outside (believed 3, dismissed 1), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 2 seasons, as a punishment in 5. Seasons that ran the full 28 days: 1.
- **Stories that formed** (story sifting): secret held 306, enemies alone 282, plot 154, near freedom 120, triangle 100, betrayed protector 90, plot suspected 70, silent witness 65, contradiction fear 53, grudge 39, unrequited 11, lovers breaking 5, alliance strain 4.
- **Season length:** median 11.5 days (shortest 4, longest 28).
- **How seasons ended:** THE SHOW SURRENDERS 11, RESCUE 8, THE LAST BATTLE 8, THE LAST ONE STANDING 4, TEREVI IS SHUT DOWN 3, THE WINNERS 3, NOBODY LEFT 1, CROWNED BY WHIM 1, RESCUE, TOO LATE 1.
- **Deaths per season:** 6.3 on average. Causes: murdered 52, executed after the trial 36, escaped on a raft 36, escaped the island 25, wrongly executed 24, died in the final battle 19, killed 16, died in an accident 13.
- **Trials:** 61 in all, 36 right verdicts.
- **Newcomers:** 1.9 per season on average; 45 of the survivors were newcomers.
- **Rafts launched:** 22 (believed 11, sea 7, lost 2, dismissed 1, ashore 1). Rescue countdowns started: 15.
- **Ways out at the end:** the furthest route reached 72% on average (best 100%).
- **Who walked out alive (seasons):** Chloe 17, Shintaro 16, Seul 15, Ayden 15, Vixen 13, Ilya 12, Mara 12, Cail 12, Noah 9, June 8, Szymon 7, Dario 5, Bram 4, Hana 3, Rosa 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 19 | NOBODY LEFT | bad | none | 13 | 4 | 4 (1) |
| 2 | 7 | CROWNED BY WHIM: CHLOE | bad | Chloe | 7 | 0 | 1 (0) |
| 3 | 18 | RESCUE | bittersweet | Dario, Hana, Ilya, June, Mara | 8 | 5 | 2 (1) |
| 4 | 11 | THE LAST BATTLE: CHLOE STANDS | bad | Chloe | 7 | 0 | 2 (1) |
| 5 | 16 | TEREVI IS SHUT DOWN | good | Bram, Dario, Hana, Ilya, June, Mara, Seul | 7 | 6 | 1 (1) |
| 6 | 16 | THE SHOW SURRENDERS | good | Ayden, Dario, Ilya, June, Mara, Vixen | 6 | 4 | 1 (1) |
| 7 | 14 | THE LAST BATTLE: SHINTARO STANDS | bad | Shintaro | 9 | 2 | 2 (1) |
| 8 | 11 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 7 | 0 | 1 (0) |
| 9 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 10 | 12 | THE LAST BATTLE: CHLOE STANDS | bad | Chloe | 9 | 2 | 2 (1) |
| 11 | 11 | THE WINNERS | bittersweet | Cail, Chloe, Seul | 5 | 0 | 1 (0) |
| 12 | 10 | RESCUE | bittersweet | Bram, Chloe, Dario, Ilya | 7 | 3 | 2 (0) |
| 13 | 19 | THE LAST BATTLE: SZYMON STANDS | bad | Szymon | 10 | 2 | 3 (3) |
| 14 | 13 | RESCUE | bittersweet | Chloe, June, Shintaro | 7 | 2 | 2 (2) |
| 15 | 7 | RESCUE | bittersweet | Ayden, Chloe, Noah, Seul, Szymon, Vixen | 2 | 0 | 0 (0) |
| 16 | 15 | THE SHOW SURRENDERS | good | Bram, Dario, Hana, Ilya, June, Mara, Rosa, Shintaro | 7 | 7 | 2 (0) |
| 17 | 28 | THE LAST BATTLE: BRAM STANDS | bad | Bram | 16 | 8 | 5 (4) |
| 18 | 10 | THE WINNERS | bittersweet | Ilya, June, Mara | 8 | 3 | 1 (1) |
| 19 | 10 | THE LAST ONE STANDING | bittersweet | Seul | 7 | 0 | 2 (1) |
| 20 | 7 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 21 | 14 | THE LAST ONE STANDING | bittersweet | June | 9 | 2 | 3 (2) |
| 22 | 21 | THE LAST BATTLE: ILYA STANDS | bad | Ilya | 10 | 3 | 2 (1) |
| 23 | 14 | RESCUE | bittersweet | Ayden, Chloe, June, Mara, Shintaro | 5 | 2 | 1 (1) |
| 24 | 23 | RESCUE, TOO LATE | bittersweet | Chloe | 9 | 1 | 2 (1) |
| 25 | 6 | THE SHOW SURRENDERS | bittersweet | Chloe, Noah, Seul, Shintaro, Vixen | 3 | 0 | 1 (1) |
| 26 | 11 | TEREVI IS SHUT DOWN | good | Chloe, Noah, Seul, Shintaro, Vixen | 3 | 0 | 1 (0) |
| 27 | 6 | THE SHOW SURRENDERS | bittersweet | Ayden, Cail, Chloe, Seul, Shintaro | 3 | 0 | 0 (0) |
| 28 | 7 | THE SHOW SURRENDERS | good | Ayden, Cail, Noah, Seul, Shintaro, Vixen | 2 | 0 | 0 (0) |
| 29 | 11 | THE LAST BATTLE: SHINTARO STANDS | bad | Shintaro | 9 | 2 | 1 (1) |
| 30 | 11 | RESCUE | good | Ayden, Cail, Ilya, Mara, Seul, Shintaro, Vixen | 3 | 2 | 0 (0) |
| 31 | 8 | THE SHOW SURRENDERS | good | Ayden, Cail, Ilya, Mara, Noah, Seul | 4 | 2 | 1 (1) |
| 32 | 21 | THE LAST ONE STANDING | bittersweet | Cail | 10 | 2 | 3 (2) |
| 33 | 23 | RESCUE | good | Cail, Ilya, Mara, Vixen | 8 | 3 | 2 (2) |
| 34 | 13 | THE LAST ONE STANDING | bittersweet | Ayden | 7 | 0 | 2 (2) |
| 35 | 4 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 36 | 21 | TEREVI IS SHUT DOWN | bittersweet | Mara | 11 | 3 | 4 (1) |
| 37 | 14 | THE WINNERS | bittersweet | Ayden, Vixen | 6 | 0 | 2 (1) |
| 38 | 8 | RESCUE | bittersweet | Ayden, Cail, Ilya, Mara, Shintaro, Vixen | 4 | 2 | 0 (0) |
| 39 | 12 | THE SHOW SURRENDERS | good | Ayden, Chloe, Ilya, Mara, Shintaro, Szymon | 4 | 2 | 2 (2) |
| 40 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |

## Violent mock cast

- **Ending tiers:** good 17, bittersweet 10, bad 13.
- **NeoVi's fate:** none 27, participant 8, betrayer 4, martyr 1. Romances at the end: 21 in all.
- **Kumiko:** helped the cast 32 times; told someone her real name in 16 seasons; a romance with someone in 8; punished: re-education 1.
- **Minds:** 2486 thoughts shown; 5 beliefs warped by fear, 5 hallucinations, 3 false memories of a crime scene, 3 seen through later; acted on: 0 paranoid plots, 0 hid; 15 plotters overheard muttering; 3 trials heard testimony from a broken mind.
- **Rare turns:** took blame 5, killer helps 4, confession 3, neovi defects 1.
- **Love life:** 39 nights together, 3 affairs (2 found out), 1 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 9, one survivor or fewer walked out of the house 4, TereVi took someone with her 1.
- **Killers the show let go:** 27; 4 tried to help from outside (believed 0, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 8 seasons, as a punishment in 0. Seasons that ran the full 28 days: 0.
- **Stories that formed** (story sifting): plot 211, secret held 157, silent witness 114, near freedom 113, enemies alone 99, plot suspected 96, triangle 88, contradiction fear 76, betrayed protector 74, grudge 45, unrequited 10, alliance strain 3, lovers breaking 1.
- **Season length:** median 10.0 days (shortest 5, longest 27).
- **How seasons ended:** THE SHOW SURRENDERS 13, THE LAST BATTLE 9, THE WINNERS 5, RESCUE 4, THE LAST ONE STANDING 4, CROWNED BY WHIM 3, TEREVI IS SHUT DOWN 1, NOBODY LEFT 1.
- **Deaths per season:** 7.5 on average. Causes: murdered 85, executed after the trial 69, escaped on a raft 37, escaped the island 27, wrongly executed 25, killed 20, died in the final battle 17, died in an accident 9.
- **Trials:** 96 in all, 69 right verdicts.
- **Newcomers:** 2.4 per season on average; 51 of the survivors were newcomers.
- **Rafts launched:** 19 (sea 14, believed 4, ashore 1). Rescue countdowns started: 5.
- **Ways out at the end:** the furthest route reached 64% on average (best 100%).
- **Who walked out alive (seasons):** Ilya 14, Ayden 12, Mara 11, Shintaro 10, Cail 9, Szymon 9, Vixen 9, Seul 9, June 9, Chloe 7, Dario 6, Noah 5, Hana 5, Kumiko 4, Bram 3, Felix 1, Teo 1, Rosa 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 12 | RESCUE | good | Cail, Szymon, Vixen | 5 | 0 | 1 (1) |
| 2 | 10 | THE LAST ONE STANDING | bittersweet | Mara | 9 | 2 | 3 (2) |
| 3 | 7 | THE WINNERS | bittersweet | Ayden, Cail | 6 | 0 | 2 (2) |
| 4 | 6 | THE SHOW SURRENDERS | good | Ayden, Chloe, Noah, Shintaro, Szymon, Vixen | 2 | 0 | 1 (1) |
| 5 | 14 | THE LAST BATTLE: SZYMON STANDS | bad | Szymon | 10 | 3 | 3 (1) |
| 6 | 9 | THE WINNERS | bittersweet | Dario, Ilya, Mara | 8 | 3 | 2 (0) |
| 7 | 6 | THE SHOW SURRENDERS | good | Ayden, Chloe, Noah, Seul, Shintaro, Vixen | 2 | 0 | 1 (1) |
| 8 | 7 | TEREVI IS SHUT DOWN | good | Chloe, Shintaro | 6 | 0 | 2 (2) |
| 9 | 7 | THE SHOW SURRENDERS | good | Cail, Seul, Shintaro, Szymon, Vixen | 3 | 0 | 1 (1) |
| 10 | 10 | THE SHOW SURRENDERS | good | Ayden, Chloe, Dario, Ilya, Mara, Seul | 5 | 3 | 2 (2) |
| 11 | 10 | THE SHOW SURRENDERS | good | Dario, Hana, Ilya, June, Mara, Seul, Shintaro | 6 | 5 | 2 (0) |
| 12 | 7 | THE WINNERS | bittersweet | Ayden, Cail, Szymon | 5 | 0 | 2 (1) |
| 13 | 16 | THE SHOW SURRENDERS | bittersweet | Hana, Ilya, June | 13 | 7 | 4 (3) |
| 14 | 11 | THE LAST BATTLE: MARA STANDS | bad | Mara | 12 | 4 | 4 (4) |
| 15 | 6 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 7 | 0 | 2 (1) |
| 16 | 11 | THE SHOW SURRENDERS | good | Bram, Dario, Ilya, Mara, Seul, Vixen | 6 | 4 | 2 (2) |
| 17 | 21 | CROWNED BY WHIM: HANA | bad | Hana | 12 | 4 | 5 (4) |
| 18 | 9 | THE SHOW SURRENDERS | good | Ayden, Dario, Ilya, June, Mara, Shintaro | 6 | 4 | 2 (2) |
| 19 | 11 | THE LAST BATTLE: KUMIKO STANDS | bad | Kumiko | 12 | 4 | 4 (3) |
| 20 | 12 | RESCUE | good | Ilya, June, Mara, Noah | 7 | 3 | 3 (2) |
| 21 | 7 | THE WINNERS | bittersweet | Ayden, Cail, Vixen | 5 | 0 | 2 (1) |
| 22 | 12 | THE WINNERS | bittersweet | Ilya, Mara, Szymon | 7 | 2 | 3 (2) |
| 23 | 17 | THE SHOW SURRENDERS | good | Bram, Felix, Ilya, June, Kumiko, Teo | 10 | 7 | 4 (3) |
| 24 | 7 | THE LAST ONE STANDING | bittersweet | Shintaro | 7 | 0 | 2 (1) |
| 25 | 11 | THE LAST BATTLE: AYDEN STANDS | bad | Ayden | 10 | 3 | 2 (0) |
| 26 | 23 | THE LAST BATTLE: KUMIKO STANDS | bad | Kumiko | 15 | 7 | 5 (3) |
| 27 | 13 | THE LAST BATTLE: ILYA STANDS | bad | Ilya | 9 | 2 | 3 (3) |
| 28 | 14 | THE LAST ONE STANDING | bittersweet | June | 9 | 2 | 1 (1) |
| 29 | 7 | CROWNED BY WHIM: CAIL | bad | Cail | 7 | 0 | 2 (2) |
| 30 | 11 | THE LAST BATTLE: ILYA STANDS | bad | Ilya | 10 | 3 | 3 (2) |
| 31 | 8 | THE SHOW SURRENDERS | good | Ayden, Hana, Ilya, June, Mara, Seul, Shintaro, Szymon | 4 | 4 | 1 (1) |
| 32 | 12 | CROWNED BY WHIM: ILYA | bad | Ilya | 10 | 3 | 2 (1) |
| 33 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Seul, Szymon, Vixen | 2 | 0 | 1 (1) |
| 34 | 13 | RESCUE | good | Ayden, June, Noah, Vixen | 7 | 3 | 2 (1) |
| 35 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Seul, Shintaro, Vixen | 2 | 0 | 1 (1) |
| 36 | 20 | RESCUE | good | Bram, Dario, Hana, June, Kumiko | 10 | 6 | 4 (4) |
| 37 | 27 | THE LAST ONE STANDING | bittersweet | Rosa | 14 | 6 | 6 (4) |
| 38 | 8 | THE SHOW SURRENDERS | good | Cail, Chloe, Ilya, Mara, Shintaro, Szymon | 4 | 2 | 2 (2) |
| 39 | 6 | NOBODY LEFT | bad | none | 8 | 0 | 2 (1) |
| 40 | 7 | THE LAST BATTLE: NOAH STANDS | bad | Noah | 7 | 0 | 0 (0) |

## Notes on this run (2026-10-19, phase F gate: the live engine, and the re-tune of the ending tiers)

- 80 seasons (40 per configuration). Tiers: 38% good, 34% bittersweet, 29% bad, against the 40/30/30 target.
- Before the re-tune, with phase F in: 24% good, 36% bittersweet, 40% bad (THE LAST BATTLE 21 of 80). Everything running at its own minute (F1) and the investigation focus left the cast thinner before anyone got out.
- The re-tune: `escape_rate` 3.3 to 4.6 (its range now goes to 6). At 4.0 the tiers were 32/34/34. Seasons are shorter: median about 11 days (14 before), because more groups get out sooner.
- The 80-season run also found a crash, fixed: someone who died on the way to join a conversation was then announced as joining.

## Notes on an earlier run (2026-10-19, phase G: habits, investigation focus, electricity)

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

## One season, told by its saga (default seed 17: THE LAST BATTLE: BRAM STANDS, day 28)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 7: Ayden betrayed Seul.
- Day 7: The cast voted wrongly: innocent Ayden was executed and Seul, the real culprit, escapes the island.
- Day 12: Szymon betrayed Cail.
- Day 12: Cail was found guilty and executed.
- Day 13: NeoVi's arc ended: martyr.
- Day 15: The cast tried to build a raft: it failed.
- Day 15: Ilya's death was announced: no trial, the deadline is lifted.
- Day 21: Dario betrayed Szymon.
- Day 21: Szymon was found guilty and executed.
- Day 22: The cast tried to build a raft: it failed.
- Day 25: Shintaro betrayed Hana.
- Day 26: Shintaro betrayed June.
- Day 26: Shintaro was found guilty and executed.
- Day 26: TereVi made NeoVi a contestant: Kumiko Akimoto. No newcomers will come after her.
- Day 28: Kumiko betrayed Dario.
- Day 28: Dario was found guilty and executed.
- Day 28: Day 28: the season's run is over, and TereVi ends the show her way.
- Day 28: With only 5 left, they try the build a raft before it is ready.
- Day 28: The cast tried to build a raft: it failed.

Deaths in order: day 5 Vixen (murdered); day 7 Ayden (wrongly executed); day 7 Seul (escaped the island); day 11 Noah (killed); day 12 Cail (executed after the trial); day 15 Ilya (died in an accident); day 19 Chloe (killed); day 21 Szymon (executed after the trial); day 25 Hana (murdered); day 26 Shintaro (executed after the trial); day 26 Mara (killed); day 28 Dario (executed after the trial); day 28 June (died in an accident); day 28 Rosa (died in the final battle); day 28 Teo (died in the final battle); day 28 Kumiko (died in the final battle).

## Epilogues from one season (default seed 40: THE SHOW SURRENDERS, good)

- **Szymon**: Szymon gives the officers a full statement, calmly, in order, and then throws up in a bin. Szymon sues Noah over something said on the island. Both lose. Szymon's next project is about the island. It does very well, and Szymon hates every minute of it.
- **Seul**: Seul walks off the island steadier than anyone expected. Seul and Cail never speak again. They once end up at the same awards show and sit very, very far apart. Seul buys a house with no basement, no pool and no cameras, and is happy in it, mostly.
- **Vixen**: Vixen sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Vixen sues Cail over something said on the island. Both lose. Vixen never talks about the day they decided Cail must die.
- **Noah**: Noah walks out into the daylight and, for a long moment, just stands in it. Noah never forgives Chloe, who came into their room and lied about why on day 1. They see each other once, across a street, and both keep walking. Noah quits being a musician altogether and gets a job where nobody films anything.
- **Ayden**: Ayden is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Ayden starts a podcast about true crime and quits after one episode, because it turns out it is not entertaining at all.
- **Shintaro**: Shintaro is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Shintaro and Cail meet every year on the day they got out. They mostly talk about anything else. Shintaro gets fan mail from people who thought it was all scripted. Shintaro answers every single one with the same photo of the island.
- **Chloe**: Chloe walks off the island steadier than anyone expected. Chloe writes a memoir. The publisher cuts the island chapters for being 'too much'. Chloe laughs for the first time in months.
- **Cail**: Cail is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Cail tells one interviewer about Shintaro, who Shintaro turned on them when it mattered (day 5). Shintaro's lawyers are in touch by morning. Cail turns down every interview. The one they finally give is three words long.
- **NeoVi**: Kumiko Akimoto walks out behind the others, out of uniform, and gives the first officer her real name. She gets a small flat, a cat, and a job where nobody tells her what to clean.

