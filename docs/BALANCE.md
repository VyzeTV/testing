# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 89.1 | 85.1 |
| Deaths per week | 4.2 | 3.8 |
| How the weeks ended | reckoning 2, still going 6 | battle 2, still going 6 |
| Deaths by cause | died in the Reckoning 16, murdered 6, executed after the trial 4, killed 3, wrongly executed 2, escaped the island 2, took their own life 1 | murdered 9, executed after the trial 6, killed 4, died in the final battle 4, wrongly executed 3, escaped the island 3, died in an accident 1 |
| Trials (all weeks) | 6 | 9 |
| Verdicts right / wrong / none | 4 / 2 / 0 | 6 / 3 / 0 |
| Average sanity of survivors at the end of the week | 58.4 | 54.1 |
| Median sanity at the end of each week | 65 / 39.5 / 53.0 / 68 / 68.0 / nobody left / nobody left / 64.0 | 59 / 65.0 / 64.0 / 64 / 39 / 65.5 / 39 / 48.0 |
| Aimless share of free-time activities | 0.18 | 0.17 |
| Meal attendance (share of the living) | 0.66 | 0.65 |
| Calm meals (share) | 0.56 | 0.58 |
| Night blocks where everyone sleeps (share) | 0.38 | 0.28 |
| People awake per night block | 1.51 | 1.85 |
| Exhausted at dawn (share of the living) | 0.11 | 0.17 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 4 / 0 |
| Secret meetings per week | 1.8 | 3.4 |
| Snooping per week / snoopers caught (all weeks) | 4.2 / 4 | 4.5 / 2 |
