# Baseline metrics

Mock weeks before the rebuild, the yardstick for its phase gates. 3 weeks of 7 days per configuration (seeds 11, 22, 33), default tuning. Regenerate with `python tests/baseline.py --write`.

The mock backend answers every model call, so call counts are what a real backend would be asked; the content of mock answers is scripted, so drama metrics (deaths, verdicts) only show that the machinery runs. Deaths include the deadline reckoning, which kills everyone when nobody has died by the deadline.

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 91.7 | 90.0 |
| Conversation groups per day | 9.0 | 8.9 |
| Chats per free block | 0.32 | 0.22 |
| Aimless share of free-time activities | 0.19 | 0.21 |
| Deaths per week | 4.3 | 3.0 |
| Trials (all weeks) | 2 | 3 |
| Verdicts right / wrong / none | 2 / 0 / 0 | 2 / 1 / 0 |
| Median sanity at the end of each week | nobody left, 83, 90.0 | 87, 75.5, 90.0 |
| Engine seconds per day (mock) | 0.8 | 0.8 |

## Model calls per day, by kind

- **Default:** decide 51.0, converse 9.0, reflect 7.0, judge 5.8, confess 5.8, host_json 4.2, adjudicate 3.3, broadcast 2.4, react 1.5, neovi_plan 0.9, vote 0.7
- **Violent mock cast:** decide 48.8, converse 8.8, reflect 7.0, confess 6.2, judge 5.8, host_json 4.4, adjudicate 3.5, broadcast 2.4, react 1.0, neovi_plan 1.0, vote 1.0
