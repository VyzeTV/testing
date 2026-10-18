# Whole mock seasons

40 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (20 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 15 (38%), bittersweet 14 (35%), bad 11 (28%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 7, bittersweet 9, bad 4.
- **NeoVi's fate:** none 9, betrayer 5, martyr 4, participant 2. Romances at the end: 7 in all.
- **Kumiko:** helped the cast 69 times; told someone her real name in 10 seasons; a romance with someone in 6; punished: humiliation 4, re-education 4, participant 2.
- **Minds:** 2292 thoughts shown; 45 beliefs warped by fear, 34 hallucinations, 14 false memories of a crime scene, 8 seen through later; acted on: 5 paranoid plots, 17 hid; 6 plotters overheard muttering; 9 trials heard testimony from a broken mind.
- **Rare turns:** took blame 3, confession 1.
- **Love life:** 48 nights together, 3 affairs (1 found out), 5 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 7, one survivor or fewer walked out of the house 4, NeoVi gave her life for it 3.
- **Season length:** median 13.5 days (shortest 6, longest 41).
- **How seasons ended:** RESCUE 4, THE LAST ONE STANDING 4, THE WINNERS 3, THE LAST BATTLE 3, THE SHOW SURRENDERS 3, TEREVI IS SHUT DOWN 2, CROWNED BY WHIM 1.
- **Deaths per season:** 8.1 on average. Causes: murdered 39, executed after the trial 27, escaped on a raft 24, escaped the island 22, wrongly executed 21, killed 12, died in the final battle 6, died in an accident 3.
- **Trials:** 49 in all, 27 right verdicts.
- **Newcomers:** 3.6 per season on average; 40 of the survivors were newcomers.
- **Rafts launched:** 12 (sea 6, believed 4, dismissed 1, ashore 1). Rescue countdowns started: 5.
- **Ways out at the end:** the furthest route reached 66% on average (best 100%).
- **Who walked out alive (seasons):** Ilya 10, Shintaro 7, Dario 7, Chloe 6, Bram 5, Cail 5, Mara 5, Vixen 5, Ayden 4, Seul 4, June 3, Szymon 2, Hana 2, Rosa 2, Teo 2, Felix 1, Omar 1, Priya 1, Nadia 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 13 | THE WINNERS | bittersweet | Shintaro, Szymon | 6 | 0 | 1 (0) |
| 2 | 13 | THE LAST BATTLE: ILYA STANDS | bad | Ilya | 9 | 2 | 2 (1) |
| 3 | 25 | TEREVI IS SHUT DOWN | good | Bram, Dario, Hana, June, Rosa, Shintaro | 9 | 7 | 3 (3) |
| 4 | 10 | RESCUE | good | Ayden, Bram, Cail, Chloe, Dario, Ilya, Mara, Seul | 4 | 4 | 1 (1) |
| 5 | 24 | THE SHOW SURRENDERS | good | Hana, Ilya, June, Mara, Rosa, Teo | 10 | 8 | 4 (4) |
| 6 | 6 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Seul, Shintaro, Szymon | 2 | 0 | 0 (0) |
| 7 | 14 | THE LAST ONE STANDING | bittersweet | Ilya | 10 | 3 | 3 (1) |
| 8 | 37 | RESCUE | good | Bram, Felix, Omar, Priya, Teo | 17 | 13 | 6 (3) |
| 9 | 11 | THE LAST BATTLE: MARA STANDS | bad | Mara | 9 | 2 | 3 (2) |
| 10 | 10 | THE LAST ONE STANDING | bittersweet | Vixen | 7 | 0 | 2 (1) |
| 11 | 11 | THE LAST BATTLE: VIXEN STANDS | bad | Vixen | 7 | 0 | 2 (1) |
| 12 | 10 | THE LAST ONE STANDING | bittersweet | Seul | 7 | 0 | 2 (0) |
| 13 | 20 | CROWNED BY WHIM: ILYA | bad | Ilya | 11 | 4 | 3 (2) |
| 14 | 16 | THE WINNERS | bittersweet | Ayden, Dario, Ilya | 8 | 3 | 2 (0) |
| 15 | 11 | RESCUE | good | Ayden, Cail, Chloe, Dario, Ilya, June, Mara, Shintaro | 4 | 4 | 1 (1) |
| 16 | 41 | THE LAST ONE STANDING | bittersweet | Nadia | 21 | 13 | 8 (3) |
| 17 | 16 | TEREVI IS SHUT DOWN | bittersweet | Chloe, Dario, Ilya, Seul, Shintaro, Vixen | 4 | 2 | 2 (2) |
| 18 | 14 | THE WINNERS | bittersweet | Cail, Vixen | 6 | 0 | 2 (0) |
| 19 | 15 | RESCUE | bittersweet | Bram, Cail, Chloe, Dario, Ilya, Mara, Shintaro | 5 | 4 | 1 (1) |
| 20 | 11 | THE SHOW SURRENDERS | good | Bram, Chloe, Dario, Ilya, Shintaro, Vixen | 5 | 3 | 1 (1) |

## Violent mock cast

- **Ending tiers:** good 8, bittersweet 5, bad 7.
- **NeoVi's fate:** none 14, betrayer 4, martyr 2. Romances at the end: 5 in all.
- **Kumiko:** helped the cast 22 times; told someone her real name in 5 seasons; a romance with someone in 1; punished: humiliation 3, re-education 1.
- **Minds:** 1436 thoughts shown; 7 beliefs warped by fear, 8 hallucinations, 1 false memories of a crime scene, 3 seen through later; acted on: 0 paranoid plots, 2 hid; 5 plotters overheard muttering; 0 trials heard testimony from a broken mind.
- **Rare turns:** neovi defects 1, raft returned 1, took blame 1, confession 1.
- **Love life:** 22 nights together, 0 affairs (0 found out), 2 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 4, one survivor or fewer walked out of the house 1.
- **Season length:** median 12.5 days (shortest 5, longest 23).
- **How seasons ended:** THE SHOW SURRENDERS 5, THE LAST BATTLE 4, THE WINNERS 3, RESCUE 3, NOBODY LEFT 2, THE LAST ONE STANDING 1, RESCUE, TOO LATE 1, CROWNED BY WHIM 1.
- **Deaths per season:** 7.7 on average. Causes: executed after the trial 50, murdered 46, killed 15, escaped on a raft 9, died in the final battle 9, wrongly executed 9, escaped the island 9, died in an accident 2.
- **Trials:** 59 in all, 50 right verdicts.
- **Newcomers:** 2.6 per season on average; 27 of the survivors were newcomers.
- **Rafts launched:** 6 (believed 4, ashore 1, returned 1). Rescue countdowns started: 6.
- **Ways out at the end:** the furthest route reached 67% on average (best 100%).
- **Who walked out alive (seasons):** Ilya 7, Cail 5, Vixen 5, Noah 4, Ayden 4, Seul 4, Shintaro 4, Dario 4, Chloe 3, Szymon 3, Mara 3, June 3, Hana 2, Teo 2, Bram 2, Rosa 1, Elsa 1, Felix 1, Nadia 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 14 | THE WINNERS | bittersweet | Cail, Noah | 8 | 2 | 3 (3) |
| 2 | 19 | THE LAST BATTLE: CAIL STANDS | bad | Cail | 9 | 2 | 4 (4) |
| 3 | 7 | THE SHOW SURRENDERS | good | Ayden, Chloe, Seul, Shintaro, Szymon, Vixen | 2 | 0 | 1 (1) |
| 4 | 14 | THE LAST ONE STANDING | bittersweet | Noah | 9 | 2 | 4 (4) |
| 5 | 10 | THE WINNERS | bittersweet | Dario, Ilya | 10 | 4 | 4 (4) |
| 6 | 18 | THE SHOW SURRENDERS | good | Ayden, Dario, Hana, Rosa, Teo, Vixen | 10 | 8 | 5 (5) |
| 7 | 7 | THE LAST BATTLE: NOAH STANDS | bad | Noah | 7 | 0 | 2 (1) |
| 8 | 13 | NOBODY LEFT | bad | none | 10 | 2 | 4 (3) |
| 9 | 13 | THE WINNERS | bittersweet | Mara, Shintaro | 8 | 2 | 4 (4) |
| 10 | 11 | RESCUE | good | Cail, Chloe, Ilya, Mara, Vixen | 6 | 3 | 2 (1) |
| 11 | 5 | NOBODY LEFT | bad | none | 8 | 0 | 2 (1) |
| 12 | 23 | RESCUE | good | Bram, Dario, Elsa, Felix, Hana, June, Nadia, Teo | 11 | 11 | 4 (3) |
| 13 | 14 | THE LAST BATTLE: ILYA STANDS | bad | Ilya | 9 | 2 | 3 (2) |
| 14 | 12 | THE SHOW SURRENDERS | good | Ilya, Seul, Shintaro, Szymon | 6 | 2 | 3 (3) |
| 15 | 6 | THE LAST BATTLE: NOAH STANDS | bad | Noah | 7 | 0 | 2 (1) |
| 16 | 12 | THE SHOW SURRENDERS | good | Ayden, Ilya, June, Mara | 7 | 3 | 2 (1) |
| 17 | 13 | RESCUE, TOO LATE | bittersweet | Ilya, June | 9 | 3 | 2 (1) |
| 18 | 5 | THE SHOW SURRENDERS | good | Cail, Chloe, Seul, Shintaro, Szymon, Vixen | 2 | 0 | 1 (1) |
| 19 | 10 | RESCUE | good | Ayden, Cail, Dario, Ilya, Seul, Vixen | 4 | 2 | 2 (2) |
| 20 | 14 | CROWNED BY WHIM: BRAM | bad | Bram | 11 | 4 | 5 (5) |

## Notes on this run (2026-10-18, phase 7b step 7: balance and epilogues)

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

## One season, told by its saga (default seed 16: THE LAST ONE STANDING, day 41)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 6: Szymon betrayed Seul.
- Day 7: Vixen betrayed Chloe.
- Day 7: The cast voted wrongly: innocent Chloe was executed and Szymon, the real culprit, escapes the island.
- Day 9: The cast voted wrongly: innocent Cail was executed and Shintaro, the real culprit, escapes the island.
- Day 13: The cast tried to threaten to blow up the island: it failed.
- Day 13: NeoVi's arc ended: betrayer.
- Day 15: Ayden was found guilty and executed.
- Day 15: The cast tried to threaten to blow up the island: it failed.
- Day 18: Seul betrayed Ilya.
- Day 20: Seul was found guilty and executed.
- Day 27: The cast voted wrongly: innocent Omar was executed and Felix, the real culprit, escapes the island.
- Day 29: TereVi made NeoVi a contestant: Kumiko Akimoto. No newcomers will come after her.
- Day 31: The house collapsed into a killing spree.
- Day 32: Bram betrayed Hana.
- Day 32: Mara betrayed Hana.
- Day 32: Hana was found guilty and executed. Mara was exposed as the killer's alibi, but TereVi tries only one culprit: whoever struck the blow.
- Day 33: Bram betrayed June.
- Day 34: June betrayed Bram.
- Day 34: The cast voted wrongly: innocent Bram was executed and Kumiko, the real culprit, escapes the island.
- Day 41: The cast voted wrongly: innocent Kenji was executed and June, the real culprit, escapes the island. Nadia was exposed as the killer's alibi, but TereVi tries only one culprit: whoever struck t
- Day 41: With only 1 left, they try the build a raft before it is ready.
- Day 41: The cast tried to build a raft: it failed.

Deaths in order: day 5 Noah (murdered); day 7 Chloe (wrongly executed); day 7 Szymon (escaped the island); day 7 Vixen (was poisoned); day 9 Cail (wrongly executed); day 9 Shintaro (escaped the island); day 13 Dario (murdered); day 15 Ayden (executed after the trial); day 18 Ilya (killed); day 20 Seul (executed after the trial); day 26 Rosa (murdered); day 27 Omar (wrongly executed); day 27 Felix (escaped the island); day 31 Teo (murdered); day 32 Hana (executed after the trial); day 32 Mara (murdered); day 34 Bram (wrongly executed); day 34 Kumiko (escaped the island); day 39 Lucas (murdered); day 41 Kenji (wrongly executed); day 41 June (escaped the island).

## Epilogues from one season (default seed 15: RESCUE, good)

- **Ayden**: Ayden is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Ayden and Cail never speak again. They once end up at the same awards show and sit very, very far apart. Ayden gets fan mail from people who thought it was all scripted. Ayden answers every single one with the same photo of the island.
- **Shintaro**: Shintaro gives the officers a full statement, calmly, in order, and then throws up in a bin. Shintaro and Seul have a group chat with one other member. The other member is a picture of the island, with a rude caption. Shintaro turns down every interview. The one they finally give is three words long.
- **Chloe**: Chloe walks out into the daylight and, for a long moment, just stands in it. Chloe sues Szymon over something said on the island. Both lose. Chloe goes back to being an artist, and is better at it, and does not know why that makes them angry.
- **Cail**: Cail still checks every room twice before sitting down. Cail and Dario meet every year on the day they got out. They mostly talk about anything else. Cail buys a house with no basement, no pool and no cameras, and is happy in it, mostly.
- **Ilya**: Ilya sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Ilya and Mara never speak again. They once end up at the same awards show and sit very, very far apart. Ilya quits being a chess grandmaster altogether and gets a job where nobody films anything.
- **Mara**: Mara walks off the island steadier than anyone expected. Mara is godparent to Dario's first child. Nobody at the christening asks why they both flinch at the doorbell. Mara writes a memoir. The publisher cuts the island chapters for being 'too much'. Mara laughs for the first time in months.
- **June**: June gives the officers a full statement, calmly, in order, and then throws up in a bin. June and Mara meet every year on the day they got out. They mostly talk about anything else. June starts a podcast about true crime and quits after one episode, because it turns out it is not entertaining at all.
- **Dario**: Dario is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Dario is always the one who books the table with Mara, and always the one who leaves first. Dario's next project is about the island. It does very well, and Dario hates every minute of it.
- **Seul**: Seul gives the officers a full statement, calmly, in order, and then throws up in a bin. Seul is always the one who books the table with Shintaro, and always the one who leaves first. Seul goes back to being a competitive gamer, and is better at it, and does not know why that makes them angry.
- **Szymon**: Szymon sleeps with the lights on for a year. Szymon and Shintaro meet every year on the day they got out. They mostly talk about anything else. Szymon turns down every interview. The one they finally give is three words long.
- **NeoVi**: Kumiko Akimoto walks out behind the others, out of uniform for the first time in years, and takes Ayden's hand at the gate. She gets a small flat with a window that catches the afternoon sun, and a cat, and makes every decision herself, slowly.
