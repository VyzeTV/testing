"""Compare whole-season romance formations, including relationships that later ended.

Run: python tests/relationship_seasons.py --seeds 40 --output /tmp/relationships.json
Uses only the mock backend and the existing full-season runner.
"""
import argparse
import json
import os
from pathlib import Path
import sys
from collections import Counter
from multiprocessing import Pool
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tests")]
import season
import murder.relationships as relationships
original = relationships.record_bond
counts = Counter()
formed_people = Counter()
active_pairs = set()
def record(state, bond, now, action, reason):
    if bond['kind'] == 'romance':
        pair = tuple(sorted((bond['a'], bond['b'])))
        if action == 'formed':
            counts['formed'] += 1
            counts['duplicate'] += pair in active_pairs
            active_pairs.add(pair)
            formed_people.update(pair)
        elif action == 'ended':
            active_pairs.discard(pair)
            counts['ended'] += 1
    return original(state, bond, now, action, reason)
relationships.record_bond = record

def run(job):
    counts.clear(); formed_people.clear(); active_pairs.clear()
    result = season.one_season(job)
    result['relationship_sample'] = dict(counts, per_person=dict(formed_people))
    return result
def summary(results):
    for violent in (False, True):
        rows = [r for r in results if r['violent'] == violent]
        people = []
        for row in rows:
            # NeoVi and participant Kumiko are the same person.
            per_person = Counter()
            for who, count in row['relationship_sample']['per_person'].items():
                per_person['neovi' if who == 'kumiko' else who] += count
            people.append(per_person)
        yield dict(violent=violent, seasons=len(rows),
                   new_romances=sum(r['relationship_sample'].get('formed', 0) for r in rows),
                   maximum_per_person=max((max(p.values(), default=0) for p in people), default=0),
                   duplicate_announcements=sum(r['relationship_sample'].get('duplicate', 0) for r in rows),
                   story_issues=sum(len(r['story_issues']) for r in rows),
                   tiers=dict(Counter(r['tier'] for r in rows)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seeds', type=int, default=40)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error('--seeds must be positive')
    with Pool(min(5, os.cpu_count() or 2)) as pool:
        results = pool.map(run, [(v, s) for v in (False, True) for s in range(1, args.seeds + 1)])
    if args.output:
        args.output.write_text(json.dumps(results))
    for row in summary(results):
        print(json.dumps(row))
