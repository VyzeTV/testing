# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 90.1 | 86.7 |
| Deaths per week | 3.4 | 3.0 |
| How the weeks ended | reckoning 1, still going 7 | still going 8 |
| Deaths by cause | murdered 8, died in the Reckoning 8, executed after the trial 4, escaped the island 3, wrongly executed 2, killed 2 | murdered 11, executed after the trial 7, killed 4, escaped the island 2 |
| Trials (all weeks) | 7 | 9 |
| Verdicts right / wrong / none | 4 / 2 / 1 | 7 / 0 / 2 |
| Average sanity of survivors at the end of the week | 61.8 | 59.6 |
| Median sanity at the end of each week | 61.0 / 67 / 68.0 / 64.0 / nobody left / 68.0 / 62 / 68 | 62 / 56 / 50.0 / 63 / 65.0 / 68.0 / 63.5 / 62 |
| Aimless share of free-time activities | 0.17 | 0.18 |
| Meal attendance (share of the living) | 0.65 | 0.64 |
| Calm meals (share) | 0.52 | 0.5 |
| Night blocks where everyone sleeps (share) | 0.38 | 0.33 |
| People awake per night block | 1.47 | 1.56 |
| Exhausted at dawn (share of the living) | 0.09 | 0.13 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 4 / 0 | 1 / 0 |
| Secret meetings per week | 1.8 | 1.8 |
| Snooping per week / snoopers caught (all weeks) | 6.6 / 8 | 3.6 / 3 |
