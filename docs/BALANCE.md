# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 89.4 | 75.4 |
| Deaths per week | 2.1 | 5.2 |
| How the weeks ended | shutdown 2, still going 6 | battle 3, extinction 1, shutdown 1, still going 3 |
| Deaths by cause | murdered 6, executed after the trial 4, killed 2, wrongly executed 2, escaped the island 2, took their own life 1 | murdered 12, died in the final battle 8, executed after the trial 7, wrongly executed 5, escaped the island 5, escaped on a raft 3, killed 2 |
| Trials (all weeks) | 6 | 12 |
| Verdicts right / wrong / none | 4 / 2 / 0 | 7 / 5 / 0 |
| Average sanity of survivors at the end of the week | 60.7 | 52.5 |
| Median sanity at the end of each week | 63.5 / 57 / 59.5 / 68.0 / 68 / 63 / 60 / 60 | 62 / 61.0 / 57.5 / 64.0 / 40 / nobody left / 40 / 47 |
| Aimless share of free-time activities | 0.29 | 0.25 |
| Meal attendance (share of the living) | 0.66 | 0.68 |
| Calm meals (share) | 0.65 | 0.69 |
| Night blocks where everyone sleeps (share) | 0.41 | 0.35 |
| People awake per night block | 1.36 | 1.36 |
| Exhausted at dawn (share of the living) | 0.06 | 0.09 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.001 | 0.0 |
| Lies caught: real / honest people wrongly caught | 4 / 0 | 1 / 0 |
| Secret meetings per week | 1.9 | 1.1 |
| Snooping per week / snoopers caught (all weeks) | 1.8 / 2 | 1.9 / 5 |
| Intrusions and waking (all weeks) | confronted 43, walked_in 40, thrown_out 19, welcome 16, woke 5, bedside_strike 3, confront 3, scream 2, pretend 1, fight 1 | confronted 41, walked_in 33, woke 12, welcome 8, scream 8, bedside_strike 6, confront 5, pretend 4, bedside_held_back 1 |
| Pastimes per week (films, sunsets, talks, journals...) | 71.0 | 56.2 |
| How pastimes went (all weeks) | done 301, good 136, alone 91, tense 18, flat 10, sour 9, seen 2, caught 1 | done 199, good 138, alone 58, tense 37, sour 11, flat 5, seen 2 |
