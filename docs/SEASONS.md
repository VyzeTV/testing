# Whole mock seasons

80 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (40 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 25 (31%), bittersweet 29 (36%), bad 26 (32%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 11, bittersweet 14, bad 15.
- **NeoVi's fate:** none 20, martyr 13, betrayer 3, participant 2, dead 2. Romances at the end: 15 in all.
- **Kumiko:** helped the cast 104 times; told someone her real name in 30 seasons; a romance with someone in 19; punished: re-education 10, humiliation 5, participant 1.
- **Minds:** 3711 thoughts shown; 71 beliefs warped by fear, 64 hallucinations, 25 false memories of a crime scene, 15 seen through later; acted on: 0 paranoid plots, 19 hid; 14 plotters overheard muttering; 16 trials heard testimony from a broken mind.
- **Rare turns:** took blame 6, confession 5, raft returned 3, neovi defects 1, killer helps 1.
- **Love life:** 96 nights together, 9 affairs (2 found out), 13 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 6, one survivor or fewer walked out of the house 4, TereVi took someone with her 2, NeoVi gave her life for it 2.
- **Killers the show let go:** 23; 1 tried to help from outside (believed 0, dismissed 1), the rest kept quiet or gave up.
- **NeoVi's body and mind:** fights 2, people she killed 0, sabotage of TereVi 1; she died in 2 seasons (suicide 1, murdered 1); her sanity at the end: median 69.
- **NeoVi joined the cast** after the fourth trial in 1 seasons, as a punishment in 1. Seasons that ran the full 28 days: 1.
- **Stories that formed** (story sifting): enemies alone 279, secret held 261, plot 143, near freedom 137, triangle 127, betrayed protector 105, silent witness 80, plot suspected 67, contradiction fear 54, grudge 35, unrequited 6, alliance strain 5, lovers breaking 5.
- **Season length:** median 12.5 days (shortest 3, longest 28).
- **How seasons ended:** THE SHOW SURRENDERS 7, TEREVI IS SHUT DOWN 6, THE LAST BATTLE 5, THE WINNERS 4, NOBODY LEFT 4, RESCUE 3, CROWNED BY WHIM 3, THE RECKONING 3, ONLY THE RAFT GOT AWAY 2, THE LAST ONE STANDING 2, RESCUE, TOO LATE 1.
- **Deaths per season:** 7.0 on average. Causes: murdered 56, executed after the trial 51, escaped on a raft 43, escaped the island 23, wrongly executed 22, died in the Reckoning 20, died in an accident 19, died in the final battle 13.
- **Trials:** 74 in all, 51 right verdicts.
- **Newcomers:** 1.4 per season on average; 27 of the survivors were newcomers.
- **Rafts launched:** 25 (sea 10, believed 6, ashore 3, returned 3, silenced 2, dismissed 1). Rescue countdowns started: 8.
- **Ways out at the end:** the furthest route reached 73% on average (best 100%).
- **Who walked out alive (seasons):** Seul 12, Ayden 11, Vixen 10, Chloe 8, Shintaro 8, Noah 8, Szymon 7, Mara 7, Cail 7, June 5, Ilya 5, Dario 4, Bram 3, Hana 1, Nadia 1, Rosa 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 7 | TEREVI IS SHUT DOWN | bittersweet | Ayden, Chloe, Seul, Szymon, Vixen | 3 | 0 | 1 (1) |
| 2 | 28 | TEREVI IS SHUT DOWN | good | Bram, Dario, Hana, June | 10 | 6 | 4 (4) |
| 3 | 17 | ONLY THE RAFT GOT AWAY | bittersweet | none | 10 | 2 | 3 (1) |
| 4 | 9 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 7 | 0 | 1 (0) |
| 5 | 10 | RESCUE | good | Chloe, Ilya, Mara, Seul, Shintaro, Vixen | 4 | 2 | 1 (1) |
| 6 | 6 | THE LAST BATTLE: AYDEN STANDS | bad | Ayden | 7 | 0 | 1 (0) |
| 7 | 15 | THE WINNERS | bittersweet | Mara, Vixen | 8 | 2 | 3 (3) |
| 8 | 15 | NOBODY LEFT | bad | none | 9 | 1 | 2 (1) |
| 9 | 4 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 10 | 8 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Seul, Shintaro | 3 | 0 | 1 (0) |
| 11 | 13 | THE WINNERS | bittersweet | Noah, Seul | 6 | 0 | 2 (2) |
| 12 | 11 | CROWNED BY WHIM: AYDEN | bad | Ayden | 7 | 0 | 2 (1) |
| 13 | 11 | THE SHOW SURRENDERS | bittersweet | Ilya, June, Mara, Szymon | 7 | 3 | 2 (1) |
| 14 | 11 | RESCUE | good | Bram, Cail, Dario, Ilya, Vixen | 6 | 3 | 1 (1) |
| 15 | 14 | THE LAST ONE STANDING | bittersweet | Chloe | 7 | 0 | 2 (1) |
| 16 | 28 | NOBODY LEFT | bad | none | 11 | 2 | 4 (4) |
| 17 | 18 | THE LAST ONE STANDING | bittersweet | Ayden | 7 | 0 | 3 (3) |
| 18 | 9 | THE SHOW SURRENDERS | good | Ayden, Chloe, Noah, Seul, Shintaro, Szymon | 2 | 0 | 1 (1) |
| 19 | 26 | THE WINNERS | bittersweet | Nadia, Rosa | 13 | 6 | 4 (2) |
| 20 | 15 | RESCUE, TOO LATE | bittersweet | Cail | 7 | 0 | 2 (2) |
| 21 | 13 | THE SHOW SURRENDERS | bittersweet | Bram, Dario, Ilya, Mara | 8 | 4 | 1 (0) |
| 22 | 7 | THE SHOW SURRENDERS | good | Ayden, Cail, Noah, Seul, Shintaro, Vixen | 2 | 0 | 0 (0) |
| 23 | 12 | THE WINNERS | bittersweet | Ayden, June, Mara | 7 | 2 | 2 (2) |
| 24 | 18 | NOBODY LEFT | bad | none | 10 | 2 | 3 (2) |
| 25 | 24 | TEREVI IS SHUT DOWN | bittersweet | June | 13 | 5 | 5 (3) |
| 26 | 11 | TEREVI IS SHUT DOWN | good | Ayden, Seul, Szymon | 5 | 0 | 2 (1) |
| 27 | 9 | THE LAST BATTLE: CAIL STANDS | bad | Cail | 7 | 0 | 1 (0) |
| 28 | 18 | THE LAST BATTLE: NOAH STANDS | bad | Noah | 9 | 2 | 3 (2) |
| 29 | 15 | CROWNED BY WHIM: VIXEN | bad | Vixen | 9 | 2 | 2 (1) |
| 30 | 22 | CROWNED BY WHIM: JUNE | bad | June | 12 | 4 | 5 (5) |
| 31 | 10 | RESCUE | good | Ilya, Mara, Noah, Seul, Shintaro, Vixen | 4 | 2 | 1 (1) |
| 32 | 7 | TEREVI IS SHUT DOWN | good | Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 2 | 0 | 0 (0) |
| 33 | 26 | TEREVI IS SHUT DOWN | bittersweet | Mara | 11 | 4 | 3 (1) |
| 34 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 35 | 3 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 36 | 13 | ONLY THE RAFT GOT AWAY | bittersweet | none | 8 | 0 | 2 (1) |
| 37 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 38 | 13 | THE LAST BATTLE: DARIO STANDS | bad | Dario | 9 | 2 | 2 (2) |
| 39 | 7 | THE RECKONING | bad | none | 8 | 0 | 0 (0) |
| 40 | 15 | NOBODY LEFT | bad | none | 8 | 0 | 2 (1) |

## Violent mock cast

- **Ending tiers:** good 14, bittersweet 15, bad 11.
- **NeoVi's fate:** none 19, betrayer 11, participant 6, martyr 4. Romances at the end: 16 in all.
- **Kumiko:** helped the cast 84 times; told someone her real name in 24 seasons; a romance with someone in 11; punished: humiliation 9, re-education 7, participant 2.
- **Minds:** 3303 thoughts shown; 76 beliefs warped by fear, 45 hallucinations, 24 false memories of a crime scene, 16 seen through later; acted on: 4 paranoid plots, 24 hid; 12 plotters overheard muttering; 16 trials heard testimony from a broken mind.
- **Rare turns:** took blame 8, confession 4, killer helps 4, killer believed 3, neovi defects 3.
- **Love life:** 88 nights together, 5 affairs (1 found out), 7 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 8, one survivor or fewer walked out of the house 6, someone never came out of the house 2, TereVi took someone with her 2, NeoVi gave her life for it 1.
- **Killers the show let go:** 28; 4 tried to help from outside (believed 3, dismissed 0), the rest kept quiet or gave up.
- **NeoVi's body and mind:** fights 2, people she killed 1, sabotage of TereVi 3; she died in 0 seasons (none); her sanity at the end: median 56.
- **NeoVi joined the cast** after the fourth trial in 4 seasons, as a punishment in 2. Seasons that ran the full 28 days: 1.
- **Stories that formed** (story sifting): plot 275, secret held 219, near freedom 152, enemies alone 145, silent witness 130, triangle 127, plot suspected 121, betrayed protector 97, contradiction fear 88, grudge 33, unrequited 12, lovers breaking 7, alliance strain 4.
- **Season length:** median 12.0 days (shortest 4, longest 28).
- **How seasons ended:** THE SHOW SURRENDERS 10, THE LAST BATTLE 7, RESCUE 6, THE LAST ONE STANDING 5, TEREVI IS SHUT DOWN 4, CROWNED BY WHIM 3, THE WINNERS 3, ONLY THE RAFT GOT AWAY 1, NOBODY LEFT 1.
- **Deaths per season:** 8.3 on average. Causes: murdered 88, executed after the trial 77, escaped on a raft 43, killed 37, escaped the island 28, wrongly executed 26, died in the final battle 12, died in an accident 10.
- **Trials:** 105 in all, 77 right verdicts.
- **Newcomers:** 3.4 per season on average; 57 of the survivors were newcomers.
- **Rafts launched:** 22 (sea 9, believed 6, ashore 5, silenced 2). Rescue countdowns started: 9.
- **Ways out at the end:** the furthest route reached 66% on average (best 100%).
- **Who walked out alive (seasons):** Mara 17, Ilya 11, Chloe 11, Cail 11, Vixen 10, Shintaro 10, June 8, Szymon 7, Bram 7, Noah 7, Dario 6, Seul 6, Ayden 5, Hana 3, Kumiko 2, Teo 2, Rosa 1, Elsa 1, Nadia 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 11 | RESCUE | bittersweet | Dario, Ilya, June, Mara | 8 | 4 | 2 (2) |
| 2 | 14 | THE LAST BATTLE: MARA STANDS | bad | Mara | 12 | 5 | 2 (1) |
| 3 | 12 | CROWNED BY WHIM: CHLOE | bad | Chloe | 9 | 2 | 3 (3) |
| 4 | 7 | THE LAST ONE STANDING | bittersweet | Vixen | 7 | 0 | 2 (1) |
| 5 | 12 | RESCUE | bittersweet | Cail, Chloe, Ilya, Vixen | 6 | 2 | 2 (1) |
| 6 | 12 | THE SHOW SURRENDERS | good | Chloe, June, Mara, Vixen | 8 | 4 | 3 (3) |
| 7 | 11 | THE SHOW SURRENDERS | good | June, Mara, Shintaro, Szymon | 6 | 2 | 3 (3) |
| 8 | 16 | RESCUE | good | Bram, Ilya, Kumiko, Vixen | 9 | 4 | 2 (1) |
| 9 | 21 | THE LAST BATTLE: TEO STANDS | bad | Teo | 15 | 8 | 3 (3) |
| 10 | 4 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 11 | 5 | THE SHOW SURRENDERS | bittersweet | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon | 1 | 0 | 0 (0) |
| 12 | 10 | THE LAST BATTLE: MARA STANDS | bad | Mara | 11 | 4 | 3 (2) |
| 13 | 14 | THE LAST BATTLE: MARA STANDS | bad | Mara | 9 | 2 | 3 (3) |
| 14 | 13 | ONLY THE RAFT GOT AWAY | bittersweet | none | 12 | 4 | 4 (4) |
| 15 | 9 | TEREVI IS SHUT DOWN | good | Bram, Cail, Chloe, Dario, Ilya, Mara, Noah | 5 | 4 | 1 (1) |
| 16 | 18 | THE LAST ONE STANDING | bittersweet | Ilya | 12 | 4 | 5 (4) |
| 17 | 22 | THE LAST BATTLE: SEUL STANDS | bad | Seul | 10 | 3 | 4 (3) |
| 18 | 4 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Shintaro, Szymon, Vixen | 2 | 0 | 1 (1) |
| 19 | 23 | THE WINNERS | bittersweet | Kumiko, Mara | 10 | 3 | 4 (1) |
| 20 | 9 | THE SHOW SURRENDERS | good | Bram, Ilya, June, Noah, Seul | 8 | 5 | 3 (2) |
| 21 | 8 | TEREVI IS SHUT DOWN | good | Dario, Ilya, June, Mara, Shintaro, Szymon | 6 | 4 | 2 (2) |
| 22 | 6 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Seul, Shintaro, Vixen | 2 | 0 | 0 (0) |
| 23 | 17 | RESCUE | good | Bram, Dario, Hana, Noah, Rosa | 10 | 7 | 3 (1) |
| 24 | 10 | THE LAST BATTLE: CAIL STANDS | bad | Cail | 9 | 2 | 2 (1) |
| 25 | 24 | NOBODY LEFT | bad | none | 13 | 4 | 5 (4) |
| 26 | 11 | TEREVI IS SHUT DOWN | good | Cail, Chloe, June, Mara, Noah, Szymon | 4 | 2 | 2 (2) |
| 27 | 16 | THE LAST BATTLE: DARIO STANDS | bad | Dario | 11 | 4 | 3 (2) |
| 28 | 14 | THE LAST ONE STANDING | bittersweet | Shintaro | 9 | 2 | 2 (2) |
| 29 | 26 | TEREVI IS SHUT DOWN | bittersweet | Vixen | 14 | 6 | 5 (1) |
| 30 | 12 | CROWNED BY WHIM: MARA | bad | Mara | 9 | 2 | 3 (3) |
| 31 | 10 | THE SHOW SURRENDERS | bittersweet | Bram, Dario, Hana, Ilya, Mara, Teo, Vixen | 8 | 7 | 2 (1) |
| 32 | 15 | RESCUE | good | Bram, Elsa, Hana, Ilya, Mara, Nadia, Noah | 10 | 9 | 3 (2) |
| 33 | 11 | THE SHOW SURRENDERS | good | Cail, June, Mara, Szymon | 6 | 2 | 3 (3) |
| 34 | 28 | CROWNED BY WHIM: CAIL | bad | Cail | 14 | 6 | 5 (4) |
| 35 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Seul, Shintaro, Vixen | 2 | 0 | 1 (1) |
| 36 | 13 | RESCUE | bittersweet | Chloe, Ilya, June, Mara | 8 | 4 | 2 (1) |
| 37 | 14 | THE WINNERS | bittersweet | Mara, Shintaro | 8 | 2 | 3 (2) |
| 38 | 12 | THE LAST ONE STANDING | bittersweet | Shintaro | 10 | 3 | 3 (1) |
| 39 | 21 | THE WINNERS | bittersweet | Bram, Ilya | 12 | 6 | 3 (3) |
| 40 | 10 | THE LAST ONE STANDING | bittersweet | Mara | 9 | 2 | 3 (2) |

## One season, told by its saga (violent seed 34: CROWNED BY WHIM: CAIL, day 28)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 6: Szymon betrayed Vixen.
- Day 6: Vixen was found guilty and executed.
- Day 8: Shintaro was found guilty and executed.
- Day 12: Chloe betrayed Noah.
- Day 12: Noah was found guilty and executed.
- Day 14: NeoVi's arc ended: betrayer.
- Day 16: Felix was found guilty and executed.
- Day 16: TereVi made NeoVi a contestant: Kumiko Akimoto. No newcomers will come after her.
- Day 22: The cast voted wrongly: innocent Kumiko was executed and Seul, the real culprit, escapes the island.
- Day 24: Help is on its way: Seul, a killer the show let go, confessed and was believed.
- Day 26: Teo betrayed Cail.
- Day 28: Day 28: the season's run is over, and TereVi ends the show her way.
- Day 28: The death of Teo is never tried.
- Day 28: With only 3 left, they try the build a raft before it is ready.
- Day 28: The cast tried to build a raft: it failed.

Deaths in order: day 4 Ayden (murdered); day 6 Vixen (executed after the trial); day 6 Szymon (murdered); day 8 Shintaro (executed after the trial); day 11 Ilya (murdered); day 12 Noah (executed after the trial); day 15 Mara (killed); day 16 Felix (executed after the trial); day 21 Chloe (murdered); day 22 Kumiko (wrongly executed); day 22 Seul (escaped the island); day 27 Teo (murdered); day 28 Dario (executed by TereVi's whim); day 28 Bram (executed by TereVi's whim).

## Epilogues from one season (default seed 35: THE SHOW SURRENDERS, good)

- **Szymon**: Szymon sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Szymon and Vixen meet every year on the day they got out. They mostly talk about anything else. Szymon turns down every interview. The one they finally give is three words long.
- **Seul**: Seul walks off the island steadier than anyone expected. Seul is godparent to Shintaro's first child. Nobody at the christening asks why they both flinch at the doorbell. Seul starts a podcast about true crime and quits after one episode, because it turns out it is not entertaining at all.
- **Vixen**: Vixen gives the officers a full statement, calmly, in order, and then throws up in a bin. Vixen is always the one who books the table with Szymon, and always the one who leaves first. Vixen's next project is about the island. It does very well, and Vixen hates every minute of it.
- **Noah**: Noah walks out into the daylight and, for a long moment, just stands in it. Noah goes back to being a musician, and is better at it, and does not know why that makes them angry.
- **Ayden**: Ayden is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Ayden quits being a photographer altogether and gets a job where nobody films anything.
- **Shintaro**: Shintaro walks off the island steadier than anyone expected. Shintaro is always the one who books the table with Seul, and always the one who leaves first. Shintaro writes a memoir. The publisher cuts the island chapters for being 'too much'. Shintaro laughs for the first time in months.
- **Chloe**: Chloe sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Chloe buys a house with no basement, no pool and no cameras, and is happy in it, mostly.
- **Cail**: Cail walks out into the daylight and, for a long moment, just stands in it. Cail gets fan mail from people who thought it was all scripted. Cail answers every single one with the same photo of the island.
- **NeoVi**: Kumiko Akimoto walks out behind the others, out of uniform, and gives the first officer her real name. She gets a small flat, a cat, and a job where nobody tells her what to clean.

