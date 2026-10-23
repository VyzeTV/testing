"""Forced story-invariant regressions; no paid model calls or real save writes."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from murder.storylint import StoryLinter


def world():
    return {"day": 3, "cast": {c: {"short": n} for c, n in (("a", "Alice"), ("b", "Bob"), ("c", "Carol"))},
            "agents": {c: {"status": "alive"} for c in "abc"}}


def tick(**fields):
    return {"day": 3, "hour": 8, "idx": 0, "events": [], "talk": [], "broadcasts": [], **fields}


class StoryChecks(unittest.TestCase):
    def setUp(self):
        self.lint = StoryLinter(world())

    def codes(self):
        return [i["code"] for i in self.lint.issues]

    def test_multiple_finders_before_announcement_are_valid(self):
        self.lint.feed(tick(events=[{"type": "body", "who": c, "victim": "a"} for c in "bc"],
                            broadcasts=[{"kind": "body", "victim": "a"}]))
        self.assertEqual(self.codes(), [])
        self.assertEqual(self.lint.checks["body_discovery"], 2)

    def test_repeated_finder_and_rediscovery_report_locations(self):
        found = {"type": "body", "who": "b", "victim": "a", "m": 12, "text": "Bob finds Alice."}
        self.lint.feed(tick(events=[found]))
        self.lint.feed(tick(hour=10, events=[found], broadcasts=[{"kind": "body", "victim": "a"}]))
        self.lint.feed(tick(day=4, events=[found]))
        self.assertEqual(self.codes(), ["duplicate_finder", "body_rediscovered"])
        self.assertEqual(self.lint.issues[0]["minute"], 12)
        self.assertEqual(self.lint.issues[0]["related"]["text"], "Bob finds Alice.")

    def test_repeat_announcement_includes_nontrial_deaths(self):
        b = {"kind": "verdict", "story_kind": "spree_death", "victim": "a"}
        self.lint.feed(tick(broadcasts=[b, b]))
        self.assertEqual(self.codes(), ["duplicate_body_announcement"])

    def test_actions_before_same_block_death_are_allowed(self):
        state = world()
        state["agents"]["a"]["status"] = "dead"
        self.lint.feed(tick(state=state, talk=[{"lines": [{"speaker": "a", "text": "Goodbye."}]}]))
        self.assertEqual(self.codes(), [])
        self.lint.feed(tick(hour=10, talk=[{"lines": [{"speaker": "a", "text": "Still here."}]}]))
        self.assertEqual(self.codes(), ["inactive_actor"])

    def test_event_can_report_a_death_within_the_same_block(self):
        self.lint.feed(tick(events=[{"type": "craft", "actor": "a", "actor_status": "dead"}]))
        self.assertEqual(self.codes(), ["inactive_actor"])

    def test_dead_neovi_cannot_speak(self):
        state = world()
        state["npcs"] = {"neovi": {"dead": {"how": "murder"}, "room": "none"}}
        self.lint.begin_day(state)
        self.lint.feed(tick(talk=[{"lines": [{"speaker": "neovi", "text": "Hello."}]}]))
        self.assertEqual(self.codes(), ["inactive_actor"])

    def test_inactive_actor_address_and_gossip_are_checked(self):
        state = world()
        state["agents"]["a"]["status"] = "executed"
        self.lint.begin_day(state)
        self.lint.feed(tick(events=[{"type": "craft", "who": "a"}],
                            talk=[{"lines": [{"speaker": "b", "to": "a", "move": "warn", "about": "a"}]}]))
        self.assertEqual(self.codes(), ["inactive_actor", "inactive_actor", "inactive_topic"])

    def test_remembrance_is_not_present_tense_gossip(self):
        state = world()
        state["agents"]["a"]["status"] = "dead"
        self.lint.begin_day(state)
        self.lint.feed(tick(talk=[{"lines": [{"speaker": "b", "move": "remember", "about": "a", "text": "I miss Alice."}]}]))
        self.assertEqual(self.codes(), [])

    def test_resurrection_is_reported(self):
        state = world()
        state["agents"]["a"]["status"] = "dead"
        self.lint.begin_day(state)
        self.lint.feed(tick(state=world()))
        self.assertEqual(self.codes(), ["resurrection"])

    def test_raft_return_allows_escapees_but_not_dead_people(self):
        state = world()
        state["agents"]["a"]["status"] = "escaped"
        state["agents"]["b"]["status"] = "dead"
        self.lint.begin_day(state)
        self.lint.feed(tick(state=world(), events=[{"story_kind": "raft_return", "returned": ["a", "b"]}]))
        self.assertEqual(self.codes(), ["resurrection"])
        self.assertIn("b", self.lint.issues[0]["source"])

    def test_madness_repeat_has_a_three_day_window(self):
        e = {"type": "madness", "who": "a", "text": "Alice has snapped."}
        self.lint.feed(tick(events=[e]))
        self.lint.feed(tick(day=4, events=[e]))
        self.lint.feed(tick(day=7, events=[e]))
        self.assertEqual(self.codes(), ["repeated_madness"])

    def test_distinct_spree_episodes_are_not_duplicate_threshold_notices(self):
        event = {"type": "madness", "who": "a", "episode": 1, "text": "The frenzy begins."}
        self.lint.feed(tick(events=[event]))
        self.lint.feed(tick(hour=10, events=[dict(event, episode=2)]))
        self.lint.feed(tick(hour=12, events=[dict(event, episode=2)]))
        self.assertEqual(self.codes(), ["repeated_madness"])

    def test_host_must_attend_or_have_a_reason(self):
        e = {"type": "occasion", "stage": "begin", "who": "a", "attendees": ["b"]}
        self.lint.feed(tick(events=[e, dict(e, absence_reason="hospitalized")]))
        self.assertEqual(self.codes(), ["absent_host"])

    def test_evidence_requires_defence_if_it_names_presenter(self):
        line = {"speaker": "a", "move": "evidence", "evidence": {"named": ["a"], "weight": 2}}
        self.lint.feed(tick(talk=[{"lines": [line, dict(line, move="defence"), dict(line, evidence={"named": ["a"], "weight": -2})]}]))
        self.assertEqual(self.codes(), ["self_incriminating_evidence"])

    def test_alibi_changes_allow_explicit_lies(self):
        line = {"speaker": "a", "claim_at": {"t": 80, "r": "kitchen", "true": True}}
        other = {"speaker": "a", "claim_at": {"t": 80, "r": "lounge", "true": True}}
        self.lint.feed(tick(talk=[{"lines": [line, other]}]))
        self.assertEqual(self.codes(), ["contradictory_alibi"])
        self.lint = StoryLinter(world())
        self.lint.feed(tick(talk=[{"lines": [line, {"speaker": "a", "claim_at": dict(other["claim_at"], true=False)}]}]))
        self.assertEqual(self.codes(), [])

    def test_checker_does_not_modify_inputs(self):
        state = world()
        t = tick(state=state)
        before = json.dumps([state, t], sort_keys=True)
        self.lint.begin_day(state)
        self.lint.feed(t)
        self.assertEqual(json.dumps([state, t], sort_keys=True), before)


class EngineStoryChecks(unittest.TestCase):
    def setUp(self):
        from murder.engine import DayRunner
        from murder.llm import LLM
        from murder.world import World, new_state
        self.world = World(new_state(3))
        self.runner = DayRunner(self.world, LLM(backend="mock"), lambda t: None, seed=42,
                                rule_mode="none", confessionals=False)
        self.runner.init_item_log()

    def test_actual_voice_prompt_gets_adult_register_before_and_after_reveal(self):
        from murder.voice import voice_prompt
        r, w = self.runner, self.world
        a, b = sorted(w.agents)[:2]
        for revealed in (False, True):
            w.state["revealed"] = revealed
            system, user = voice_prompt(r, {"members": [a, b], "room": "foyer", "hour": 8},
                                        [{"who": a, "to": b, "move": "joke", "outcome": "ok", "m": 5}])
            self.assertIn("uncensored", system)
            self.assertIn("innuendo", system)
            self.assertIn("fade to black before sexual activity", system)
            self.assertIn(f"age {w.cast[a]['age']}", user)
            self.assertIn(w.cast[a]["candor"], user)
            self.assertIn("never change who wins or loses", user)
            if not revealed:
                self.assertNotIn("horror-film explicit", system)

    def test_tone_off_preserves_relationships_without_requesting_spicy_dialogue(self):
        r = self.runner
        r.tuning_get = lambda: {"flirt_level": 0, "banter_level": 0}
        guide = r.bible()
        self.assertIn("Do not add sexual innuendo", guide)
        self.assertIn("preserve existing relationship facts", guide)
        self.assertNotIn("cheekily dirty", guide)
        self.assertNotIn("Nobody here is interested in romance", guide)
        self.assertIn("uncensored", guide)

    def test_mock_banter_respects_mutual_comfort_and_tone_setting(self):
        from unittest.mock import Mock
        from murder.voice import template_line
        r, w = self.runner, self.world
        a, b = sorted(w.agents)[:2]
        rng = Mock(random=lambda: 1.0, choice=lambda lines: lines[0])
        beat = {"who": a, "to": b, "move": "joke", "outcome": "ok"}
        w.agents[a]["aff"][b] = w.agents[b]["aff"][a] = 3
        self.assertIn("fucking", template_line(r, beat, rng)["text"])
        r.tuning_get = lambda: {"banter_level": 0}
        self.assertNotIn("fucking", template_line(r, beat, rng)["text"])
        r.tuning_get = lambda: {"banter_level": 2}
        w.agents[b]["aff"][a] = -3
        self.assertNotIn("fucking", template_line(r, beat, rng)["text"])
        self.assertNotIn("trades", r.card_tone(a, [a, b]))

    def test_mock_flirting_is_nonphysical_and_needs_adult_mutual_interest(self):
        from unittest.mock import Mock
        from murder.voice import template_line
        r, w = self.runner, self.world
        a, b = sorted(w.agents)[:2]
        rng = Mock(random=lambda: 1.0, choice=lambda lines: lines[0])
        beat = {"who": a, "to": b, "move": "flirt", "outcome": "ok"}
        w.agents[a]["aff"][b] = w.agents[b]["aff"][a] = 9
        w.state["bonds"] = [{"a": a, "b": b, "kind": "romance", "since": 3}]
        line = template_line(r, beat, rng)
        self.assertEqual(line["kind"], "say")
        self.assertIn("difficult to behave", line["text"])
        self.assertEqual(len(w.state["bonds"]), 1)
        self.assertEqual(w.agents[a]["aff"][b], 9)
        beat["outcome"] = "fail"
        self.assertNotIn("difficult to behave", template_line(r, beat, rng)["text"])
        beat["outcome"] = "ok"
        w.cast[b]["age"] = 17
        self.assertEqual(r.flirty_pairs([a, b]), [])
        self.assertFalse(r.free_tonight(b))
        self.assertNotIn("difficult to behave", template_line(r, beat, rng)["text"])

    def test_madness_threshold_announced_once_per_window(self):
        r, w = self.runner, self.world
        cid = sorted(w.agents)[0]
        w.agents[cid]["sanity"] = 5
        t = r.new_tick(8)
        r.check_madness(t, cid, 100)
        r.check_madness(t, cid, 100)
        self.assertEqual(len([e for e in t["events"] if e["type"] == "madness"]), 1)

    def test_body_announcement_is_idempotent(self):
        r, w = self.runner, self.world
        k, v = sorted(w.agents)[:2]
        t = r.new_tick(8)
        r.open_case(t, "murder", v, culprit=k, room="foyer", hour=8, witnesses=[])
        r.announce_body(t, 8)
        before = copy.deepcopy(t)
        r.announce_body(t, 8)
        self.assertEqual(t, before)

    def test_announced_spree_remains_are_not_new_discoveries(self):
        r, w = self.runner, self.world
        cid, victim = sorted(w.agents)[:2]
        w.state["bodies"] = [{"victim": victim, "room": w.agents[cid]["room"], "day": 1, "by": [], "desc": "a body"}]
        t = r.new_tick(8)
        r.spree_upkeep(t, 8)
        self.assertTrue(any(e["type"] == "body_seen" for e in t["events"]))
        self.assertFalse(any(e["type"] == "body" for e in t["events"]))
        self.assertNotIn("scene_body", t)

    def test_evidence_prefers_another_finder(self):
        r, w = self.runner, self.world
        a, b = sorted(w.agents)[:2]
        c = {"room": "foyer", "day": 3, "hour": 8, "clues": [
            {"text": f"{r.nm(a)} left blood on the weapon.", "kind": "weapon", "found_by": [a, b]}]}
        facts = r.trial_facts(c, list(w.agents))
        self.assertTrue(any(f["by"] == b and f["about"] == a for f in facts))
        self.assertFalse(any(f["by"] == a and f["about"] == a for f in facts))

    def test_a_lethal_storm_records_the_victim_as_a_subject(self):
        r, w = self.runner, self.world
        cid = sorted(w.agents)[0]
        for a in w.agents.values():
            a["room"] = "lounge"
        w.agents[cid].update(room="garden", hp=4)
        w.state["island"] = {"id": "storm"}
        r.island_live = lambda island: True
        t = r.new_tick(10)
        r.island_tick_effects(t, 10)
        self.assertNotIn(cid, w.agents)
        events = [e for e in t["events"] if e["type"] == "island" and e["who"] == cid]
        self.assertEqual(len(events), 1)
        self.assertNotIn("actor", events[0])

    def test_occasion_records_the_host_and_attendees(self):
        r, w = self.runner, self.world
        host, guest = sorted(w.agents)[:2]
        w.agents[host]["room"] = w.agents[guest]["room"] = "foyer"
        w.state["occasion"] = {"status": "announced", "host": host, "where": "foyer", "kind": "get-together",
                               "invite_ids": [guest], "open": False, "text": "Let's meet."}
        t = r.new_tick(8)
        r.resolve_occasion(t, 8)
        began = [e for e in t["events"] if e.get("stage") == "begin"]
        self.assertEqual(len(began), 1)
        self.assertIn(host, began[0]["attendees"])
        lint = StoryLinter(w.dump())
        lint.feed(t)
        self.assertEqual(lint.checks["host_attendance"], 1)
        self.assertEqual(lint.issues, [])

    def test_a_sole_named_finder_answers_evidence_as_defence(self):
        r, w = self.runner, self.world
        killer, victim = sorted(w.agents)[:2]
        t = r.new_tick(10)
        r.open_case(t, "murder", victim, culprit=killer, room="foyer", hour=8, witnesses=[])
        case = w.state["case"]
        case["clues"] = [{"text": f"{r.nm(killer)} left blood on the weapon.", "kind": "weapon", "found_by": [killer]}]
        r.willingness = lambda *args: 1.0
        r.run_claim_trial(t, 10, case)
        evidence = [line for group in t["talk"] for line in group["lines"] if line.get("evidence")]
        self.assertTrue(evidence)
        self.assertTrue(all(line["move"] == "defence" for line in evidence if line["speaker"] == killer))
        lint = StoryLinter(w.dump())
        lint.feed(t)
        self.assertFalse(any(i["code"] == "self_incriminating_evidence" for i in lint.issues))

    def test_old_rumours_cannot_target_a_dead_person_as_present(self):
        r, w = self.runner, self.world
        a, b, dead = sorted(w.agents)[:3]
        w.end_agent(dead, "dead")
        w.agents[a]["aff"][b] = w.agents[b]["aff"][a] = 3
        w.state["rumors"] = [{"about": dead, "by": b, "heard": [a], "claim": "They keep asking questions."}]
        options = r.move_options({"members": [a, b], "used": {}, "room": "foyer"}, a, b)
        self.assertFalse(any(move in ("gossip", "warn") and about == dead for _, move, about in options))


class RecordingChecks(unittest.TestCase):
    def test_recording_is_read_only_and_reports_file_line(self):
        from story_lint import recording
        with tempfile.TemporaryDirectory(prefix="mc_story_record_") as tmp:
            base = Path(tmp)
            (base / "starts").mkdir()
            (base / "starts" / "day_03_start.json").write_text(json.dumps(world()), encoding="utf-8")
            day = base / "runs" / "day_03"
            day.mkdir(parents=True)
            file = day / "ticks.jsonl"
            b = {"kind": "body", "victim": "a", "text": "A body has been found."}
            file.write_text(json.dumps(tick(broadcasts=[b])) + "\n" + json.dumps(tick(hour=10, broadcasts=[b])) + "\n", encoding="utf-8")
            before = file.read_bytes()
            result = recording(base)
            self.assertEqual(len(result["story_issues"]), 1)
            issue = result["story_issues"][0]
            self.assertEqual(issue["code"], "duplicate_body_announcement")
            self.assertEqual(issue["record_line"], 2)
            self.assertEqual(issue["file"], str(file))
            self.assertEqual(file.read_bytes(), before)

    def test_empty_recording_fails_clearly(self):
        from story_lint import recording
        with tempfile.TemporaryDirectory(prefix="mc_story_empty_") as tmp:
            with self.assertRaisesRegex(ValueError, "No day_"):
                recording(tmp)


if __name__ == "__main__":
    unittest.main(verbosity=2)
