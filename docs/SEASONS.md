# Whole mock seasons

40 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (20 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 14 (35%), bittersweet 16 (40%), bad 10 (25%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 9, bittersweet 7, bad 4.
- **NeoVi's fate:** none 13, participant 5, betrayer 1, martyr 1. Romances at the end: 17 in all.
- **Kumiko:** helped the cast 39 times; told someone her real name in 11 seasons; a romance with someone in 5; punished: humiliation 3, participant 2.
- **Minds:** 1717 thoughts shown; 15 beliefs warped by fear, 14 hallucinations, 5 false memories of a crime scene, 7 seen through later; acted on: 0 paranoid plots, 2 hid; 2 plotters overheard muttering; 3 trials heard testimony from a broken mind.
- **Rare turns:** killer helps 3, raft returned 1, took blame 1, confession 1.
- **Love life:** 60 nights together, 5 affairs (1 found out), 7 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 4, TereVi took someone with her 1, someone never came out of the house 1, NeoVi gave her life for it 1, one survivor or fewer walked out of the house 1.
- **Killers the show let go:** 8; 3 tried to help from outside (believed 0, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 3 seasons, as a punishment in 2. Seasons that ran the full 28 days: 1.
- **Stories that formed** (story sifting): enemies alone 139, secret held 134, triangle 82, plot 75, near freedom 66, silent witness 45, betrayed protector 25, plot suspected 19, grudge 15, contradiction fear 5, alliance strain 4, unrequited 3, lovers breaking 1.
- **Season length:** median 10.5 days (shortest 5, longest 28).
- **How seasons ended:** TEREVI IS SHUT DOWN 6, THE SHOW SURRENDERS 5, THE WINNERS 3, THE LAST BATTLE 2, RESCUE 1, THE RECKONING 1, CROWNED BY WHIM 1, THE LAST ONE STANDING 1.
- **Deaths per season:** 6.0 on average. Causes: executed after the trial 26, escaped on a raft 25, murdered 23, killed 10, escaped the island 8, died in the Reckoning 8, wrongly executed 6, lost at sea 3.
- **Trials:** 34 in all, 26 right verdicts.
- **Newcomers:** 2.1 per season on average; 29 of the survivors were newcomers.
- **Rafts launched:** 14 (sea 5, believed 3, ashore 2, dismissed 2, returned 1, lost 1). Rescue countdowns started: 3.
- **Ways out at the end:** the furthest route reached 78% on average (best 100%).
- **Who walked out alive (seasons):** Chloe 10, Cail 9, Mara 9, Seul 8, Ayden 8, Vixen 7, Dario 7, Ilya 6, Shintaro 5, Noah 5, Szymon 3, June 3, Bram 3, Kumiko 2, Teo 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 9 | THE SHOW SURRENDERS | good | Cail, Chloe, Ilya, Mara, Seul, Shintaro, Vixen | 3 | 2 | 1 (1) |
| 2 | 10 | THE WINNERS | bittersweet | Cail, Noah, Shintaro | 5 | 0 | 1 (1) |
| 3 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 4 | 21 | THE WINNERS | bittersweet | June, Kumiko, Noah | 10 | 4 | 4 (4) |
| 5 | 6 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 6 | 7 | THE LAST BATTLE: CHLOE STANDS | bad | Chloe | 7 | 0 | 1 (1) |
| 7 | 17 | TEREVI IS SHUT DOWN | good | Ayden, Bram, Cail, Chloe, Dario, Ilya, Mara, Seul | 4 | 4 | 2 (2) |
| 8 | 15 | TEREVI IS SHUT DOWN | bittersweet | Bram, Chloe, Dario, Ilya, June, Mara, Teo | 7 | 6 | 2 (2) |
| 9 | 9 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Shintaro | 3 | 0 | 1 (0) |
| 10 | 17 | RESCUE | bittersweet | Dario, Kumiko, Mara, Vixen | 8 | 3 | 2 (0) |
| 11 | 11 | THE WINNERS | bittersweet | Ayden, Cail, Seul | 5 | 0 | 1 (1) |
| 12 | 14 | THE SHOW SURRENDERS | bittersweet | Ayden, Chloe, Dario, Ilya, June, Mara | 6 | 4 | 2 (1) |
| 13 | 28 | THE LAST BATTLE: DARIO STANDS | bad | Dario | 14 | 6 | 4 (3) |
| 14 | 8 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Seul, Szymon, Vixen | 2 | 0 | 1 (1) |
| 15 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 16 | 9 | CROWNED BY WHIM: MARA | bad | Mara | 9 | 2 | 2 (1) |
| 17 | 10 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Dario, Ilya, Mara, Seul | 5 | 3 | 1 (1) |
| 18 | 15 | TEREVI IS SHUT DOWN | good | Chloe, Vixen | 7 | 0 | 2 (1) |
| 19 | 19 | THE LAST ONE STANDING | bittersweet | Mara | 12 | 4 | 5 (5) |
| 20 | 15 | TEREVI IS SHUT DOWN | good | Bram, Dario, Ilya, Mara, Seul, Vixen | 6 | 4 | 2 (1) |

## Violent mock cast

- **Ending tiers:** good 5, bittersweet 9, bad 6.
- **NeoVi's fate:** none 13, participant 5, martyr 2. Romances at the end: 4 in all.
- **Kumiko:** helped the cast 21 times; told someone her real name in 3 seasons; a romance with someone in 2; punished: humiliation 1, re-education 1.
- **Minds:** 1354 thoughts shown; 13 beliefs warped by fear, 6 hallucinations, 6 false memories of a crime scene, 0 seen through later; acted on: 1 paranoid plots, 5 hid; 7 plotters overheard muttering; 5 trials heard testimony from a broken mind.
- **Rare turns:** took blame 4, confession 2, killer helps 2, neovi defects 1.
- **Love life:** 37 nights together, 3 affairs (1 found out), 2 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 7, one survivor or fewer walked out of the house 3, TereVi took someone with her 1.
- **Killers the show let go:** 13; 2 tried to help from outside (believed 0, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 5 seasons, as a punishment in 0. Seasons that ran the full 28 days: 0.
- **Stories that formed** (story sifting): plot 110, secret held 87, enemies alone 57, triangle 51, near freedom 49, silent witness 47, plot suspected 44, betrayed protector 20, grudge 19, unrequited 10, contradiction fear 6, alliance strain 2.
- **Season length:** median 10.0 days (shortest 3, longest 25).
- **How seasons ended:** THE WINNERS 4, THE LAST BATTLE 4, THE SHOW SURRENDERS 3, TEREVI IS SHUT DOWN 3, THE LAST ONE STANDING 3, CROWNED BY WHIM 2, ONLY THE RAFT GOT AWAY 1.
- **Deaths per season:** 7.0 on average. Causes: murdered 36, executed after the trial 36, escaped the island 13, wrongly executed 12, killed 12, escaped on a raft 12, died in the final battle 8, died in an accident 4.
- **Trials:** 49 in all, 36 right verdicts.
- **Newcomers:** 1.9 per season on average; 9 of the survivors were newcomers.
- **Rafts launched:** 6 (sea 6). Rescue countdowns started: 0.
- **Ways out at the end:** the furthest route reached 59% on average (best 100%).
- **Who walked out alive (seasons):** Noah 8, Ayden 7, Chloe 7, Seul 7, Shintaro 6, Szymon 6, Cail 5, Vixen 5, Ilya 3, June 2, Mara 2, Hana 1, Bram 1, Kumiko 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 6 | THE WINNERS | bittersweet | Ayden, Chloe, Seul | 5 | 0 | 2 (2) |
| 2 | 21 | THE WINNERS | bittersweet | Hana, Ilya | 12 | 5 | 5 (5) |
| 3 | 3 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 4 | 10 | THE LAST BATTLE: ILYA STANDS | bad | Ilya | 10 | 3 | 3 (1) |
| 5 | 13 | THE LAST BATTLE: ILYA STANDS | bad | Ilya | 12 | 4 | 4 (3) |
| 6 | 22 | ONLY THE RAFT GOT AWAY | bittersweet | none | 14 | 5 | 5 (3) |
| 7 | 14 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 9 | 2 | 3 (2) |
| 8 | 13 | CROWNED BY WHIM: JUNE | bad | June | 11 | 4 | 3 (2) |
| 9 | 5 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 10 | 7 | CROWNED BY WHIM: SEUL | bad | Seul | 7 | 0 | 2 (1) |
| 11 | 7 | THE LAST ONE STANDING | bittersweet | Ayden | 7 | 0 | 2 (2) |
| 12 | 19 | THE WINNERS | bittersweet | June, Noah | 11 | 4 | 5 (5) |
| 13 | 10 | THE LAST ONE STANDING | bittersweet | Chloe | 7 | 0 | 2 (1) |
| 14 | 5 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 15 | 4 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 16 | 7 | THE LAST BATTLE: SZYMON STANDS | bad | Szymon | 7 | 0 | 2 (1) |
| 17 | 16 | THE WINNERS | bittersweet | Bram, Mara, Noah | 9 | 4 | 3 (2) |
| 18 | 5 | TEREVI IS SHUT DOWN | bittersweet | Ayden, Cail, Chloe, Noah, Shintaro, Szymon, Vixen | 1 | 0 | 0 (0) |
| 19 | 11 | THE SHOW SURRENDERS | good | Mara, Noah, Shintaro | 7 | 2 | 3 (2) |
| 20 | 25 | THE LAST ONE STANDING | bittersweet | Kumiko | 12 | 4 | 5 (4) |

## Notes on this run (2026-10-19, phase A and B follow-ups: consistent talk about people, pastimes)

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

## One season, told by its saga (violent seed 6: ONLY THE RAFT GOT AWAY, day 22)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 5: Cail was found guilty and executed.
- Day 10: Chloe betrayed Vixen.
- Day 10: Szymon betrayed Noah.
- Day 10: The cast voted wrongly: innocent Noah was executed and Vixen, the real culprit, escapes the island. Szymon was exposed as the killer's alibi, but TereVi tries only one culprit: whoever struck 
- Day 12: NeoVi's arc ended: martyr.
- Day 15: Szymon was found guilty and executed.
- Day 15: The cast tried to shut terevi down: it failed.
- Day 18: Chloe betrayed Mara.
- Day 18: Mara was found guilty and executed.
- Day 18: TereVi made NeoVi a contestant: Kumiko Akimoto. No newcomers will come after her.
- Day 19: Hana betrayed Chloe.
- Day 22: The cast voted wrongly: innocent Chloe was executed and June, the real culprit, escapes the island.
- Day 22: With only 2 left, they try the build a raft before it is ready.
- Day 22: The cast tried to build a raft: it worked.

Deaths in order: day 3 Seul (murdered); day 5 Cail (executed after the trial); day 8 Ayden (murdered); day 10 Noah (wrongly executed); day 10 Vixen (escaped the island); day 13 Shintaro (was poisoned); day 15 Szymon (executed after the trial); day 17 Ilya (murdered); day 18 Mara (executed after the trial); day 20 Hana (murdered); day 22 Chloe (wrongly executed); day 22 June (escaped the island); day 22 Dario (escaped on a raft); day 22 Kumiko (escaped on a raft).

## Epilogues from one season (violent seed 15: THE SHOW SURRENDERS, good)

- **Szymon**: Szymon is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Szymon and Seul meet every year on the day they got out. They mostly talk about anything else. Szymon quits being an urban explorer altogether and gets a job where nobody films anything.
- **Seul**: Seul sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Seul is always the one who books the table with Szymon, and always the one who leaves first. Seul buys a house with no basement, no pool and no cameras, and is happy in it, mostly.
- **Vixen**: Vixen walks off the island steadier than anyone expected. Vixen turns down every interview. The one they finally give is three words long.
- **Noah**: Noah gives the officers a full statement, calmly, in order, and then throws up in a bin. Noah tells one interviewer about Vixen, who caught them going through their things on night 1. Vixen's lawyers are in touch by morning. Noah starts a podcast about true crime and quits after one episode, because it turns out it is not entertaining at all.
- **Ayden**: Ayden walks out into the daylight and, for a long moment, just stands in it. Ayden never talks about the day they decided Seul must die.
- **Shintaro**: Shintaro sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Shintaro and Noah never speak again. They once end up at the same awards show and sit very, very far apart. Shintaro's next project is about the island. It does very well, and Shintaro hates every minute of it.
- **Chloe**: Chloe sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Chloe and Szymon have a group chat with one other member. The other member is a picture of the island, with a rude caption. Chloe gets fan mail from people who thought it was all scripted. Chloe answers every single one with the same photo of the island.
- **Cail**: Cail walks out into the daylight and, for a long moment, just stands in it. Cail is godparent to Szymon's first child. Nobody at the christening asks why they both flinch at the doorbell. Cail writes a memoir. The publisher cuts the island chapters for being 'too much'. Cail laughs for the first time in months.
- **NeoVi**: Kumiko Akimoto walks out behind the others, out of uniform, and gives the first officer her real name. She gets a small flat, a cat, and a job where nobody tells her what to clean.
