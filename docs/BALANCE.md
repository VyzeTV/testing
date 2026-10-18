# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 90.0 | 85.2 |
| Deaths per week | 4.1 | 3.5 |
| How the weeks ended | reckoning 2, still going 6 | sole 1, still going 6, winners 1 |
| Deaths by cause | died in the Reckoning 16, murdered 7, wrongly executed 3, escaped the island 3, executed after the trial 2, killed 1, took their own life 1 | murdered 10, wrongly executed 5, escaped the island 5, executed after the trial 4, killed 2, executed by TereVi's whim 1, died in an accident 1 |
| Trials (all weeks) | 5 | 9 |
| Verdicts right / wrong / none | 2 / 3 / 0 | 4 / 5 / 0 |
| Average sanity of survivors at the end of the week | 58.2 | 57.4 |
| Median sanity at the end of each week | 62 / 39.5 / 53.0 / 68 / 68.0 / nobody left / nobody left / 68 | 65 / 62 / 64.0 / 68.0 / 46 / 65.5 / 55 / 48.0 |
| Aimless share of free-time activities | 0.17 | 0.17 |
| Meal attendance (share of the living) | 0.66 | 0.64 |
| Calm meals (share) | 0.56 | 0.54 |
| Night blocks where everyone sleeps (share) | 0.35 | 0.29 |
| People awake per night block | 1.61 | 1.98 |
| Exhausted at dawn (share of the living) | 0.12 | 0.17 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 3 / 0 |
| Secret meetings per week | 2.2 | 3.6 |
| Snooping per week / snoopers caught (all weeks) | 4.4 / 4 | 4.4 / 1 |
