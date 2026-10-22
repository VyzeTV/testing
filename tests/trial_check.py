"""Forced trial reasoning cases. Run: python tests/trial_check.py (mock models only)."""
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from murder.engine import DayRunner
from murder.llm import LLM
from murder.world import World, new_state


class TrialChecks(unittest.TestCase):
    def setUp(self):
        self.world = World(new_state(3))
        self.r = DayRunner(self.world, LLM(backend="mock"), lambda t: None, seed=550,
                           rule_mode="none", confessionals=False)
        self.r.init_item_log()
        ids = sorted(self.world.agents)
        self.k, self.h, self.j, self.other, self.victim = ids[0], ids[1], ids[2], ids[3], ids[-1]
        t = self.r.new_tick(10)
        self.r.open_case(t, "murder", self.victim, culprit=self.k, room="foyer", hour=10, witnesses=[])
        self.case = self.world.state["case"]
        self.case.update(clues=[], marks={}, glimpses=[], handmark=None)
        self.ids = sorted(self.world.agents)
        for cid in self.ids:
            self.world.agents[cid]["aff"] = {o: 0 for o in self.ids if o != cid}
            self.world.agents[cid]["sanity"] = 90
        self.r.slip_chance = lambda cid: 0
        self.r.willingness = lambda *args: 1.0
        self.r.has_trait = lambda *args: False

    def run_trial(self):
        tick = self.r.new_tick(12)
        votes = self.r.run_claim_trial(tick, 12, self.case)
        return tick, votes

    def fact(self, by, about, weight, text="Evidence", **fields):
        return {"by": by, "about": about, "w": weight, "text": text, "kind": "clue", **fields}

    def public(self, facts):
        self.r._trial_public = facts
        self.r._trial_family_push = {}
        self.r._trial_arguments = {c: [] for c in self.ids}
        meter = {c: 0.0 for c in self.ids}
        for f in facts:
            meter[f["about"]] += f["w"]
            self.r._trial_arguments[f["about"]].append({"text": f["text"], "kind": f["kind"], "weight": f["w"], "by": f["by"]})
        return meter

    def test_physical_trace_outweighs_many_motive_clues(self):
        self.case["clues"] = [
            {"kind": "weapon", "text": f"{self.r.nm(self.k)} left blood on the weapon.", "found_by": [self.j]},
            *[{"kind": "herring", "text": f"{self.r.nm(self.h)} disliked the victim ({i}).", "found_by": [self.j]} for i in range(8)]]
        tick, votes = self.run_trial()
        self.assertGreater(tick["claim_trial"]["meter"][self.k], tick["claim_trial"]["meter"][self.h])
        self.assertGreater(sum(v["target"] == self.k for v in votes), len(votes) // 2)

    def test_visible_hair_and_hand_comparison_reaches_the_meter(self):
        self.case["clues"] = [
            {"kind": "scene", "text": "The body.", "found_by": [self.j]},
            {"kind": "weapon", "text": "A handprint on the handle.", "found_by": [self.j]},
            {"kind": "hair", "text": "A hair in the victim's fingers.", "hair": list(self.r.looks(self.k)["hair"]), "found_by": [self.j]}]
        self.case["handmark"] = self.r.build_of(self.k)["hand"]
        self.r.willingness = lambda *args: 0.0
        self.run_trial()
        self.assertTrue(any(f["kind"] == "look" and f["about"] == self.k for f in self.r._trial_public))
        self.assertTrue(any(f["kind"] == "mark" and f["about"] == self.k for f in self.r._trial_public))

    def test_motive_private_total_is_capped(self):
        facts = [self.fact(self.j, self.h, 0.35, str(i), family="motive") for i in range(8)]
        private = self.r.trial_private_facts(self.j, facts)
        self.assertAlmostEqual(sum(f["w"] for f in private), 0.9)

    def test_public_fact_is_not_double_counted_for_its_finder(self):
        fact = self.fact(self.j, self.k, 3.5, "Blood on their clothes.")
        meter = self.public([fact])
        score = self.r.personal_suspicion(self.j, self.ids, meter, [fact], self.k, self.case)
        self.assertEqual(score[self.k], 3.5)

    def test_other_finders_know_their_unspoken_clue(self):
        fact = self.fact(self.h, self.k, 3.5, known_by=[self.h, self.j])
        self.assertEqual(len(self.r.trial_private_facts(self.j, [fact])), 1)
        self.assertEqual(self.r.trial_private_facts(self.other, [fact]), [])

    def test_vote_reason_cannot_quote_another_persons_hidden_evidence(self):
        secret = self.fact(self.j, self.k, 9, "PRIVATE: I alone found the stained gloves.")
        meter = self.public([])
        votes = self.r.compute_votes(self.ids, meter, [secret], self.k, self.case)
        self.assertTrue(any("PRIVATE:" in v["reason"] for v in votes if v["voter"] == self.j))
        self.assertFalse(any("PRIVATE:" in v["reason"] for v in votes if v["voter"] != self.j))

    def test_false_planted_evidence_can_produce_a_wrong_verdict(self):
        self.case["clues"] = [{"kind": "planted", "text": f"{self.r.nm(self.h)}'s bloodstained weapon lies at the scene.", "found_by": [self.j]}]
        _, votes = self.run_trial()
        self.assertGreater(sum(v["target"] == self.h for v in votes), len(votes) // 2)

    def test_vote_trace_reconstructs_its_final_score(self):
        facts = [self.fact(self.h, self.k, 3.5, "Stained clothes.")]
        meter = self.public(facts)
        votes = self.r.compute_votes(self.ids, meter, facts, self.k, self.case)
        for vote in votes:
            trace = vote["reasoning"]
            total = sum(trace[k] for k in ("public_score", "private_score", "relationship_bias", "trusted_sway", "framing_bias"))
            self.assertAlmostEqual(total, trace["final_score"], places=2)

    def test_socially_swung_vote_names_the_trusted_person(self):
        public = [self.fact(self.other, self.k, 1, "A weak case against the first suspect."),
                  self.fact(self.other, self.h, 0.7, "A weak case against the second suspect.")]
        secret = self.fact(self.other, self.h, 3, "Their private observation.")
        meter = self.public(public)
        self.world.agents[self.j]["aff"][self.other] = 4
        votes = self.r.compute_votes(self.ids, meter, public + [secret], self.k, self.case)
        vote = next(v for v in votes if v["voter"] == self.j)
        self.assertEqual(vote["target"], self.h)
        self.assertIn(self.r.nm(self.other), vote["reason"])
        self.assertNotIn("private observation", vote["reason"])

    def test_45_minute_old_sighting_is_not_a_murder_time_sighting(self):
        t = self.r.case_time(self.case)
        self.r.believe(self.j, {"k": "at", "s": self.k, "r": "foyer", "t0": t - 0.6, "t1": t - 0.6,
                                "src": "seen", "c": 0.9, "true": True})
        facts = self.r.trial_facts(self.case, self.ids)
        self.assertFalse(any(f["kind"] == "near_scene" and f["about"] == self.k for f in facts))

    def test_murder_time_sighting_is_kept(self):
        t = self.r.case_time(self.case)
        self.r.believe(self.j, {"k": "at", "s": self.k, "r": "foyer", "t0": t, "t1": t,
                                "src": "seen", "c": 0.9, "true": True})
        self.assertTrue(any(f["kind"] == "near_scene" for f in self.r.trial_facts(self.case, self.ids)))

    def test_hearsay_is_not_presented_as_an_eyewitness_sighting(self):
        t = self.r.case_time(self.case)
        self.r.believe(self.j, {"k": "at", "s": self.k, "r": "foyer", "t0": t, "t1": t,
                                "src": "heard", "c": 0.9, "true": False, "by": self.h})
        self.assertFalse(any(f["kind"] == "near_scene" for f in self.r.trial_facts(self.case, self.ids)))

    def test_public_witness_statement_keeps_its_attribution(self):
        fact = self.fact(self.h, self.k, 4, "I saw the attack.")
        meter = self.public([fact])
        votes = self.r.compute_votes(self.ids, meter, [fact], self.k, self.case)
        vote = next(v for v in votes if v["voter"] == self.j)
        self.assertIn(self.r.nm(self.h) + " said:", vote["reason"])

    def test_withheld_body_marks_are_not_public_facts(self):
        self.case["marks"] = {"hand": self.r.build_of(self.k)["hand"]}
        self.case["clues"] = [{"kind": "scene", "found_by": [self.j], "held": [self.j], "text": "A mark on the body."}]
        self.assertEqual(self.r.mark_facts(self.case, self.ids), [])

    def test_clearing_evidence_is_retained_instead_of_clamped_away(self):
        self.case["clues"] = [{"kind": "frame_flaw", "text": f"{self.r.nm(self.h)} was unconscious before the killing.", "found_by": [self.j]}]
        tick, _ = self.run_trial()
        self.assertLess(tick["claim_trial"]["meter"][self.h], 0)

    def claims(self):
        t = self.r.case_time(self.case)
        return {c: {"r": "library", "t": t, "text": "I was in the library.", "lie": False, "with": []} for c in self.ids}

    def test_incompatible_companion_accounts_are_raised_without_proving_a_liar(self):
        claims = self.claims()
        claims[self.h]["r"] = "kitchen"
        claims[self.h]["with"] = [self.j]
        self.r.trial_claims = lambda *args: claims
        tick, _ = self.run_trial()
        self.assertEqual(len(tick["claim_trial"]["alibi_conflicts"]), 1)
        self.assertTrue(any(line["move"] == "alibi_conflict" for group in tick["talk"] for line in group["lines"]))
        self.assertEqual(tick["claim_trial"]["lies_proven"], {})

    def test_matching_companions_do_not_conflict(self):
        claims = self.claims()
        claims[self.h]["with"] = [self.j]
        self.assertEqual(self.r.alibi_conflicts(claims, self.ids), [])

    def test_accounts_of_different_times_do_not_conflict(self):
        claims = self.claims()
        claims[self.h].update(r="kitchen")
        claims[self.h]["with"] = [self.j]
        claims[self.j]["t"] += 1
        self.assertEqual(self.r.alibi_conflicts(claims, self.ids), [])

    def test_rehearsed_alibi_does_not_randomly_change(self):
        first = self.r.testimony_for(self.k)
        self.world.state.setdefault("where_log", {})[self.k] = [[3, 8, "library"], [3, 9, "kitchen"]]
        second = self.r.testimony_for(self.k)
        self.assertEqual(first, second)

    def test_not_seen_by_a_camera_is_not_positive_proof(self):
        self.case["clues"] = [{"kind": "ledger", "text": f"Nobody placed elsewhere. Not placed: {self.r.nm(self.k)}.", "found_by": [self.j]}]
        facts = self.r.trial_facts(self.case, self.ids)
        self.assertFalse(any(f["about"] == self.k and f["w"] > 0 for f in facts))


if __name__ == "__main__":
    unittest.main(verbosity=2)
