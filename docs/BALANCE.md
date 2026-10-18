# Balance numbers

How the game plays on mock weeks: 4 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 81.0 | 78.1 |
| Deaths per week | 3.0 | 4.2 |
| How the weeks ended | still going 4 | still going 4 |
| Deaths by cause | executed after the trial 4, murdered 4, died in an accident 1, killed 1, wrongly executed 1, escaped the island 1 | murdered 9, executed after the trial 6, killed 1, escaped the island 1 |
| Trials (all weeks) | 5 | 7 |
| Verdicts right / wrong / none | 4 / 1 / 0 | 6 / 0 / 1 |
| Average sanity of survivors at the end of the week | 60.9 | 59.7 |
| Median sanity at the end of each week | 66 / 62.0 / 60.5 / 66 | 66.5 / 66 / 62 / 59 |
| Aimless share of free-time activities | 0.18 | 0.16 |
| Meal attendance (share of the living) | 0.7 | 0.65 |
| Calm meals (share) | 0.68 | 0.62 |
| Night blocks where everyone sleeps (share) | 0.62 | 0.56 |
| People awake per night block | 0.64 | 0.8 |
| Exhausted at dawn (share of the living) | 0.02 | 0.06 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 1 / 0 | 12 / 0 |
