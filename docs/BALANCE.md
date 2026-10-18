# Balance numbers

How the game plays on mock weeks: 4 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 84.0 | 80.8 |
| Deaths per week | 2.5 | 4.5 |
| How the weeks ended | still going 4 | battle 1, still going 3 |
| Deaths by cause | murdered 4, died in an accident 2, executed after the trial 2, escaped the island 2 | murdered 7, executed after the trial 4, wrongly executed 2, escaped the island 2, died in the final battle 2, killed 1 |
| Trials (all weeks) | 4 | 6 |
| Verdicts right / wrong / none | 2 / 0 / 2 | 4 / 2 / 0 |
| Average sanity of survivors at the end of the week | 63.2 | 53.4 |
| Median sanity at the end of each week | 66.0 / 65.0 / 62.0 / 66.0 | 30 / 60 / 62 / 71 |
| Aimless share of free-time activities | 0.2 | 0.16 |
| Meal attendance (share of the living) | 0.72 | 0.59 |
| Calm meals (share) | 0.7 | 0.55 |
| Night blocks where everyone sleeps (share) | 0.36 | 0.31 |
| People awake per night block | 1.51 | 1.49 |
| Exhausted at dawn (share of the living) | 0.1 | 0.13 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 0 / 0 |
| Secret meetings per week | 4.2 | 2.5 |
| Snooping per week / snoopers caught (all weeks) | 3.0 / 1 | 3.8 / 1 |
