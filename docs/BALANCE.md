# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 86.6 | 71.3 |
| Deaths per week | 2.9 | 6.0 |
| How the weeks ended | still going 6, ultimatum 2 | battle 2, raft 1, still going 4, ultimatum 1 |
| Deaths by cause | murdered 8, executed after the trial 4, wrongly executed 3, escaped the island 3, escaped on a raft 2, died in an accident 1, took their own life 1, was poisoned 1 | murdered 11, executed after the trial 8, killed 7, escaped the island 7, wrongly executed 5, escaped on a raft 4, died in the final battle 4, was poisoned 1, died in an accident 1 |
| Trials (all weeks) | 7 | 15 |
| Verdicts right / wrong / none | 4 / 3 / 0 | 8 / 5 / 2 |
| Average sanity of survivors at the end of the week | 64.6 | 55.4 |
| Median sanity at the end of each week | 68 / 70.0 / 67 / 65.0 / 66 / 64.0 / 68 / 68 | nobody left / 70 / 67.0 / 59.5 / 31 / 55.5 / 42.5 / 64.5 |
| Aimless share of free-time activities | 0.32 | 0.29 |
| Meal attendance (share of the living) | 0.67 | 0.66 |
| Calm meals (share) | 0.68 | 0.64 |
| Night blocks where everyone sleeps (share) | 0.43 | 0.39 |
| People awake per night block | 1.22 | 1.08 |
| Exhausted at dawn (share of the living) | 0.06 | 0.11 |
| Beliefs per survivor at the end | 79.8 | 80.0 |
| False beliefs (share) | 0.0 | 0.006 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 1 / 1 |
| Secret meetings per week | 2.9 | 1.0 |
| Snooping per week / snoopers caught (all weeks) | 2.8 / 2 | 2.2 / 1 |
| Intrusions and waking (all weeks) | walked_in 40, confronted 19, welcome 10, woke 7, pretend 3, scream 3, confront 2, bedside_held_back 2, bedside_strike 2 | walked_in 31, confronted 26, welcome 10, woke 7, pretend 4, thrown_out 4, confront 3, bedside_strike 2, scream 1 |
| Pastimes per week (films, sunsets, talks, journals...) | 50.6 | 30.9 |
| How pastimes went (all weeks) | done 185, good 125, alone 69, flat 9, sour 7, tense 6, caught 3, seen 1 | done 102, good 80, alone 47, sour 6, tense 6, flat 4, caught 1, seen 1 |
