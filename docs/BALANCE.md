# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 91.2 | 87.4 |
| Deaths per week | 4.0 | 2.6 |
| How the weeks ended | reckoning 2, still going 6 | still going 8 |
| Deaths by cause | died in the Reckoning 16, murdered 7, executed after the trial 3, escaped the island 2, killed 2, wrongly executed 1, took their own life 1 | murdered 10, executed after the trial 5, escaped the island 3, killed 2, died in an accident 1 |
| Trials (all weeks) | 5 | 8 |
| Verdicts right / wrong / none | 3 / 1 / 1 | 5 / 0 / 3 |
| Average sanity of survivors at the end of the week | 59.9 | 60.4 |
| Median sanity at the end of each week | 65.0 / 53.0 / 62 / 63 / 62 / nobody left / nobody left / 60 | 61 / 65.0 / 61.0 / 67 / 65 / 67.0 / 64.0 / 48.0 |
| Aimless share of free-time activities | 0.18 | 0.17 |
| Meal attendance (share of the living) | 0.66 | 0.65 |
| Calm meals (share) | 0.5 | 0.57 |
| Night blocks where everyone sleeps (share) | 0.37 | 0.33 |
| People awake per night block | 1.52 | 1.84 |
| Exhausted at dawn (share of the living) | 0.11 | 0.15 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 1 / 0 | 3 / 0 |
| Secret meetings per week | 1.8 | 3.6 |
| Snooping per week / snoopers caught (all weeks) | 4.1 / 4 | 4.0 / 1 |
