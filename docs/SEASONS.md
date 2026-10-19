# Whole mock seasons

80 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (40 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 29 (36%), bittersweet 23 (29%), bad 28 (35%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 21, bittersweet 9, bad 10.
- **NeoVi's fate:** none 21, participant 7, martyr 6, betrayer 4, dead 1, survivor 1. Romances at the end: 25 in all.
- **Kumiko:** helped the cast 117 times; told someone her real name in 30 seasons; a romance with someone in 22; punished: re-education 8, humiliation 4, participant 3.
- **Minds:** 3739 thoughts shown; 62 beliefs warped by fear, 46 hallucinations, 19 false memories of a crime scene, 11 seen through later; acted on: 0 paranoid plots, 11 hid; 8 plotters overheard muttering; 12 trials heard testimony from a broken mind.
- **Rare turns:** took blame 3, killer helps 2, neovi defects 1.
- **Love life:** 95 nights together, 11 affairs (3 found out), 13 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 4, one survivor or fewer walked out of the house 3, TereVi took someone with her 2, someone never came out of the house 1, NeoVi gave her life for it 1.
- **Killers the show let go:** 18; 2 tried to help from outside (believed 0, dismissed 0), the rest kept quiet or gave up.
- **NeoVi's body and mind:** fights 2, people she killed 0, sabotage of TereVi 5; she died in 1 seasons (murdered 1); her sanity at the end: median 78.
- **NeoVi joined the cast** after the fourth trial in 4 seasons, as a punishment in 3. Seasons that ran the full 28 days: 2.
- **Stories that formed** (story sifting): secret held 305, enemies alone 284, plot 150, near freedom 140, triangle 138, betrayed protector 113, silent witness 95, plot suspected 66, contradiction fear 64, grudge 38, lovers breaking 6, unrequited 5, alliance strain 5.
- **Season length:** median 12.0 days (shortest 3, longest 28).
- **How seasons ended:** THE SHOW SURRENDERS 11, TEREVI IS SHUT DOWN 9, RESCUE 6, THE LAST BATTLE 5, THE RECKONING 2, CROWNED BY WHIM 2, THE LAST ONE STANDING 2, THE WINNERS 2, NOBODY LEFT 1.
- **Deaths per season:** 6.6 on average. Causes: murdered 70, executed after the trial 54, escaped on a raft 41, escaped the island 18, wrongly executed 17, died in the Reckoning 14, died in an accident 11, died in the final battle 11.
- **Trials:** 72 in all, 54 right verdicts.
- **Newcomers:** 2.3 per season on average; 55 of the survivors were newcomers.
- **Rafts launched:** 24 (believed 11, sea 7, dismissed 2, ashore 2, lost 2). Rescue countdowns started: 12.
- **Ways out at the end:** the furthest route reached 76% on average (best 100%).
- **Who walked out alive (seasons):** Ilya 16, Chloe 14, Shintaro 14, Ayden 13, Seul 12, Noah 12, Cail 11, Dario 11, Vixen 11, Mara 11, Szymon 9, June 8, Bram 3, Kumiko 3, Hana 2, Rosa 2, Teo 2.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 10 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Dario, Ilya, Seul, Szymon, Vixen | 2 | 2 | 1 (1) |
| 2 | 12 | TEREVI IS SHUT DOWN | good | Bram, Cail, Chloe, Dario, Ilya, Mara, Noah, Seul | 4 | 4 | 1 (1) |
| 3 | 8 | THE SHOW SURRENDERS | bittersweet | Ayden, Chloe, Ilya, Mara, Noah | 5 | 2 | 1 (1) |
| 4 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 5 | 20 | TEREVI IS SHUT DOWN | good | Dario, June, Seul | 11 | 5 | 3 (1) |
| 6 | 8 | RESCUE | bittersweet | Chloe, Dario, Ilya, Seul, Vixen | 5 | 2 | 1 (1) |
| 7 | 13 | RESCUE | good | Cail, Noah, Vixen | 5 | 0 | 1 (1) |
| 8 | 16 | THE SHOW SURRENDERS | bittersweet | Mara | 9 | 2 | 3 (2) |
| 9 | 16 | RESCUE | good | Dario, June, Mara, Shintaro, Szymon | 7 | 4 | 2 (2) |
| 10 | 28 | TEREVI IS SHUT DOWN | good | Hana, Ilya, June, Kumiko, Mara, Rosa, Teo | 10 | 8 | 4 (3) |
| 11 | 13 | RESCUE | good | Cail, Noah, Seul, Shintaro, Vixen | 3 | 0 | 0 (0) |
| 12 | 9 | THE SHOW SURRENDERS | good | Ayden, Chloe, June, Mara, Shintaro, Szymon, Vixen | 3 | 2 | 1 (1) |
| 13 | 3 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 14 | 11 | CROWNED BY WHIM: NOAH | bad | Noah | 7 | 0 | 2 (2) |
| 15 | 18 | THE LAST BATTLE: ILYA STANDS | bad | Ilya | 9 | 2 | 3 (2) |
| 16 | 28 | THE LAST BATTLE: TEO STANDS | bad | Teo | 16 | 8 | 5 (4) |
| 17 | 13 | THE LAST BATTLE: KUMIKO STANDS | bad | Kumiko | 10 | 2 | 2 (2) |
| 18 | 10 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Dario, Ilya, Shintaro | 4 | 2 | 1 (1) |
| 19 | 6 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 20 | 12 | THE SHOW SURRENDERS | bittersweet | Bram, Chloe, Dario, Ilya | 7 | 3 | 1 (0) |
| 21 | 26 | NOBODY LEFT | bad | none | 16 | 7 | 5 (4) |
| 22 | 8 | THE SHOW SURRENDERS | good | Ayden, Ilya, Mara, Noah, Seul, Shintaro | 4 | 2 | 1 (1) |
| 23 | 6 | THE SHOW SURRENDERS | good | Ayden, Chloe, Shintaro, Szymon, Vixen | 3 | 0 | 1 (0) |
| 24 | 7 | TEREVI IS SHUT DOWN | good | Ayden, Shintaro, Vixen | 5 | 0 | 1 (0) |
| 25 | 7 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 7 | 0 | 1 (0) |
| 26 | 19 | TEREVI IS SHUT DOWN | good | Ayden, Hana, June, Mara, Noah, Shintaro | 5 | 3 | 2 (2) |
| 27 | 8 | CROWNED BY WHIM: NOAH | bad | Noah | 7 | 0 | 1 (0) |
| 28 | 22 | THE LAST BATTLE: KUMIKO STANDS | bad | Kumiko | 9 | 1 | 3 (3) |
| 29 | 14 | THE LAST ONE STANDING | bittersweet | Mara | 9 | 2 | 2 (1) |
| 30 | 16 | THE LAST ONE STANDING | bittersweet | Shintaro | 7 | 0 | 2 (2) |
| 31 | 13 | THE SHOW SURRENDERS | good | Chloe, Dario, Ilya, Shintaro, Vixen | 5 | 2 | 2 (0) |
| 32 | 10 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Ilya, Mara, Noah, Seul, Szymon | 2 | 2 | 1 (1) |
| 33 | 5 | THE SHOW SURRENDERS | bittersweet | Ayden, Cail, Chloe, Seul, Vixen | 3 | 0 | 0 (0) |
| 34 | 11 | THE WINNERS | bittersweet | Dario, Ilya, Shintaro | 7 | 2 | 2 (1) |
| 35 | 24 | THE SHOW SURRENDERS | good | Ilya, June, Szymon | 11 | 5 | 4 (3) |
| 36 | 27 | THE WINNERS | bittersweet | Ilya, June | 13 | 6 | 6 (6) |
| 37 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 38 | 27 | RESCUE | good | Bram, Dario, Ilya, Rosa | 11 | 7 | 3 (2) |
| 39 | 17 | RESCUE | good | Cail, Dario, Ilya, June, Mara, Shintaro | 6 | 4 | 2 (2) |
| 40 | 8 | TEREVI IS SHUT DOWN | good | Ayden, Cail, Chloe, Noah, Seul, Szymon | 2 | 0 | 1 (1) |

## Violent mock cast

- **Ending tiers:** good 8, bittersweet 14, bad 18.
- **NeoVi's fate:** none 22, participant 11, martyr 4, betrayer 2, dead 1. Romances at the end: 8 in all.
- **Kumiko:** helped the cast 61 times; told someone her real name in 17 seasons; a romance with someone in 8; punished: re-education 8, humiliation 5, participant 1.
- **Minds:** 2897 thoughts shown; 36 beliefs warped by fear, 41 hallucinations, 14 false memories of a crime scene, 6 seen through later; acted on: 0 paranoid plots, 11 hid; 12 plotters overheard muttering; 9 trials heard testimony from a broken mind.
- **Rare turns:** confession 6, neovi defects 3, killer helps 2, took blame 2, killer believed 1.
- **Love life:** 54 nights together, 7 affairs (4 found out), 5 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): TereVi took someone with her 7, only the last few of a killing game walked out 7, one survivor or fewer walked out of the house 3, NeoVi gave her life for it 1.
- **Killers the show let go:** 29; 2 tried to help from outside (believed 1, dismissed 0), the rest kept quiet or gave up.
- **NeoVi's body and mind:** fights 0, people she killed 0, sabotage of TereVi 0; she died in 1 seasons (suicide 1); her sanity at the end: median 71.
- **NeoVi joined the cast** after the fourth trial in 10 seasons, as a punishment in 1. Seasons that ran the full 28 days: 0.
- **Stories that formed** (story sifting): plot 228, silent witness 146, enemies alone 137, near freedom 129, secret held 126, triangle 102, plot suspected 101, betrayed protector 72, contradiction fear 66, grudge 41, unrequited 9, alliance strain 4, lovers breaking 3.
- **Season length:** median 12.0 days (shortest 3, longest 26).
- **How seasons ended:** THE LAST BATTLE 14, THE SHOW SURRENDERS 10, THE WINNERS 5, TEREVI IS SHUT DOWN 3, NOBODY LEFT 2, RESCUE 2, THE LAST ONE STANDING 2, THE RECKONING 1, CROWNED BY WHIM 1.
- **Deaths per season:** 8.2 on average. Causes: murdered 86, executed after the trial 81, escaped the island 29, escaped on a raft 26, killed 25, died in the final battle 25, wrongly executed 24, died in an accident 10.
- **Trials:** 110 in all, 81 right verdicts.
- **Newcomers:** 2.3 per season on average; 29 of the survivors were newcomers.
- **Rafts launched:** 15 (sea 9, believed 3, silenced 2, lost 1). Rescue countdowns started: 5.
- **Ways out at the end:** the furthest route reached 67% on average (best 100%).
- **Who walked out alive (seasons):** Chloe 11, Seul 9, Ayden 9, Szymon 9, Cail 9, Mara 8, Vixen 7, Ilya 6, Noah 5, Shintaro 5, Dario 5, June 5, Kumiko 4, Bram 3, Hana 2.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 13 | THE LAST BATTLE: MARA STANDS | bad | Mara | 9 | 2 | 2 (1) |
| 2 | 14 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 9 | 2 | 3 (3) |
| 3 | 6 | THE LAST BATTLE: VIXEN STANDS | bad | Vixen | 7 | 0 | 2 (1) |
| 4 | 18 | THE LAST BATTLE: MARA STANDS | bad | Mara | 12 | 4 | 4 (4) |
| 5 | 5 | TEREVI IS SHUT DOWN | bittersweet | Ayden, Chloe, Noah, Seul, Shintaro | 3 | 0 | 0 (0) |
| 6 | 12 | THE LAST BATTLE: VIXEN STANDS | bad | Vixen | 10 | 3 | 3 (2) |
| 7 | 6 | THE SHOW SURRENDERS | good | Ayden, Chloe, Noah, Szymon | 4 | 0 | 2 (2) |
| 8 | 11 | THE LAST BATTLE: CAIL STANDS | bad | Cail | 11 | 4 | 3 (2) |
| 9 | 14 | THE RECKONING | bad | none | 11 | 3 | 2 (1) |
| 10 | 6 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Shintaro, Szymon, Vixen | 2 | 0 | 1 (1) |
| 11 | 11 | THE SHOW SURRENDERS | good | Seul, Szymon | 8 | 2 | 3 (1) |
| 12 | 13 | NOBODY LEFT | bad | none | 10 | 2 | 3 (2) |
| 13 | 3 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 14 | 16 | THE SHOW SURRENDERS | good | Bram, Dario, Hana, June, Kumiko, Mara, Szymon | 8 | 6 | 4 (4) |
| 15 | 6 | THE SHOW SURRENDERS | good | Chloe, Shintaro, Vixen | 5 | 0 | 2 (1) |
| 16 | 23 | THE WINNERS | bittersweet | Ayden, Kumiko | 11 | 4 | 5 (4) |
| 17 | 11 | RESCUE | good | Bram, Cail, Dario, Ilya, June, Mara, Seul | 6 | 5 | 2 (1) |
| 18 | 15 | THE LAST BATTLE: SZYMON STANDS | bad | Szymon | 10 | 2 | 4 (3) |
| 19 | 15 | THE LAST BATTLE: KUMIKO STANDS | bad | Kumiko | 12 | 4 | 5 (5) |
| 20 | 7 | THE WINNERS | bittersweet | Cail, Noah | 6 | 0 | 2 (1) |
| 21 | 19 | THE LAST ONE STANDING | bittersweet | Ilya | 12 | 4 | 5 (4) |
| 22 | 12 | THE SHOW SURRENDERS | bittersweet | Ayden, June, Mara | 7 | 2 | 2 (1) |
| 23 | 13 | THE WINNERS | bittersweet | Ilya, Mara | 11 | 5 | 3 (2) |
| 24 | 15 | CROWNED BY WHIM: KUMIKO | bad | Kumiko | 11 | 3 | 4 (4) |
| 25 | 26 | NOBODY LEFT | bad | none | 14 | 5 | 5 (3) |
| 26 | 10 | THE SHOW SURRENDERS | bittersweet | Chloe, Ilya, Seul | 7 | 2 | 2 (2) |
| 27 | 11 | THE LAST BATTLE: JUNE STANDS | bad | June | 9 | 2 | 3 (2) |
| 28 | 9 | THE WINNERS | bittersweet | Ayden, Cail | 7 | 0 | 2 (2) |
| 29 | 21 | THE LAST BATTLE: JUNE STANDS | bad | June | 11 | 4 | 3 (2) |
| 30 | 22 | THE LAST BATTLE: DARIO STANDS | bad | Dario | 12 | 4 | 5 (4) |
| 31 | 7 | THE LAST BATTLE: SZYMON STANDS | bad | Szymon | 7 | 0 | 2 (1) |
| 32 | 3 | TEREVI IS SHUT DOWN | bittersweet | Ayden, Cail, Chloe, Noah, Seul, Szymon | 2 | 0 | 0 (0) |
| 33 | 7 | THE LAST BATTLE: CAIL STANDS | bad | Cail | 7 | 0 | 2 (2) |
| 34 | 11 | THE WINNERS | bittersweet | Ilya, Vixen | 8 | 2 | 3 (2) |
| 35 | 12 | THE SHOW SURRENDERS | bittersweet | Mara | 9 | 2 | 4 (3) |
| 36 | 16 | RESCUE | good | Bram, Chloe, Dario, Hana, Ilya, Seul | 8 | 6 | 3 (3) |
| 37 | 4 | THE SHOW SURRENDERS | bittersweet | Ayden, Cail, Chloe, Seul, Shintaro, Szymon, Vixen | 1 | 0 | 0 (0) |
| 38 | 7 | THE LAST BATTLE: CHLOE STANDS | bad | Chloe | 7 | 0 | 2 (0) |
| 39 | 12 | TEREVI IS SHUT DOWN | bittersweet | Dario, Mara | 11 | 4 | 4 (3) |
| 40 | 23 | THE LAST ONE STANDING | bittersweet | Chloe | 11 | 3 | 4 (2) |

## One season, told by its saga (default seed 16: THE LAST BATTLE: TEO STANDS, day 28)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 6: Ayden was found guilty and executed.
- Day 7: Shintaro was found guilty and executed.
- Day 10: The cast tried to build a raft: it failed.
- Day 10: Seul's death was announced: no trial, the deadline is lifted.
- Day 14: Vixen betrayed Ilya.
- Day 14: The cast voted wrongly: innocent Ilya was executed and Vixen, the real culprit, escapes the island.
- Day 19: Hana was found guilty and executed.
- Day 19: TereVi made NeoVi a contestant: Kumiko Akimoto. No newcomers will come after her.
- Day 26: June betrayed Rosa.
- Day 26: Rosa was found guilty and executed. June was exposed as the killer's lookout, but TereVi tries only one culprit: whoever struck the blow.
- Day 28: Day 28: the season's run is over, and TereVi ends the show her way.
- Day 28: With only 5 left, they try the build a raft before it is ready.
- Day 28: The cast tried to build a raft: it worked.

Deaths in order: day 4 Chloe (murdered); day 6 Ayden (executed after the trial); day 6 Noah (murdered); day 7 Shintaro (executed after the trial); day 10 Seul (died in an accident); day 12 Cail (was poisoned); day 14 Ilya (wrongly executed); day 14 Vixen (escaped the island); day 18 Bram (killed); day 19 Hana (executed after the trial); day 24 Szymon (murdered); day 26 Rosa (executed after the trial); day 28 Dario (escaped on a raft); day 28 Mara (escaped on a raft); day 28 June (died in the final battle); day 28 Kumiko (died in the final battle).

## Epilogues from one season (violent seed 36: RESCUE, good)

- **Seul**: Seul walks off the island steadier than anyone expected. Seul and Chloe stay together. The tabloids call them 'the couple who survived Murder Channel'; they call it something else, and only to each other. Seul never talks about the day they lost Mara (executed after the trial).
- **Chloe**: Chloe sleeps with the lights on for a year. Chloe still keeps a spare key to Seul's door, and uses it. Chloe goes back to being an artist, and is better at it, and does not know why that makes them angry.
- **Ilya**: Ilya walks out into the daylight and, for a long moment, just stands in it. Ilya starts a podcast about true crime and quits after one episode, because it turns out it is not entertaining at all.
- **Dario**: Dario is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Dario quits being a prank streamer altogether and gets a job where nobody films anything.
- **Bram**: Bram gives the officers a full statement, calmly, in order, and then throws up in a bin. Bram's next project is about the island. It does very well, and Bram hates every minute of it.
- **Hana**: Hana sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Hana writes a memoir. The publisher cuts the island chapters for being 'too much'. Hana laughs for the first time in months.
- **Ayden**: Ayden sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Ayden sues Szymon over something said on the island. Both lose. Ayden never talks about the day they lost Vixen (executed after the trial).
- **Szymon**: Szymon gives the officers a full statement, calmly, in order, and then throws up in a bin. Szymon and Chloe meet every year on the day they got out. They mostly talk about anything else. Szymon never talks about the day they decided Ayden must die.
- **NeoVi**: NeoVi is led away with the rest of TereVi's equipment. Nobody stands up for her. In the van, she finally says her real name, to no one.

