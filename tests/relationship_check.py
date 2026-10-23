"""I4: shared history, asymmetric trust, lasting betrayal and honest relationship state."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('MC_DATA_DIR', tempfile.mkdtemp(prefix='mc_relationships_'))
from murder.engine import DayRunner
from murder.llm import LLM
from murder.world import World, new_state
from murder import relationships as rel
from murder.storylint import StoryLinter


class RelationshipChecks(unittest.TestCase):
    def setUp(self):
        self.w = World(new_state(3))
        self.w.state['bonds'] = []
        self.w.state['relationships'] = {}
        self.r = DayRunner(self.w, LLM('mock'), lambda t: None, seed=17, confessionals=False)
        self.a, self.b, self.c, self.d = sorted(self.w.agents)[:4]
        for a in self.w.agents.values():
            a.update(room='lounge', sanity=80, hp=100)
            a['aff'] = {p:8 for p in self.w.agents}
        self.at(3, 12)

    def at(self, day, hour):
        self.r.day = self.w.state['day'] = day
        self.w.state['_hour'] = hour
        self.tick = self.r.new_tick(hour)
        return self.tick

    def warm(self, a=None, b=None, days=(1,2,3)):
        for day in days:
            rel.closeness(self.w.state, a or self.a, b or self.b, day*24+10, 'a welcomed conversation')

    def form(self, a=None, b=None):
        a, b = a or self.a, b or self.b
        self.r.apply_bonds(self.tick, [{'a':a, 'b':b, 'kind':'romance'}], [a,b])

    def test_affection_alone_cannot_form_romance(self):
        self.form()
        self.assertEqual(self.w.state['bonds'], [])

    def test_spamming_warmth_in_one_day_cannot_accelerate_trust_or_romance(self):
        for hour in range(24):
            rel.closeness(self.w.state,self.a,self.b,72+hour,'flirt')
        self.assertEqual(rel.trust(self.w.state,self.a,self.b),1)
        self.form()
        self.assertFalse(self.w.state['bonds'])

    def test_three_days_require_elapsed_time_as_well_as_dates(self):
        for time in (47.9,48.1,72.1):
            rel.closeness(self.w.state,self.a,self.b,time,'chat')
        self.assertFalse(rel.romance_ready(self.w.state,self.a,self.b,73))

    def test_sustained_mutual_history_forms_once(self):
        self.warm(); self.form(); self.form()
        self.assertEqual(len(self.w.state['bonds']),1)
        self.assertEqual(sum('now in a romance' in e['text'] for e in self.tick['events']),1)

    def test_old_shared_history_goes_stale(self):
        self.warm(); self.at(15,12); self.form()
        self.assertFalse(self.w.state['bonds'])

    def test_one_sided_trust_or_affection_is_insufficient(self):
        self.warm()
        rel.distrust(self.w.state,self.b,self.a,5)
        self.form(); self.assertFalse(self.w.state['bonds'])
        self.assertEqual(rel.trust(self.w.state,self.a,self.b),3)
        self.assertEqual(rel.trust(self.w.state,self.b,self.a),-2)

    def test_unrelated_affinity_bonus_does_not_create_shared_history(self):
        self.w.adjust_aff(self.a,self.b,10)
        self.assertEqual(rel.trust(self.w.state,self.a,self.b),0)
        self.assertFalse(rel.connection(self.w.state,self.a,self.b))

    def test_reflection_repairs_trust_slowly_without_inventing_encounters(self):
        rel.betray(self.w.state,self.a,self.b,60,'betrayal')
        self.w.agents[self.a]['distrust']={self.b:2}
        for _ in range(3):
            self.r.apply_choices(self.a,self.tick,[{'kind':'trust','about':self.b,'dir':'up'}])
        self.assertEqual(rel.trust(self.w.state,self.a,self.b),-7.75)
        self.assertIn(self.b,self.w.agents[self.a]['distrust'])
        self.assertFalse(rel.connection(self.w.state,self.a,self.b)['close'])

    def test_betrayal_invalidates_only_the_victims_prefetched_decision(self):
        victim=self.r.ahead_sig(self.b)
        bystander=self.r.ahead_sig(self.c)
        rel.betray(self.w.state,self.b,self.a,84,'betrayal')
        self.assertNotEqual(self.r.ahead_sig(self.b),victim)
        self.assertEqual(self.r.ahead_sig(self.c),bystander)

    def test_lost_affection_breaks_trust_immediately(self):
        self.warm(); self.w.adjust_aff(self.a,self.b,-6)
        self.assertEqual(rel.trust(self.w.state,self.a,self.b),-3)
        self.assertEqual(rel.trust(self.w.state,self.b,self.a),3)

    def test_actual_welcomed_social_move_adds_closeness_rejection_does_not(self):
        conv={'members':[self.a,self.b], 'room':'lounge', 'hour':12, 'beats':[], 'used':{}}
        with patch.object(self.r.rng,'random',return_value=0):
            self.r.resolve_move(self.tick,conv,self.a,self.b,'chat')
        self.assertEqual(rel.trust(self.w.state,self.a,self.b),1)
        self.at(4,12)
        with patch.object(self.r.rng,'random',return_value=.999):
            self.r.resolve_move(self.tick,conv,self.a,self.b,'flirt')
        self.assertEqual(len(rel.connection(self.w.state,self.a,self.b)['close']),1)

    def test_staged_mutual_warmth_counts_only_present_people(self):
        fx={'affinity':[{'from':self.a,'to':self.b,'delta':1},{'from':self.b,'to':self.a,'delta':1}],
            'special':[{'kind':'comfort','who':[self.a,self.c]}]}
        self.r.apply_talk_fx(self.tick,'lounge',[self.a,self.b],fx,12)
        self.assertEqual(rel.trust(self.w.state,self.a,self.b),1)
        self.assertFalse(rel.connection(self.w.state,self.a,self.c))

    def test_current_partner_prevents_a_second_unacknowledged_romance(self):
        self.warm(); self.warm(self.a,self.c); self.form()
        self.at(5,12); self.form(self.a,self.c)
        self.assertEqual(len(self.w.state['bonds']),1)

    def test_first_night_obeys_history_gate(self):
        self.w.state['revealed']=True
        with patch.object(self.r,'drawn_pairs',return_value=[(self.a,self.b)]), patch.object(self.r.rng,'random',return_value=0):
            self.assertEqual(self.r.intimacy_night(self.tick),[])
        self.assertFalse(self.w.state.get('nights'))

    def test_betrayal_survives_save_and_weeks_of_polite_words(self):
        self.warm(); self.form()
        self.r.betrayal(self.tick,self.a,self.b,'exposed a private confidence')
        w=World(json.loads(json.dumps(self.w.dump())))
        for day in range(4,18):
            for _ in range(4): rel.closeness(w.state,self.a,self.b,day*24+12,'apology')
        self.assertTrue(rel.wary(w.state,self.b,self.a,17*24+12))
        self.assertLess(rel.trust(w.state,self.b,self.a),2)
        self.assertFalse(rel.bond_allowed(w.state,self.a,self.b,'pact',17*24+12))
        self.assertFalse(rel.bond_allowed(w.state,self.a,self.b,'romance',17*24+12))

    def test_betrayal_changes_receptivity_and_confiding_after_old_ties_are_gone(self):
        before=self.r.receptivity(self.b,self.a)
        rel.betray(self.w.state,self.b,self.a,84,'a private betrayal')
        self.at(17,12)
        self.w.state['ties']=[]
        self.assertLess(self.r.receptivity(self.b,self.a),before)
        conv={'members':[self.a,self.b], 'used':{}, 'beats':[]}
        self.assertNotIn('confide',[o[1] for o in self.r.move_options(conv,self.b,self.a)])
        self.assertFalse(self.r.close_pair(self.a,self.b))

    def test_trust_can_recover_after_sustained_repair(self):
        rel.betray(self.w.state,self.b,self.a,84,'betrayal')
        for day in range(4,42): self.warm(days=(day,))
        self.assertFalse(rel.wary(self.w.state,self.b,self.a,42*24))
        self.assertTrue(rel.romance_ready(self.w.state,self.a,self.b,42*24))

    def test_betrayal_cannot_reset_the_daily_trust_gain_budget(self):
        self.warm()
        rel.betray(self.w.state,self.b,self.a,84,'betrayal')
        before=rel.trust(self.w.state,self.b,self.a)
        rel.closeness(self.w.state,self.a,self.b,85,'an apology')
        self.assertEqual(rel.trust(self.w.state,self.b,self.a),before)

    def test_private_reason_stays_out_of_shared_voice_context(self):
        rel.betray(self.w.state,self.a,self.b,84,'a secret hidden in the vault')
        private=rel.context(self.w.state,self.a,90,self.r.nm)
        shared=rel.context(self.w.state,self.a,90,self.r.nm,[self.a,self.b])
        self.assertIn('secret hidden',private)
        self.assertNotIn('secret hidden',shared)
        self.assertIn('guarded',shared)
        self.assertEqual(rel.context(self.w.state,self.a,90,self.r.nm,[self.a,self.c]),'')

    def test_repeated_affair_disclosure_has_one_cost(self):
        self.warm(); self.form()
        self.r.affair_found(self.tick,self.b,self.a,self.c)
        state=copy.deepcopy(self.w.dump())
        self.r.affair_found(self.tick,self.b,self.a,self.c)
        self.assertEqual(self.w.dump(),state)
        self.assertTrue(rel.wary(self.w.state,self.b,self.a,84))

    def test_affair_records_both_betrayed_partners_and_discovery_is_not_automatic(self):
        self.warm(); self.warm(self.c,self.d); self.form(); self.form(self.c,self.d)
        self.r.night_together(self.tick,self.a,self.c,affair=self.b)
        n=self.w.state['nights'][-1]
        self.assertEqual({b['partner'] for b in n['betrayals']},{self.b,self.d})
        self.assertFalse(rel.wary(self.w.state,self.b,self.a,84))
        with patch.object(self.r.rng,'random',return_value=0): self.r.intimacy_dawn(self.tick)
        self.assertTrue(rel.wary(self.w.state,self.b,self.a,84))
        self.assertTrue(rel.wary(self.w.state,self.d,self.c,84))
        self.assertFalse(self.w.state['bonds'])

    def test_old_bonds_survive_upgrade_without_inventing_dating_history(self):
        state=new_state(3)
        state.pop('relationships',None)
        state['bonds']=[{'a':self.a,'b':self.b,'kind':'romance','since':1}]
        w=World(state)
        self.assertEqual(len(w.state['bonds']),1)
        self.assertFalse(rel.connection(w.state,self.a,self.b))
        self.assertEqual(rel.partners(w.state,self.a),{self.b})

    def test_neovi_uses_shared_history_and_existing_partner_rules(self):
        self.warm('neovi',self.a)
        self.assertTrue(rel.bond_allowed(self.w.state,'neovi',self.a,'romance',84))
        self.w.state['npcs']['neovi']['lover']=self.a
        self.warm(self.a,self.b)
        self.assertFalse(rel.bond_allowed(self.w.state,self.a,self.b,'romance',120))
        self.assertEqual(self.r.partner_of(self.a),'neovi')

    def test_neovi_can_discover_a_lovers_affair_once(self):
        self.w.state['npcs']['neovi']['lover']=self.a
        self.r.affair_found(self.tick,'neovi',self.a,self.b)
        self.assertIsNone(self.w.state['npcs']['neovi']['lover'])
        self.assertTrue(rel.wary(self.w.state,'neovi',self.a,84))
        state=copy.deepcopy(self.w.dump())
        self.r.affair_found(self.tick,'neovi',self.a,self.b)
        self.assertEqual(self.w.dump(),state)

    def test_becoming_a_participant_preserves_identity_trust_and_romance_age(self):
        self.warm('neovi',self.a)
        nv=self.w.state['npcs']['neovi']
        nv['lover']=self.a
        nv['aff'][self.a]=9
        self.w.agents[self.a]['nv_aff']=9
        rel.record_bond(self.w.state,{'a':'neovi','b':self.a,'kind':'romance'},60,'formed','shared history')
        rel.betray(self.w.state,'neovi',self.b,70,'a private betrayal')
        self.r.make_participant(self.tick)
        from murder.kumiko import KUMIKO_ID
        self.assertEqual(rel.partners(self.w.state,self.a),{KUMIKO_ID})
        self.assertEqual(rel.trust(self.w.state,self.a,KUMIKO_ID),3)
        self.assertTrue(rel.wary(self.w.state,KUMIKO_ID,self.b,84))
        self.assertEqual(self.w.state['bonds'][0]['formed_at'],60)
        self.assertNotIn('neovi',self.w.state['relationships'])
        self.assertIsNone(nv['lover'])

    def test_checker_catches_repeat_romance_but_allows_breakup_and_reconciliation(self):
        checker=StoryLinter(self.w.dump())
        bond={'a':self.a,'b':self.b,'kind':'romance'}
        rel.record_bond(self.w.state,bond,84,'formed','mutual history')
        self.tick['state']=self.w.snapshot(); checker.feed(self.tick)
        rel.record_bond(self.w.state,bond,85,'formed','duplicate announcement')
        self.tick['state']=self.w.snapshot(); checker.feed(self.tick)
        self.assertIn('duplicate_romance',[i['code'] for i in checker.issues])
        checker=StoryLinter(self.w.dump())
        rel.record_bond(self.w.state,bond,86,'ended','feelings cooled')
        rel.record_bond(self.w.state,bond,160,'formed','reconciled')
        self.tick['state']=self.w.snapshot(); checker.feed(self.tick)
        self.assertFalse(checker.issues)

if __name__=='__main__': unittest.main(verbosity=2)
