# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 87.1 | 79.5 |
| Deaths per week | 2.8 | 3.9 |
| How the weeks ended | still going 7, ultimatum 1 | battle 1, shutdown 1, still going 5, ultimatum 1 |
| Deaths by cause | escaped the island 5, murdered 5, killed 4, wrongly executed 4, executed after the trial 2, died in an accident 2 | murdered 11, wrongly executed 5, escaped the island 5, executed after the trial 3, killed 2, escaped on a raft 2, died in the final battle 2, was poisoned 1 |
| Trials (all weeks) | 7 | 8 |
| Verdicts right / wrong / none | 2 / 4 / 1 | 3 / 5 / 0 |
| Average sanity of survivors at the end of the week | 59.6 | 53.5 |
| Median sanity at the end of each week | 68.0 / 68 / 60.0 / 56.0 / 61.0 / 62 / 68 / 44 | 56 / 61 / 35 / 54.0 / 45 / 53.0 / 62 / 68.0 |
| Aimless share of free-time activities | 0.3 | 0.29 |
| Meal attendance (share of the living) | 0.67 | 0.65 |
| Calm meals (share) | 0.63 | 0.64 |
| Night blocks where everyone sleeps (share) | 0.38 | 0.34 |
| People awake per night block | 1.32 | 1.43 |
| Exhausted at dawn (share of the living) | 0.09 | 0.11 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.002 | 0.002 |
| Lies caught: real / honest people wrongly caught | 2 / 0 | 2 / 0 |
| Secret meetings per week | 1.5 | 0.6 |
| Snooping per week / snoopers caught (all weeks) | 3.2 / 4 | 2.1 / 4 |
| Intrusions and waking (all weeks) | confronted 49, walked_in 36, thrown_out 18, woke 12, welcome 8, scream 8, confront 5, pretend 4, bedside_held_back 2 | confronted 43, walked_in 33, welcome 18, woke 7, confront 4, scream 3, bedside_strike 3, pretend 2, bedside_held_back 2, thrown_out 2 |
| Pastimes per week (films, sunsets, talks, journals...) | 68.1 | 55.8 |
| How pastimes went (all weeks) | done 296, good 119, alone 84, tense 27, flat 9, sour 7, seen 2, caught 1 | done 213, good 145, alone 46, tense 28, sour 9, flat 4, seen 1 |
