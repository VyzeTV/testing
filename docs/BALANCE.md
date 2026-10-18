# Balance numbers

How the game plays on mock weeks: 4 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 82.7 | 76.3 |
| Deaths per week | 2.8 | 4.2 |
| How the weeks ended | still going 3, winners 1 | still going 3, winners 1 |
| Deaths by cause | murdered 3, executed after the trial 3, died in an accident 2, killed 1, wrongly executed 1, escaped the island 1 | murdered 8, executed after the trial 6, wrongly executed 1, escaped the island 1, died in an accident 1 |
| Trials (all weeks) | 4 | 7 |
| Verdicts right / wrong / none | 3 / 1 / 0 | 6 / 1 / 0 |
| Average sanity of survivors at the end of the week | 54.8 | 58.4 |
| Median sanity at the end of each week | 66.0 / 66.0 / 29 / 64.5 | 71 / 47 / 70.5 / 53 |
| Aimless share of free-time activities | 0.19 | 0.17 |
| Meal attendance (share of the living) | 0.7 | 0.57 |
| Calm meals (share) | 0.71 | 0.53 |
| Night blocks where everyone sleeps (share) | 0.31 | 0.36 |
| People awake per night block | 1.63 | 1.48 |
| Exhausted at dawn (share of the living) | 0.12 | 0.14 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 9 / 0 |
| Secret meetings per week | 4.8 | 1.2 |
| Snooping per week / snoopers caught (all weeks) | 2.0 / 1 | 3.0 / 0 |
