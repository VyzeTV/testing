"""Review I6 on a scratch day. Defaults to free mock; real backends consume usage.

python tests/real_decision_day.py --backend mock --output /tmp/i6-day.json
After authorization/configuration, use --backend cli or --backend api. Roughly
60–120 calls; --call-cap bounds the day. Review the saved reasons and later lines
manually: a script cannot establish whether free prose gives a believable motive.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from murder.llm import LLM, find_api_key


class Audited(LLM):
    def __init__(self, backend):
        super().__init__(backend)
        self.answers = []

    def decide(self, system, user, ctx):
        answer = super().decide(system, user, ctx)
        with self._lock:
            self.answers.append(dict(cid=ctx['cid'], hour=ctx['hour'],
                                     options=ctx['options'], answer=answer))
        return answer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=('mock', 'cli', 'api'), default='mock')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--call-cap', type=int, default=120)
    args = parser.parse_args()
    if args.backend == 'cli' and not shutil.which('claude'):
        parser.error('Claude CLI is not configured; install/login or use --backend mock.')
    if args.backend == 'api' and not find_api_key():
        parser.error('Anthropic API credentials are not configured; use your environment or --backend mock.')
    if args.call_cap < 1:
        parser.error('--call-cap must be positive')
    if args.output.is_dir():
        parser.error('--output must be a file')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='mc_i6_day_') as scratch:
        os.environ['MC_DATA_DIR'] = scratch
        from murder.engine import DayRunner
        from murder.world import World, new_state
        world = World(new_state(3))
        llm, ticks = Audited(args.backend), []
        runner = DayRunner(world, llm, ticks.append, seed=606, murders=False, rule_mode='none', call_cap=args.call_cap)
        a, b = sorted(world.agents)[:2]
        world.agents[a]['room'] = world.agents[b]['room'] = 'lounge'
        setup = runner.new_tick(8)
        runner.commitments.request(setup, a, dict(kind='thank', target=b, hours=24))
        runner.emotions.put(a, 'loneliness', 6, 'spent a long stretch awake alone', 'i6-validation:alone', setup)
        runner.run()
        errors = [e for t in ticks for e in t.get('errors', [])]
        errors += [str(t[k]) for t in ticks for k in ('live_error', 'env_error', 'mind_error') if t.get(k)]
        records = [r for rows in world.state['decision_history'].values() for r in rows]
        report = dict(backend=args.backend, usage=llm.usage, decisions=len(llm.answers), errors=errors,
                      real_model_day=args.backend != 'mock', semantic_review_required=True,
                      statuses=dict(Counter(r['status'] for r in records)),
                      missing_reasons=sum(not r['reason'] and r['status'] != 'rejected' for r in records))
        payload = dict(report=report, calls=llm.answers, motives=world.state['decision_history'],
                       dialogues=[dict(hour=t['hour'], groups=t.get('talk', [])) for t in ticks],
                       diaries={p: a['memory']['diary'] for p, a in world.all_agents.items()})
        args.output.write_text(json.dumps(payload, indent=2), encoding='utf-8')
        print(json.dumps(report, indent=2))
        if errors:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
