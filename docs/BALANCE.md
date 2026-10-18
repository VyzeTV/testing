# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 88.9 | 82.0 |
| Deaths per week | 4.0 | 4.0 |
| How the weeks ended | reckoning 2, still going 6 | battle 1, sole 1, still going 6 |
| Deaths by cause | died in the Reckoning 16, wrongly executed 4, escaped the island 4, murdered 3, killed 3, executed after the trial 2 | murdered 9, executed after the trial 9, killed 4, wrongly executed 3, escaped the island 3, executed by TereVi's whim 2, died in the final battle 1, died in an accident 1 |
| Trials (all weeks) | 6 | 12 |
| Verdicts right / wrong / none | 2 / 4 / 0 | 9 / 3 / 0 |
| Average sanity of survivors at the end of the week | 62.8 | 55.3 |
| Median sanity at the end of each week | 68 / nobody left / 62 / 62 / 68.0 / nobody left / 60 / 66.5 | 24 / 62 / 65.0 / 64.0 / 65.0 / 68.0 / 49 / 62 |
| Aimless share of free-time activities | 0.18 | 0.16 |
| Meal attendance (share of the living) | 0.65 | 0.68 |
| Calm meals (share) | 0.53 | 0.58 |
| Night blocks where everyone sleeps (share) | 0.39 | 0.21 |
| People awake per night block | 1.5 | 1.87 |
| Exhausted at dawn (share of the living) | 0.08 | 0.19 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 2 / 0 |
| Secret meetings per week | 2.4 | 3.0 |
| Snooping per week / snoopers caught (all weeks) | 2.5 / 3 | 2.1 / 3 |
