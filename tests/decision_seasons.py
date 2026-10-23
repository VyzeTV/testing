"""Whole-season stated-motive coverage, plus relationship and story checks.

python tests/decision_seasons.py --seeds 40 --output /tmp/decisions.json
The observer retains record references until each season ends; it changes no choices.
"""
import argparse
from collections import Counter
import json
import os
from multiprocessing import Pool
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from murder.decisions import DecisionManager
import relationship_seasons

original = DecisionManager.record
records = []


def record(self, *args, **kwargs):
    result = original(self, *args, **kwargs)
    records.append(result)
    return result


DecisionManager.record = record


def run(job):
    records.clear()
    result = relationship_seasons.run(job)
    result['decision_sample'] = dict(total=len(records),
        statuses=dict(Counter(r['status'] for r in records)),
        kinds=dict(Counter(r.get('kind', 'decision') for r in records)),
        missing_reasons=sum(not r['reason'] and r['status'] != 'rejected' for r in records),
        rejections=dict(Counter(r.get('change', 'invalid proposal') for r in records if r['status'] == 'rejected')))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', type=int, default=40)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error('--seeds must be positive')
    with Pool(min(5, os.cpu_count() or 2)) as pool:
        rows = pool.map(run, [(v, seed) for v in (False, True) for seed in range(1, args.seeds + 1)])
    if args.output:
        args.output.write_text(json.dumps(rows))
    for summary in relationship_seasons.summary(rows):
        samples = [r['decision_sample'] for r in rows if r['violent'] == summary['violent']]
        summary.update(decisions=sum(r['total'] for r in samples),
                       missing_reasons=sum(r['missing_reasons'] for r in samples),
                       statuses=dict(sum((Counter(r['statuses']) for r in samples), Counter())),
                       rejections=dict(sum((Counter(r['rejections']) for r in samples), Counter())))
        print(json.dumps(summary))
