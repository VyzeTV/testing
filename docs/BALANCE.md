# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 88.2 | 80.7 |
| Deaths per week | 4.2 | 4.0 |
| How the weeks ended | reckoning 2, still going 6 | sole 1, still going 7 |
| Deaths by cause | died in the Reckoning 16, murdered 5, wrongly executed 4, escaped the island 4, killed 3, executed after the trial 2 | murdered 11, executed after the trial 9, killed 5, wrongly executed 2, escaped the island 2, executed by TereVi's whim 2, died in an accident 1 |
| Trials (all weeks) | 6 | 11 |
| Verdicts right / wrong / none | 2 / 4 / 0 | 9 / 2 / 0 |
| Average sanity of survivors at the end of the week | 62.3 | 57.9 |
| Median sanity at the end of each week | 61.0 / nobody left / 65.0 / 62 / 68.0 / nobody left / 60 / 68.0 | 64.0 / 62 / 60 / 60 / 64.5 / 68 / 49 / 55 |
| Aimless share of free-time activities | 0.17 | 0.16 |
| Meal attendance (share of the living) | 0.65 | 0.68 |
| Calm meals (share) | 0.57 | 0.61 |
| Night blocks where everyone sleeps (share) | 0.42 | 0.31 |
| People awake per night block | 1.34 | 1.5 |
| Exhausted at dawn (share of the living) | 0.07 | 0.14 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.001 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 6 / 0 |
| Secret meetings per week | 1.9 | 2.2 |
| Snooping per week / snoopers caught (all weeks) | 2.2 / 3 | 2.0 / 2 |
