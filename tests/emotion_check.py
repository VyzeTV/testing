"""I3: known causes, persistence, privacy, measured decay and behavioral follow-through."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('MC_DATA_DIR', tempfile.mkdtemp(prefix='mc_emotions_'))
from murder import emotions as em
from murder.engine import DayRunner
from murder.world import World, new_state
from murder.llm import LLM
from murder.voice import voice_prompt


class EmotionChecks(unittest.TestCase):
    def setUp(self):
        self.w = World(new_state(3))
        self.w.state['bonds'] = []
        self.r = DayRunner(self.w, LLM('mock'), lambda t: None, seed=45, rule_mode='none')
        self.a, self.b, self.c = sorted(self.w.agents)[:3]
        for agent in self.w.agents.values():
            agent.update(room='lounge', hp=100, sanity=80)
            agent['aff'] = {p:0 for p in self.w.agents}
        self.at(3, 12)

    def at(self, day, hour):
        self.r.day = self.w.state['day'] = day
        self.w.state['_hour'] = hour
        self.tick = self.r.new_tick(hour)
        return self.tick

    def put(self, kind='grief', who=None, **fields):
        return self.r.emotions.put(who or self.a, kind, 8, 'a checked event', 'test', self.tick, **fields)

    def test_feelings_last_days_and_use_absolute_time(self):
        e=self.put()
        self.assertGreater(em.strength(e,86),7)
        self.assertEqual(em.strength(e,156),4)
        self.assertEqual(em.strength(e,e['expires']),0)
        self.assertEqual(em.strength(e,83),0)

    def test_queries_are_read_only_and_consistent(self):
        self.put(target=self.b)
        before=copy.deepcopy(self.w.dump())
        for _ in range(3):
            self.r.emotions.context(self.a)
            self.r.emotions.view(self.a)
            self.r.emotions.level(self.a,'grief')
        self.assertEqual(self.w.dump(),before)

    def test_duplicate_event_survives_json_reload_without_resetting_duration(self):
        e=self.put(target=self.b)
        state=json.loads(json.dumps(self.w.dump()))
        old=copy.deepcopy(state['emotions'])
        self.assertIsNone(em.add(state,self.a,'grief',8,100,'a checked event','test',self.b))
        self.assertEqual(state['emotions'],old)
        self.assertEqual(e['expires'],420)

    def test_new_public_knowledge_can_expand_a_private_emotion_without_refreshing_it(self):
        e=self.put(target=self.b)
        self.assertEqual(e['known_by'],[self.a])
        self.assertIsNone(em.add(self.w.state,self.a,'grief',8,100,'a checked event','test',self.b,known_by=[self.a,self.c]))
        self.assertEqual(e['updated'],84)
        self.assertIn(self.c,e['known_by'])

    def test_comfort_can_help_once_per_day_without_erasing_grief_in_one_conversation(self):
        e=self.put()
        before=e['expires']
        for _ in range(20): self.r.emotions.social(self.tick,self.b,self.a,'comfort','ok')
        self.assertGreater(self.r.emotions.level(self.a,'grief'),7)
        self.assertEqual(e['expires'],before)
        self.assertGreater(self.r.emotions.level(self.a,'relief'),0)

    def test_hidden_death_does_not_create_grief_or_inner_knowledge(self):
        self.w.agents[self.a]['aff'][self.b]=8
        self.w.end_agent(self.b,'dead')
        self.assertEqual(self.r.emotions.level(self.a,'grief'),0)
        self.assertNotEqual(self.r.inner_topic(self.a)[0],'grief')

    def test_loss_is_appraised_only_for_people_informed_and_depends_on_relationship(self):
        self.w.agents[self.a]['aff'][self.b]=8
        self.r.emotions.loss(self.tick,self.b,'library',[self.a,self.c])
        self.assertGreater(self.r.emotions.level(self.a,'grief',self.b),6)
        self.assertEqual(self.r.emotions.level(self.c,'grief'),0)
        self.assertGreater(self.r.emotions.level(self.c,'fear'),0)
        unknown=next(p for p in self.w.agents if p not in (self.a,self.b,self.c))
        self.assertEqual(self.r.emotions.view(unknown),[])
        self.assertEqual(self.r.emotions.level(self.a,'anger'),0)

    def test_aware_killer_has_private_guilt_without_publicly_identifying_them(self):
        case={'killer':self.a,'victim':self.b,'room':'library','culprit_aware':True}
        self.r.emotions.guilt(self.tick,case)
        self.assertGreater(self.r.emotions.level(self.a,'guilt'),0)
        self.assertIn(self.r.nm(self.b),self.r.emotions.context(self.a))
        self.assertEqual(self.r.emotions.context(self.a,[self.a,self.c]),'')
        self.assertEqual(self.r.emotions.view(self.c),[])

    def test_unaware_killer_does_not_feel_guilt_until_realization(self):
        case={'killer':self.a,'victim':self.b,'room':'library','culprit_aware':False}
        self.w.state['case']=case
        self.r.emotions.guilt(self.tick,case)
        self.assertEqual(self.r.emotions.level(self.a,'guilt'),0)
        self.r.realize(self.tick,self.a,12)
        self.assertGreater(self.r.emotions.level(self.a,'guilt'),0)

    def test_private_poisoning_does_not_tell_the_victim_who_poisoned_them(self):
        e={'type':'attack','who':self.a,'target':self.b,'room':'lounge','vis':'gm','text':'a secret poisoning'}
        self.r.log_event(self.tick,e,actor=self.a)
        self.assertFalse(self.r.emotions.view(self.b))

    def test_visible_attack_creates_targeted_fear_and_is_appraised_once(self):
        e={'type':'attack','who':self.a,'target':self.b,'room':'lounge','vis':'public','text':'a checked assault'}
        with patch.object(self.r,'in_dark',return_value=False), patch.object(self.r,'perceived_identity',return_value=self.a):
            self.r.emotions.event(self.tick,e,[self.b],self.a)
            before=copy.deepcopy(self.w.state['emotions'])
            self.r.emotions.event(self.tick,e,[self.b],self.a)
        self.assertEqual(self.w.state['emotions'],before)
        self.assertGreater(self.r.emotions.level(self.b,'fear',self.a),6)

    def test_blind_or_dark_witness_does_not_learn_attacker_identity_from_emotion(self):
        e={'type':'attack','target':self.b,'room':'lounge','vis':'public'}
        with patch.object(self.r,'blind',return_value=True):
            self.r.emotions.event(self.tick,e,[],self.a)
        fear=self.r.emotions.view(self.b)[0]
        self.assertIsNone(fear['target'])
        self.assertNotIn(self.r.nm(self.a),fear['cause'])

    def test_public_voice_cards_do_not_include_a_private_betrayal(self):
        self.r.emotions.betrayed(self.tick,self.b,self.a,'exposed a private secret',True)
        self.assertIn('secret',self.r.emotions.context(self.a))
        self.assertEqual(self.r.emotions.context(self.a,[self.a,self.c]),'')
        conv={'members':[self.a,self.c], 'room':'lounge', 'hour':12, 'beats':[], 'id':'test', 'kind':'chat', 'why':'talking'}
        _,prompt=voice_prompt(self.r,conv,[])
        self.assertNotIn('exposed a private secret',prompt)

    def test_diary_and_inner_voice_use_the_same_persistent_feeling(self):
        e=self.put(target=self.b)
        self.at(6,12)
        self.assertIn('grief',self.r.reflect_prompt(self.a)[1])
        topic,feeling=self.r.inner_topic(self.a)
        self.assertEqual(topic,'emotion')
        self.assertEqual(feeling['id'],e['id'])
        self.assertIn('miss',self.r.inner_text(self.a,topic,feeling))

    def test_reminder_temporarily_reactivates_feeling_without_extending_its_life(self):
        self.r.emotions.remind(self.tick,self.a,'lounge')
        e=self.put(target=self.b,room='library')
        due=e['expires']
        self.at(4,12)
        before=em.strength(e,108)
        self.r.emotions.remind(self.tick,self.a,'library')
        self.assertGreater(em.strength(e,108),before)
        self.assertEqual(e['expires'],due)
        count=len(self.tick['events'])
        self.r.emotions.remind(self.tick,self.a,'lounge')
        self.r.emotions.remind(self.tick,self.a,'library')
        self.assertEqual(len(self.tick['events']),count)
        self.assertLess(em.strength(e,112),before)

    def test_hidden_person_is_not_a_reminder_of_their_location(self):
        e=self.put('fear',target=self.b)
        self.w.agents[self.b]['hiding']=True
        self.r.emotions.remind(self.tick,self.a,'library')
        self.r.emotions.remind(self.tick,self.a,'lounge')
        self.assertNotIn('reminded_until',e)

    def test_company_seeking_and_known_scene_avoidance_have_real_scores(self):
        self.put(room='library')
        self.assertGreater(self.r.emotions.score(self.a,'chat','lounge'),0)
        self.assertLess(self.r.emotions.score(self.a,'read','library'),0)
        self.assertEqual(self.r.emotions.score(self.a,'rescue','library'),0)
        self.assertEqual(self.r.emotions.score(self.a,'eat','library'),0)

    def test_emotion_does_not_locate_an_unseen_person_elsewhere_in_the_house(self):
        self.put('fear',target=self.b,room='library')
        self.w.agents[self.b]['room']='garden'
        self.assertEqual(self.r.emotions.score(self.a,'read','garden'),0)

    def test_loneliness_does_not_send_someone_into_a_friends_bathroom_or_bedroom(self):
        self.put('loneliness')
        self.w.agents[self.a]['aff'][self.b]=8
        for room in ('bathroom', self.w.cast[self.b]['home']):
            self.w.agents[self.b]['room']=room
            options=[]
            self.r.emotions.options(self.tick,self.a,lambda *a,**k:options.append(a))
            self.assertEqual(options,[])

    def test_fear_affects_willingness_to_receive_an_advance_from_the_threat(self):
        before=self.r.receptivity(self.a,self.b)
        self.put('fear',target=self.b)
        self.assertLess(self.r.receptivity(self.a,self.b),before)

    def test_injury_and_unconsciousness_take_priority_over_emotional_company_seeking(self):
        self.put()
        self.w.agents[self.a]['hp']=20
        options=[]
        self.r.emotions.options(self.tick,self.a,lambda *a,**k:options.append(a))
        self.assertEqual(options,[])
        self.assertEqual(self.r.emotions.score(self.a,'rest','library'),0)

    def test_fear_can_motivate_securing_an_empty_bedroom(self):
        home=self.w.cast[self.a]['home']
        self.w.agents[self.a]['room']=home
        self.r.mind(self.a)['needs']={k:100 for k in self.r.mind(self.a)['needs']}
        self.put('fear',target=self.b)
        self.assertEqual(self.r.routine_decision(self.a,12)['action'],'lock')

    def test_bold_vengeful_person_can_plan_against_a_known_threat(self):
        self.w.state['revealed']=True
        self.r.mind(self.a)['facets'].update(vengefulness=90,courage=90)
        self.put('fear',target=self.b)
        self.assertTrue(any(x[1]==self.b and x[3]=='fear' for x in self.r.plot_motives(self.a)))

    def test_anger_biases_confrontation_and_attraction_biases_existing_flirt_options(self):
        self.put('anger',target=self.b)
        options=self.r.emotions.move_options(self.a,self.b,[(1,'chat',None)])
        self.assertIn('confront',[m for _,m,_ in options])
        self.put('attraction',target=self.b)
        options=self.r.emotions.move_options(self.a,self.b,[(1,'flirt',None)])
        self.assertGreater(options[0][0],1)

    def test_shame_follows_declined_advance_but_no_attraction_or_romance_is_invented(self):
        self.r.mind(self.a)['facets']['vanity']=80
        self.r.emotions.social(self.tick,self.a,self.b,'flirt','fail')
        self.assertGreater(self.r.emotions.level(self.a,'shame'),0)
        self.assertEqual(self.r.emotions.level(self.b,'attraction'),0)
        self.assertFalse(self.w.state['bonds'])

    def test_guilt_encourages_confessional_without_fabricating_a_confession(self):
        self.put('guilt')
        options=[]
        self.r.emotions.options(self.tick,self.a,lambda weight,act,**fields:options.append(act))
        self.assertIn('confess',options)
        self.assertEqual(self.w.state.get('case'),None)
        self.assertGreater(self.r.booth_urge(self.a)[0],0)

    def test_trial_emotion_bias_needs_existing_support_and_is_bounded(self):
        self.put('anger',target=self.b)
        self.assertEqual(self.r.emotions.trial_bias(self.a,self.b,False),0)
        self.assertGreater(self.r.emotions.trial_bias(self.a,self.b,True),0)
        self.assertLessEqual(self.r.emotions.trial_bias(self.a,self.b,True),.6)

    def test_trial_report_matches_emotion_bias_when_positive_and_negative_evidence_cancel(self):
        self.put('anger',target=self.b)
        facts=[{'about':self.b,'w':3,'text':'a supporting clue'}, {'about':self.b,'w':-3,'text':'a clearing clue'}]
        support=[{'weight':f['w'],'text':f['text']} for f in facts]
        with patch.object(self.r,'trial_private_facts',side_effect=lambda voter,_:facts if voter==self.a else []), patch.object(self.r,'trial_vote_support',return_value=support), patch.object(self.r.rng,'random',return_value=1):
            votes=self.r.compute_votes([self.a,self.b,self.c],{self.a:0,self.b:0,self.c:0},[],None,{})
        vote=next(v for v in votes if v['voter']==self.a)
        self.assertEqual(vote['target'],self.b)
        self.assertEqual(vote['reasoning']['private_score'],0)
        self.assertEqual(vote['reasoning']['emotion_bias'],.28)

    def test_grieving_witness_is_more_willing_to_offer_real_evidence(self):
        self.w.state['case']={'victim':self.b,'killer':None}
        baseline=self.r.willingness(self.a,self.c,.3)
        self.put(target=self.b)
        self.assertGreater(self.r.willingness(self.a,self.c,.3),baseline)

    def test_loneliness_requires_a_long_awake_isolation_and_sleep_resets_that_clock(self):
        for who in self.w.agents:
            self.w.agents[who]['room']=self.w.cast[who]['home']
        self.at(3,8); self.r.emotions.sync(self.tick)
        self.at(3,20); self.r.emotions.sync(self.tick)
        self.assertGreater(self.r.emotions.level(self.a,'loneliness'),0)
        self.w.agents[self.a]['asleep']=True
        self.at(3,22); self.r.emotions.sync(self.tick)
        self.w.agents[self.a]['asleep']=False
        self.at(4,8); self.r.emotions.sync(self.tick)
        self.assertEqual(self.w.state['emotion_company'][self.a]['since'],104)

    def test_save_load_does_not_reset_decay_or_refresh_an_old_loss(self):
        self.w.agents[self.a]['aff'][self.b]=8
        self.w.agents[self.a]['memory']['lost']=[{'id':self.b,'name':self.r.nm(self.b),'day':3,'how':'died'}]
        self.r.emotions.loss(self.tick,self.b,'library',[self.a])
        self.at(5,12)
        value=self.r.emotions.level(self.a,'grief')
        w=World(json.loads(json.dumps(self.w.dump())))
        r=DayRunner(w,LLM('mock'),lambda t:None,seed=1)
        self.assertAlmostEqual(r.emotions.level(self.a,'grief'),value)
        self.assertEqual(r.emotions.view(self.a)[0]['updated'],84)

    def test_old_save_imports_only_the_owners_known_losses_once(self):
        state=new_state(5)
        state['agents'][self.a]['aff'][self.b]=8
        state['agents'][self.a]['memory']['lost']=[{'id':self.b,'name':'a friend','day':3,'how':'died'}]
        w=World(state)
        r=DayRunner(w,LLM('mock'),lambda t:None,seed=1)
        self.assertGreater(r.emotions.level(self.a,'grief'),0)
        before=copy.deepcopy(w.state['emotions'])
        DayRunner(w,LLM('mock'),lambda t:None,seed=2)
        self.assertEqual(w.state['emotions'],before)

    def test_store_stays_bounded_and_history_queries_do_not_refresh_expired_feelings(self):
        for n in range(2200): em.add(self.w.state,self.a,'anger',1,84,'different event',str(n),target=str(n))
        self.assertLessEqual(len(self.w.state['emotions'][self.a]),16)
        self.assertLessEqual(len(self.w.state['emotion_sources']),2048)
        self.assertEqual(em.active(self.w.state,self.a,1000),[])

    def test_gm_snapshot_exposes_named_strength_and_cause(self):
        self.put()
        self.w.agents[self.a]['emotions_view']=self.r.emotions.view(self.a)
        snapshot=self.w.snapshot()['agents'][self.a]['emotions']
        self.assertEqual(snapshot[0]['kind'],'grief')
        self.assertEqual(snapshot[0]['intensity'],8)

    def test_a_new_shock_invalidates_only_its_owners_early_decision(self):
        before=self.r.ahead_sig(self.a)
        other=self.r.ahead_sig(self.b)
        self.put('fear')
        after=self.r.ahead_sig(self.a)
        self.assertNotEqual(before,after)
        self.assertEqual(other,self.r.ahead_sig(self.b))
        self.at(3,14)
        self.assertEqual(after,self.r.ahead_sig(self.a))

    def test_paired_death_report_does_not_tag_a_deceased_person_as_an_active_actor(self):
        from murder.storylint import StoryLinter
        lint=StoryLinter(self.w.dump())
        self.r.two_deaths(self.tick,self.a,self.b,'a tragic paired death','died together','Both people are dead.')
        event=next(e for e in self.tick['events'] if e.get('story_kind')=='death_report')
        self.assertNotIn('actor',event)
        self.assertEqual(event['deceased'],[self.a,self.b])
        self.tick['state']=self.w.snapshot()
        lint.feed(self.tick)
        self.assertEqual(lint.issues,[])

if __name__=='__main__': unittest.main(verbosity=2)
