# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 82.2 | 74.9 |
| Deaths per week | 1.6 | 3.8 |
| How the weeks ended | still going 2, ultimatum 6 | battle 1, still going 2, ultimatum 5 |
| Deaths by cause | executed after the trial 3, murdered 3, killed 2, wrongly executed 2, escaped the island 2, was poisoned 1 | murdered 11, executed after the trial 6, wrongly executed 4, escaped the island 4, killed 2, died in the final battle 2, died in an accident 1 |
| Trials (all weeks) | 5 | 10 |
| Verdicts right / wrong / none | 3 / 2 / 0 | 6 / 4 / 0 |
| Average sanity of survivors at the end of the week | 62.9 | 51.8 |
| Median sanity at the end of each week | 68 / 60 / 64.5 / 58.0 / 52.0 / 68.5 / 73 / 69.5 | 66.5 / 11.0 / 61.0 / 55.5 / 43.5 / 47 / 67.5 / 67.0 |
| Aimless share of free-time activities | 0.29 | 0.26 |
| Meal attendance (share of the living) | 0.71 | 0.68 |
| Calm meals (share) | 0.65 | 0.71 |
| Night blocks where everyone sleeps (share) | 0.47 | 0.35 |
| People awake per night block | 1.06 | 1.27 |
| Exhausted at dawn (share of the living) | 0.03 | 0.09 |
| Beliefs per survivor at the end | 80.0 | 78.5 |
| False beliefs (share) | 0.0 | 0.002 |
| Lies caught: real / honest people wrongly caught | 2 / 0 | 1 / 0 |
| Secret meetings per week | 1.2 | 1.4 |
| Snooping per week / snoopers caught (all weeks) | 2.9 / 1 | 1.8 / 3 |
| Intrusions and waking (all weeks) | walked_in 37, confronted 27, welcome 11, woke 4, confront 3, pretend 2, thrown_out 1, bedside_held_back 1, scream 1 | walked_in 23, confronted 18, welcome 9, woke 5, scream 3, confront 2, pretend 1, bedside_strike 1, fight 1 |
| Pastimes per week (films, sunsets, talks, journals...) | 31.8 | 24.8 |
| How pastimes went (all weeks) | done 92, good 81, alone 59, flat 10, sour 7, caught 2, tense 2, seen 1 | done 75, good 62, alone 39, flat 8, tense 6, sour 6, caught 2 |
