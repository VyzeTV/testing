"""Describe mock choices and participation over matching short runs, without AI calls.

python tests/mock_metrics.py --output /tmp/mock-metrics.json
Rates describe decisions, not promises that an offered activity was completed.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from murder.engine import DayRunner
from murder.llm import LLM
from murder.world import World, new_state


class Observed(LLM):
    def __init__(self):
        super().__init__('mock')
        self.choices = Counter()

    def decide(self, system, user, ctx):
        out = super().decide(system, user, ctx)
        with self._lock:
            self.choices['decisions'] += 1
            self.choices['plots'] += bool(out.get('plot'))
            self.choices['attacks'] += out.get('action') == 'attack'
            self.choices['talk_intentions'] += bool(out.get('talk_to') or any(p['do'] == 'talk' for p in out.get('plan', [])))
            self.choices['work_intentions'] += any(p['do'] == 'work' for p in out.get('plan', []))
            self.choices['experiments'] += out.get('action') == 'experiment'
            self.choices['hosts'] += bool(out.get('host'))
        return out


def sample(seed, violent, days, brain=False):
    LLM.mock_plot_prob = .04 if violent else 0
    LLM.mock_murder_prob = .02 if violent else 0
    w = World(new_state(1))
    choices, participants, errors = Counter(), set(), []
    conversations, joined = set(), set()
    played = 0
    for day in range(1, days + 1):
        if w.state.get('over') or not w.agents:
            break
        w.state['day'] = day
        llm, ticks = Observed(), []
        runner = DayRunner(w, llm, ticks.append, seed=seed * 1000 + day, rule_mode='roulette')
        if brain:
            runner.tuning_get = lambda: {'brain': 1}
        runner.run()
        choices.update(llm.choices)
        for tick in ticks:
            errors.extend(tick.get('errors', []))
            errors.extend(str(tick[k]) for k in ('live_error', 'env_error', 'mind_error') if tick.get(k))
            for group in tick.get('talk', []):
                participants.update(line['speaker'] for line in group.get('lines', []) if line['speaker'] in w.cast)
                if group.get('conv'):
                    key = (day, group['conv'])
                    conversations.add(key)
                    if group.get('joined'):
                        joined.add(key)
        played += 1
    helpers = set()
    for route in w.state.get('escape', {}).get('routes', {}).values():
        helpers.update(route.get('contributors', []))
    plotters = sorted({c['owner'] for c in w.state.get('commitment_history', []) if c['kind'] == 'plot' and c['status'] == 'active'})
    return dict(seed=seed, violent=violent, brain=brain, days=played, choices=dict(choices),
                live_conversations=len(conversations), conversations_with_joiners=len(joined), plotters=plotters,
                speakers=sorted(participants), escape_helpers=sorted(helpers), errors=errors)


def summary(rows):
    counts = sum((Counter(r['choices']) for r in rows), Counter())
    n = counts['decisions'] or 1
    return dict(runs=len(rows), days=sum(r['days'] for r in rows), choices=dict(counts),
                percent_per_decision={k: round(100 * v / n, 2) for k, v in sorted(counts.items()) if k != 'decisions'},
                speakers_per_run=[len(r['speakers']) for r in rows],
                escape_helpers_per_run=[len(r['escape_helpers']) for r in rows],
                plotters_per_run=[len(r.get('plotters', [])) for r in rows],
                live_conversations=sum(r.get('live_conversations', 0) for r in rows),
                conversations_with_joiners=sum(r.get('conversations_with_joiners', 0) for r in rows),
                errors=sum(len(r['errors']) for r in rows))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--days', type=int, default=5)
    parser.add_argument('--brain', action='store_true', help='also enable the optional memory/plan dial')
    args = parser.parse_args()
    if args.days < 1:
        parser.error('--days must be positive')
    rows = [sample(seed, violent, args.days, args.brain) for violent in (False, True) for seed in (11, 22, 33)]
    report = dict(summary=summary(rows), runs=rows)
    if args.output:
        args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report['summary'], indent=2))
