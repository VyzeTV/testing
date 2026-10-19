# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 86.7 | 75.2 |
| Deaths per week | 4.1 | 5.4 |
| How the weeks ended | battle 1, still going 6, winners 1 | battle 3, still going 3, winners 2 |
| Deaths by cause | murdered 9, executed after the trial 7, escaped on a raft 5, killed 4, died in the final battle 2, wrongly executed 2, escaped the island 2, died in an accident 2 | murdered 11, escaped the island 8, wrongly executed 7, died in the final battle 4, executed after the trial 4, escaped on a raft 4, killed 3, died in an accident 2 |
| Trials (all weeks) | 9 | 12 |
| Verdicts right / wrong / none | 7 / 2 / 0 | 4 / 7 / 1 |
| Average sanity of survivors at the end of the week | 57.7 | 53.0 |
| Median sanity at the end of each week | 68.0 / 75 / 47 / 64.0 / 34.5 / 58.0 / 58 / 68.0 | 19 / 52.5 / 61.0 / 40 / 65.0 / 70 / 67 / 55 |
| Aimless share of free-time activities | 0.3 | 0.29 |
| Meal attendance (share of the living) | 0.66 | 0.68 |
| Calm meals (share) | 0.63 | 0.67 |
| Night blocks where everyone sleeps (share) | 0.37 | 0.35 |
| People awake per night block | 1.47 | 1.4 |
| Exhausted at dawn (share of the living) | 0.09 | 0.12 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.001 | 0.001 |
| Lies caught: real / honest people wrongly caught | 8 / 0 | 3 / 0 |
| Secret meetings per week | 3.1 | 0.6 |
| Snooping per week / snoopers caught (all weeks) | 2.0 / 2 | 2.1 / 4 |
| Intrusions and waking (all weeks) | walked_in 46, confronted 30, welcome 11, woke 11, pretend 6, scream 3, bedside_held_back 2, bedside_strike 2, confront 2 | confronted 53, walked_in 26, welcome 15, woke 14, confront 6, scream 5, pretend 5, fight 2, bedside_held_back 1, thrown_out 1 |
| Pastimes per week (films, sunsets, talks, journals...) | 73.6 | 50.6 |
| How pastimes went (all weeks) | done 302, good 137, alone 87, tense 37, sour 13, flat 9, seen 4 | done 200, good 111, alone 50, tense 29, flat 7, sour 5, seen 2, caught 1 |
