"""I6: checked choices, private stated motives, overrides and dawn follow-through."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('MC_DATA_DIR', tempfile.mkdtemp(prefix='mc_decisions_'))
from murder import decisions, emotions
from murder.commitments import start
from murder.engine import DayRunner
from murder.llm import LLM, LLMError
from murder.world import World, new_state
from murder.voice import voice_prompt


class DecisionChecks(unittest.TestCase):
    def setUp(self):
        self.w = World(new_state(3))
        self.r = DayRunner(self.w, LLM('mock'), lambda t: None, seed=404, rule_mode='none',
                           tuning_get=lambda: {'engine_decisions': 0})
        self.a, self.b, self.c = sorted(self.w.agents)[:3]
        for agent in self.w.agents.values():
            agent.update(room='lounge', hp=100, sanity=80, asleep=False)
        self.w.state['_hour'] = 12
        self.tick = self.r.new_tick(12)

    def finish(self, **fields):
        raw = dict(option='act:rest', reason='I need to recover before facing anyone.', **fields)
        return self.r.decide_finish(self.a, 12, raw, None)

    def record(self, **fields):
        d, err = self.finish(**fields)
        self.assertIsNone(err)
        return self.r.decisions.current(self.a, d), d

    def test_options_are_checked_stable_requests(self):
        offers = self.r.decisions.offers(self.a, 12)
        ids = [o['id'] for o in offers]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn('act:rest', ids)
        self.assertIn('go:library', ids)
        self.assertIn('talk:' + self.b, ids)
        self.assertEqual(offers, self.r.decisions.offers(self.a, 12))

    def test_menu_honors_murders_reveal_case_and_items(self):
        self.r.murders = False
        self.w.state['revealed'] = False
        ids = {o['id'] for o in self.r.decisions.offers(self.a, 12)}
        self.assertNotIn('act:attack', ids)
        self.assertNotIn('act:experiment', ids)
        self.assertNotIn('use:imaginary', ids)

    def test_blind_actor_gets_no_visual_item_menu(self):
        with patch.object(self.r, 'in_dark', return_value=True):
            offers = self.r.decisions.offers(self.a, 12)
        self.assertFalse(any(o['id'].startswith('take:') for o in offers))
        self.assertIn('talk:' + self.b, {o['id'] for o in offers})

    def test_prepare_is_read_only_apart_from_existing_prompt_telemetry(self):
        # Ahead preparation runs after an ordinary prompt has initialized lazy
        # habit, belief and environment stores for this actor.
        self.r.decide_prepare(self.a, 12)
        before, rng = copy.deepcopy(self.w.dump()), self.r.rng.getstate()
        self.r.decisions.offers(self.a, 12)
        self.r.decisions.prompt(self.a, 12)
        self.assertEqual(self.w.dump(), before)
        self.assertEqual(self.r.rng.getstate(), rng)
        self.r.decide_prepare_dry(self.a, 12)
        self.assertEqual(self.w.dump(), before)
        self.assertEqual(self.r.rng.getstate(), rng)

    def test_option_fills_exact_action_and_destination(self):
        raw = dict(option='go:library', reason='I want a quiet place to think.')
        d, err = self.r.decide_finish(self.a, 12, raw, None)
        self.assertIsNone(err)
        self.assertEqual((d['action'], d['target_room']), ('stay', 'library'))
        self.assertEqual(self.r.decisions.current(self.a, d)['reason'], raw['reason'])

    def test_contradictory_option_is_rejected_without_reusing_reason(self):
        d, err = self.finish(action='attack')
        self.assertIsNone(err)
        self.assertEqual(d['action'], 'stay')
        rec = self.r.decisions.current(self.a, d)
        self.assertEqual(rec['status'], 'rejected')
        self.assertEqual(rec['selected']['action'], 'attack')
        self.assertEqual(rec['fallback']['action'], 'stay')

    def test_unknown_option_has_safe_fallback_without_retry(self):
        d, err = self.r.decide_finish(self.a, 12, dict(option='teleport:moon', reason='I want out.'), None)
        self.assertIsNone(err)
        self.assertEqual(d['action'], 'stay')
        self.assertEqual(self.r.decisions.current(self.a, d)['status'], 'rejected')

    def test_unreachable_destination_and_dead_target_are_rejected(self):
        checked, why = self.r.decisions.resolve(self.a, 12, dict(action='stay', target_room='moon'))
        self.assertIsNone(checked)
        self.assertIn('destination', why)
        checked, why = self.r.decisions.resolve(self.a, 12, dict(action='stay', talk_to=['dead']))
        self.assertIsNone(checked)
        self.assertIn('target', why)

    def test_prefetched_option_is_rechecked_against_current_world(self):
        offers = self.r.decisions.offers(self.a, 12)
        del self.w.state['agents'][self.b]
        d, err = self.r.decide_finish(self.a, 12, dict(option='talk:' + self.b, reason='I want to thank them.'), None, offers)
        self.assertIsNone(err)
        self.assertEqual(self.r.decisions.current(self.a, d)['status'], 'rejected')

    def test_prefetched_item_offer_is_rechecked_after_item_is_gone(self):
        self.w.state['room_items']['lounge']['sweets'] = 1
        offers = self.r.decisions.offers(self.a, 12)
        self.w.state['room_items']['lounge'].pop('sweets')
        checked, why = self.r.decisions.resolve(self.a, 12, dict(option='take:sweets'), offers)
        self.assertIsNone(checked)
        self.assertTrue(why)

    def test_legacy_reply_keeps_action_without_inventing_a_reason(self):
        d, err = self.r.decide_finish(self.a, 12, dict(action='rest', thought='Unrelated thoughts.'), None)
        self.assertIsNone(err)
        rec = self.r.decisions.current(self.a, d)
        self.assertEqual(d['action'], 'rest')
        self.assertEqual(rec['reason'], '')
        self.assertNotIn('Unrelated', self.r.decisions.context(self.a))

    def test_malformed_reason_is_not_coerced_and_long_prose_is_bounded(self):
        d, _ = self.r.decide_finish(self.a, 12, dict(action='rest', reason={'private': 'junk'}), None)
        self.assertEqual(self.r.decisions.current(self.a, d)['reason'], '')
        d, _ = self.r.decide_finish(self.a, 12, dict(action='rest', reason='word ' * 1000), None)
        reason = self.r.decisions.current(self.a, d)['reason']
        self.assertLessEqual(len(reason), 200)
        self.assertLessEqual(len(reason.split()), 25)

    def test_reference_ids_must_belong_to_owner_and_still_be_active(self):
        mine = start(self.w.state, self.a, 'protect', 'protect a friend', 80, target=self.b)
        other = start(self.w.state, self.b, 'protect', 'private protection', 80, target=self.c)
        feeling = emotions.add(self.w.state, self.a, 'fear', 8, 80, 'known danger', 'test', self.b)
        rec, _ = self.record(reason_refs=dict(commitments=[mine['id'], other['id'], 'unknown'], emotions=[feeling['id'], 'fake']))
        self.assertEqual(rec['refs'], dict(commitments=[mine['id']], emotions=[feeling['id']]))

    def test_reason_is_private_in_shared_scenes_and_trial_cards(self):
        rec, d = self.record()
        self.assertIn(rec['reason'], self.r.decisions.context(self.a))
        self.assertNotIn(rec['reason'], self.r.talk_prompt('lounge', [self.a, self.b], {}, 12))
        _, user = voice_prompt(self.r, dict(members=[self.a, self.b], room='lounge'), [])
        self.assertNotIn(rec['reason'], user)
        self.assertEqual(rec['known_by'], [self.a])

    def test_stated_alibi_does_not_create_trial_evidence_or_change_suspicion(self):
        self.r.init_item_log()
        victim = sorted(self.w.agents)[-1]
        self.r.open_case(self.tick, 'murder', victim, culprit=self.c, room='lounge', hour=12, witnesses=[])
        case = self.w.state['case']
        ids = sorted(self.w.agents)
        facts = self.r.trial_facts(case, ids)
        meter = {p: 0 for p in ids}
        scores = self.r.personal_suspicion(self.b, ids, meter, facts, self.c, case)
        raw = dict(option='act:rest', reason='I was in the library and I am innocent.')
        d, err = self.r.decide_finish(self.a, 12, raw, None)
        self.assertIsNone(err)
        self.assertEqual(self.r.trial_facts(case, ids), facts)
        self.assertEqual(self.r.personal_suspicion(self.b, ids, meter, facts, self.c, case), scores)
        self.assertNotIn(raw['reason'], self.r.trial_cards(case))

    def test_diary_memory_cannot_leak_an_unspoken_motive_into_brain_scene(self):
        self.r.tuning_get = lambda: {'brain': 1}
        rec, d = self.record()
        self.r.brain_night(self.a, 'I chose rest because ' + rec['reason'])
        for i in range(3):
            self.r.mem_add(self.a, f'ordinary memory {i}', 'event', 2)
        self.assertNotIn(rec['reason'], self.r.mem_card(self.a, [self.a, self.b]))
        self.assertIn(rec['reason'], self.r.reflect_prompt(self.a)[1])

    def test_explicit_disclosure_is_heard_once_and_only_by_actual_listeners(self):
        rec, d = self.record(say_reason=True)
        self.w.agents[self.c]['room'] = 'library'
        self.r.decisions.applied(self.tick, self.a, d)
        with patch.object(self.r, 'event_witnesses', return_value=[self.b]):
            self.r.decisions.say(self.tick, self.a, d)
            self.r.decisions.say(self.tick, self.a, d)
        self.assertEqual(len([e for e in self.tick['events'] if e['type'] == 'decision']), 1)
        self.assertIn(rec['reason'], self.r.decisions.context(self.a, [self.a, self.b]))
        self.assertEqual(self.r.decisions.context(self.a, [self.a, self.c]), '')

    def test_rejected_or_changed_decision_never_speaks_original_reason(self):
        rec, d = self.record(say_reason=True)
        d.update(action='stay', target_room='library', activity='Getting urgent care')
        self.r.decisions.applied(self.tick, self.a, d)
        self.r.decisions.say(self.tick, self.a, d)
        self.assertFalse(rec.get('said'))
        self.assertEqual(rec['status'], 'changed')
        self.assertIn('urgent care', rec['change'])

    def test_actual_attempt_is_distinct_from_completion(self):
        rec, d = self.record()
        self.r.apply_decision(self.tick, self.a, d, {}, [])
        self.assertEqual(rec['status'], 'attempted')
        self.assertNotIn('completed', self.r.decisions.context(self.a))
        self.assertEqual(rec['selected']['action'], 'rest')

    def test_blocked_movement_is_kept_as_a_blocked_intention(self):
        raw = dict(option='go:library', reason='I want a quiet place to think.')
        d, _ = self.r.decide_finish(self.a, 12, raw, None)
        with patch.object(self.w, 'move', return_value=dict(path=['lounge'], blocked='locked door', arrived=False, events=[])):
            self.r.apply_decision(self.tick, self.a, d, {}, [])
        rec = self.r.decisions.current(self.a, d)
        self.assertEqual(rec['status'], 'blocked')
        self.assertIn('locked door', rec['change'])

    def test_lost_consciousness_is_not_reported_as_follow_through(self):
        rec, d = self.record()
        self.w.agents[self.a]['out'] = dict(cause='fainted')
        self.r.apply_decision(self.tick, self.a, d, {}, [])
        self.assertEqual(rec['status'], 'blocked')

    def test_backend_failure_creates_no_stated_motive(self):
        self.r.decide_finish(self.a, 12, None, LLMError('temporary failure'))
        self.assertFalse(self.w.state['decision_history'].get(self.a))

    def test_save_reload_and_legacy_upgrade(self):
        rec, d = self.record()
        reloaded = World(json.loads(json.dumps(self.w.dump())))
        r = DayRunner(reloaded, LLM('mock'), lambda t: None, seed=404)
        self.assertEqual(r.decisions.view(self.a)[-1], rec)
        old = new_state(3)
        old.pop('decision_history', None)
        old.pop('decision_seq', None)
        legacy = World(old)
        self.assertEqual(legacy.state['decision_history'], {})

    def test_history_is_bounded_and_queries_do_not_mutate(self):
        for i in range(100):
            decisions.remember(self.w.state, self.a, 3, i, dict(action='rest'), 'I need rest.', 'mock')
        self.assertEqual(len(self.w.state['decision_history'][self.a]), decisions.LIMIT)
        before = copy.deepcopy(self.w.dump())
        self.r.decisions.view(self.a)
        self.r.decisions.context(self.a)
        self.assertEqual(self.w.dump(), before)

    def test_dawn_keep_does_not_refresh_a_deadline(self):
        c = start(self.w.state, self.a, 'protect', 'protect a friend', 80, 100, target=self.b)
        reply = dict(commitment_updates=[dict(op='keep', id=c['id'])])
        self.r.decisions.reflect(self.tick, self.a, reply)
        self.r.decisions.reflect(self.tick, self.a, reply)
        self.assertEqual(c['due'], 100)

    def test_dawn_cannot_drop_someone_elses_promise_or_claim_fulfillment(self):
        c = start(self.w.state, self.b, 'protect', 'protect a friend', 80, 100, target=self.c)
        updates = [dict(op='drop', id=c['id'], reason='I learned about a betrayal.'), dict(op='fulfilled', id=c['id'])]
        self.assertEqual(self.r.decisions.reflect(self.tick, self.a, dict(commitment_updates=updates)), [])
        self.assertEqual(c['status'], 'active')

    def test_dawn_abandonment_requires_reason_and_has_existing_cost(self):
        c = start(self.w.state, self.a, 'protect', 'protect a friend', 70, 100, target=self.b)
        self.r.decisions.reflect(self.tick, self.a, dict(commitment_updates=[dict(op='drop', id=c['id'], reason='')]))
        self.assertEqual(c['status'], 'active')
        self.r.decisions.reflect(self.tick, self.a, dict(commitment_updates=[dict(op='drop', id=c['id'], reason='They attacked me after I offered protection.')]))
        self.assertEqual(c['status'], 'abandoned')
        self.assertTrue(c['reason'])

    def test_dawn_request_creates_private_intention_and_is_idempotent(self):
        reply = dict(commitment_updates=[dict(op='request', request=dict(kind='thank', target=self.b, hours=24))])
        self.r.decisions.reflect(self.tick, self.a, reply)
        self.r.decisions.reflect(self.tick, self.a, reply)
        records = self.r.commitments.active(self.a)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['known_by'], [self.a])
        self.assertEqual(records[0]['not_before'], 104)

    def test_actual_dawn_applies_model_commitment_update(self):
        def reply(system, user, ctx):
            return dict(diary='Tomorrow I will thank them.', drive='keep', commitment_updates=[
                dict(op='request', request=dict(kind='thank', target=self.b, hours=24))] if ctx['cid'] == self.a else [])
        with patch.object(self.r.llm, 'reflect', side_effect=reply):
            self.r.run_dawn()
        self.assertTrue(any(c.get('target') == self.b and c.get('action') == 'thank' for c in self.r.commitments.active(self.a)))

    def test_dawn_does_not_fabricate_a_spoken_promise(self):
        reply = dict(commitment_updates=[dict(op='request', request=dict(kind='promise', target=self.b, hours=24))])
        self.assertEqual(self.r.decisions.reflect(self.tick, self.a, reply), [])

    def test_pending_diary_invalidates_only_when_owners_context_changes(self):
        before = self.r.diary_sig(self.a)
        self.r.decide_finish(self.b, 12, dict(action='rest', reason='I need a break.'), None)
        self.assertEqual(before, self.r.diary_sig(self.a))
        self.record()
        self.assertNotEqual(before, self.r.diary_sig(self.a))

    def test_mock_and_model_protocol_match_and_diary_recalls_reason(self):
        _, (_, prompt, ctx) = self.r.decide_prepare(self.a, 12)
        self.assertIn('CHECKED REQUESTS', prompt)
        raw = self.r.llm.decide('', prompt, ctx)
        self.assertTrue(raw['option'])
        self.assertTrue(raw['reason'])
        d, err = self.r.decide_finish(self.a, 12, raw, None, ctx['options'])
        self.assertIsNone(err)
        self.assertNotEqual(self.r.decisions.current(self.a, d)['status'], 'rejected')
        sysm, user, reflection = self.r.reflect_prompt(self.a)
        self.assertIn(raw['reason'][:80], user)
        diary = self.r.llm.reflect(sysm, user, reflection)['diary']
        self.assertIn(raw['reason'][:80], diary)

    def test_snapshot_exposes_diagnostic_records(self):
        rec, _ = self.record()
        self.w.agents[self.a]['decisions_view'] = self.r.decisions.view(self.a)
        self.assertEqual(self.w.snapshot()['agents'][self.a]['decisions'][0]['id'], rec['id'])

    def test_reactions_retain_a_private_reason_without_adding_a_call(self):
        reply = dict(reaction='comfort', target=self.b, line='Breathe.', reason='I want to steady my friend.')
        with patch.object(self.r.llm, 'react', return_value=reply) as call:
            self.r.react_one(self.tick, self.a, 'lounge', [(self.c, 'a shock')], [], 12)
        self.assertEqual(call.call_count, 1)
        rec = self.r.decisions.view(self.a)[-1]
        self.assertEqual(rec['kind'], 'reaction')
        self.assertEqual(rec['reason'], reply['reason'])
        self.assertEqual(rec['known_by'], [self.a])

    def test_proposal_reason_is_an_intention_not_a_performed_move(self):
        reply = dict(move='comfort', to=self.b, reason='I want to reassure my friend.')
        with patch.object(self.r.llm, 'propose', return_value=reply):
            self.assertTrue(self.r.propose_move(self.tick, self.a))
        rec = self.r.decisions.view(self.a)[-1]
        self.assertEqual(rec['status'], 'proposal accepted')
        self.assertEqual(rec['selected']['action'], 'propose_comfort')

    def test_identity_change_preserves_motives_and_audience(self):
        rec = decisions.remember(self.w.state, 'neovi', 3, 12, dict(action='stay', talk_to=[self.a]), 'I want company.', 'mock')
        other = decisions.remember(self.w.state, self.a, 3, 12, dict(action='give', to='neovi'), 'I want to help.', 'mock')
        decisions.rename_person(self.w.state, 'neovi', 'kumiko')
        self.assertEqual(rec['owner'], 'kumiko')
        self.assertEqual(rec['known_by'], ['kumiko'])
        self.assertEqual(other['selected']['to'], 'kumiko')


if __name__ == '__main__':
    unittest.main(verbosity=2)
