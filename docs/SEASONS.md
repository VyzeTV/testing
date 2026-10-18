# Whole mock seasons

40 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (20 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

## Default

- **Season length:** median 30.0 days (shortest 7, longest 98).
- **How seasons ended:** THE LAST BATTLE 7, THE WINNERS 6, CROWNED BY WHIM 5, NOBODY LEFT 1, THE RECKONING 1.
- **Deaths per season:** 16.8 on average. Causes: murdered 84, executed after the trial 77, escaped the island 48, wrongly executed 44, killed 32, died in the final battle 16, was poisoned 10, executed by TereVi's whim 8.
- **Trials:** 125 in all, 77 right verdicts.
- **Newcomers:** 10.2 per season on average; 20 of the survivors were newcomers.
- **Ways out at the end:** the furthest route reached 63% on average (best 100%).
- **Who walked out alive (seasons):** Chloe 3, Mara 3, Shintaro 2, Rosa 2, Bram 2, Yuki 2, Priya 2, Teo 2, Seul 2, Ines 1, Ilya 1, Elsa 1, Dario 1, Omar 1, Ravi 1, Szymon 1, Carmen 1.

| Season | Days | Ending | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 21 | THE LAST BATTLE: SHINTARO STANDS | Shintaro | 9 | 2 | 3 (2) |
| 2 | 28 | THE LAST BATTLE: ROSA STANDS | Rosa | 13 | 6 | 5 (4) |
| 3 | 27 | THE LAST BATTLE: BRAM STANDS | Bram | 13 | 6 | 4 (2) |
| 4 | 59 | CROWNED BY WHIM: INES | Ines | 28 | 21 | 12 (9) |
| 5 | 20 | THE WINNERS | Chloe, Ilya, Mara | 8 | 3 | 3 (1) |
| 6 | 56 | CROWNED BY WHIM: YUKI | Yuki | 27 | 20 | 10 (6) |
| 7 | 42 | THE WINNERS | Elsa, Priya, Teo | 16 | 11 | 6 (3) |
| 8 | 21 | THE WINNERS | Bram, Dario, Mara | 10 | 5 | 4 (2) |
| 9 | 98 | NOBODY LEFT | none | 38 | 30 | 16 (13) |
| 10 | 48 | CROWNED BY WHIM: PRIYA | Priya | 21 | 14 | 8 (5) |
| 11 | 14 | THE WINNERS | Chloe, Seul | 6 | 0 | 2 (1) |
| 12 | 55 | THE LAST BATTLE: YUKI STANDS | Yuki | 27 | 20 | 10 (5) |
| 13 | 32 | THE WINNERS | Omar, Rosa | 16 | 10 | 6 (2) |
| 14 | 65 | THE LAST BATTLE: RAVI STANDS | Ravi | 30 | 23 | 11 (6) |
| 15 | 11 | CROWNED BY WHIM: SEUL | Seul | 7 | 0 | 2 (0) |
| 16 | 32 | THE LAST BATTLE: TEO STANDS | Teo | 14 | 7 | 5 (4) |
| 17 | 21 | THE WINNERS | Mara, Shintaro, Szymon | 7 | 2 | 3 (2) |
| 18 | 74 | THE LAST BATTLE: CARMEN STANDS | Carmen | 31 | 24 | 13 (10) |
| 19 | 7 | THE RECKONING | none | 8 | 0 | 0 (0) |
| 20 | 11 | CROWNED BY WHIM: CHLOE | Chloe | 7 | 0 | 2 (0) |

## Violent mock cast

- **Season length:** median 19.0 days (shortest 6, longest 48).
- **How seasons ended:** THE LAST BATTLE 9, THE WINNERS 6, CROWNED BY WHIM 3, NOBODY LEFT 2.
- **Deaths per season:** 13.6 on average. Causes: murdered 86, executed after the trial 73, escaped the island 28, killed 27, wrongly executed 26, died in the final battle 21, executed by TereVi's whim 5, died in an accident 3.
- **Trials:** 101 in all, 73 right verdicts.
- **Newcomers:** 7.1 per season on average; 19 of the survivors were newcomers.
- **Ways out at the end:** the furthest route reached 45% on average (best 99%).
- **Who walked out alive (seasons):** Cail 3, June 3, Chloe 2, Ilya 2, Szymon 2, Hana 2, Vixen 2, Nadia 2, Mara 1, Seul 1, Shintaro 1, Elsa 1, Omar 1, Malik 1, Ravi 1, Carmen 1, Lena 1, Bram 1, Felix 1, Rosa 1.

| Season | Days | Ending | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 21 | THE LAST BATTLE: CHLOE STANDS | Chloe | 13 | 6 | 6 (6) |
| 2 | 13 | THE WINNERS | Ilya, Mara, Szymon | 9 | 4 | 4 (3) |
| 3 | 7 | THE WINNERS | Cail, Seul, Szymon | 5 | 0 | 2 (1) |
| 4 | 7 | CROWNED BY WHIM: SHINTARO | Shintaro | 7 | 0 | 2 (0) |
| 5 | 18 | THE WINNERS | Chloe, Hana, Ilya | 9 | 4 | 4 (4) |
| 6 | 6 | THE LAST BATTLE: VIXEN STANDS | Vixen | 7 | 0 | 2 (1) |
| 7 | 25 | THE LAST BATTLE: NADIA STANDS | Nadia | 18 | 11 | 7 (5) |
| 8 | 6 | THE LAST BATTLE: CAIL STANDS | Cail | 7 | 0 | 1 (1) |
| 9 | 24 | NOBODY LEFT | none | 15 | 7 | 5 (3) |
| 10 | 19 | CROWNED BY WHIM: ELSA | Elsa | 14 | 7 | 6 (5) |
| 11 | 40 | THE LAST BATTLE: OMAR STANDS | Omar | 24 | 17 | 8 (5) |
| 12 | 38 | THE WINNERS | Malik, Nadia, Ravi | 22 | 17 | 8 (6) |
| 13 | 48 | CROWNED BY WHIM: CARMEN | Carmen | 27 | 20 | 10 (8) |
| 14 | 13 | THE WINNERS | Cail, June, Vixen | 8 | 3 | 3 (1) |
| 15 | 40 | THE LAST BATTLE: LENA STANDS | Lena | 24 | 17 | 9 (7) |
| 16 | 13 | THE LAST BATTLE: HANA STANDS | Hana | 12 | 5 | 4 (2) |
| 17 | 12 | NOBODY LEFT | none | 10 | 2 | 3 (2) |
| 18 | 19 | THE LAST BATTLE: JUNE STANDS | June | 13 | 6 | 5 (4) |
| 19 | 20 | THE LAST BATTLE: JUNE STANDS | June | 13 | 6 | 5 (3) |
| 20 | 26 | THE WINNERS | Bram, Felix, Rosa | 15 | 10 | 7 (6) |

## Notes on this run (2026-10-18, after phase 7)

These notes are written by hand and are not regenerated.

- With the weekly refill, seasons run about twice as long as without it (median 30 days in the default configuration, against 15.5 before), and 14 to 17 people die in a season instead of about 6.
- Every season in this run ended through killing: TereVi's endgame when three or fewer were left, nobody left, or the Reckoning. In an earlier run of the same script, 2 of 20 default seasons ended with TereVi shut down.
- The ways out need every step of a route at 100%. The furthest route ended at about 45 to 63% on average. In default season 9 a team tried to shut TereVi down on day 90 and failed; nobody was left by day 98. Escapes are reachable, but rare and late.
- Most survivors are newcomers: 20 of 28 in the default configuration and 19 of 30 in the violent one. Arriving later means fewer days at risk.
- Killers who get away after a wrong verdict count as "escaped the island": they leave alive.
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
