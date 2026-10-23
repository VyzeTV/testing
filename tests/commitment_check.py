"""I2: persistence, checked follow-through, privacy and reasons for changing course."""
import copy
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("MC_DATA_DIR", tempfile.mkdtemp(prefix="mc_commitments_"))
from murder.commitments import active, start, end, clean_request
from murder.engine import DayRunner
from murder.llm import LLM
from murder.world import World, new_state
from murder.voice import voice_prompt, template_line


class CommitmentChecks(unittest.TestCase):
    def setUp(self):
        state = new_state(3)
        state["bonds"] = []
        self.w = World(state)
        self.r = DayRunner(self.w, LLM("mock"), lambda t: None, seed=45, rule_mode="none", confessionals=False)
        self.a, self.b, self.c = sorted(self.w.agents)[:3]
        for agent in self.w.agents.values():
            agent.update(room="lounge", sanity=80, hp=100)
            agent["aff"] = {cid: 0 for cid in self.w.agents if self.w.agents[cid] is not agent}
        self.at(12)

    def at(self, hour, day=3):
        self.r.day = self.w.state["day"] = day
        self.w.state["_hour"] = hour
        self.tick = self.r.new_tick(hour)
        return self.tick

    def request(self, kind="protect", **fields):
        return self.r.commitments.request(self.tick, self.a, dict(kind=kind, target=self.b, hours=24, **fields))

    def conv(self):
        return {"members": [self.a, self.b], "initiator": self.a, "room": "lounge", "hour": 12,
                "used": {}, "beats": [], "opens": {}, "why": "a conversation"}

    def test_request_validation_leaves_no_obligation_on_bad_input(self):
        for raw in (None, [], {"kind": "kill"}, {"kind": "protect", "hours": "nan"}, {"kind": "protect", "hours": {} }):
            self.assertIsNone(clean_request(raw))
        self.assertIsNone(self.r.commitments.request(self.tick, self.a, {"kind": "protect", "target": "absent"}))
        self.assertIsNone(self.request("promise", action="give", item="nonexistent"))
        self.assertFalse(self.r.commitments.active(self.a))

    def test_repeating_a_vow_does_not_reset_its_deadline_or_announce_it_again(self):
        choices = [{"kind": "protect", "about": self.b}]
        self.r.apply_choices(self.a, self.tick, choices)
        record = self.r.commitments.active(self.a)[0]
        due = record["due"]
        self.at(22, 4)
        self.assertEqual(self.r.apply_choices(self.a, self.tick, choices), [])
        self.assertEqual(record["due"], due)
        self.assertEqual(len(self.r.commitments.active(self.a)), 1)

    def test_reflection_cannot_silently_replace_a_protection_vow(self):
        old = self.request()
        self.at(22)
        self.r.apply_choices(self.a, self.tick, [{"kind": "protect", "about": self.c}])
        self.assertEqual(self.r.commitments.active(self.a)[0]["id"], old["id"])
        self.assertTrue(self.r.committed_to(self.a, self.b))
        self.assertFalse(self.r.committed_to(self.a, self.c))
        self.r.apply_choices(self.a, self.tick, [{"kind": "protect", "about": self.c, "reason": "They asked me to help their injured friend instead."}])
        self.assertEqual(old["status"], "abandoned")
        self.assertIn("injured friend", old["reason"])
        self.assertTrue(self.r.committed_to(self.a, self.c))

    def test_same_block_reversals_and_vague_reasons_are_refused(self):
        c = self.request()
        reason = "New evidence makes keeping this vow dangerous."
        self.assertFalse(self.r.commitments.drop(self.tick, self.a, c["id"], reason))
        self.at(14)
        self.assertFalse(self.r.commitments.drop(self.tick, self.a, c["id"], "changed my mind"))
        self.assertFalse(self.r.commitments.drop(self.tick, self.b, c["id"], reason))
        self.assertTrue(self.r.commitments.drop(self.tick, self.a, c["id"], reason))
        self.assertEqual(c["status"], "abandoned")
        self.assertEqual(self.w.agents[self.a]["sanity"], 79)
        self.assertFalse(self.r.commitments.drop(self.tick, self.a, c["id"], reason))
        self.assertEqual(self.w.agents[self.a]["sanity"], 79)

    def test_wavering_and_lifecycle_events_keep_the_turn_minute(self):
        self.r.clock_start()
        self.r.clock_to(7)
        c = self.request()
        self.r.clock_to(19)
        self.r.commitments.request(self.tick, self.a, {"kind": "protect", "target": self.c})
        self.assertEqual(self.tick["events"][-1]["status"], "considered")
        self.assertEqual(self.tick["events"][-1]["m"], 19)
        self.r.commitments.finish(self.tick, c, "cancelled", "An injury prevents keeping the vow.")
        self.assertEqual(self.tick["events"][-1]["m"], 19)

    def test_staged_host_conversation_keeps_its_prompt_without_changing_the_scene(self):
        self.r.keep_voice = True
        self.r.run_conversations(self.tick, {"lounge": [self.a, self.b]}, {}, 12, mode="occasion")
        self.assertTrue(self.tick["talk"])
        scene = self.tick["talk"][0]
        self.assertIn("vp", scene)
        self.assertEqual(scene["vp"]["c"]["mode"], "occasion")
        self.r.vkeep_flush(self.tick)
        self.assertIn(scene["vp"]["s"], self.tick["vsys"])

    def test_abandoned_intentions_cannot_be_restarted_in_the_next_block(self):
        c = self.request("thank")
        self.at(14)
        self.r.commitments.drop(self.tick, self.a, c["id"], "An attack made me reconsider thanking them.")
        self.at(16)
        self.assertIsNone(self.request("thank"))

    def test_reflection_intention_waits_until_tomorrow_and_does_not_get_overwritten(self):
        self.at(22)
        self.r.apply_choices(self.a, self.tick, [{"kind": "resolve", "about": self.b, "act": "apologise"}])
        record = self.r.commitments.active(self.a, "resolve")[0]
        self.assertIsNone(self.r.commitments.planned_move(self.a, self.b, self.conv()))
        self.at(8, 4)
        self.assertEqual(self.r.commitments.planned_move(self.a, self.b, self.conv()), "apologise")
        self.r.apply_choices(self.a, self.tick, [{"kind": "resolve", "about": self.c, "act": "confront"}])
        self.assertEqual(self.r.commitments.active(self.a, "resolve")[0]["id"], record["id"])

    def test_apology_is_spoken_and_can_be_rejected_without_erasing_the_attempt(self):
        c = self.request("apologise")
        conv = self.conv()
        self.assertEqual(self.r.pick_move(conv, self.a, self.b), ("apologise", None))
        self.assertEqual(c["status"], "active")  # Selecting a move alone is not follow-through.
        with patch.object(self.r.rng, "random", return_value=.999):
            beats = self.r.resolve_move(self.tick, conv, self.a, self.b, "apologise")
        self.assertEqual(beats[0]["move"], "apologise")
        self.assertEqual(beats[1]["move"], "rebuff")
        self.assertEqual(c["status"], "fulfilled")
        self.assertEqual(self.w.agents[self.b]["aff"][self.a], 0)
        beats[0]["m"] = beats[1]["m"] = 5
        _, prompt = voice_prompt(self.r, conv, beats)
        self.assertIn("COMMITMENTS:", prompt)
        self.assertIn("fulfilled", prompt)
        line = template_line(self.r, beats[0], random.Random(2))
        self.assertTrue("apology" in line["text"] or "sorry" in line["text"])

    def test_all_reflection_followups_have_actual_social_moves(self):
        for kind in ("confront", "ask", "thank"):
            with self.subTest(kind=kind):
                self.setUp()
                c = self.request(kind)
                self.r.resolve_move(self.tick, self.conv(), self.a, self.b, kind)
                self.assertEqual(c["status"], "fulfilled")

    def test_private_pursuit_does_not_override_urgent_care_or_enter_a_bathroom(self):
        c = self.request("thank")
        d = self.r.clean_decision({"action": "stay"})
        self.r.commitments.direct(self.tick, self.a, d)
        self.assertEqual(d["talk_to"], [self.b])
        self.w.agents[self.b]["room"] = "bathroom"
        d = self.r.clean_decision({"action": "stay"})
        self.r.commitments.direct(self.tick, self.a, d)
        self.assertEqual(d["talk_to"], [])
        self.w.agents[self.b]["room"] = "lounge"
        d = self.r.clean_decision({"action": "rest"})
        self.r.commitments.direct(self.tick, self.a, d)
        self.assertEqual(d["action"], "rest")
        self.assertEqual(c["status"], "active")

    def test_public_promise_requires_recipient_to_be_there_and_awake(self):
        self.w.agents[self.b]["room"] = "library"
        self.assertIsNone(self.request("promise"))
        self.w.agents[self.b].update(room="lounge", asleep=True)
        self.assertIsNone(self.request("promise"))
        self.w.agents[self.b].pop("asleep")
        self.assertIsNotNone(self.request("promise"))

    def test_promise_to_give_is_fulfilled_only_after_actual_transfer(self):
        self.w.agents[self.a]["inv"]["sweets"] = 1
        c = self.request("promise", action="give", item="sweets")
        self.assertEqual(c["status"], "active")
        decision = self.r.clean_decision({"action": "give", "to": self.b, "item": "sweets"})
        self.r.apply_act(self.tick, self.a, decision, {}, [], "lounge")
        self.assertEqual(c["status"], "fulfilled")
        self.assertNotIn("sweets", self.w.agents[self.a]["inv"])
        self.assertGreaterEqual(self.w.agents[self.b]["inv"]["sweets"], 1)

    def test_promise_to_talk_is_not_completed_by_sitting_in_a_room(self):
        c = self.request("promise")
        self.r.commitments.sync(self.tick)
        self.assertEqual(c["status"], "active")
        self.r.resolve_move(self.tick, self.conv(), self.a, self.b, "chat")
        self.assertEqual(c["status"], "fulfilled")

    def test_missing_a_public_promise_has_a_once_only_social_cost(self):
        c = self.request("promise")
        self.at(12, 4)
        self.r.commitments.sync(self.tick)
        self.assertEqual(c["status"], "failed")
        self.assertEqual(self.w.agents[self.b]["aff"][self.a], -2)
        sanity = self.w.agents[self.a]["sanity"]
        self.r.commitments.sync(self.tick)
        self.assertEqual(self.w.agents[self.a]["sanity"], sanity)

    def test_injury_and_departure_end_impossible_commitments_with_reasons(self):
        c = self.request("thank")
        self.w.agents[self.a]["hp"] = 20
        self.at(12, 4)
        self.r.commitments.sync(self.tick)
        self.assertEqual(c["status"], "cancelled")
        self.assertIn("injury", c["reason"])
        self.assertEqual(self.w.agents[self.a]["sanity"], 80)
        self.at(12, 5)
        self.w.agents[self.a]["hp"] = 100
        c = self.request()
        self.w.end_agent(self.b, "escaped")
        self.r.commitments.sync(self.tick)
        self.assertEqual(c["status"], "cancelled")
        self.assertIn("escaped", c["reason"])

    def test_protection_remains_until_deadline_and_an_attack_breaks_it(self):
        c = self.request()
        self.assertTrue(self.r.committed_to(self.a, self.b))
        self.r.betrayal(self.tick, self.a, self.b, "attacked")
        self.assertEqual(c["status"], "broken")
        self.assertFalse(self.r.committed_to(self.a, self.b))

    def test_host_attends_instead_of_following_an_unrelated_routine(self):
        self.r.proposals = [(self.a, {"kind": "party", "where": "lounge", "invite": [self.b], "text": "Come talk."})]
        self.r.queue_occasion(self.tick, 12)
        oc = self.w.state["occasion"]
        record = self.r.commitments.active(self.a, "host")[0]
        self.at(14)
        self.w.agents[self.a]["room"] = "library"
        d = self.r.clean_decision({"action": "search", "target_room": "garden"})
        self.r.commitments.direct(self.tick, self.a, d)
        self.assertEqual(d["target_room"], "lounge")
        self.assertEqual(d["action"], "stay")
        self.w.agents[self.a]["room"] = "lounge"
        self.r.resolve_occasion(self.tick, 14)
        self.assertEqual(record["status"], "fulfilled")
        self.assertIn(self.a, self.r.occasion_now["attendees"])
        self.assertEqual(oc["commitment_id"], record["id"])

    def test_host_cancels_for_a_real_obstacle_and_records_it(self):
        self.r.proposals = [(self.a, {"kind": "party", "where": "lounge", "invite": "all", "text": "Come talk."})]
        self.r.queue_occasion(self.tick, 12)
        c = self.r.commitments.active(self.a, "host")[0]
        self.at(14)
        self.w.agents[self.a]["hp"] = 20
        d = self.r.clean_decision({"action": "rest"})
        self.r.commitments.direct(self.tick, self.a, d)
        self.assertIsNone(self.w.state["occasion"])
        self.assertEqual(c["status"], "cancelled")
        self.assertIn("injury", c["reason"])
        self.assertTrue(any(e.get("commitment") == c["id"] for e in self.tick["events"]))

    def test_pact_and_plot_link_to_their_existing_sources(self):
        self.w.state["bonds"] = [{"a": self.a, "b": self.b, "kind": "pact", "since": 3}]
        self.w.state["plots"][self.c] = {"target": self.b, "stage": "brooding", "since": 3}
        self.r.commitments.sync(self.tick)
        self.assertTrue(self.r.committed_to(self.a, self.b))
        self.assertTrue(self.r.committed_to(self.b, self.a))
        self.assertEqual(len(self.r.commitments.active(self.c, "plot")), 1)
        self.r.abandon_plot(self.tick, self.c, "The target saved my life during the fire.")
        self.r.commitments.sync(self.tick)
        record = next(c for c in self.w.state["commitments"] if c["owner"] == self.c and c["kind"] == "plot")
        self.assertEqual(record["status"], "abandoned")
        self.assertIn("saved my life", record["reason"])

    def test_dares_are_obligations_only_when_accepted_and_use_checked_outcomes(self):
        d = {"who": self.a, "kind": "go", "room": "library", "task": "visit the library", "status": "open", "due": 86, "willing": False}
        self.w.state["dares"] = [d]
        self.r.commitments.sync(self.tick)
        self.assertFalse(self.r.commitments.active(self.a, "dare"))
        d["willing"] = True
        self.r.commitments.sync(self.tick)
        c = self.r.commitments.active(self.a, "dare")[0]
        d["status"] = "done"
        self.r.commitments.sync(self.tick)
        self.assertEqual(c["status"], "fulfilled")
        self.r.commitments.sync(self.tick)
        self.assertFalse(self.r.commitments.active(self.a, "dare"))

    def test_private_plot_is_not_exposed_in_another_persons_voice_card(self):
        self.w.state["plots"][self.a] = {"target": self.c, "stage": "brooding", "since": 3, "method": "", "cover": "", "log": []}
        self.r.commitments.sync(self.tick)
        private = self.r.commitments.context(self.a)
        self.assertIn("plan against", private)
        self.assertEqual(self.r.commitments.context(self.a, [self.a, self.b]), "")
        self.assertIn("COMMITMENTS:", self.r.decision_prompt(self.a, 12))
        self.assertIn("COMMITMENTS:", self.r.reflect_prompt(self.a)[1])

    def test_old_saves_keep_protection_and_pending_reflection_across_reload(self):
        state = new_state(3)
        state["agents"][self.a]["commit"] = {"protect": self.b, "day": 3, "until": 6}
        state["agents"][self.c]["want_talk"] = {"who": [self.b], "day": 4, "why": f"apologise to {self.b}"}
        w = World(state)
        r = DayRunner(w, LLM("mock"), lambda t: None, seed=45)
        before = copy.deepcopy(w.state["commitments"])
        for _ in range(3):
            w = World(json.loads(json.dumps(w.dump())))
            r = DayRunner(w, LLM("mock"), lambda t: None, seed=45)
            self.assertEqual(w.state["commitments"], before)
            self.assertTrue(r.committed_to(self.a, self.b))
            self.assertTrue(r.commitments.active(self.c, "resolve"))

    def test_prefetched_decision_is_invalidated_when_a_commitment_changes(self):
        before = self.r.ahead_sig(self.a)
        self.request()
        self.assertNotEqual(self.r.ahead_sig(self.a), before)
        before = copy.deepcopy(self.w.dump())
        self.r.commitments.context(self.a)
        self.assertEqual(self.w.dump(), before)
        other = self.r.ahead_sig(self.c)
        self.r.commitments.request(self.tick, self.b, {"kind": "thank", "target": self.a})
        self.assertEqual(self.r.ahead_sig(self.c), other)

    def test_invalid_replacement_does_not_drop_an_existing_vow(self):
        old = self.request()
        self.at(14)
        self.r.commitments.drop(self.tick, self.a, old["id"], "The target asked me to stop protecting them.")
        self.at(16)
        current = self.r.commitments.request(self.tick, self.a, {"kind": "protect", "target": self.c})
        self.at(18)
        self.assertIsNone(self.request(reason="I wanted to change my protection back."))
        self.assertEqual(current["status"], "active")

    def test_irrelevant_model_fields_cannot_change_a_vow_or_break_a_promise(self):
        old = self.request()
        again = self.request(item="imaginary_item", room="moon_base", action="nonsense")
        self.assertEqual(old["id"], again["id"])
        promise = self.request("promise", room="moon_base", action="talk")
        self.assertEqual(promise["room"], "")

    def test_wavering_is_visible_once_per_day_without_abandoning_the_vow(self):
        c = self.request()
        for _ in range(3):
            self.r.commitments.request(self.tick, self.a, {"kind": "protect", "target": self.c})
        self.assertEqual(c["status"], "active")
        self.assertEqual(sum(e.get("status") == "considered" for e in self.tick["events"]), 1)

    def test_visit_promise_requires_an_actual_arrival(self):
        c = self.request("promise", action="visit", room="library")
        self.assertEqual(c["status"], "active")
        self.at(14)
        d = self.r.clean_decision({"action": "stay", "target_room": "library"})
        self.r.apply_decision(self.tick, self.a, d, {}, [])
        self.assertEqual(self.w.agents[self.a]["room"], "library")
        self.assertEqual(c["status"], "fulfilled")

    def test_checker_reports_unexplained_or_reopened_commitments(self):
        from murder.storylint import StoryLinter
        checker = StoryLinter(self.w.dump())
        tick = self.r.new_tick(12)
        tick["events"] = [{"type": "commitment", "commitment": "c42", "status": "failed", "who": self.a},
                          {"type": "commitment", "commitment": "c42", "status": "active", "who": self.a}]
        checker.feed(tick)
        codes = [i["code"] for i in checker.issues]
        self.assertIn("unexplained_commitment_end", codes)
        self.assertIn("commitment_reopened", codes)

    def test_checker_accepts_real_commitment_lifecycle_and_keeps_input_unchanged(self):
        from murder.storylint import StoryLinter
        checker = StoryLinter(self.w.dump())
        self.request("thank")
        self.r.resolve_move(self.tick, self.conv(), self.a, self.b, "thank")
        tick = copy.deepcopy(self.tick)
        checker.feed(tick)
        self.assertEqual(checker.issues, [])
        self.assertEqual(tick, self.tick)

    def test_history_is_bounded_without_evicting_active_commitments(self):
        state = {}
        keep = start(state, "a", "protect", "keep me", 0, 200)
        for n in range(220):
            c = start(state, "b", "resolve", "a task", n, n + 1)
            self.assertTrue(end(state, c, n + 1, "fulfilled", "a checked action"))
            self.assertFalse(end(state, c, n + 1, "failed", "a duplicate"))
        self.assertIn(keep, active(state))
        self.assertEqual(len(state["commitment_history"]), 200)
        self.assertEqual(len(state["commitments"]), 101)


if __name__ == "__main__":
    unittest.main(verbosity=2)
