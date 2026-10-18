# Whole mock seasons

40 seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week (20 per configuration: the default mock cast and a violent one, as in `tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.

**Ending tiers, all seasons:** good 16 (40%), bittersweet 12 (30%), bad 12 (30%). Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).

## Default

- **Ending tiers:** good 8, bittersweet 4, bad 8.
- **NeoVi's fate:** none 10, martyr 5, betrayer 2, participant 2, survivor 1. Romances at the end: 7 in all.
- **Kumiko:** helped the cast 58 times; told someone her real name in 10 seasons; a romance with someone in 5; punished: re-education 4, humiliation 3, participant 1.
- **Minds:** 2250 thoughts shown; 63 beliefs warped by fear, 33 hallucinations, 15 false memories of a crime scene, 17 seen through later; acted on: 1 paranoid plots, 11 hid; 1 plotters overheard muttering; 9 trials heard testimony from a broken mind.
- **Rare turns:** took blame 2, killer helps 1, confession 1.
- **Love life:** 58 nights together, 2 affairs (1 found out), 5 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 2, one survivor or fewer walked out of the house 2, someone never came out of the house 1, NeoVi gave her life for it 1.
- **Killers the show let go:** 15; 1 tried to help from outside (believed 0, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 1 seasons, as a punishment in 1. Seasons that ran the full 28 days: 3.
- **Season length:** median 13.5 days (shortest 5, longest 28).
- **How seasons ended:** THE LAST BATTLE 7, THE SHOW SURRENDERS 6, RESCUE 3, THE WINNERS 1, THE LAST ONE STANDING 1, TEREVI IS SHUT DOWN 1, THE RECKONING 1.
- **Deaths per season:** 7.7 on average. Causes: murdered 33, escaped on a raft 26, executed after the trial 24, escaped the island 15, wrongly executed 14, died in the final battle 12, killed 11, died in an accident 9.
- **Trials:** 39 in all, 24 right verdicts.
- **Newcomers:** 2.9 per season on average; 29 of the survivors were newcomers.
- **Rafts launched:** 13 (sea 5, believed 4, ashore 3, silenced 1). Rescue countdowns started: 5.
- **Ways out at the end:** the furthest route reached 75% on average (best 100%).
- **Who walked out alive (seasons):** Cail 8, Ilya 7, Mara 7, Dario 6, June 5, Ayden 5, Chloe 5, Vixen 5, Noah 4, Shintaro 4, Bram 3, Seul 3, Szymon 3, Kumiko 1, Rosa 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 28 | THE LAST BATTLE: JUNE STANDS | bad | June | 13 | 6 | 3 (3) |
| 2 | 12 | THE LAST BATTLE: CAIL STANDS | bad | Cail | 7 | 0 | 2 (1) |
| 3 | 16 | THE WINNERS | bittersweet | Ilya, June, Mara | 8 | 3 | 2 (0) |
| 4 | 16 | THE SHOW SURRENDERS | good | Bram, Cail, Dario, Ilya, Mara | 7 | 4 | 2 (1) |
| 5 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 6 | 10 | THE SHOW SURRENDERS | good | Chloe, Shintaro, Szymon, Vixen | 4 | 0 | 2 (2) |
| 7 | 28 | THE LAST BATTLE: KUMIKO STANDS | bad | Kumiko | 12 | 4 | 4 (4) |
| 8 | 28 | THE LAST BATTLE: DARIO STANDS | bad | Dario | 14 | 7 | 3 (2) |
| 9 | 9 | RESCUE | bittersweet | Ayden, Bram, Chloe, Dario, Ilya, Mara, Vixen | 5 | 4 | 1 (1) |
| 10 | 13 | THE LAST ONE STANDING | bittersweet | Chloe | 10 | 3 | 3 (1) |
| 11 | 23 | THE SHOW SURRENDERS | bittersweet | June | 15 | 7 | 5 (2) |
| 12 | 25 | THE LAST BATTLE: JUNE STANDS | bad | June | 12 | 5 | 3 (3) |
| 13 | 14 | TEREVI IS SHUT DOWN | good | Cail, Dario, Ilya, Mara | 7 | 3 | 2 (1) |
| 14 | 11 | THE LAST BATTLE: CAIL STANDS | bad | Cail | 7 | 0 | 1 (0) |
| 15 | 11 | RESCUE | good | Ayden, Dario, Ilya, Mara, Noah, Seul | 5 | 3 | 0 (0) |
| 16 | 8 | THE SHOW SURRENDERS | good | Cail, Ilya, Mara, Noah, Shintaro | 5 | 2 | 1 (0) |
| 17 | 14 | THE RECKONING | bad | none | 8 | 0 | 1 (1) |
| 18 | 5 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Noah, Seul, Shintaro, Szymon, Vixen | 0 | 0 | 0 (0) |
| 19 | 22 | RESCUE | good | Ayden, Bram, Dario, Ilya, June, Mara, Rosa, Vixen | 7 | 7 | 3 (2) |
| 20 | 9 | THE LAST BATTLE: CAIL STANDS | bad | Cail | 7 | 0 | 1 (0) |

## Violent mock cast

- **Ending tiers:** good 8, bittersweet 8, bad 4.
- **NeoVi's fate:** none 8, participant 6, betrayer 3, martyr 3. Romances at the end: 12 in all.
- **Kumiko:** helped the cast 29 times; told someone her real name in 8 seasons; a romance with someone in 0; punished: humiliation 1, participant 1.
- **Minds:** 1800 thoughts shown; 45 beliefs warped by fear, 18 hallucinations, 12 false memories of a crime scene, 6 seen through later; acted on: 0 paranoid plots, 12 hid; 3 plotters overheard muttering; 11 trials heard testimony from a broken mind.
- **Rare turns:** took blame 4, confession 4, killer helps 3, killer believed 1, neovi defects 1.
- **Love life:** 40 nights together, 3 affairs (3 found out), 6 pangs of jealousy.
- **Wins at a price** (good endings made bittersweet): only the last few of a killing game walked out 6, NeoVi gave her life for it 2, one survivor or fewer walked out of the house 2, TereVi took someone with her 1.
- **Killers the show let go:** 14; 3 tried to help from outside (believed 1, dismissed 0), the rest kept quiet or gave up.
- **NeoVi joined the cast** after the fourth trial in 5 seasons, as a punishment in 1. Seasons that ran the full 28 days: 0.
- **Season length:** median 13.5 days (shortest 6, longest 26).
- **How seasons ended:** THE WINNERS 4, THE SHOW SURRENDERS 4, TEREVI IS SHUT DOWN 4, CROWNED BY WHIM 2, THE LAST BATTLE 2, RESCUE 2, THE LAST ONE STANDING 2.
- **Deaths per season:** 8.4 on average. Causes: murdered 58, executed after the trial 49, escaped on a raft 15, escaped the island 14, wrongly executed 13, killed 10, executed by TereVi's whim 3, died in an accident 3.
- **Trials:** 63 in all, 49 right verdicts.
- **Newcomers:** 3.1 per season on average; 25 of the survivors were newcomers.
- **Rafts launched:** 7 (sea 5, believed 2). Rescue countdowns started: 4.
- **Ways out at the end:** the furthest route reached 70% on average (best 100%).
- **Who walked out alive (seasons):** Dario 7, Vixen 7, Ilya 6, Cail 6, Seul 5, Ayden 4, Mara 4, Chloe 4, Shintaro 3, June 2, Kumiko 2, Szymon 2, Teo 2, Noah 2, Nadia 1, Rosa 1, Bram 1, Hana 1.

| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 12 | THE WINNERS | bittersweet | Dario, Ilya, Seul | 7 | 2 | 2 (1) |
| 2 | 20 | THE SHOW SURRENDERS | good | Ayden, Dario, June, Kumiko, Mara, Seul, Vixen | 8 | 6 | 4 (4) |
| 3 | 23 | CROWNED BY WHIM: DARIO | bad | Dario | 15 | 7 | 6 (4) |
| 4 | 11 | CROWNED BY WHIM: ILYA | bad | Ilya | 9 | 2 | 2 (2) |
| 5 | 26 | THE WINNERS | bittersweet | Nadia, Rosa | 14 | 7 | 6 (4) |
| 6 | 7 | THE LAST BATTLE: CHLOE STANDS | bad | Chloe | 7 | 0 | 3 (3) |
| 7 | 10 | RESCUE | good | Dario, Ilya, Shintaro, Vixen | 6 | 2 | 1 (1) |
| 8 | 25 | TEREVI IS SHUT DOWN | good | Dario, Kumiko | 13 | 6 | 6 (5) |
| 9 | 15 | THE SHOW SURRENDERS | bittersweet | Bram, Dario, Hana, June, Mara, Szymon, Teo, Vixen | 7 | 7 | 3 (3) |
| 10 | 14 | TEREVI IS SHUT DOWN | bittersweet | Cail, Chloe | 8 | 2 | 3 (2) |
| 11 | 7 | THE SHOW SURRENDERS | good | Ayden, Chloe, Noah, Seul, Shintaro, Vixen | 2 | 0 | 1 (1) |
| 12 | 11 | THE WINNERS | bittersweet | Ayden, Cail | 8 | 2 | 3 (3) |
| 13 | 14 | RESCUE | good | Cail, Ilya, Mara, Noah | 6 | 2 | 2 (2) |
| 14 | 14 | THE WINNERS | bittersweet | Mara, Seul | 8 | 2 | 3 (3) |
| 15 | 7 | THE LAST BATTLE: VIXEN STANDS | bad | Vixen | 7 | 0 | 1 (0) |
| 16 | 18 | TEREVI IS SHUT DOWN | good | Cail, Shintaro | 10 | 3 | 4 (2) |
| 17 | 13 | THE LAST ONE STANDING | bittersweet | Ilya | 9 | 2 | 3 (2) |
| 18 | 6 | THE SHOW SURRENDERS | good | Ayden, Cail, Chloe, Seul, Szymon, Vixen | 2 | 0 | 1 (1) |
| 19 | 11 | TEREVI IS SHUT DOWN | good | Cail, Dario, Ilya, Vixen | 7 | 3 | 3 (2) |
| 20 | 26 | THE LAST ONE STANDING | bittersweet | Teo | 16 | 8 | 6 (4) |

## Notes on this run (2026-10-18, phase 7b final touches)

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

## One season, told by its saga (violent seed 20: THE LAST ONE STANDING, day 26)

- Day 1: TereVi revealed the truth on Day 1: the killing game is real.
- Day 5: Szymon betrayed Shintaro.
- Day 5: Shintaro was found guilty and executed.
- Day 7: Szymon betrayed Vixen.
- Day 7: Szymon was found guilty and executed.
- Day 7: The cast tried to build a raft: it failed.
- Day 7: Chloe's death was announced: no trial, the deadline is lifted.
- Day 7: With only 3 left, they try the build a raft before it is ready.
- Day 7: The cast tried to build a raft: it failed.
- Day 8: Seul's death was announced: no trial, the deadline is lifted.
- Day 10: Ayden betrayed Vixen.
- Day 11: Ayden was found guilty and executed.
- Day 15: The cast voted wrongly: innocent Dario was executed and Mara, the real culprit, escapes the island.
- Day 15: TereVi made NeoVi a contestant: Kumiko Akimoto. No newcomers will come after her.
- Day 18: Kumiko was found guilty and executed.
- Day 26: The cast voted wrongly: innocent Rosa was executed and Bram, the real culprit, escapes the island.

Deaths in order: day 3 Cail (murdered); day 5 Shintaro (executed after the trial); day 5 Noah (murdered); day 7 Szymon (executed after the trial); day 7 Chloe (died in an accident); day 7 Seul (died in an accident); day 10 Vixen (murdered); day 11 Ayden (executed after the trial); day 13 Ilya (murdered); day 15 Dario (wrongly executed); day 15 Mara (escaped the island); day 16 June (murdered); day 18 Kumiko (executed after the trial); day 24 Hana (murdered); day 26 Rosa (wrongly executed); day 26 Bram (escaped the island).

## Epilogues from one season (default seed 15: RESCUE, good)

- **Seul**: Seul walks off the island steadier than anyone expected. Seul is godparent to Dario's first child. Nobody at the christening asks why they both flinch at the doorbell. Seul never talks about the day they decided Cail must die.
- **Noah**: Noah walks out into the daylight and, for a long moment, just stands in it. Noah and Mara meet every year on the day they got out. They mostly talk about anything else. Nobody outside ever learns what Noah did on the island. Noah does, every night.
- **Ayden**: Ayden gives the officers a full statement, calmly, in order, and then throws up in a bin. Ayden and Noah have a group chat with one other member. The other member is a picture of the island, with a rude caption. Ayden never talks about the day they decided Chloe must die.
- **Ilya**: Ilya sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Ilya is godparent to Noah's first child. Nobody at the christening asks why they both flinch at the doorbell. Ilya turns down every interview. The one they finally give is three words long.
- **Dario**: Dario is the one who carries the others' bags to the boat, and does not stop moving until the island is out of sight. Dario and Ayden have a group chat with one other member. The other member is a picture of the island, with a rude caption. Dario's next project is about the island. It does very well, and Dario hates every minute of it.
- **Mara**: Mara sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Mara is always the one who books the table with Noah, and always the one who leaves first. Mara starts a podcast about true crime and quits after one episode, because it turns out it is not entertaining at all.
- **Szymon**: Szymon sleeps for fourteen hours on the boat and wakes up hungry, which feels like a miracle. Szymon and Shintaro never speak again. They once end up at the same awards show and sit very, very far apart. Szymon quits being an urban explorer altogether and gets a job where nobody films anything.
- **Shintaro**: Shintaro walks out into the daylight and, for a long moment, just stands in it. Shintaro buys a house with no basement, no pool and no cameras, and is happy in it, mostly.
- **Vixen**: Vixen walks off the island steadier than anyone expected. Vixen tells one interviewer about Noah, who caught them going through their things on night 2. Noah's lawyers are in touch by morning. Vixen never talks about the day they decided Noah must die.
- **NeoVi**: Kumiko Akimoto walks out behind the others, out of uniform for the first time in years, and takes Ayden's hand at the gate. She gets a small flat with a window that catches the afternoon sun, and a cat, and makes every decision herself, slowly.
