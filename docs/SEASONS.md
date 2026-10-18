# Whole mock seasons

40 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (20 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 20 (50%), bittersweet 3 (8%), bad 17 (42%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 13, bittersweet 1, bad 6.
- **NeoVi's fate:** martyr 7, none 6, participant 3, betrayer 3, survivor 1. Romances at the end: 3 in all.
- **Kumiko:** helped the cast 123 times; told someone her real name in 17 seasons; a romance with someone in 14; punished: re-education 11, humiliation 5, participant 3.
- **Season length:** median 20.0 days (shortest 9, longest 42).
- **How seasons ended:** THE SHOW SURRENDERS 7, THE WINNERS 4, THE LAST BATTLE 3, NOBODY LEFT 2, TEREVI IS SHUT DOWN 1, THE LAST ONE STANDING 1, RESCUE 1, CROWNED BY WHIM 1.
- **Deaths per season:** 9.4 on average. Causes: murdered 60, executed after the trial 40, escaped the island 25, wrongly executed 23, killed 15, died in the final battle 11, died in an accident 5, escaped on a raft 4.
- **Trials:** 65 in all, 40 right verdicts.
- **Newcomers:** 5.0 per season on average; 36 of the survivors were newcomers.
- **Rafts launched:** 2 (believed 1, sea 1). Rescue countdowns started: 1.
- **Ways out at the end:** the furthest route reached 89% on average (best 100%).
- **Who walked out alive (seasons):** Vixen 7, Seul 6, Shintaro 6, Ayden 5, Ilya 5, Bram 5, Mara 4, Hana 4, Chloe 3, Noah 3, Cail 3, Szymon 3, Nadia 3, Dario 2, June 2, Kumiko 2, Rosa 2, Teo 2, Elsa 2, Felix 2, Kenji 1, Omar 1, Priya 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 10 | TEREVI IS SHUT DOWN | good | Ayden, Chloe, Ilya, Mara, Noah, Seul, Shintaro, Vixen | 2 | 2 | 1 (1) |
| 2 | 26 | THE SHOW SURRENDERS | good | Bram, Dario, Hana, Ilya, June, Kumiko, Mara, Rosa, Teo | 8 | 8 | 3 (2) |
| 3 | 11 | THE SHOW SURRENDERS | good | Ayden, Cail, Ilya, June, Mara, Noah, Seul, Shintaro | 3 | 3 | 1 (0) |
| 4 | 12 | THE SHOW SURRENDERS | good | Cail, Chloe, Seul, Shintaro, Szymon, Vixen | 2 | 0 | 1 (1) |
| 5 | 10 | THE LAST BATTLE: VIXEN STANDS | bad | Vixen | 7 | 0 | 2 (1) |
| 6 | 25 | NOBODY LEFT | bad | none | 13 | 5 | 3 (2) |
| 7 | 20 | THE WINNERS | good | Bram, Dario, Mara | 9 | 4 | 4 (3) |
| 8 | 37 | THE SHOW SURRENDERS | good | Ilya, Kumiko, Nadia, Rosa | 14 | 9 | 6 (3) |
| 9 | 14 | THE SHOW SURRENDERS | good | Chloe, Seul, Shintaro, Szymon, Vixen | 3 | 0 | 1 (1) |
| 10 | 34 | THE LAST ONE STANDING | bittersweet | Bram | 19 | 12 | 6 (3) |
| 11 | 9 | THE SHOW SURRENDERS | good | Ayden, Noah, Seul, Shintaro, Szymon, Vixen | 2 | 0 | 1 (1) |
| 12 | 19 | THE LAST BATTLE: HANA STANDS | bad | Hana | 11 | 4 | 4 (3) |
| 13 | 30 | RESCUE | good | Bram, Elsa, Felix, Hana, Nadia, Teo | 13 | 11 | 4 (2) |
| 14 | 11 | THE WINNERS | good | Ayden, Cail, Vixen | 6 | 1 | 0 (0) |
| 15 | 34 | THE SHOW SURRENDERS | good | Bram, Elsa, Felix, Hana, Nadia | 14 | 11 | 6 (4) |
| 16 | 39 | THE WINNERS | good | Kenji, Omar, Priya | 19 | 14 | 7 (3) |
| 17 | 20 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 11 | 4 | 3 (2) |
| 18 | 42 | NOBODY LEFT | bad | none | 18 | 9 | 7 (6) |
| 19 | 21 | CROWNED BY WHIM: ILYA | bad | Ilya | 9 | 2 | 3 (1) |
| 20 | 14 | THE WINNERS | good | Ayden, Shintaro, Vixen | 5 | 0 | 2 (1) |

## Violent mock cast

- **Ending tiers:** good 7, bittersweet 2, bad 11.
- **NeoVi's fate:** none 9, betrayer 6, martyr 3, participant 1, survivor 1. Romances at the end: 2 in all.
- **Kumiko:** helped the cast 43 times; told someone her real name in 8 seasons; a romance with someone in 3; punished: re-education 2, participant 1, humiliation 1.
- **Season length:** median 16.0 days (shortest 7, longest 35).
- **How seasons ended:** CROWNED BY WHIM 5, THE LAST BATTLE 4, THE WINNERS 4, THE SHOW SURRENDERS 2, THE LAST ONE STANDING 2, THE RECKONING 1, NOBODY LEFT 1, TEREVI IS SHUT DOWN 1.
- **Deaths per season:** 11.4 on average. Causes: murdered 72, executed after the trial 71, escaped the island 20, wrongly executed 17, killed 16, died in the final battle 9, died in the Reckoning 8, executed by TereVi's whim 6.
- **Trials:** 91 in all, 71 right verdicts.
- **Newcomers:** 5.5 per season on average; 24 of the survivors were newcomers.
- **Rafts launched:** 1 (believed 1). Rescue countdowns started: 1.
- **Ways out at the end:** the furthest route reached 71% on average (best 100%).
- **Who walked out alive (seasons):** Vixen 5, Seul 5, Chloe 3, Teo 3, Ayden 3, Mara 3, Bram 3, June 3, Elsa 2, Felix 2, Ilya 2, Dario 2, Omar 1, Rosa 1, Cail 1, Nadia 1, Noah 1, Hana 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 28 | THE LAST BATTLE: ELSA STANDS | bad | Elsa | 19 | 12 | 9 (9) |
| 2 | 24 | THE SHOW SURRENDERS | good | Chloe, Felix, Ilya, Omar, Rosa, Teo, Vixen | 11 | 10 | 5 (5) |
| 3 | 14 | CROWNED BY WHIM: SEUL | bad | Seul | 9 | 2 | 4 (4) |
| 4 | 32 | CROWNED BY WHIM: TEO | bad | Teo | 15 | 7 | 6 (6) |
| 5 | 10 | THE SHOW SURRENDERS | good | Ayden, Cail, Ilya, Mara, Seul, Vixen | 4 | 2 | 2 (2) |
| 6 | 21 | THE LAST ONE STANDING | bittersweet | Bram | 13 | 6 | 6 (4) |
| 7 | 12 | THE WINNERS | good | Ayden, June, Vixen | 8 | 3 | 3 (2) |
| 8 | 14 | CROWNED BY WHIM: MARA | bad | Mara | 9 | 2 | 4 (4) |
| 9 | 35 | CROWNED BY WHIM: DARIO | bad | Dario | 21 | 14 | 8 (3) |
| 10 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 11 | 12 | THE LAST BATTLE: JUNE STANDS | bad | June | 9 | 2 | 3 (2) |
| 12 | 26 | NOBODY LEFT | bad | none | 17 | 9 | 6 (4) |
| 13 | 7 | THE WINNERS | good | Chloe, Seul, Vixen | 5 | 0 | 2 (1) |
| 14 | 24 | THE LAST BATTLE: BRAM STANDS | bad | Bram | 17 | 10 | 6 (4) |
| 15 | 7 | CROWNED BY WHIM: VIXEN | bad | Vixen | 7 | 0 | 2 (0) |
| 16 | 27 | THE WINNERS | good | Bram, Elsa, Nadia | 15 | 10 | 7 (6) |
| 17 | 12 | THE LAST ONE STANDING | bittersweet | Noah | 9 | 2 | 4 (3) |
| 18 | 12 | THE WINNERS | good | Chloe, Dario, Seul | 8 | 3 | 3 (1) |
| 19 | 21 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 15 | 8 | 6 (6) |
| 20 | 18 | TEREVI IS SHUT DOWN | good | Ayden, Felix, Hana, June, Mara, Teo | 10 | 8 | 5 (5) |

## Notes on this run (2026-10-18, phase 7b step 4: NeoVi as Kumiko)

These notes are written by hand and are not regenerated.

- NeoVi now visits one door a night, feelings grow both ways, and she confides once trust is mutual. She told someone her real name in 25 of 40 seasons and fell in love with someone in 17.
- She helped the cast 166 times in all (a part, the locks, a camera, covering for someone). Caught helping, TereVi re-educated her 13 times, humiliated her on air 6 times and made her a contestant 4 times. Kumiko then plays as a participant; she walked out alive in 2 of those 4 seasons, and no newcomers came after her.
- Tiers: 50% good, 8% bittersweet, 42% bad, against 40/30/30. Step 7 (balance) tunes the mix.

## One season, told by its saga (violent seed 9: CROWNED BY WHIM: DARIO, day 35)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 5: The cast voted wrongly: innocent Chloe was executed and Seul, the real culprit, escapes the island.
- Day 8: The cast voted wrongly: innocent Mara was executed and Cail, the real culprit, escapes the island.
- Day 13: NeoVi's arc ended: martyr.
- Day 14: Szymon betrayed Ilya.
- Day 14: Szymon betrayed Vixen.
- Day 14: June betrayed Szymon.
- Day 15: Ilya was found guilty and executed. Szymon was exposed as the killer's cleanup, but TereVi tries only one culprit: whoever struck the blow.
- Day 20: Vixen betrayed Szymon.
- Day 20: Szymon was found guilty and executed.
- Day 26: The cast could not agree. Hana, the culprit, escapes the island.
- Day 28: Teo was found guilty and executed.
- Day 30: The cast voted wrongly: innocent Felix was executed and Vixen, the real culprit, escapes the island.
- Day 35: Elsa betrayed Priya.
- Day 35: The cast could not agree. Priya, the culprit, escapes the island.

Deaths in order: day 3 Shintaro (murdered); day 5 Chloe (wrongly executed); day 5 Seul (escaped the island); day 6 Noah (was poisoned); day 8 Mara (wrongly executed); day 8 Cail (escaped the island); day 14 Ayden (murdered); day 15 Ilya (executed after the trial); day 19 Rosa (murdered); day 20 Szymon (executed after the trial); day 24 June (murdered); day 26 Hana (escaped the island); day 27 Bram (killed); day 28 Teo (executed after the trial); day 28 Nadia (murdered); day 30 Felix (wrongly executed); day 30 Vixen (escaped the island); day 33 Omar (murdered); day 35 Priya (escaped the island); day 35 Elsa (executed by TereVi's whim); day 35 Kenji (executed by TereVi's whim).
