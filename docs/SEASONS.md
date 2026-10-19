# Whole mock seasons

40 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (20 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 17 (42%), bittersweet 13 (32%), bad 10 (25%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 10, bittersweet 6, bad 4.
- **NeoVi's fate:** none 13, betrayer 4, martyr 2, participant 1. Romances at the end: 20 in all.
- **Kumiko:** helped the cast 36 times; told someone her real name in 8 seasons; a romance with someone in 4; punished: re-education 3, humiliation 2, participant 1.
- **Minds:** 1817 thoughts shown; 22 beliefs warped by fear, 16 hallucinations, 5 false memories of a crime scene, 1 seen through later; acted on: 0 paranoid plots, 7 hid; 11 plotters overheard muttering; 5 trials heard testimony from a broken mind.
- **Rare turns:** confession 3, killer helps 2, took blame 2, raft returned 1, killer believed 1.
- **Love life:** 39 nights together, 4 affairs (2 found out), 3 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): TereVi took someone with her 2, only the last few of a killing game walked out 2, someone never came out of the house 1.
- **Killers the show let go:** 12; 2 tried to help from outside (believed 1, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 0 seasons, as a punishment in 1. Seasons that ran the full 28 days: 1.
- **Stories that formed** (story sifting): enemies alone 158, secret held 126, plot 75, near freedom 65, triangle 50, betrayed protector 45, plot suspected 43, silent witness 38, contradiction fear 21, grudge 19, unrequited 8, lovers breaking 4, alliance strain 3.
- **Season length:** median 10.0 days (shortest 4, longest 28).
- **How seasons ended:** THE SHOW SURRENDERS 6, RESCUE 4, TEREVI IS SHUT DOWN 3, THE LAST BATTLE 2, THE WINNERS 2, THE RECKONING 2, RESCUE, TOO LATE 1.
- **Deaths per season:** 6.3 on average. Causes: escaped on a raft 25, murdered 19, executed after the trial 16, died in the Reckoning 14, escaped the island 12, wrongly executed 11, killed 10, died in an accident 7.
- **Trials:** 28 in all, 16 right verdicts.
- **Newcomers:** 2.6 per season on average; 38 of the survivors were newcomers.
- **Rafts launched:** 14 (believed 6, ashore 3, sea 3, returned 1, silenced 1). Rescue countdowns started: 6.
- **Ways out at the end:** the furthest route reached 77% on average (best 100%).
- **Who walked out alive (seasons):** Ilya 9, Vixen 9, Szymon 8, Dario 7, June 7, Chloe 7, Mara 6, Ayden 6, Cail 5, Bram 5, Noah 5, Seul 4, Shintaro 4, Teo 2, Hana 2, Kumiko 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 20 | RESCUE | good | Cail, Dario, Ilya, Mara, Teo | 8 | 5 | 2 (1) |
| 2 | 8 | THE SHOW SURRENDERS | bittersweet | Bram, Dario, Ilya, Vixen | 8 | 4 | 2 (1) |
| 3 | 7 | THE LAST BATTLE: VIXEN STANDS | bad | Vixen | 7 | 0 | 1 (1) |
| 4 | 28 | THE WINNERS | bittersweet | Bram, Dario, Hana, June, Kumiko, Mara | 9 | 6 | 4 (4) |
| 5 | 8 | THE SHOW SURRENDERS | good | Ayden, Ilya, June, Mara, Noah, Seul, Szymon, Vixen | 3 | 3 | 1 (0) |
| 6 | 23 | TEREVI IS SHUT DOWN | good | Bram, Dario, June | 11 | 6 | 2 (1) |
| 7 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 8 | 7 | THE LAST BATTLE: SZYMON STANDS | bad | Szymon | 7 | 0 | 1 (0) |
| 9 | 6 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 10 | 12 | THE SHOW SURRENDERS | good | Ayden, Chloe, Szymon, Vixen | 4 | 0 | 1 (1) |
| 11 | 11 | RESCUE | good | Ayden, Chloe, Ilya, Szymon, Vixen | 5 | 2 | 1 (0) |
| 12 | 17 | RESCUE | bittersweet | Bram, Hana, June, Teo | 12 | 8 | 3 (1) |
| 13 | 21 | THE WINNERS | bittersweet | June, Noah, Szymon | 9 | 4 | 3 (1) |
| 14 | 12 | RESCUE | good | Ayden, Ilya, June, Mara, Noah, Shintaro | 5 | 3 | 1 (0) |
| 15 | 20 | RESCUE, TOO LATE | bittersweet | Chloe, Ilya | 8 | 2 | 2 (2) |
| 16 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 17 | 20 | THE SHOW SURRENDERS | good | Dario, Ilya, June, Mara | 8 | 4 | 3 (3) |
| 18 | 4 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 19 | 8 | THE SHOW SURRENDERS | good | Bram, Cail, Chloe, Dario, Ilya, Seul, Shintaro, Vixen | 3 | 3 | 0 (0) |
| 20 | 9 | THE SHOW SURRENDERS | bittersweet | Cail, Chloe, Dario, Ilya, Mara, Szymon, Vixen | 4 | 3 | 1 (0) |

## Violent mock cast

- **Ending tiers:** good 7, bittersweet 7, bad 6.
- **NeoVi's fate:** none 10, participant 8, betrayer 1, martyr 1. Romances at the end: 12 in all.
- **Kumiko:** helped the cast 31 times; told someone her real name in 7 seasons; a romance with someone in 3; punished: re-education 2.
- **Minds:** 1743 thoughts shown; 16 beliefs warped by fear, 13 hallucinations, 6 false memories of a crime scene, 7 seen through later; acted on: 1 paranoid plots, 1 hid; 2 plotters overheard muttering; 5 trials heard testimony from a broken mind.
- **Rare turns:** confession 6, took blame 3, killer helps 2.
- **Love life:** 38 nights together, 6 affairs (0 found out), 4 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 6, one survivor or fewer walked out of the house 3.
- **Killers the show let go:** 24; 2 tried to help from outside (believed 0, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 8 seasons, as a punishment in 0. Seasons that ran the full 28 days: 1.
- **Stories that formed** (story sifting): plot 145, secret held 112, triangle 77, enemies alone 74, silent witness 65, plot suspected 60, near freedom 55, betrayed protector 51, grudge 23, contradiction fear 17, unrequited 11, alliance strain 3, lovers breaking 2.
- **Season length:** median 13.5 days (shortest 4, longest 28).
- **How seasons ended:** THE LAST BATTLE 4, TEREVI IS SHUT DOWN 4, THE LAST ONE STANDING 3, THE WINNERS 3, THE SHOW SURRENDERS 3, CROWNED BY WHIM 1, ONLY THE RAFT GOT AWAY 1, NOBODY LEFT 1.
- **Deaths per season:** 9.4 on average. Causes: murdered 56, executed after the trial 40, escaped the island 24, escaped on a raft 20, wrongly executed 19, killed 15, died in the final battle 7, died in an accident 3.
- **Trials:** 64 in all, 40 right verdicts.
- **Newcomers:** 3.5 per season on average; 17 of the survivors were newcomers.
- **Rafts launched:** 10 (sea 4, believed 3, ashore 2, silenced 1). Rescue countdowns started: 3.
- **Ways out at the end:** the furthest route reached 64% on average (best 100%).
- **Who walked out alive (seasons):** Kumiko 5, Ilya 5, Ayden 5, Cail 4, Szymon 4, Vixen 4, Chloe 3, Noah 3, Shintaro 3, Bram 3, Mara 2, Hana 2, Teo 2, Seul 2, June 1, Dario 1, Rosa 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 20 | THE LAST BATTLE: KUMIKO STANDS | bad | Kumiko | 15 | 7 | 5 (4) |
| 2 | 12 | THE LAST BATTLE: KUMIKO STANDS | bad | Kumiko | 12 | 4 | 4 (3) |
| 3 | 11 | TEREVI IS SHUT DOWN | good | Ilya, Mara | 10 | 4 | 3 (1) |
| 4 | 13 | THE LAST ONE STANDING | bittersweet | Cail | 9 | 2 | 3 (2) |
| 5 | 21 | CROWNED BY WHIM: KUMIKO | bad | Kumiko | 13 | 5 | 4 (1) |
| 6 | 7 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Noah, Shintaro, Szymon | 2 | 0 | 1 (1) |
| 7 | 11 | ONLY THE RAFT GOT AWAY | bittersweet | none | 11 | 3 | 3 (1) |
| 8 | 12 | THE WINNERS | bittersweet | Ayden, Ilya, Vixen | 8 | 3 | 3 (1) |
| 9 | 4 | TEREVI IS SHUT DOWN | good | Ayden, Chloe, Noah, Shintaro, Szymon, Vixen | 2 | 0 | 1 (1) |
| 10 | 12 | THE LAST ONE STANDING | bittersweet | Ilya | 9 | 2 | 3 (1) |
| 11 | 14 | THE LAST ONE STANDING | bittersweet | Chloe | 7 | 0 | 2 (1) |
| 12 | 17 | THE SHOW SURRENDERS | good | Bram, Hana, June, Teo | 11 | 7 | 3 (3) |
| 13 | 16 | THE LAST BATTLE: VIXEN STANDS | bad | Vixen | 12 | 4 | 4 (4) |
| 14 | 9 | THE SHOW SURRENDERS | good | Ayden, Cail, Ilya, Mara, Noah, Seul, Shintaro, Vixen | 2 | 2 | 1 (1) |
| 15 | 28 | TEREVI IS SHUT DOWN | good | Ayden, Bram, Kumiko, Teo | 12 | 7 | 4 (2) |
| 16 | 16 | THE WINNERS | bittersweet | Cail, Szymon | 11 | 4 | 5 (3) |
| 17 | 25 | THE WINNERS | bittersweet | Dario, Kumiko | 11 | 4 | 5 (5) |
| 18 | 5 | THE LAST BATTLE: SZYMON STANDS | bad | Szymon | 7 | 0 | 2 (1) |
| 19 | 18 | NOBODY LEFT | bad | none | 14 | 5 | 5 (2) |
| 20 | 15 | THE SHOW SURRENDERS | good | Bram, Hana, Ilya, Rosa, Seul | 11 | 8 | 3 (2) |

## Notes on this run (2026-10-19, phase C: intrusions and waking)

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

## One season, told by its saga (violent seed 1: THE LAST BATTLE: KUMIKO STANDS, day 20)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 4: Seul betrayed Ayden.
- Day 5: The house collapsed into a killing spree.
- Day 6: Szymon betrayed Vixen.
- Day 6: Vixen was found guilty and executed.
- Day 8: Noah was found guilty and executed.
- Day 12: Seul was found guilty and executed.
- Day 12: NeoVi's arc ended: martyr.
- Day 13: The cast tried to build a raft: it failed.
- Day 14: The cast tried to build a raft: it failed.
- Day 14: Cail's death was announced: no trial, the deadline is lifted.
- Day 14: With only 3 left, they try the build a raft before it is ready.
- Day 14: The cast tried to build a raft: it failed.
- Day 15: Mara betrayed Szymon.
- Day 16: Mara was found guilty and executed.
- Day 16: TereVi made NeoVi a contestant: Kumiko Akimoto. No newcomers will come after her.
- Day 17: The cast tried to build a raft: it worked.
- Day 18: Help is on its way: Chloe, Dario reached the mainland and were believed.
- Day 20: The cast voted wrongly: innocent Bram was executed and Teo, the real culprit, escapes the island.

Deaths in order: day 5 Ayden (murdered); day 6 Vixen (executed after the trial); day 6 Shintaro (murdered); day 8 Noah (executed after the trial); day 10 Ilya (was poisoned); day 12 Seul (executed after the trial); day 14 Cail (died in an accident); day 15 Szymon (murdered); day 16 Mara (executed after the trial); day 17 Chloe (escaped on a raft); day 17 Dario (escaped on a raft); day 18 Hana (killed); day 20 Bram (wrongly executed); day 20 Teo (escaped the island); day 20 June (died in the final battle).

## Epilogues from one season (default seed 19: THE SHOW SURRENDERS, good)

- **Seul**: Seul sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Seul and Chloe move in together within a month, which everyone says is too fast, and which is the only thing about the last year that has felt right. Seul turns down every interview. The one they finally give is three words long.
- **Vixen**: Vixen gives the officers a full statement, calmly, in order, and then throws up in a bin. Vixen and Shintaro stay together. The tabloids call them 'the couple who survived Murder Channel'; they call it something else, and only to each other. Vixen gets fan mail from people who thought it was all scripted. Vixen answers every single one with the same photo of the island.
- **Shintaro**: Shintaro is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Shintaro still keeps a spare key to Vixen's door, and uses it. Shintaro goes back to being a prodigy student, and is better at it, and does not know why that makes them angry.
- **Chloe**: Chloe walks off the island steadier than anyone expected. Chloe still keeps a spare key to Seul's door, and uses it. Chloe starts a podcast about true crime and quits after one episode, because it turns out it is not entertaining at all.
- **Cail**: Cail walks out into the daylight and, for a long moment, just stands in it. Cail and Vixen meet every year on the day they got out. They mostly talk about anything else. Cail's next project is about the island. It does very well, and Cail hates every minute of it.
- **Ilya**: Ilya walks out into the daylight and, for a long moment, just stands in it. Ilya quits being a chess grandmaster altogether and gets a job where nobody films anything.
- **Dario**: Dario walks off the island steadier than anyone expected. Dario buys a house with no basement, no pool and no cameras, and is happy in it, mostly.
- **Bram**: Bram is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Bram writes a memoir. The publisher cuts the island chapters for being 'too much'. Bram laughs for the first time in months.
- **NeoVi**: Kumiko Akimoto walks out behind the others, out of uniform, and gives the first officer her real name. She gets a small flat, a cat, and a job where nobody tells her what to clean.
