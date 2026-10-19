# Whole mock seasons

40 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (20 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 16 (40%), bittersweet 14 (35%), bad 10 (25%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 8, bittersweet 7, bad 5.
- **NeoVi's fate:** none 10, participant 3, martyr 3, betrayer 2, survivor 2. Romances at the end: 8 in all.
- **Kumiko:** helped the cast 43 times; told someone her real name in 8 seasons; a romance with someone in 4; punished: humiliation 4, re-education 2, participant 1.
- **Minds:** 2084 thoughts shown; 67 beliefs warped by fear, 42 hallucinations, 19 false memories of a crime scene, 7 seen through later; acted on: 2 paranoid plots, 21 hid; 10 plotters overheard muttering; 9 trials heard testimony from a broken mind.
- **Rare turns:** neovi defects 1, confession 1, killer helps 1, raft returned 1, hallucination kill 1, took blame 1.
- **Love life:** 67 nights together, 8 affairs (5 found out), 7 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): someone never came out of the house 3, only the last few of a killing game walked out 3, one survivor or fewer walked out of the house 2, TereVi took someone with her 1, NeoVi gave her life for it 1.
- **Killers the show let go:** 7; 1 tried to help from outside (believed 0, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 2 seasons, as a punishment in 1. Seasons that ran the full 28 days: 1.
- **Stories that formed** (story sifting): secret held 192, enemies alone 162, triangle 84, plot 83, near freedom 64, silent witness 36, plot suspected 27, betrayed protector 17, contradiction fear 13, grudge 11, lovers breaking 7, unrequited 5, alliance strain 5.
- **Season length:** median 13.0 days (shortest 4, longest 28).
- **How seasons ended:** RESCUE 5, THE SHOW SURRENDERS 5, TEREVI IS SHUT DOWN 2, THE LAST BATTLE 2, THE LAST ONE STANDING 2, THE WINNERS 1, CROWNED BY WHIM 1, THE RECKONING 1, NOBODY LEFT 1.
- **Deaths per season:** 6.5 on average. Causes: murdered 36, executed after the trial 30, escaped on a raft 15, died in an accident 11, wrongly executed 7, escaped the island 7, died in the Reckoning 6, died in the final battle 4.
- **Trials:** 37 in all, 30 right verdicts.
- **Newcomers:** 2.5 per season on average; 28 of the survivors were newcomers.
- **Rafts launched:** 9 (believed 3, sea 3, ashore 2, returned 1). Rescue countdowns started: 6.
- **Ways out at the end:** the furthest route reached 79% on average (best 100%).
- **Who walked out alive (seasons):** Ayden 8, Szymon 8, Vixen 7, Cail 7, Noah 6, Seul 6, Shintaro 6, June 5, Chloe 5, Bram 4, Dario 4, Mara 4, Hana 3, Ilya 3, Kumiko 2, Elsa 1, Nadia 1, Rosa 1, Felix 1, Teo 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 16 | RESCUE | bittersweet | Bram, Dario, Hana, Ilya, June, Vixen | 8 | 6 | 2 (2) |
| 2 | 28 | THE WINNERS | bittersweet | Ayden, Bram, Elsa, Kumiko, Nadia, Rosa | 12 | 9 | 4 (4) |
| 3 | 22 | RESCUE | bittersweet | Bram, Dario, Felix, Hana, June, Mara, Teo | 9 | 8 | 3 (3) |
| 4 | 4 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 5 | 28 | CROWNED BY WHIM: KUMIKO | bad | Kumiko | 15 | 7 | 5 (4) |
| 6 | 18 | THE LAST BATTLE: JUNE STANDS | bad | June | 9 | 2 | 3 (2) |
| 7 | 7 | THE SHOW SURRENDERS | good | Noah, Shintaro, Szymon, Vixen | 4 | 0 | 2 (2) |
| 8 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 9 | 6 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 10 | 28 | NOBODY LEFT | bad | none | 12 | 3 | 4 (4) |
| 11 | 10 | THE LAST ONE STANDING | bittersweet | Ayden | 7 | 0 | 2 (1) |
| 12 | 20 | TEREVI IS SHUT DOWN | good | Chloe, Dario, June, Mara | 8 | 4 | 3 (3) |
| 13 | 21 | RESCUE | good | Bram, Dario, Hana, Ilya, June, Szymon, Vixen | 7 | 6 | 3 (3) |
| 14 | 14 | THE LAST ONE STANDING | bittersweet | Cail | 7 | 0 | 2 (1) |
| 15 | 8 | THE LAST BATTLE: CHLOE STANDS | bad | Chloe | 7 | 0 | 1 (0) |
| 16 | 12 | RESCUE | good | Cail, Ilya, Mara, Vixen | 6 | 2 | 1 (1) |
| 17 | 9 | THE SHOW SURRENDERS | bittersweet | Ayden, Cail, Noah, Seul, Szymon | 6 | 3 | 1 (0) |
| 18 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 19 | 7 | THE SHOW SURRENDERS | good | Ayden, Cail, Seul, Shintaro, Szymon | 3 | 0 | 1 (0) |
| 20 | 15 | RESCUE | bittersweet | Ayden, Mara, Noah, Seul, Shintaro, Szymon | 3 | 1 | 0 (0) |

## Violent mock cast

- **Ending tiers:** good 8, bittersweet 7, bad 5.
- **NeoVi's fate:** participant 9, none 6, martyr 4, betrayer 1. Romances at the end: 10 in all.
- **Kumiko:** helped the cast 35 times; told someone her real name in 7 seasons; a romance with someone in 2; punished: humiliation 4, participant 2.
- **Minds:** 1694 thoughts shown; 22 beliefs warped by fear, 11 hallucinations, 9 false memories of a crime scene, 10 seen through later; acted on: 0 paranoid plots, 2 hid; 4 plotters overheard muttering; 7 trials heard testimony from a broken mind.
- **Rare turns:** took blame 4, confession 2, killer helps 1.
- **Love life:** 48 nights together, 1 affairs (1 found out), 6 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 3, NeoVi gave her life for it 2, someone never came out of the house 1.
- **Killers the show let go:** 14; 1 tried to help from outside (believed 0, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 7 seasons, as a punishment in 2. Seasons that ran the full 28 days: 0.
- **Stories that formed** (story sifting): plot 146, secret held 109, triangle 96, silent witness 88, enemies alone 78, near freedom 67, plot suspected 60, betrayed protector 29, grudge 22, contradiction fear 11, unrequited 9, lovers breaking 4, alliance strain 3.
- **Season length:** median 13.5 days (shortest 6, longest 25).
- **How seasons ended:** THE SHOW SURRENDERS 5, THE LAST BATTLE 5, THE WINNERS 3, TEREVI IS SHUT DOWN 3, ONLY THE RAFT GOT AWAY 2, RESCUE 2.
- **Deaths per season:** 8.4 on average. Causes: executed after the trial 50, murdered 48, killed 20, wrongly executed 14, escaped the island 14, escaped on a raft 8, died in the final battle 8, died in an accident 3.
- **Trials:** 64 in all, 50 right verdicts.
- **Newcomers:** 3.2 per season on average; 30 of the survivors were newcomers.
- **Rafts launched:** 5 (sea 3, believed 2). Rescue countdowns started: 3.
- **Ways out at the end:** the furthest route reached 72% on average (best 100%).
- **Who walked out alive (seasons):** Kumiko 7, Szymon 7, Dario 6, Ilya 6, June 5, Ayden 4, Hana 4, Chloe 4, Vixen 4, Mara 3, Cail 3, Rosa 2, Seul 2, Bram 2, Shintaro 2, Teo 2, Noah 2.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 16 | THE SHOW SURRENDERS | good | Ayden, Dario, Hana, Ilya, June, Kumiko, Rosa | 8 | 6 | 4 (4) |
| 2 | 13 | ONLY THE RAFT GOT AWAY | bittersweet | none | 8 | 0 | 3 (3) |
| 3 | 6 | THE WINNERS | bittersweet | Chloe, Seul, Szymon | 5 | 0 | 1 (1) |
| 4 | 15 | THE SHOW SURRENDERS | bittersweet | Bram, Dario, Hana, June, Mara, Shintaro, Teo, Vixen | 7 | 7 | 3 (2) |
| 5 | 6 | THE LAST BATTLE: NOAH STANDS | bad | Noah | 7 | 0 | 2 (1) |
| 6 | 12 | THE LAST BATTLE: SZYMON STANDS | bad | Szymon | 9 | 2 | 3 (2) |
| 7 | 15 | TEREVI IS SHUT DOWN | good | Ayden, Chloe, Dario, June, Kumiko | 8 | 4 | 4 (4) |
| 8 | 6 | THE SHOW SURRENDERS | good | Cail, Noah, Seul, Shintaro, Szymon, Vixen | 2 | 0 | 1 (1) |
| 9 | 23 | THE LAST BATTLE: KUMIKO STANDS | bad | Kumiko | 15 | 7 | 6 (6) |
| 10 | 12 | TEREVI IS SHUT DOWN | good | Mara, Szymon, Vixen | 7 | 2 | 3 (2) |
| 11 | 16 | RESCUE | bittersweet | Bram, Dario, Ilya, Kumiko, Mara | 8 | 4 | 2 (2) |
| 12 | 14 | ONLY THE RAFT GOT AWAY | bittersweet | none | 13 | 4 | 5 (3) |
| 13 | 16 | THE SHOW SURRENDERS | good | Cail, Hana, June, Kumiko, Rosa, Teo | 11 | 8 | 4 (3) |
| 14 | 13 | THE WINNERS | bittersweet | Cail, Chloe, Ilya | 7 | 2 | 3 (2) |
| 15 | 15 | THE WINNERS | bittersweet | Ilya, Szymon | 9 | 2 | 4 (3) |
| 16 | 25 | RESCUE | good | Dario, Ilya, Kumiko, Vixen | 11 | 6 | 4 (2) |
| 17 | 7 | THE LAST BATTLE: AYDEN STANDS | bad | Ayden | 7 | 0 | 2 (1) |
| 18 | 10 | THE SHOW SURRENDERS | good | Ayden, Chloe, Dario, Ilya, Szymon | 5 | 2 | 2 (1) |
| 19 | 25 | TEREVI IS SHUT DOWN | good | Hana, June, Kumiko | 12 | 6 | 5 (4) |
| 20 | 12 | THE LAST BATTLE: SZYMON STANDS | bad | Szymon | 9 | 2 | 3 (3) |

## Notes on this run (2026-10-19, phase 8e: the model proposer)

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

## One season, told by its saga (violent seed 9: THE LAST BATTLE: KUMIKO STANDS, day 23)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 4: Szymon was found guilty and executed.
- Day 4: Vixen betrayed Cail.
- Day 8: The house collapsed into a killing spree.
- Day 10: Vixen betrayed Seul.
- Day 10: Seul was found guilty and executed.
- Day 12: NeoVi's arc ended: betrayer.
- Day 13: Vixen betrayed Cail.
- Day 13: Cail was found guilty and executed.
- Day 14: Ilya's death was announced: no trial, the deadline is lifted.
- Day 14: With only 3 left, they try the build a raft before it is ready.
- Day 14: The cast tried to build a raft: it failed.
- Day 15: Vixen's death was announced: no trial, the deadline is lifted.
- Day 16: Chloe betrayed Teo.
- Day 17: Mara betrayed Bram.
- Day 17: Bram was found guilty and executed.
- Day 17: TereVi made NeoVi a contestant: Kumiko Akimoto. No newcomers will come after her.
- Day 21: June betrayed Mara.
- Day 21: Mara was found guilty and executed. June was exposed as the killer's alibi, but TereVi tries only one culprit: whoever struck the blow.
- Day 23: Chloe betrayed Kumiko.
- Day 23: Chloe was found guilty and executed.

Deaths in order: day 2 Shintaro (murdered); day 4 Szymon (executed after the trial); day 9 Noah (killed); day 10 Seul (executed after the trial); day 11 Ayden (murdered); day 13 Cail (executed after the trial); day 13 Ilya (died in an accident); day 14 Vixen (died in an accident); day 15 Dario (murdered); day 17 Bram (executed after the trial); day 19 Teo (murdered); day 21 Mara (executed after the trial); day 21 Felix (murdered); day 23 Chloe (executed after the trial); day 23 June (died in the final battle).

## Epilogues from one season (default seed 18: THE SHOW SURRENDERS, good)

- **Szymon**: Szymon walks off the island steadier than anyone expected. Szymon and Shintaro have a group chat with one other member. The other member is a picture of the island, with a rude caption. Szymon's next project is about the island. It does very well, and Szymon hates every minute of it.
- **Seul**: Seul is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Seul and Noah move in together within a month, which everyone says is too fast, and which is the only thing about the last year that has felt right. Seul quits being a competitive gamer altogether and gets a job where nobody films anything.
- **Vixen**: Vixen sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Vixen sues Noah over something said on the island. Both lose. Vixen gets fan mail from people who thought it was all scripted. Vixen answers every single one with the same photo of the island.
- **Noah**: Noah walks out into the daylight and, for a long moment, just stands in it. Noah still keeps a spare key to Seul's door, and uses it. Noah never talks about the day they decided Ayden must die.
- **Ayden**: Ayden gives the officers a full statement, calmly, in order, and then throws up in a bin. Ayden and Noah never speak again. They once end up at the same awards show and sit very, very far apart. Ayden starts a podcast about true crime and quits after one episode, because it turns out it is not entertaining at all.
- **Shintaro**: Shintaro walks off the island steadier than anyone expected. Shintaro is always the one who books the table with Szymon, and always the one who leaves first. Shintaro turns down every interview. The one they finally give is three words long.
- **Chloe**: Chloe walks off the island steadier than anyone expected. Chloe and Szymon never speak again. They once end up at the same awards show and sit very, very far apart. Chloe writes a memoir. The publisher cuts the island chapters for being 'too much'. Chloe laughs for the first time in months.
- **Cail**: Cail is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Cail and Shintaro meet every year on the day they got out. They mostly talk about anything else. Cail buys a house with no basement, no pool and no cameras, and is happy in it, mostly.
- **NeoVi**: Kumiko Akimoto walks out behind the others, out of uniform, and gives the first officer her real name. She gets a small flat, a cat, and a job where nobody tells her what to clean.
