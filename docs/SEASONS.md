# Whole mock seasons

40 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (20 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 21 (52%), bittersweet 0 (0%), bad 19 (48%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 11, bittersweet 0, bad 9.
- **NeoVi's fate:** none 12, betrayer 4, martyr 3, survivor 1. Romances at the end: 9 in all.
- **Season length:** median 21.5 days (shortest 7, longest 49).
- **How seasons ended:** THE LAST BATTLE 8, THE WINNERS 4, RESCUE 3, THE SHOW SURRENDERS 3, TEREVI IS SHUT DOWN 1, THE RECKONING 1.
- **Deaths per season:** 9.9 on average. Causes: murdered 50, executed after the trial 36, escaped the island 30, wrongly executed 29, killed 16, died in the final battle 14, escaped on a raft 8, died in the Reckoning 8.
- **Trials:** 66 in all, 36 right verdicts.
- **Newcomers:** 4.8 per season on average; 35 of the survivors were newcomers.
- **Rafts launched:** 4 (believed 3, sea 1). Rescue countdowns started: 3.
- **Ways out at the end:** the furthest route reached 76% on average (best 100%).
- **Who walked out alive (seasons):** Noah 5, Bram 5, Dario 5, June 4, Seul 4, Shintaro 3, Nadia 3, Rosa 3, Teo 3, Chloe 3, Szymon 2, Hana 2, Vixen 2, Ilya 2, Cail 2, Mara 2, Elsa 1, Ayden 1, Carmen 1, Lucas 1, Omar 1, Priya 1, Felix 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 11 | THE WINNERS | good | Noah, Shintaro, Szymon | 5 | 0 | 2 (1) |
| 2 | 33 | RESCUE | good | Bram, Elsa, June, Nadia, Rosa, Teo | 12 | 10 | 4 (2) |
| 3 | 38 | THE LAST BATTLE: DARIO STANDS | bad | Dario | 18 | 11 | 7 (5) |
| 4 | 25 | THE SHOW SURRENDERS | good | Bram, Dario, Hana, June, Rosa, Teo | 10 | 8 | 4 (2) |
| 5 | 14 | THE WINNERS | good | Ayden, Seul | 6 | 0 | 1 (0) |
| 6 | 9 | THE SHOW SURRENDERS | good | Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 2 | 0 | 1 (1) |
| 7 | 19 | TEREVI IS SHUT DOWN | good | Bram, Dario, Ilya, June, Vixen | 8 | 5 | 3 (1) |
| 8 | 10 | THE WINNERS | good | Cail, Chloe, Shintaro | 5 | 0 | 2 (1) |
| 9 | 49 | RESCUE | good | Carmen, Lucas, Omar, Priya | 22 | 18 | 8 (4) |
| 10 | 31 | THE LAST BATTLE: NADIA STANDS | bad | Nadia | 18 | 11 | 5 (3) |
| 11 | 24 | THE SHOW SURRENDERS | good | Bram, Dario, Ilya, Mara, Seul, Teo | 7 | 5 | 3 (3) |
| 12 | 28 | THE LAST BATTLE: HANA STANDS | bad | Hana | 14 | 7 | 5 (3) |
| 13 | 9 | THE LAST BATTLE: NOAH STANDS | bad | Noah | 7 | 0 | 2 (0) |
| 14 | 28 | THE LAST BATTLE: FELIX STANDS | bad | Felix | 14 | 7 | 5 (2) |
| 15 | 13 | THE LAST BATTLE: NOAH STANDS | bad | Noah | 7 | 0 | 2 (1) |
| 16 | 28 | THE LAST BATTLE: JUNE STANDS | bad | June | 12 | 5 | 4 (2) |
| 17 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 18 | 11 | THE LAST BATTLE: NOAH STANDS | bad | Noah | 7 | 0 | 2 (1) |
| 19 | 24 | RESCUE | good | Bram, Dario, Mara, Nadia, Rosa | 11 | 8 | 4 (3) |
| 20 | 14 | THE WINNERS | good | Cail, Chloe, Seul | 5 | 0 | 2 (1) |

## Violent mock cast

- **Ending tiers:** good 10, bittersweet 0, bad 10.
- **NeoVi's fate:** none 15, martyr 2, betrayer 2, survivor 1. Romances at the end: 0 in all.
- **Season length:** median 13.5 days (shortest 7, longest 43).
- **How seasons ended:** THE WINNERS 8, THE LAST BATTLE 7, NOBODY LEFT 2, TEREVI IS SHUT DOWN 1, THE SHOW SURRENDERS 1, CROWNED BY WHIM 1.
- **Deaths per season:** 11.2 on average. Causes: murdered 76, executed after the trial 69, killed 21, escaped the island 19, wrongly executed 18, died in the final battle 16, escaped on a raft 3, executed by TereVi's whim 2.
- **Trials:** 88 in all, 69 right verdicts.
- **Newcomers:** 5.2 per season on average; 20 of the survivors were newcomers.
- **Rafts launched:** 1 (sea 1). Rescue countdowns started: 0.
- **Ways out at the end:** the furthest route reached 67% on average (best 100%).
- **Who walked out alive (seasons):** Szymon 4, Ayden 4, Dario 3, Vixen 3, Ilya 3, June 3, Chloe 2, Hana 2, Shintaro 2, Nadia 2, Seul 2, Mara 1, Lena 1, Lucas 1, Priya 1, Cail 1, Rosa 1, Bram 1, Elsa 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 12 | THE WINNERS | good | Dario, Mara, Szymon | 8 | 3 | 3 (1) |
| 2 | 33 | THE LAST BATTLE: LENA STANDS | bad | Lena | 22 | 15 | 9 (7) |
| 3 | 43 | THE WINNERS | good | Lucas, Priya | 26 | 20 | 10 (9) |
| 4 | 19 | TEREVI IS SHUT DOWN | good | Cail, Chloe, Hana, Rosa | 12 | 8 | 6 (6) |
| 5 | 7 | THE WINNERS | good | Ayden, Chloe, Vixen | 5 | 0 | 2 (1) |
| 6 | 12 | THE LAST BATTLE: SHINTARO STANDS | bad | Shintaro | 11 | 4 | 4 (2) |
| 7 | 7 | THE WINNERS | good | Ayden, Szymon, Vixen | 5 | 0 | 2 (1) |
| 8 | 7 | THE WINNERS | good | Ayden, Shintaro, Szymon | 5 | 0 | 2 (1) |
| 9 | 7 | THE LAST BATTLE: AYDEN STANDS | bad | Ayden | 7 | 0 | 2 (1) |
| 10 | 13 | NOBODY LEFT | bad | none | 12 | 4 | 3 (3) |
| 11 | 24 | THE WINNERS | good | Bram, Ilya, Nadia | 14 | 9 | 6 (4) |
| 12 | 12 | THE WINNERS | good | Dario, June, Seul | 9 | 4 | 4 (3) |
| 13 | 31 | THE SHOW SURRENDERS | good | Dario, Hana, June, Nadia | 13 | 9 | 5 (5) |
| 14 | 7 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 7 | 0 | 2 (1) |
| 15 | 20 | THE LAST BATTLE: ILYA STANDS | bad | Ilya | 15 | 8 | 6 (5) |
| 16 | 14 | THE WINNERS | good | Szymon, Vixen | 6 | 0 | 3 (3) |
| 17 | 28 | THE LAST BATTLE: ELSA STANDS | bad | Elsa | 17 | 10 | 7 (6) |
| 18 | 19 | CROWNED BY WHIM: JUNE | bad | June | 13 | 6 | 5 (3) |
| 19 | 14 | THE LAST BATTLE: ILYA STANDS | bad | Ilya | 9 | 2 | 4 (4) |
| 20 | 13 | NOBODY LEFT | bad | none | 9 | 1 | 3 (3) |

## Notes on this run (2026-10-18, phase 7b step 3: the raft and the rescue)

These notes are written by hand and are not regenerated.

- The raft is now small (two or three), launches as a live scene, and does not end the show. The crew's journey is rolled off-screen each dawn.
- 5 rafts launched over 40 seasons; 3 crews were believed, which started a rescue countdown, and 3 seasons ended in a rescue (all with enough people alive, so good). A believed broadcast of the truth also starts a countdown now, rather than ending the show at once.
- Each route has its own pace (the raft quickest, the bomb slowest). The bomb threat and the raid still end seasons too.
- Tiers: 52% good, 0% bittersweet, 48% bad, against 40/30/30. Bittersweet endings come only from a lone survivor, a late rescue or a raft crew outliving the island, and none happened here. Step 7 (balance) is where the mix gets tuned.

## One season, told by its saga (violent seed 3: THE WINNERS, day 43)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 6: The house collapsed into a killing spree.
- Day 8: Vixen was found guilty and executed.
- Day 13: Seul was found guilty and executed.
- Day 15: Shintaro was found guilty and executed.
- Day 17: NeoVi's arc ended: martyr.
- Day 21: Ayden was found guilty and executed.
- Day 24: Mara was found guilty and executed. Dario was exposed as the killer's alibi, but TereVi tries only one culprit: whoever struck the blow.
- Day 26: Bram betrayed Felix.
- Day 26: Bram was found guilty and executed.
- Day 32: Kenji was found guilty and executed.
- Day 34: The house collapsed into a killing spree.
- Day 35: Hana betrayed Teo.
- Day 37: Hana was found guilty and executed.
- Day 41: Nadia betrayed Elsa.
- Day 41: Elsa was found guilty and executed. Nadia was exposed as the killer's alibi, but TereVi tries only one culprit: whoever struck the blow.
- Day 43: The cast voted wrongly: innocent Anton was executed and Nadia, the real culprit, escapes the island.
- Day 43: The cast tried to build a raft: it worked.

Deaths in order: day 6 Noah (murdered); day 6 Cail (murdered); day 8 Vixen (executed after the trial); day 11 Szymon (killed); day 13 Seul (executed after the trial); day 13 Ilya (killed); day 15 Shintaro (executed after the trial); day 20 Chloe (murdered); day 21 Ayden (executed after the trial); day 22 June (murdered); day 24 Mara (executed after the trial); day 25 Dario (murdered); day 26 Bram (executed after the trial); day 31 Felix (murdered); day 32 Kenji (executed after the trial); day 35 Omar (murdered); day 35 Teo (murdered); day 37 Hana (executed after the trial); day 40 Ravi (murdered); day 41 Elsa (executed after the trial); day 41 Rosa (killed); day 43 Anton (wrongly executed); day 43 Nadia (escaped the island); day 43 Emil (escaped on a raft); day 43 Malik (escaped on a raft); day 43 Lena (escaped on a raft).
