# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 87.7 | 81.1 |
| Deaths per week | 4.4 | 4.1 |
| How the weeks ended | reckoning 2, still going 6 | still going 7, winners 1 |
| Deaths by cause | died in the Reckoning 16, murdered 4, wrongly executed 4, escaped the island 4, killed 4, executed after the trial 3 | murdered 15, executed after the trial 10, killed 4, wrongly executed 2, escaped the island 2 |
| Trials (all weeks) | 7 | 12 |
| Verdicts right / wrong / none | 3 / 4 / 0 | 10 / 2 / 0 |
| Average sanity of survivors at the end of the week | 62.3 | 53.1 |
| Median sanity at the end of each week | 67.0 / nobody left / 62 / 62 / 68.0 / nobody left / 60 / 65.0 | 10.0 / 62 / 58 / 65.0 / 56 / 47 / 60 / 64.0 |
| Aimless share of free-time activities | 0.17 | 0.15 |
| Meal attendance (share of the living) | 0.66 | 0.68 |
| Calm meals (share) | 0.58 | 0.61 |
| Night blocks where everyone sleeps (share) | 0.44 | 0.21 |
| People awake per night block | 1.3 | 1.75 |
| Exhausted at dawn (share of the living) | 0.07 | 0.19 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 5 / 0 |
| Secret meetings per week | 1.6 | 2.6 |
| Snooping per week / snoopers caught (all weeks) | 2.2 / 3 | 1.4 / 1 |
