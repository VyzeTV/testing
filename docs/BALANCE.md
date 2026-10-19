# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 87.9 | 80.9 |
| Deaths per week | 2.9 | 3.5 |
| How the weeks ended | shutdown 1, still going 6, ultimatum 1 | shutdown 1, still going 7 |
| Deaths by cause | murdered 6, executed after the trial 4, escaped the island 3, died in an accident 3, killed 2, wrongly executed 2, lost at sea 1, escaped on a raft 1, taken by TereVi's parting shot 1 | murdered 8, executed after the trial 7, killed 6, wrongly executed 3, escaped the island 3, was poisoned 1 |
| Trials (all weeks) | 7 | 10 |
| Verdicts right / wrong / none | 4 / 2 / 1 | 7 / 3 / 0 |
| Average sanity of survivors at the end of the week | 60.4 | 60.3 |
| Median sanity at the end of each week | 68 / 65.0 / 61.0 / 61.0 / 64.0 / 57 / 56.0 / 60 | 65 / 68.0 / 55.5 / 68 / 68 / 68 / 47 / 62 |
| Aimless share of free-time activities | 0.3 | 0.28 |
| Meal attendance (share of the living) | 0.65 | 0.66 |
| Calm meals (share) | 0.62 | 0.62 |
| Night blocks where everyone sleeps (share) | 0.38 | 0.39 |
| People awake per night block | 1.3 | 1.3 |
| Exhausted at dawn (share of the living) | 0.06 | 0.12 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.001 | 0.002 |
| Lies caught: real / honest people wrongly caught | 6 / 0 | 10 / 2 |
| Secret meetings per week | 1.8 | 2.0 |
| Snooping per week / snoopers caught (all weeks) | 2.8 / 4 | 1.6 / 3 |
| Intrusions and waking (all weeks) | confronted 62, walked_in 44, thrown_out 32, welcome 15, woke 7, bedside_strike 6, scream 4, pretend 4, confront 4, fight 2 | confronted 41, walked_in 31, woke 11, welcome 9, scream 6, confront 4, bedside_strike 3, pretend 3, fight 2 |
| Pastimes per week (films, sunsets, talks, journals...) | 70.5 | 62.4 |
| How pastimes went (all weeks) | done 298, good 130, alone 87, tense 27, sour 11, flat 8, seen 2, caught 1 | done 246, good 128, alone 58, tense 49, flat 10, sour 7, seen 1 |
