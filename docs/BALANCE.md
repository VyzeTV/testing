# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 89.5 | 77.1 |
| Deaths per week | 3.1 | 4.9 |
| How the weeks ended | still going 8 | battle 1, sole 1, still going 4, ultimatum 1, winners 1 |
| Deaths by cause | murdered 10, executed after the trial 4, wrongly executed 3, escaped the island 3, escaped on a raft 2, took their own life 1, took their own life (a pact) 1, was poisoned 1 | murdered 15, executed after the trial 11, escaped on a raft 4, wrongly executed 2, escaped the island 2, died in the final battle 2, executed by TereVi's whim 2, killed 1 |
| Trials (all weeks) | 7 | 13 |
| Verdicts right / wrong / none | 4 / 3 / 0 | 11 / 2 / 0 |
| Average sanity of survivors at the end of the week | 59.4 | 59.0 |
| Median sanity at the end of each week | 64.0 / 68 / 60 / 64.0 / 68 / 36 / 68 / 65.0 | 68 / 46 / 76 / 56.5 / 48 / 68 / 62.0 / 55.5 |
| Aimless share of free-time activities | 0.31 | 0.3 |
| Meal attendance (share of the living) | 0.71 | 0.69 |
| Calm meals (share) | 0.66 | 0.65 |
| Night blocks where everyone sleeps (share) | 0.39 | 0.41 |
| People awake per night block | 1.4 | 1.29 |
| Exhausted at dawn (share of the living) | 0.06 | 0.07 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 9 / 0 |
| Secret meetings per week | 3.5 | 2.5 |
| Snooping per week / snoopers caught (all weeks) | 4.4 / 5 | 1.9 / 2 |
| Pastimes per week (films, sunsets, talks, journals...) | 59.4 | 40.5 |
| How pastimes went (all weeks) | done 225, good 115, alone 97, flat 22, sour 11, caught 2, tense 2, seen 1 | done 150, good 87, alone 63, flat 10, sour 7, tense 5, caught 1, seen 1 |
