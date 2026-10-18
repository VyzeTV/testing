# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 89.3 | 80.9 |
| Deaths per week | 2.8 | 3.6 |
| How the weeks ended | still going 8 | still going 8 |
| Deaths by cause | murdered 7, executed after the trial 6, killed 4, wrongly executed 2, escaped the island 2, died in an accident 1 | murdered 10, executed after the trial 10, killed 6, wrongly executed 1, escaped the island 1, died in an accident 1 |
| Trials (all weeks) | 8 | 11 |
| Verdicts right / wrong / none | 6 / 2 / 0 | 10 / 1 / 0 |
| Average sanity of survivors at the end of the week | 60.2 | 57.6 |
| Median sanity at the end of each week | 64 / 51 / 68.0 / 53 / 62.0 / 68 / 56 / 62 | 62 / 43.0 / 59.5 / 64 / 60 / 60 / 64.0 / 62 |
| Aimless share of free-time activities | 0.18 | 0.17 |
| Meal attendance (share of the living) | 0.65 | 0.66 |
| Calm meals (share) | 0.56 | 0.7 |
| Night blocks where everyone sleeps (share) | 0.32 | 0.33 |
| People awake per night block | 1.69 | 1.55 |
| Exhausted at dawn (share of the living) | 0.14 | 0.15 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 4 / 0 | 2 / 0 |
| Secret meetings per week | 2.8 | 2.5 |
| Snooping per week / snoopers caught (all weeks) | 4.4 / 6 | 2.9 / 2 |
