# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 87.5 | 78.9 |
| Deaths per week | 2.8 | 4.2 |
| How the weeks ended | still going 8 | battle 1, still going 7 |
| Deaths by cause | murdered 10, executed after the trial 5, wrongly executed 3, escaped the island 3, died in an accident 1 | murdered 19, executed after the trial 10, died in the final battle 2, killed 1, wrongly executed 1, escaped the island 1 |
| Trials (all weeks) | 8 | 11 |
| Verdicts right / wrong / none | 5 / 3 / 0 | 10 / 1 / 0 |
| Average sanity of survivors at the end of the week | 61.6 | 55.2 |
| Median sanity at the end of each week | 65 / 60 / 61 / 68.0 / 68.0 / 65.0 / 65 / 62.5 | 62.0 / 25 / 60 / 65.0 / 67.5 / 65 / 54 / 59.5 |
| Aimless share of free-time activities | 0.17 | 0.16 |
| Meal attendance (share of the living) | 0.66 | 0.65 |
| Calm meals (share) | 0.57 | 0.61 |
| Night blocks where everyone sleeps (share) | 0.37 | 0.38 |
| People awake per night block | 1.49 | 1.47 |
| Exhausted at dawn (share of the living) | 0.1 | 0.14 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 2 / 0 | 15 / 0 |
| Secret meetings per week | 2.0 | 2.2 |
| Snooping per week / snoopers caught (all weeks) | 4.4 / 5 | 3.1 / 5 |
