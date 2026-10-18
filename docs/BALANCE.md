# Balance numbers

How the game plays on mock weeks: 4 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 82.3 | 82.6 |
| Deaths per week | 3.0 | 4.2 |
| How the weeks ended | still going 4 | sole 1, still going 3 |
| Deaths by cause | murdered 5, executed after the trial 3, died in an accident 2, wrongly executed 1, escaped the island 1 | murdered 7, executed after the trial 4, escaped the island 2, executed by TereVi's whim 2, killed 1, wrongly executed 1 |
| Trials (all weeks) | 4 | 6 |
| Verdicts right / wrong / none | 3 / 1 / 0 | 4 / 1 / 1 |
| Average sanity of survivors at the end of the week | 64.2 | 57.9 |
| Median sanity at the end of each week | 66.0 / 62.0 / 67.5 / 67.0 | 62 / 56 / 56 / 61.0 |
| Aimless share of free-time activities | 0.18 | 0.17 |
| Meal attendance (share of the living) | 0.71 | 0.67 |
| Calm meals (share) | 0.6 | 0.67 |
| Night blocks where everyone sleeps (share) | 0.43 | 0.36 |
| People awake per night block | 1.27 | 1.46 |
| Exhausted at dawn (share of the living) | 0.07 | 0.1 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 6 / 0 |
| Secret meetings per week | 4.0 | 1.5 |
| Snooping per week / snoopers caught (all weeks) | 2.2 / 1 | 2.5 / 2 |
