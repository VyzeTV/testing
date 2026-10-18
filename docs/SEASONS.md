# Whole mock seasons

40 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (20 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 16 (40%), bittersweet 11 (28%), bad 13 (32%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 12, bittersweet 2, bad 6.
- **NeoVi's fate:** none 13, betrayer 4, survivor 2, martyr 1. Romances at the end: 15 in all.
- **Kumiko:** helped the cast 24 times; told someone her real name in 7 seasons; a romance with someone in 2; punished: humiliation 1, re-education 1.
- **Minds:** 1572 thoughts shown; 29 beliefs warped by fear, 10 hallucinations, 7 false memories of a crime scene, 4 seen through later; acted on: 1 paranoid plots, 6 hid; 4 plotters overheard muttering; 3 trials heard testimony from a broken mind.
- **Rare turns:** took blame 2, neovi defects 1, raft returned 1, hallucination kill 1, killer helps 1.
- **Love life:** 54 nights together, 2 affairs (1 found out), 7 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): TereVi took someone with her 1, only the last few of a killing game walked out 1.
- **Killers the show let go:** 9; 1 tried to help from outside (believed 0, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 0 seasons, as a punishment in 0. Seasons that ran the full 28 days: 0.
- **Stories that formed** (story sifting): secret held 176, enemies alone 145, plot 65, triangle 61, near freedom 45, plot suspected 28, betrayed protector 24, silent witness 20, grudge 12, contradiction fear 6, lovers breaking 3, alliance strain 2, unrequited 1.
- **Season length:** median 10.5 days (shortest 4, longest 21).
- **How seasons ended:** THE SHOW SURRENDERS 7, TEREVI IS SHUT DOWN 3, RESCUE 3, THE LAST BATTLE 3, THE RECKONING 2, NOBODY LEFT 1, THE WINNERS 1.
- **Deaths per season:** 5.2 on average. Causes: murdered 24, executed after the trial 16, died in the Reckoning 14, escaped on a raft 10, wrongly executed 9, escaped the island 9, died in the final battle 8, died in an accident 7.
- **Trials:** 25 in all, 16 right verdicts.
- **Newcomers:** 1.6 per season on average; 25 of the survivors were newcomers.
- **Rafts launched:** 6 (ashore 2, believed 2, returned 1, sea 1). Rescue countdowns started: 5.
- **Ways out at the end:** the furthest route reached 86% on average (best 100%).
- **Who walked out alive (seasons):** Szymon 10, Vixen 9, Cail 9, Seul 9, Shintaro 8, Noah 7, Ilya 6, Ayden 6, Mara 5, Chloe 5, June 4, Dario 3, Hana 3, Bram 2, Rosa 2.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 14 | TEREVI IS SHUT DOWN | good | Ilya, June, Mara, Noah, Shintaro, Vixen | 5 | 3 | 2 (1) |
| 2 | 8 | TEREVI IS SHUT DOWN | good | Cail, Chloe, Noah, Seul, Vixen | 3 | 0 | 1 (0) |
| 3 | 11 | THE SHOW SURRENDERS | good | Bram, Cail, Chloe, Dario, Ilya, Mara, Seul, Szymon | 4 | 4 | 1 (1) |
| 4 | 4 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 5 | 20 | THE SHOW SURRENDERS | good | Dario, Hana, Ilya, June, Rosa, Szymon | 8 | 6 | 2 (0) |
| 6 | 16 | RESCUE | good | Ayden, Hana, Ilya, June, Mara, Rosa, Shintaro, Szymon | 5 | 5 | 2 (2) |
| 7 | 7 | THE SHOW SURRENDERS | good | Noah, Shintaro, Szymon, Vixen | 4 | 0 | 2 (2) |
| 8 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 9 | 6 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 10 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 11 | 10 | THE LAST BATTLE: SHINTARO STANDS | bad | Shintaro | 7 | 0 | 2 (1) |
| 12 | 20 | THE LAST BATTLE: MARA STANDS | bad | Mara | 9 | 2 | 2 (2) |
| 13 | 21 | RESCUE | good | Bram, Dario, Hana, Ilya, June, Szymon, Vixen | 7 | 6 | 3 (3) |
| 14 | 13 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 7 | 0 | 1 (0) |
| 15 | 13 | NOBODY LEFT | bad | none | 8 | 0 | 2 (2) |
| 16 | 12 | RESCUE | good | Cail, Ilya, Mara, Vixen | 6 | 2 | 1 (1) |
| 17 | 9 | THE SHOW SURRENDERS | bittersweet | Ayden, Cail, Noah, Seul, Szymon | 6 | 3 | 1 (0) |
| 18 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 19 | 7 | THE SHOW SURRENDERS | good | Ayden, Cail, Seul, Shintaro, Szymon | 3 | 0 | 1 (0) |
| 20 | 13 | THE WINNERS | bittersweet | Cail, Seul, Vixen | 5 | 0 | 2 (1) |

## Violent mock cast

- **Ending tiers:** good 4, bittersweet 9, bad 7.
- **NeoVi's fate:** participant 8, none 7, betrayer 4, martyr 1. Romances at the end: 7 in all.
- **Kumiko:** helped the cast 26 times; told someone her real name in 4 seasons; a romance with someone in 2; punished: humiliation 6, re-education 1.
- **Minds:** 1763 thoughts shown; 38 beliefs warped by fear, 45 hallucinations, 8 false memories of a crime scene, 13 seen through later; acted on: 4 paranoid plots, 12 hid; 2 plotters overheard muttering; 6 trials heard testimony from a broken mind.
- **Rare turns:** neovi defects 3, confession 2, death pact 1, took blame 1, killer helps 1.
- **Love life:** 27 nights together, 2 affairs (1 found out), 2 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 4, TereVi took someone with her 1, one survivor or fewer walked out of the house 1.
- **Killers the show let go:** 11; 1 tried to help from outside (believed 0, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 8 seasons, as a punishment in 0. Seasons that ran the full 28 days: 0.
- **Stories that formed** (story sifting): plot 140, secret held 92, triangle 89, near freedom 82, enemies alone 71, silent witness 69, plot suspected 60, betrayed protector 23, grudge 14, contradiction fear 8, unrequited 7, alliance strain 3, lovers breaking 2.
- **Season length:** median 13.0 days (shortest 6, longest 24).
- **How seasons ended:** THE SHOW SURRENDERS 4, ONLY THE RAFT GOT AWAY 4, THE LAST BATTLE 4, THE WINNERS 3, NOBODY LEFT 2, TEREVI IS SHUT DOWN 1, CROWNED BY WHIM 1, THE LAST ONE STANDING 1.
- **Deaths per season:** 9.6 on average. Causes: executed after the trial 58, murdered 56, killed 16, escaped on a raft 13, died in the final battle 11, escaped the island 11, died in an accident 10, wrongly executed 10.
- **Trials:** 69 in all, 58 right verdicts.
- **Newcomers:** 3.1 per season on average; 20 of the survivors were newcomers.
- **Rafts launched:** 8 (sea 7, lost 1). Rescue countdowns started: 0.
- **Ways out at the end:** the furthest route reached 60% on average (best 100%).
- **Who walked out alive (seasons):** Mara 7, Ilya 4, Cail 3, Dario 3, Hana 3, Chloe 3, Shintaro 3, June 2, Noah 2, Szymon 2, Vixen 2, Kumiko 2, Felix 1, Seul 1, Ayden 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 10 | THE SHOW SURRENDERS | bittersweet | Cail, Dario, Hana, June, Mara | 8 | 5 | 2 (2) |
| 2 | 13 | ONLY THE RAFT GOT AWAY | bittersweet | none | 8 | 0 | 3 (3) |
| 3 | 24 | THE WINNERS | bittersweet | Felix, Hana | 16 | 9 | 5 (5) |
| 4 | 13 | THE LAST BATTLE: MARA STANDS | bad | Mara | 9 | 2 | 3 (3) |
| 5 | 6 | THE LAST BATTLE: NOAH STANDS | bad | Noah | 7 | 0 | 2 (1) |
| 6 | 11 | THE LAST BATTLE: CHLOE STANDS | bad | Chloe | 9 | 2 | 2 (1) |
| 7 | 8 | THE SHOW SURRENDERS | good | Chloe, Dario, Ilya, June, Mara, Shintaro | 6 | 4 | 3 (3) |
| 8 | 6 | THE SHOW SURRENDERS | good | Cail, Noah, Seul, Shintaro, Szymon, Vixen | 2 | 0 | 1 (1) |
| 9 | 14 | NOBODY LEFT | bad | none | 10 | 2 | 3 (3) |
| 10 | 12 | TEREVI IS SHUT DOWN | good | Mara, Szymon, Vixen | 7 | 2 | 3 (2) |
| 11 | 12 | ONLY THE RAFT GOT AWAY | bittersweet | none | 8 | 0 | 3 (3) |
| 12 | 14 | ONLY THE RAFT GOT AWAY | bittersweet | none | 13 | 4 | 5 (3) |
| 13 | 18 | ONLY THE RAFT GOT AWAY | bittersweet | none | 13 | 4 | 5 (5) |
| 14 | 13 | THE LAST BATTLE: ILYA STANDS | bad | Ilya | 13 | 5 | 4 (3) |
| 15 | 9 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Ilya, Mara, Shintaro | 4 | 2 | 2 (2) |
| 16 | 22 | NOBODY LEFT | bad | none | 16 | 7 | 7 (5) |
| 17 | 22 | THE WINNERS | bittersweet | Hana, Kumiko | 13 | 6 | 4 (3) |
| 18 | 21 | CROWNED BY WHIM: KUMIKO | bad | Kumiko | 11 | 3 | 4 (3) |
| 19 | 18 | THE WINNERS | bittersweet | Dario, Ilya, Mara | 10 | 4 | 5 (5) |
| 20 | 12 | THE LAST ONE STANDING | bittersweet | Mara | 9 | 2 | 3 (2) |

## Notes on this run (2026-10-18, phase 8: stories, goals, pauses, reflection)

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

## One season, told by its saga (violent seed 16: NOBODY LEFT, day 22)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 5: The cast voted wrongly: innocent Shintaro was executed and Ayden, the real culprit, escapes the island.
- Day 9: Vixen betrayed Szymon.
- Day 9: Szymon was found guilty and executed.
- Day 11: Cail betrayed Seul.
- Day 11: Vixen was found guilty and executed.
- Day 11: NeoVi's arc ended: martyr.
- Day 15: Seul was found guilty and executed.
- Day 15: TereVi made NeoVi a contestant: Kumiko Akimoto. No newcomers will come after her.
- Day 17: Kumiko was found guilty and executed.
- Day 18: Bram betrayed Teo.
- Day 19: June betrayed Cail.
- Day 19: Cail betrayed Ilya.
- Day 20: Bram was found guilty and executed.
- Day 20: With only 3 left, they try the shut terevi down before it is ready.
- Day 20: The cast tried to shut terevi down: it failed.
- Day 20: June's death was announced: no trial, the deadline is lifted.
- Day 22: The cast could not agree. Cail, the culprit, escapes the island.

Deaths in order: day 3 Chloe (murdered); day 5 Shintaro (wrongly executed); day 5 Ayden (escaped the island); day 8 Mara (murdered); day 9 Szymon (executed after the trial); day 10 Noah (killed); day 11 Vixen (executed after the trial); day 13 Dario (murdered); day 15 Seul (executed after the trial); day 15 Hana (murdered); day 17 Kumiko (executed after the trial); day 18 Teo (murdered); day 20 Bram (executed after the trial); day 20 June (died in an accident); day 20 Ilya (murdered); day 22 Cail (escaped the island).

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
