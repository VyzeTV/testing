"""Session lifecycle regressions. Run: python tests/session_check.py (no AI calls)."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from murder import session as mod


class SessionChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mc_session_")
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.state = base / "state"
        self.runs = base / "runs"
        self.cp = self.state / "checkpoint.json"
        self.paths = patch.multiple(mod, STATE_DIR=str(self.state), RUNS_DIR=str(self.runs),
                                    CHECKPOINT=str(self.cp), TUNING=str(self.state / "tuning.json"))
        self.paths.start()
        self.addCleanup(self.paths.stop)
        self.game = mod.Game()
        self.addCleanup(self.shutdown)

    def shutdown(self):
        self.game.stop()
        sess = self.game.session
        if sess and isinstance(sess.get("thread"), threading.Thread):
            sess["thread"].join(timeout=10)
            self.assertFalse(sess["thread"].is_alive())

    def checkpoint(self):
        self.cp.write_text(json.dumps({"day": 3, "hour": 10, "idx": 0, "v": 2,
                                       "state": self.game.load_current()}), encoding="utf-8")
        Path(str(self.cp) + ".tmp").write_text("partial", encoding="utf-8")
        d = self.runs / "day_03"
        d.mkdir(exist_ok=True)
        (d / "ticks.partial.jsonl").write_text('{"idx":0,"hour":10}\n', encoding="utf-8")

    def test_unsafe_slot_names_never_touch_files(self):
        self.game.save_slot("keep")
        before = Path(self.game.current_path()).read_bytes()
        names = (".", "..", "...", " . ", " .. ", "", "   ", "../other", "a/b",
                 "a\\b", "C:other", "save.", "CON", "nul.txt", "COM1", "LPT9.log",
                 "a" * 41)
        for name in names:
            for operation in (self.game.save_slot, self.game.load_slot, self.game.delete_slot):
                with self.subTest(name=name, operation=operation.__name__):
                    with patch.object(mod.shutil, "rmtree") as remove:
                        with self.assertRaises(ValueError):
                            operation(name)
                        remove.assert_not_called()
        self.assertEqual(Path(self.game.current_path()).read_bytes(), before)
        self.assertTrue((self.state / "slots" / "keep" / "current.json").exists())

    def test_slot_paths_reject_directory_redirects(self):
        realpath = os.path.realpath
        base = os.path.normcase(str(self.state / "slots"))
        child = os.path.normcase(str(self.state / "slots" / "redirect"))
        for redirected in (base, child):
            def resolve(path, *args, **kwargs):
                if os.path.normcase(str(path)) == redirected:
                    return str(self.state)
                return realpath(path, *args, **kwargs)
            for operation in (self.game.save_slot, self.game.load_slot, self.game.delete_slot):
                with self.subTest(redirected=redirected, operation=operation.__name__):
                    with patch.object(mod.os.path, "realpath", side_effect=resolve):
                        with patch.object(mod.shutil, "rmtree") as remove:
                            with self.assertRaises(ValueError):
                                operation("redirect")
                            remove.assert_not_called()

    def test_normal_slot_save_load_delete(self):
        name = "Season 1 - day_03.v2"
        state = self.game.load_current()
        state["slot_probe"] = "saved"
        self.game.save_current(state)
        self.game.save_slot(name)
        state["slot_probe"] = "changed"
        self.game.save_current(state)
        self.game.load_slot(name)
        self.assertEqual(self.game.load_current()["slot_probe"], "saved")
        self.game.delete_slot(name)
        self.assertFalse(Path(self.game._slot_path(name)).exists())
        self.assertTrue(Path(self.game.current_path()).exists())

    def test_reset_removes_checkpoint(self):
        self.checkpoint()
        self.game.new_game(3, False)
        self.assertIsNone(self.game.checkpoint_info())
        self.assertFalse(Path(str(self.cp) + ".tmp").exists())
        self.assertIsNone(self.game.status()["checkpoint"])

    def test_load_slot_removes_old_checkpoint(self):
        self.game.save_slot("before")
        self.checkpoint()
        self.game.load_slot("before")
        self.assertIsNone(self.game.checkpoint_info())

    def recorded_day(self):
        d = self.runs / "day_03"
        d.mkdir(exist_ok=True)
        (d / "meta.json").write_text('{"day":3,"ticks":1}', encoding="utf-8")
        (self.state / "day_03_start.json").write_text(
            json.dumps(self.game.load_current()), encoding="utf-8")

    def test_rewind_removes_checkpoint(self):
        self.checkpoint()
        self.recorded_day()
        self.game.rewind()
        self.assertIsNone(self.game.checkpoint_info())

    def test_day_start_removes_checkpoint(self):
        self.checkpoint()
        self.recorded_day()
        self.game.goto_day_start(3)
        self.assertIsNone(self.game.checkpoint_info())

    def test_failed_serialization_preserves_save(self):
        before = Path(self.game.current_path()).read_bytes()
        with self.assertRaises(TypeError):
            self.game.save_current({"bad": object()})
        self.assertEqual(Path(self.game.current_path()).read_bytes(), before)
        self.assertEqual(list(self.state.glob("current-*.tmp")), [])

    def test_failed_replace_preserves_save(self):
        before = Path(self.game.current_path()).read_bytes()
        with patch.object(mod.os, "replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                self.game.save_current({"day": 99})
        self.assertEqual(Path(self.game.current_path()).read_bytes(), before)
        self.assertEqual(list(self.state.glob("current-*.tmp")), [])

    def test_readers_observe_complete_saves(self):
        barrier = threading.Barrier(3)
        errors = []
        state = self.game.load_current()

        def writer():
            try:
                barrier.wait(timeout=5)
                for n in range(15):
                    self.game.save_current(dict(state, probe=n))
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                barrier.wait(timeout=5)
                for _ in range(30):
                    self.assertEqual(self.game.load_current()["day"], 3)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer), threading.Thread(target=reader)]
        for t in threads:
            t.start()
        barrier.wait(timeout=5)
        for t in threads:
            t.join(timeout=10)
            self.assertFalse(t.is_alive())
        self.assertEqual(errors, [])

    def test_missing_resume_recording_surfaces_error(self):
        self.checkpoint()
        (self.runs / "day_03" / "ticks.partial.jsonl").unlink()
        with contextlib.redirect_stderr(io.StringIO()):
            self.game.start(3, "live", "mock", resume=True)
            sess = self.game.session
            sess["thread"].join(timeout=5)
        self.assertFalse(sess["thread"].is_alive())
        self.assertIn("FileNotFoundError", sess["error"])

    def test_runner_construction_failure_closes_recording(self):
        self.checkpoint()
        with patch.object(mod, "DayRunner", side_effect=RuntimeError("bad constructor")):
            with contextlib.redirect_stderr(io.StringIO()):
                self.game.start(3, "live", "mock")
                sess = self.game.session
                sess["thread"].join(timeout=5)
        self.assertIn("bad constructor", sess["error"])
        self.assertIsNone(self.game.checkpoint_info())
        # On Windows an open recording cannot be unlinked.
        (self.runs / "day_03" / "ticks.partial.jsonl").unlink()

    def stubborn_session(self):
        thread = Mock()
        thread.is_alive.return_value = True
        sess = {"thread": thread, "mode": "live", "done": False,
                "aborted": False, "error": None, "stop": False}
        self.game.session = sess
        return sess

    def test_reset_timeout_preserves_files_and_session(self):
        self.checkpoint()
        sess = self.stubborn_session()
        before = Path(self.game.current_path()).read_bytes()
        with self.assertRaisesRegex(ValueError, "still stopping"):
            self.game.new_game(1)
        self.assertIs(self.game.session, sess)
        self.assertTrue(sess["stop"])
        self.assertTrue(self.cp.exists())
        self.assertTrue((self.runs / "day_03" / "ticks.partial.jsonl").exists())
        self.assertEqual(Path(self.game.current_path()).read_bytes(), before)

    def test_replacement_timeout_does_not_start_worker(self):
        sess = self.stubborn_session()
        with patch.object(mod, "LLM") as llm:
            with self.assertRaisesRegex(ValueError, "still stopping"):
                self.game.start(3, "live", "mock")
        llm.assert_not_called()
        self.assertIs(self.game.session, sess)

    def test_busy_until_worker_exits_even_after_error(self):
        sess = self.stubborn_session()
        sess["error"] = "failed"
        self.assertTrue(self.game._busy())
        with self.assertRaisesRegex(ValueError, "Stop or finish"):
            self.game.save_slot("busy")

    def test_start_joins_previous_worker_before_replacement(self):
        finished = threading.Event()
        sess = {"mode": "live", "done": False, "aborted": False,
                "error": None, "stop": False}

        def worker():
            with self.game.cv:
                self.game.cv.wait_for(lambda: sess["stop"], timeout=5)
            finished.set()

        sess["thread"] = threading.Thread(target=worker)
        self.game.session = sess
        sess["thread"].start()

        def next_worker(new):
            self.assertTrue(finished.is_set())
            self.assertFalse(sess["thread"].is_alive())
            new["aborted"] = True

        with patch.object(self.game, "_run_live", side_effect=next_worker) as run:
            self.game.start(3, "live", "mock")
            self.game.session["thread"].join(timeout=5)
        run.assert_called_once()
        self.assertTrue(self.game.session["aborted"])

    def test_simultaneous_starts_do_not_overlap(self):
        barrier = threading.Barrier(3)
        active, maximum = 0, 0
        errors = []

        def worker(sess):
            nonlocal active, maximum
            with self.game.cv:
                active += 1
                maximum = max(maximum, active)
                self.game.cv.wait_for(lambda: sess["stop"], timeout=5)
                active -= 1
                sess["aborted"] = True

        def start():
            try:
                barrier.wait(timeout=5)
                self.game.start(3, "live", "mock")
            except Exception as e:
                errors.append(e)

        with patch.object(self.game, "_run_live", side_effect=worker):
            callers = [threading.Thread(target=start) for _ in range(2)]
            for t in callers:
                t.start()
            barrier.wait(timeout=5)
            for t in callers:
                t.join(timeout=10)
                self.assertFalse(t.is_alive())
            self.shutdown()
        self.assertEqual(errors, [])
        self.assertEqual(maximum, 1)

    def test_live_day_can_stop_resume_and_commit(self):
        self.game.start(3, "live", "mock", confessionals=False, rule="none")
        original = self.game.session
        with self.game.cv:
            ready = self.game.cv.wait_for(
                lambda: len(original["ticks"]) >= 2 or original["error"], timeout=30)
        self.assertTrue(ready, "mock day did not produce ticks")
        self.assertIsNone(original["error"])
        self.game.stop()
        original["thread"].join(timeout=30)
        self.assertFalse(original["thread"].is_alive())
        self.assertTrue(original["aborted"])
        self.assertIsNotNone(self.game.checkpoint_info())
        count = len(original["ticks"])
        self.game.start(3, "live", "mock", resume=True, confessionals=False, rule="none")
        resumed = self.game.session
        self.game.fast_forward()
        resumed["thread"].join(timeout=30)
        self.assertFalse(resumed["thread"].is_alive())
        self.assertIsNone(resumed["error"])
        self.assertTrue(resumed["done"])
        self.assertGreater(len(resumed["ticks"]), count)
        self.assertEqual(resumed["ticks"][:count], original["ticks"])
        self.assertEqual(self.game.load_current()["day"], 4)
        self.assertIsNone(self.game.checkpoint_info())
        self.assertTrue((self.runs / "day_03" / "ticks.jsonl").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
