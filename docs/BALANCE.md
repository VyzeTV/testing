# Balance numbers

How the game plays on mock weeks: 4 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 86.5 | 73.8 |
| Deaths per week | 2.2 | 4.8 |
| How the weeks ended | still going 4 | still going 3, winners 1 |
| Deaths by cause | executed after the trial 4, murdered 3, died in an accident 1, was poisoned 1 | murdered 8, executed after the trial 7, escaped the island 2, wrongly executed 1, killed 1 |
| Trials (all weeks) | 4 | 9 |
| Verdicts right / wrong / none | 4 / 0 / 0 | 7 / 1 / 1 |
| Median sanity at the end of each week | 87 / 85.0 / 87.0 / 89.0 | 87.5 / 52 / 90.0 / 90.0 |
| Aimless share of free-time activities | 0.18 | 0.17 |
| Meal attendance (share of the living) | 0.72 | 0.68 |
| Calm meals (share) | 0.73 | 0.73 |
| Night blocks where everyone sleeps (share) | 0.67 | 0.6 |
| People awake per night block | 0.55 | 0.62 |
| Exhausted at dawn (share of the living) | 0.0 | 0.05 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 2 / 0 |
