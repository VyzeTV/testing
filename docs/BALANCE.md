# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 91.2 | 79.4 |
| Deaths per week | 3.8 | 4.0 |
| How the weeks ended | reckoning 2, still going 5, ultimatum 1 | battle 1, still going 7 |
| Deaths by cause | died in the Reckoning 16, murdered 3, executed after the trial 3, died in an accident 2, escaped on a raft 2, killed 1, wrongly executed 1, escaped the island 1, was poisoned 1 | executed after the trial 10, murdered 9, killed 5, escaped on a raft 4, died in an accident 1, died in the final battle 1, wrongly executed 1, escaped the island 1 |
| Trials (all weeks) | 4 | 11 |
| Verdicts right / wrong / none | 3 / 1 / 0 | 10 / 1 / 0 |
| Average sanity of survivors at the end of the week | 58.4 | 58.2 |
| Median sanity at the end of each week | 30 / 68.0 / 65.0 / 67.0 / nobody left / nobody left / 69.5 / 64.0 | 54.5 / 56.5 / 44.0 / 60 / 65.0 / 65.0 / 68 / 55.5 |
| Aimless share of free-time activities | 0.32 | 0.28 |
| Meal attendance (share of the living) | 0.67 | 0.65 |
| Calm meals (share) | 0.65 | 0.68 |
| Night blocks where everyone sleeps (share) | 0.38 | 0.35 |
| People awake per night block | 1.29 | 1.46 |
| Exhausted at dawn (share of the living) | 0.07 | 0.11 |
| Beliefs per survivor at the end | 79.7 | 80.0 |
| False beliefs (share) | 0.001 | 0.004 |
| Lies caught: real / honest people wrongly caught | 1 / 0 | 7 / 2 |
| Secret meetings per week | 0.8 | 2.2 |
| Snooping per week / snoopers caught (all weeks) | 2.2 / 7 | 2.8 / 4 |
| Intrusions and waking (all weeks) | walked_in 37, confronted 33, welcome 18, woke 6, scream 6, pretend 4, confront 3, bedside_strike 1 | walked_in 36, confronted 33, woke 9, welcome 9, scream 7, bedside_strike 4, pretend 3, confront 2, bedside_held_back 1, thrown_out 1 |
| Pastimes per week (films, sunsets, talks, journals...) | 66.6 | 60.9 |
| How pastimes went (all weeks) | done 281, good 124, alone 91, tense 19, flat 10, sour 3, seen 3, caught 2 | done 220, good 121, alone 74, tense 49, sour 11, flat 6, caught 3, seen 3 |
