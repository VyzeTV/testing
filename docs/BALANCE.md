# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 84.4 | 78.6 |
| Deaths per week | 3.1 | 4.9 |
| How the weeks ended | shutdown 1, still going 6, winners 1 | battle 2, still going 4, winners 2 |
| Deaths by cause | murdered 8, escaped on a raft 4, executed after the trial 4, wrongly executed 3, escaped the island 3, died in an accident 2, killed 1 | murdered 14, executed after the trial 11, escaped the island 3, died in the final battle 3, killed 3, wrongly executed 2, died in an accident 1, escaped on a raft 1, lost at sea 1 |
| Trials (all weeks) | 7 | 14 |
| Verdicts right / wrong / none | 4 / 3 / 0 | 11 / 2 / 1 |
| Average sanity of survivors at the end of the week | 56.6 | 53.3 |
| Median sanity at the end of each week | 51 / 64.0 / 68.0 / 49 / 56.5 / 61.0 / 51 / 68 | 63 / 61 / 60 / 68.0 / 68 / 9 / 68 / 26 |
| Aimless share of free-time activities | 0.31 | 0.29 |
| Meal attendance (share of the living) | 0.69 | 0.66 |
| Calm meals (share) | 0.72 | 0.55 |
| Night blocks where everyone sleeps (share) | 0.44 | 0.33 |
| People awake per night block | 1.2 | 1.52 |
| Exhausted at dawn (share of the living) | 0.06 | 0.12 |
| Beliefs per survivor at the end | 79.0 | 80.0 |
| False beliefs (share) | 0.001 | 0.002 |
| Lies caught: real / honest people wrongly caught | 5 / 0 | 6 / 0 |
| Secret meetings per week | 2.2 | 2.9 |
| Snooping per week / snoopers caught (all weeks) | 4.5 / 5 | 2.9 / 5 |
| Intrusions and waking (all weeks) | confronted 59, walked_in 33, welcome 25, thrown_out 17, confront 8, woke 7, bedside_strike 5, scream 3, bedside_held_back 1, fight 1 | confronted 58, walked_in 41, welcome 12, woke 11, scream 7, pretend 6, confront 6, bedside_strike 2, bedside_held_back 2 |
| Pastimes per week (films, sunsets, talks, journals...) | 54.8 | 46.2 |
| How pastimes went (all weeks) | done 194, good 116, alone 98, sour 12, flat 9, caught 4, seen 4, tense 1 | done 170, good 107, alone 71, flat 9, sour 8, tense 5 |
