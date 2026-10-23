"""I7: behavioral contrasts, knowledge boundaries, and reproducible model choices."""
import copy
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('MC_DATA_DIR', tempfile.mkdtemp(prefix='mc_mock_'))
from murder import emotions, mock_policy as policy
from murder.commitments import start
from murder.engine import DayRunner
from murder.llm import LLM
from murder.world import World, new_state


class MockChecks(unittest.TestCase):
    def setUp(self):
        self.knobs = LLM('mock')
        for key in ('plot', 'murder', 'suicide', 'assault', 'sabotage', 'experiment', 'host'):
            setattr(self.knobs, f'mock_{key}_prob', 0)
        self.actor = dict(cid='a', facets={}, values={}, needs={}, hp=100, sanity=80,
                          aff={'b': 5, 'c': -5}, drive={'id': 'survivor'}, emotions=[], commitments=[],
                          visible={'b': {'hp': 100, 'sanity': 80}, 'c': {'hp': 100, 'sanity': 80}})
        self.ctx = dict(actor=self.actor, hour=12, now=84, room='lounge', home='red_room',
                        reachable=['lounge', 'library', 'red_room'], humans_here=['b', 'c'],
                        brain=False, murder_ok=True, violence_ok=True, plot_ok=True)

    def choose(self, ctx=None, seed=1):
        return policy.decide(ctx or self.ctx, random.Random(seed), self.knobs)

    def rate(self, predicate, ctx=None):
        return sum(predicate(self.choose(ctx, n)) for n in range(600))

    def feel(self, kind, target=None, strength=8, room=None):
        self.actor['emotions'].append(dict(kind=kind, target=target, strength=strength, room=room, cause='a known event'))

    def test_facets_change_company_choices(self):
        self.actor['facets']['gregariousness'] = 0
        quiet = self.rate(lambda d: bool(d['talk_to']))
        self.actor['facets']['gregariousness'] = 100
        self.assertGreater(self.rate(lambda d: bool(d['talk_to'])), quiet + 100)

    def test_loneliness_and_attraction_seek_company(self):
        before = self.rate(lambda d: d['talk_to'] == ['b'])
        self.feel('loneliness')
        self.feel('attraction', 'b')
        self.assertGreater(self.rate(lambda d: d['talk_to'] == ['b']), before + 60)

    def test_fear_avoids_known_person(self):
        before = self.rate(lambda d: d['talk_to'] == ['b'])
        self.feel('fear', 'b', 10)
        self.assertLess(self.rate(lambda d: d['talk_to'] == ['b']), before / 3)

    def test_grief_avoids_known_place(self):
        before = self.rate(lambda d: d.get('target_room') == 'library')
        self.feel('grief', room='library', strength=10)
        self.assertLess(self.rate(lambda d: d.get('target_room') == 'library'), before / 3)

    def test_hurt_or_exhausted_people_recover(self):
        self.actor['hp'] = 20
        self.assertEqual(self.choose()['action'], 'rest')
        self.actor['hp'] = 100
        self.actor['needs']['rest'] = 10
        self.assertEqual(self.choose()['action'], 'rest')

    def test_late_decisions_head_to_own_reachable_bed(self):
        self.ctx['hour'] = 22
        self.assertEqual(self.choose()['target_room'], 'red_room')
        self.ctx['reachable'] = ['lounge']
        self.assertEqual(self.choose()['target_room'], 'lounge')

    def test_no_uninvited_bedroom_wandering(self):
        self.ctx['reachable'].append('blue_room')
        self.actor['private_rooms'] = ['blue_room']
        self.assertFalse(self.rate(lambda d: d.get('target_room') == 'blue_room'))

    def test_promises_prioritize_follow_through(self):
        self.actor['commitments'] = [dict(id='c1', kind='thank', target='b', title='thank b', due=90)]
        self.assertEqual(self.choose()['intent'], 'thank b')
        self.assertEqual(self.choose()['talk_to'], ['b'])

    def test_host_attends_when_due_without_spending_all_day_there(self):
        self.actor['commitments'] = [dict(id='c1', kind='host', room='library', title='host the game', due=96)]
        self.assertNotEqual(self.choose()['activity'], 'host the game')
        self.ctx['now'] = 94
        self.assertEqual(self.choose()['activity'], 'host the game')

    def test_existing_plot_is_not_replaced_by_random_attack(self):
        self.knobs.mock_plot_prob = self.knobs.mock_murder_prob = 1
        self.actor['commitments'] = [dict(id='c1', kind='plot', target='b', title='existing scheme', due=None)]
        for seed in range(30):
            d = self.choose(seed=seed)
            self.assertNotIn('plot', d)
            self.assertNotEqual(d['action'], 'attack')

    def test_violence_knobs_are_off_or_force_and_honor_case_gate(self):
        self.assertFalse(self.rate(lambda d: d['action'] == 'attack' or 'plot' in d))
        self.knobs.mock_murder_prob = 1
        self.assertEqual(self.choose()['action'], 'attack')
        self.ctx['murder_ok'] = False
        self.assertNotEqual(self.choose()['action'], 'attack')

    def test_anger_and_cruelty_change_attack_frequency(self):
        self.knobs.mock_murder_prob = .1
        self.actor['facets'] = dict(cruelty=0, anger=0, impulsiveness=0, altruism=100)
        before = self.rate(lambda d: d['action'] == 'attack')
        self.actor['facets'] = dict(cruelty=100, anger=100, impulsiveness=100, altruism=0)
        self.feel('anger', 'c')
        self.assertGreater(self.rate(lambda d: d['action'] == 'attack'), before + 60)

    def test_investigation_and_curiosity_change_search_frequency(self):
        ordinary = self.rate(lambda d: d['action'] == 'investigate')
        self.ctx['investigating'] = True
        self.actor['facets']['curiosity'] = 100
        self.assertGreater(self.rate(lambda d: d['action'] == 'investigate'), ordinary + 100)

    def test_work_uses_offered_route_and_plans_only_when_enabled(self):
        self.actor['work'] = dict(room='library', route='transmit', step='signal')
        self.knobs.mock_experiment_prob = 1
        self.assertIn('signal', self.choose()['idea'])
        self.assertNotIn('plan', self.choose())
        self.knobs.mock_experiment_prob = 0
        self.ctx['brain'] = True
        samples = [self.choose(seed=n) for n in range(100)]
        self.assertTrue(any(any(p['do'] == 'work' and p['where'] == 'library' for p in d['plan']) for d in samples))

    def test_unfinished_brain_plan_is_preserved(self):
        self.ctx['brain'] = True
        self.actor['plan'] = [dict(do='talk', who='b', where='', why='thank them')]
        self.assertEqual(self.choose()['plan'], self.actor['plan'])

    def test_no_hidden_remote_or_sleeping_targets(self):
        self.actor['visible'] = {}
        self.knobs.mock_plot_prob = self.knobs.mock_murder_prob = 1
        self.assertFalse(self.choose()['talk_to'])
        self.assertNotIn('plot', self.choose())
        self.assertNotEqual(self.choose()['action'], 'attack')

    def test_help_reactions_follow_kindness_and_protection(self):
        ctx = dict(actor=self.actor, humans=['b', 'c'], reachable=['library'])
        self.actor['visible']['b']['hp'] = 30
        self.actor['facets']['altruism'] = 0
        cold = sum(policy.react(ctx, random.Random(n))['reaction'] == 'help' for n in range(600))
        self.actor['facets']['altruism'] = 100
        self.actor['commitments'] = [dict(kind='protect', target='b')]
        caring = [policy.react(ctx, random.Random(n)) for n in range(600)]
        self.assertGreater(sum(r['reaction'] == 'help' for r in caring), cold + 200)
        self.assertTrue(all(r['target'] == 'b' for r in caring if r['reaction'] == 'help'))

    def test_reaction_cannot_confront_an_unseen_attacker(self):
        self.actor['visible'] = {}
        self.feel('anger', 'c')
        out = policy.react(dict(actor=self.actor, humans=['c'], reachable=[]), random.Random(3))
        self.assertNotEqual(out['reaction'], 'confront')

    def test_reflection_does_not_spin_goals_without_an_event(self):
        self.assertEqual(policy.reflect(dict(actor=self.actor), random.Random(1), 1)['drive'], 'keep')

    def test_reflection_changes_from_known_feeling_and_keeps_obligations(self):
        self.feel('anger', 'c')
        self.actor['facets']['vengefulness'] = 100
        ctx = dict(actor=self.actor, ids=['b', 'c'])
        out = policy.reflect(ctx, random.Random(1), 1)
        self.assertEqual((out['drive'], out['target']), ('avenger', 'c'))
        self.assertIn('anger', out['diary'])
        self.actor['commitments'] = [dict(kind='protect', target='b')]
        self.assertEqual(policy.reflect(ctx, random.Random(1), 1)['drive'], 'keep')

    def test_conversation_cannot_randomly_turn_friends_hostile(self):
        people = [dict(id='a', actor=self.actor), dict(id='b', actor=dict(aff={'a': 6}))]
        for seed in range(100):
            aff, _, _ = policy.conversation_effects(people, random.Random(seed))
            self.assertTrue(all(e['delta'] > 0 for e in aff))

    def test_social_proposals_are_valid_and_relationship_based(self):
        ctx = dict(actor=self.actor, cid='a', ids=['a', 'b', 'c'])
        for seed in range(100):
            out = policy.social_proposal(ctx, random.Random(seed))
            self.assertIn(out['move'], ('comfort', 'confide', 'flirt', 'confront'))
            self.assertIn(out['to'], ('b', 'c'))
            self.assertFalse(out['move'] == 'flirt' and out['to'] == 'c')

    def test_policy_does_not_mutate_snapshot(self):
        before = copy.deepcopy(self.ctx)
        self.choose()
        policy.react(dict(actor=self.actor), random.Random(1))
        policy.reflect(dict(actor=self.actor), random.Random(1), 1)
        self.assertEqual(self.ctx, before)

    def test_context_filters_private_causes_and_remote_health(self):
        w = World(new_state(3))
        r = DayRunner(w, LLM('mock'), lambda t: None, seed=12)
        a, b = sorted(w.agents)[:2]
        w.agents[a]['room'] = 'lounge'
        w.agents[b]['room'] = 'library'
        r.tuning_get = lambda: {'brain': 1}
        w.agents[a]['plan'] = dict(day=3, items=[dict(do='avoid', who=b, where='', why='a private suspicion')])
        emotions.add(w.state, a, 'guilt', 8, 80, 'a secret killing', 'private', b)
        start(w.state, a, 'plot', 'secret plan', 80, target=b, known_by=[a])
        own = policy.actor_context(r, a, 12)
        shared = policy.actor_context(r, a, 12, [a, b])
        self.assertTrue(own['emotions'])
        self.assertTrue(own['commitments'])
        self.assertFalse(shared['emotions'])
        self.assertFalse(shared['commitments'])
        self.assertTrue(own['plan'])
        self.assertFalse(shared['plan'])
        self.assertFalse(shared['drive'])
        self.assertNotIn(b, own['visible'])
        self.assertNotIn('killer', own)

    def test_context_leaves_world_and_rng_unchanged(self):
        w = World(new_state(3))
        r = DayRunner(w, LLM('mock'), lambda t: None, seed=12)
        cid = sorted(w.agents)[0]
        r.mind(cid)
        before, rng = copy.deepcopy(w.dump()), r.rng.getstate()
        policy.actor_context(r, cid, 12)
        self.assertEqual(w.dump(), before)
        self.assertEqual(r.rng.getstate(), rng)

    def test_save_reload_preserves_actor_information_and_choice(self):
        w = World(new_state(3))
        r = DayRunner(w, LLM('mock'), lambda t: None, seed=12)
        cid = sorted(w.agents)[0]
        emotions.add(w.state, cid, 'loneliness', 8, 80, 'time alone', 'alone')
        before = policy.actor_context(r, cid, 12)
        w2 = World(json.loads(json.dumps(w.dump())))
        r2 = DayRunner(w2, LLM('mock'), lambda t: None, seed=12)
        after = policy.actor_context(r2, cid, 12)
        self.assertEqual(before, after)
        ctx = dict(self.ctx, actor=before)
        self.assertEqual(self.choose(ctx), self.choose(dict(ctx, actor=after)))

    def test_normal_plan_proposals_only_select_checked_offers(self):
        plans = [dict(scheme='asleep', room='red_room', when='night', steps=[dict(do='wait')]),
                 dict(scheme='alone', room='library', when='any', steps=[dict(do='watch')])]
        llm = LLM('mock')
        llm.seed = 12
        for seed in range(40):
            out = llm.propose('', str(seed), dict(plans=plans, actor=self.actor))
            self.assertTrue(out.pop('reason'))
            self.assertIn(out, plans)
        self.assertEqual(llm.propose('', 'empty', dict(plans=[])), {})
        self.assertEqual(llm.propose('', 'legacy', {}), {})

    def test_seeded_answers_ignore_thread_order_and_python_collection_order(self):
        def answers(workers, reverse):
            llm = LLM('mock')
            llm.seed = 12
            prompts = list(range(20))
            if reverse:
                prompts.reverse()
            def call(n):
                ctx = copy.deepcopy(self.ctx)
                if reverse:
                    ctx['reachable'].reverse()
                    ctx['humans_here'].reverse()
                return n, llm.decide('', f'prompt:{n}', ctx)
            with ThreadPoolExecutor(max_workers=workers) as pool:
                return dict(pool.map(call, prompts))
        self.assertEqual(answers(1, False), answers(4, True))


if __name__ == '__main__':
    unittest.main(verbosity=2)
