"""Persistent story rules, save recovery, and generation diagnostics. No AI calls."""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("MC_DATA_DIR", tempfile.mkdtemp(prefix="mc_reliability_"))
from murder.engine import DayRunner
from murder.llm import LLM, LLMError
from murder.world import World, new_state
from murder.saves import SaveStore
from murder.diagnostics import generation_status
from murder.relationships import closeness
from murder import session as mod


class StoryPersistenceChecks(unittest.TestCase):
    def setUp(self):
        self.w = World(new_state(3))
        self.r = DayRunner(self.w, LLM("mock"), lambda tick: None, seed=31, rule_mode="none")
        self.a, self.b, self.c = sorted(self.w.agents)[:3]
        for target in (self.b, self.c):
            for day in (1, 2, 3):
                closeness(self.w.state, self.a, target, day * 24 + 8, "prior welcomed conversations")
        for x in self.w.agents:
            for y in self.w.agents:
                if x != y:
                    self.w.agents[x]["aff"][y] = 8

    def bond(self, hour=10, other=None, kind="romance"):
        b = other or self.b
        tick = self.r.new_tick(hour)
        self.r.apply_bonds(tick, [{"a": self.a, "b": b, "kind": kind}], [self.a, b])
        return tick

    def plot(self, kind="height"):
        p = self.r.plot_defaults({"target": self.b, "stage": "striking", "scheme": {"kind": kind, "room": "landing", "when": "day"}})
        self.w.state["plots"] = {self.a: p}
        self.w.agents[self.a]["room"] = self.w.agents[self.b]["room"] = "library"
        return p

    def test_romance_requires_strong_mutual_affection(self):
        self.w.agents[self.b]["aff"][self.a] = 6
        self.bond()
        self.assertEqual(self.w.state["bonds"], [])

    def test_romance_does_not_repeat_or_form_with_another_person_immediately(self):
        first = self.bond()
        self.assertTrue(first["events"])
        self.assertFalse(self.bond(12)["events"])
        self.assertFalse(self.bond(14, self.c)["events"])
        self.assertEqual(len(self.w.state["bonds"]), 1)
        self.assertFalse(self.bond(34, self.c)["events"])  # A current partner cannot become an unacknowledged second romance.
        self.w.agents[self.a]["aff"][self.b] = 1
        self.r.bond_upkeep(self.r.new_tick(34))
        self.assertTrue(self.bond(58, self.c)["events"])

    def test_betrayal_cooldown_survives_save_round_trip(self):
        self.bond()
        self.bond(kind="pact")
        self.r.betrayal(self.r.new_tick(12), self.a, self.b, "turns on")
        state = json.loads(json.dumps(self.w.dump()))
        self.w = World(state)
        self.r = DayRunner(self.w, LLM("mock"), lambda tick: None, seed=32)
        self.w.agents[self.a]["aff"][self.b] = self.w.agents[self.b]["aff"][self.a] = 9
        self.assertFalse(self.bond(14)["events"])
        self.assertFalse(self.bond(14, kind="pact")["events"])
        self.assertFalse(self.bond(84)["events"])  # The cooldown ending does not erase betrayal.
        for day in range(4, 41):
            closeness(self.w.state, self.a, self.b, day * 24 + 8, "sustained repair")
        self.r.day = self.w.state["day"] = 40
        self.assertTrue(self.bond(10)["events"])

    def test_cooling_and_affairs_both_prevent_immediate_reformation(self):
        for reason in ("cooling", "affair"):
            with self.subTest(reason=reason):
                self.setUp()
                self.bond()
                if reason == "cooling":
                    self.w.agents[self.a]["aff"][self.b] = 1
                    self.r.bond_upkeep(self.r.new_tick(12))
                else:
                    self.r.affair_found(self.r.new_tick(12), self.a, self.b, self.c)
                self.w.agents[self.a]["aff"][self.b] = self.w.agents[self.b]["aff"][self.a] = 9
                self.assertFalse(self.bond(14)["events"])

    def test_planned_method_waits_and_explicitly_changes_under_pressure(self):
        p = self.plot()
        tick = self.r.new_tick(14)
        self.assertIsNone(self.r.planned_attack(tick, self.a, p))
        self.assertEqual(p["scheme"]["kind"], "height")
        method = self.r.planned_attack(tick, self.a, p, urgent=True)
        self.assertTrue(method)
        self.assertEqual(p["scheme"]["kind"], "opportunity")
        self.assertIn("deadline", p["changes"][-1]["reason"])
        self.assertEqual(p["changes"][-1]["from"]["kind"], "height")
        self.assertTrue(any("changes plan" in e["text"] for e in tick["events"]))

    def test_losing_a_planned_weapon_records_the_new_method(self):
        p = self.plot("alone")
        p["scheme"].update(room="library", method="kitchen_knife")
        p["weapon"] = "kitchen_knife"
        self.w.agents[self.a]["inv"] = {}
        method = self.r.planned_attack(self.r.new_tick(14), self.a, p)
        self.assertEqual(method, "hands")
        self.assertEqual(p["changes"][-1]["reason"], "the planned weapon is no longer carried")

    def test_first_night_cannot_bypass_reconciliation_cooldown(self):
        self.bond()
        self.r.betrayal(self.r.new_tick(12), self.a, self.b, "turns on")
        self.w.agents[self.a]["aff"][self.b] = self.w.agents[self.b]["aff"][self.a] = 9
        self.w.state["revealed"] = True
        with patch.object(self.r, "drawn_pairs", return_value=[(self.a, self.b)]), patch.object(self.r.rng, "random", return_value=0):
            self.assertEqual(self.r.intimacy_night(self.r.new_tick(23)), [])
        self.assertEqual(self.w.state["bonds"], [])

    def test_target_departure_retains_the_reason_in_history(self):
        self.plot()
        self.w.end_agent(self.b, "escaped")
        self.assertNotIn(self.a, self.w.state["plots"])
        self.assertEqual(self.w.state["plot_history"][-1]["reason"], "the target is escaped")

    def test_poison_and_shock_never_fall_back_to_an_unrelated_weapon(self):
        for kind in ("poison", "shock"):
            p = self.plot(kind)
            p["scheme"]["item"] = "rat_poison"
            self.w.agents[self.a]["inv"] = {"kitchen_knife": 1}
            p["weapon"] = "kitchen_knife"
            tick = self.r.new_tick(14)
            self.r.resolve_attacks(tick, [(self.a, {"target": self.b, "method": "kitchen_knife"})], 14)
            self.assertFalse(any(e["type"] == "attack" for e in tick["events"]))
            self.assertEqual(p["scheme"]["kind"], kind)

    def test_null_plot_and_target_changes_require_a_reason(self):
        p = self.plot()
        self.w.agents[self.a]["aff"][self.b] = -5
        self.r.update_plots(self.r.new_tick(14), {self.a: {"plot_given": True, "plot": None}}, 14)
        self.assertIs(self.w.state["plots"][self.a], p)
        self.r.update_plots(self.r.new_tick(16), {self.a: {"plot_given": True, "plot": None, "plot_reason": "the target saved my life"}}, 16)
        self.assertNotIn(self.a, self.w.state["plots"])
        self.assertEqual(self.w.state["plot_history"][-1]["reason"], "the target saved my life")

    def test_failed_special_attack_does_not_turn_into_punching(self):
        tick = self.r.new_tick(14)
        self.w.agents[self.a]["room"] = self.w.agents[self.b]["room"] = "library"
        self.r.resolve_attacks(tick, [(self.a, {"target": self.b, "method": "shock"})], 14)
        self.assertFalse(any(e["type"] == "attack" for e in tick["events"]))


class SaveRecoveryChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = SaveStore(self.tmp.name)

    def save_days(self):
        for day in range(3, 8):
            self.store.save(new_state(day))

    def test_rotates_three_good_versions_and_recovers_corrupt_current(self):
        self.save_days()
        self.assertEqual([v["day"] for v in self.store.info()["backups"]], [6, 5, 4])
        Path(self.store.path).write_text('{"broken":', encoding="utf-8")
        self.assertEqual(self.store.load()["day"], 6)
        self.assertEqual(self.store.recovery["backup"], 1)
        self.assertEqual(self.store.load()["day"], 6)
        self.assertTrue((Path(self.tmp.name) / "current.corrupt.json").exists())

    def test_skips_corrupt_backup_and_recovers_a_missing_current(self):
        self.save_days()
        Path(self.store.backup(1)).write_text('{}', encoding="utf-8")
        Path(self.store.path).unlink()
        self.assertEqual(self.store.load()["day"], 5)
        self.assertEqual(self.store.recovery["backup"], 2)

    def test_failed_save_preserves_good_current_and_never_backs_up_invalid_state(self):
        self.save_days()
        before = Path(self.store.path).read_bytes()
        with self.assertRaises(ValueError):
            self.store.save({"day": 9})
        self.assertEqual(Path(self.store.path).read_bytes(), before)
        Path(self.store.path).write_text('{}', encoding="utf-8")
        self.store.save(new_state(8))
        self.assertEqual(self.store.read(self.store.backup(1))["day"], 6)

    def test_unrecoverable_save_does_not_silently_start_a_new_game(self):
        Path(self.store.path).write_text('{}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "any valid backup"):
            self.store.load()

    def test_old_saves_without_custom_casts_remain_loadable(self):
        state = new_state(3)
        del state["cast"]
        self.store.save(state)
        self.assertEqual(World(self.store.load()).state["day"], 3)

    def test_malformed_health_cannot_replace_a_good_save(self):
        self.store.save(new_state(3))
        state = new_state(4)
        next(iter(state["agents"].values()))["hp"] = "broken"
        with self.assertRaisesRegex(ValueError, "health"):
            self.store.save(state)
        self.assertEqual(self.store.load()["day"], 3)


class DiagnosticsChecks(unittest.TestCase):
    def test_parallel_ai_calls_are_tracked_and_cleared_on_error(self):
        llm = LLM("mock")
        llm.backend = "api"
        entered, release = threading.Barrier(3), threading.Event()
        def call(*args):
            entered.wait(5)
            release.wait(5)
            raise LLMError("private server response", fatal=True)
        def run():
            try:
                llm._call("test-model", "private system", "private prompt", 10)
            except LLMError:
                pass
        with patch.object(llm, "_call_api", side_effect=call):
            threads = [threading.Thread(target=run) for _ in range(2)]
            for t in threads:
                t.start()
            try:
                entered.wait(5)
                g = generation_status({"llm": llm})
                self.assertEqual(g["state"], "waiting_on_ai")
                self.assertEqual(g["ai"]["active"], 2)
                self.assertNotIn("private", json.dumps(g))
            finally:
                release.set()
                for t in threads:
                    t.join(5)
        self.assertEqual(llm.call_activity()["active"], 0)

    def test_status_distinguishes_viewer_gm_error_and_completion(self):
        s = {"waiting_on_viewer": True}
        self.assertEqual(generation_status(s)["state"], "waiting_on_viewer")
        s["roll"] = {"id": 1}
        self.assertEqual(generation_status(s)["state"], "waiting_on_gm")
        s["error"] = "private error"
        self.assertEqual(generation_status(s)["state"], "error")
        self.assertNotIn("private", json.dumps(generation_status(s)))
        s["error"] = None
        s["done"] = True
        self.assertEqual(generation_status(s)["state"], "complete")

    def test_live_gate_and_report_use_actual_runtime_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = str(Path(tmp) / "state")
            with patch.multiple(mod, STATE_DIR=state, RUNS_DIR=str(Path(tmp) / "runs"),
                                CHECKPOINT=str(Path(state) / "checkpoint.json"), TUNING=str(Path(state) / "tuning.json")):
                game = mod.Game()
                try:
                    game.start(3, "live", "mock", rule="none", confessionals=False)
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        report = game.diagnostic_report()
                        if report["generation"]["state"] == "waiting_on_viewer":
                            break
                        time.sleep(.02)
                    self.assertEqual(report["generation"]["state"], "waiting_on_viewer")
                    self.assertGreater(report["generation"]["generated_ticks"], 0)
                    self.assertNotIn("agents", json.dumps(report))
                    self.assertNotIn("ANTHROPIC", json.dumps(report))
                finally:
                    game.stop()
                    game.session["thread"].join(10)
                    self.assertFalse(game.session["thread"].is_alive())


if __name__ == "__main__":
    unittest.main(verbosity=2)
