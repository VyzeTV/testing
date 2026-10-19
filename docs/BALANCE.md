# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 89.3 | 78.4 |
| Deaths per week | 3.6 | 5.2 |
| How the weeks ended | sole 1, still going 7 | battle 2, still going 4, winners 2 |
| Deaths by cause | murdered 7, wrongly executed 4, escaped the island 4, escaped on a raft 4, killed 3, executed after the trial 3, executed by TereVi's whim 2, died in an accident 1, took their own life 1 | murdered 17, executed after the trial 8, escaped on a raft 4, killed 3, wrongly executed 3, escaped the island 3, died in the final battle 2, died in an accident 2 |
| Trials (all weeks) | 7 | 11 |
| Verdicts right / wrong / none | 3 / 4 / 0 | 8 / 3 / 0 |
| Average sanity of survivors at the end of the week | 56.2 | 48.4 |
| Median sanity at the end of each week | 34 / 45.0 / 67 / 60 / 60.0 / 68 / 64 / 65.0 | 51 / 55.5 / 62 / 13.5 / 53 / 65.0 / 42 / 55.5 |
| Aimless share of free-time activities | 0.3 | 0.29 |
| Meal attendance (share of the living) | 0.68 | 0.67 |
| Calm meals (share) | 0.55 | 0.64 |
| Night blocks where everyone sleeps (share) | 0.37 | 0.45 |
| People awake per night block | 1.25 | 1.24 |
| Exhausted at dawn (share of the living) | 0.05 | 0.09 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.001 | 0.004 |
| Lies caught: real / honest people wrongly caught | 2 / 0 | 5 / 0 |
| Secret meetings per week | 2.1 | 1.2 |
| Snooping per week / snoopers caught (all weeks) | 3.9 / 2 | 3.6 / 4 |
| Intrusions and waking (all weeks) | walked_in 44, confronted 28, welcome 26, woke 6, confront 6, bedside_strike 2, pretend 2 | walked_in 50, confronted 39, woke 13, welcome 12, scream 6, bedside_strike 5, confront 4, pretend 2, thrown_out 1 |
| Pastimes per week (films, sunsets, talks, journals...) | 55.2 | 45.0 |
| How pastimes went (all weeks) | done 199, good 111, alone 93, flat 17, sour 14, tense 3, seen 3, caught 2 | done 188, good 97, alone 63, flat 6, sour 2, tense 2, caught 1, seen 1 |
