# Whole mock seasons

40 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (20 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 12 (30%), bittersweet 0 (0%), bad 28 (70%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 6, bittersweet 0, bad 14.
- **NeoVi's fate:** betrayer 7, martyr 5, survivor 4, none 4. Romances at the end: 2 in all.
- **Season length:** median 30.0 days (shortest 7, longest 98).
- **How seasons ended:** THE LAST BATTLE 7, THE WINNERS 6, CROWNED BY WHIM 5, NOBODY LEFT 1, THE RECKONING 1.
- **Deaths per season:** 16.8 on average. Causes: murdered 84, executed after the trial 77, escaped the island 48, wrongly executed 44, killed 32, died in the final battle 16, was poisoned 10, executed by TereVi's whim 8.
- **Trials:** 125 in all, 77 right verdicts.
- **Newcomers:** 10.2 per season on average; 20 of the survivors were newcomers.
- **Ways out at the end:** the furthest route reached 63% on average (best 100%).
- **Who walked out alive (seasons):** Chloe 3, Mara 3, Shintaro 2, Rosa 2, Bram 2, Yuki 2, Priya 2, Teo 2, Seul 2, Ines 1, Ilya 1, Elsa 1, Dario 1, Omar 1, Ravi 1, Szymon 1, Carmen 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 21 | THE LAST BATTLE: SHINTARO STANDS | bad | Shintaro | 9 | 2 | 3 (2) |
| 2 | 28 | THE LAST BATTLE: ROSA STANDS | bad | Rosa | 13 | 6 | 5 (4) |
| 3 | 27 | THE LAST BATTLE: BRAM STANDS | bad | Bram | 13 | 6 | 4 (2) |
| 4 | 59 | CROWNED BY WHIM: INES | bad | Ines | 28 | 21 | 12 (9) |
| 5 | 20 | THE WINNERS | good | Chloe, Ilya, Mara | 8 | 3 | 3 (1) |
| 6 | 56 | CROWNED BY WHIM: YUKI | bad | Yuki | 27 | 20 | 10 (6) |
| 7 | 42 | THE WINNERS | good | Elsa, Priya, Teo | 16 | 11 | 6 (3) |
| 8 | 21 | THE WINNERS | good | Bram, Dario, Mara | 10 | 5 | 4 (2) |
| 9 | 98 | NOBODY LEFT | bad | none | 38 | 30 | 16 (13) |
| 10 | 48 | CROWNED BY WHIM: PRIYA | bad | Priya | 21 | 14 | 8 (5) |
| 11 | 14 | THE WINNERS | good | Chloe, Seul | 6 | 0 | 2 (1) |
| 12 | 55 | THE LAST BATTLE: YUKI STANDS | bad | Yuki | 27 | 20 | 10 (5) |
| 13 | 32 | THE WINNERS | good | Omar, Rosa | 16 | 10 | 6 (2) |
| 14 | 65 | THE LAST BATTLE: RAVI STANDS | bad | Ravi | 30 | 23 | 11 (6) |
| 15 | 11 | CROWNED BY WHIM: SEUL | bad | Seul | 7 | 0 | 2 (0) |
| 16 | 32 | THE LAST BATTLE: TEO STANDS | bad | Teo | 14 | 7 | 5 (4) |
| 17 | 21 | THE WINNERS | good | Mara, Shintaro, Szymon | 7 | 2 | 3 (2) |
| 18 | 74 | THE LAST BATTLE: CARMEN STANDS | bad | Carmen | 31 | 24 | 13 (10) |
| 19 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 20 | 11 | CROWNED BY WHIM: CHLOE | bad | Chloe | 7 | 0 | 2 (0) |

## Violent mock cast

- **Ending tiers:** good 6, bittersweet 0, bad 14.
- **NeoVi's fate:** none 13, betrayer 3, survivor 3, martyr 1. Romances at the end: 3 in all.
- **Season length:** median 19.0 days (shortest 6, longest 48).
- **How seasons ended:** THE LAST BATTLE 9, THE WINNERS 6, CROWNED BY WHIM 3, NOBODY LEFT 2.
- **Deaths per season:** 13.6 on average. Causes: murdered 86, executed after the trial 73, escaped the island 28, killed 27, wrongly executed 26, died in the final battle 21, executed by TereVi's whim 5, died in an accident 3.
- **Trials:** 101 in all, 73 right verdicts.
- **Newcomers:** 7.1 per season on average; 19 of the survivors were newcomers.
- **Ways out at the end:** the furthest route reached 45% on average (best 99%).
- **Who walked out alive (seasons):** Cail 3, June 3, Chloe 2, Ilya 2, Szymon 2, Hana 2, Vixen 2, Nadia 2, Mara 1, Seul 1, Shintaro 1, Elsa 1, Omar 1, Malik 1, Ravi 1, Carmen 1, Lena 1, Bram 1, Felix 1, Rosa 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 21 | THE LAST BATTLE: CHLOE STANDS | bad | Chloe | 13 | 6 | 6 (6) |
| 2 | 13 | THE WINNERS | good | Ilya, Mara, Szymon | 9 | 4 | 4 (3) |
| 3 | 7 | THE WINNERS | good | Cail, Seul, Szymon | 5 | 0 | 2 (1) |
| 4 | 7 | CROWNED BY WHIM: SHINTARO | bad | Shintaro | 7 | 0 | 2 (0) |
| 5 | 18 | THE WINNERS | good | Chloe, Hana, Ilya | 9 | 4 | 4 (4) |
| 6 | 6 | THE LAST BATTLE: VIXEN STANDS | bad | Vixen | 7 | 0 | 2 (1) |
| 7 | 25 | THE LAST BATTLE: NADIA STANDS | bad | Nadia | 18 | 11 | 7 (5) |
| 8 | 6 | THE LAST BATTLE: CAIL STANDS | bad | Cail | 7 | 0 | 1 (1) |
| 9 | 24 | NOBODY LEFT | bad | none | 15 | 7 | 5 (3) |
| 10 | 19 | CROWNED BY WHIM: ELSA | bad | Elsa | 14 | 7 | 6 (5) |
| 11 | 40 | THE LAST BATTLE: OMAR STANDS | bad | Omar | 24 | 17 | 8 (5) |
| 12 | 38 | THE WINNERS | good | Malik, Nadia, Ravi | 22 | 17 | 8 (6) |
| 13 | 48 | CROWNED BY WHIM: CARMEN | bad | Carmen | 27 | 20 | 10 (8) |
| 14 | 13 | THE WINNERS | good | Cail, June, Vixen | 8 | 3 | 3 (1) |
| 15 | 40 | THE LAST BATTLE: LENA STANDS | bad | Lena | 24 | 17 | 9 (7) |
| 16 | 13 | THE LAST BATTLE: HANA STANDS | bad | Hana | 12 | 5 | 4 (2) |
| 17 | 12 | NOBODY LEFT | bad | none | 10 | 2 | 3 (2) |
| 18 | 19 | THE LAST BATTLE: JUNE STANDS | bad | June | 13 | 6 | 5 (4) |
| 19 | 20 | THE LAST BATTLE: JUNE STANDS | bad | June | 13 | 6 | 5 (3) |
| 20 | 26 | THE WINNERS | good | Bram, Felix, Rosa | 15 | 10 | 7 (6) |

## Notes on this run (2026-10-18, phase 7b step 1: the baseline)

These notes are written by hand and are not regenerated.

- This is the baseline before the ways out are reworked: 30% good, 0% bittersweet, 70% bad, against a target of 40/30/30.
- Every good ending here is TereVi crowning two or three survivors. No season ended through a way out, and none left a single crowned survivor, so nothing was bittersweet.
- Bad endings are mostly the final battle and crowning one on a whim (the others executed), then nobody left and the Reckoning.
- With the weekly refill, seasons run a median of about 30 days in the default configuration; most survivors are newcomers.
- NeoVi's arc reaches a fate in most default seasons (betrayer most often), and in only a third of the violent ones, which end sooner.
- After the 8 newcomer sketches run out, later newcomers reuse those personalities under new names.

## One season, told by its saga (default seed 9: NOBODY LEFT, day 98)

- Day 22: Vixen betrayed Dario.
- Day 22: Dario was found guilty and executed.
- Day 26: Noah was found guilty and executed.
- Day 32: Chloe was found guilty and executed.
- Day 40: Hana betrayed June.
- Day 40: Omar was found guilty and executed.
- Day 42: Seul betrayed Felix.
- Day 45: Bram was found guilty and executed.
- Day 51: Seul was found guilty and executed.
- Day 53: Kenji was found guilty and executed.
- Day 60: The cast voted wrongly: innocent Felix was executed and Nadia, the real culprit, escapes the island.
- Day 66: Yuki betrayed Ravi.
- Day 66: Ravi was found guilty and executed.
- Day 73: Lucas betrayed Anton.
- Day 73: The cast voted wrongly: innocent Anton was executed and Lucas, the real culprit, escapes the island.
- Day 81: Zoe betrayed Tomas.
- Day 84: Carmen was found guilty and executed.
- Day 90: Zoe betrayed Tomas.
- Day 90: Tomas was found guilty and executed.
- Day 90: The cast tried to threaten to blow up the island: it failed.
- Day 91: Malik betrayed Zoe.
- Day 95: Malik was found guilty and executed.
- Day 98: Zoe betrayed Greta.
- Day 98: The cast voted wrongly: innocent Hugo was executed and Greta, the real culprit, escapes the island. Zoe was exposed as the killer's alibi, but TereVi tries only one culprit: whoever struck the

Deaths in order: day 7 Cail (murdered); day 8 Ayden (executed after the trial); day 12 Szymon (was poisoned); day 14 Shintaro (executed after the trial); day 21 Mara (murdered); day 22 Dario (executed after the trial); day 25 Vixen (murdered); day 26 Noah (executed after the trial); day 31 Ilya (murdered); day 32 Chloe (executed after the trial); day 39 Rosa (murdered); day 40 Omar (executed after the trial); day 44 June (murdered); day 45 Bram (executed after the trial); day 49 Hana (was poisoned); day 51 Seul (executed after the trial); day 51 Teo (murdered); day 53 Kenji (executed after the trial); day 58 Elsa (killed); day 60 Felix (wrongly executed); day 60 Nadia (escaped the island); day 64 Lena (murdered); day 66 Ravi (executed after the trial); day 71 Yuki (murdered); day 73 Anton (wrongly executed); day 73 Lucas (escaped the island); day 82 Priya (murdered); day 84 Carmen (executed after the trial); day 88 Emil (murdered); day 90 Tomas (executed after the trial); day 94 Ines (murdered); day 95 Malik (executed after the trial); day 96 Tamsin (murdered); day 98 Hugo (wrongly executed); day 98 Greta (escaped the island); day 98 Zoe (died in the final battle); day 98 Joon (died in the final battle); day 98 Pavel (died in the final battle).
