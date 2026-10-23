"""Roster selection, save compatibility, and complete mock days with the added characters."""
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
os.environ.setdefault("MC_DATA_DIR", tempfile.mkdtemp(prefix="mc_casting_"))
from murder.data_cast import CHARACTERS, DEFAULT_DRIVES, DEFAULT_ROUTES, LEGACY_CAST_IDS
from murder.data_female_cast import FEMALE_ADDITIONS
from murder.data_guest_cast import GUEST_ADDITIONS
from murder.data_male_cast import MALE_ADDITIONS
from murder.casting import select_cast, slot_for
from murder.world import World, new_state, upgrade_state, BEDROOMS
from murder.engine import DayRunner
from murder.llm import LLM
from murder.looks import LOOKS, OUTFITS
from murder.data_world import ITEMS
from murder.mind import FACETS, VALUES
from murder import session as mod


class CastingChecks(unittest.TestCase):
    def test_all_added_profiles_are_complete_and_have_usable_items_and_looks(self):
        self.assertEqual(set(FEMALE_ADDITIONS), {"itsumi", "tsutsumi", "soura", "akira", "nao"})
        self.assertEqual(sum(c["gender"] == "female" for c in CHARACTERS.values()), 11)
        self.assertEqual(set(MALE_ADDITIONS), {"accio", "jackal", "vincent", "nathan", "katsuo"})
        self.assertEqual(sum(slot_for(c) == "male" for c in CHARACTERS.values()), 10)
        for cid, c in (FEMALE_ADDITIONS | GUEST_ADDITIONS | MALE_ADDITIONS).items():
            with self.subTest(cid=cid):
                for field in ("persona", "secret", "speech", "candor", "goals", "mock_lines", "facets", "values"):
                    self.assertTrue(c[field])
                self.assertGreaterEqual(c["age"], 18)
                self.assertIn(cid, DEFAULT_DRIVES)
                self.assertIn(cid, DEFAULT_ROUTES)
                self.assertIn(cid, LOOKS)
                self.assertIn(cid, OUTFITS)
                self.assertTrue(set(c["inv"]) <= set(ITEMS))
                self.assertEqual(c["aff"], {})
                self.assertNotIn("vincent", c["aff"])
                if cid in MALE_ADDITIONS:
                    self.assertEqual(slot_for(c), "male")
                    self.assertEqual(c["pron"], "he")
                    self.assertEqual(set(c["facets"]), set(FACETS))
                    self.assertTrue(set(c["values"]) <= set(VALUES))

    def test_random_selection_keeps_four_of_each_slot_without_duplicates(self):
        seen = set()
        variants = {"female": set(), "male": set()}
        for seed in range(60):
            ids = select_cast(random.Random(seed))
            self.assertEqual(len(ids), 8)
            self.assertEqual(len(set(ids)), 8)
            self.assertEqual(len({cid for cid in ids if slot_for(CHARACTERS[cid]) == "male"}), 4)
            seen.update(ids)
            women = {cid for cid in ids if slot_for(CHARACTERS[cid]) == "female"}
            self.assertEqual(len(women), 4)

            for slot in variants:
                variants[slot].add(tuple(sorted(c for c in ids if slot_for(CHARACTERS[c]) == slot)))
        self.assertEqual(seen, set(CHARACTERS))
        for slot, lineups in variants.items():
            self.assertGreater(len(lineups), 20, slot)

    def test_seed_controls_casting_and_unique_bedrooms(self):
        a = new_state(1, True, randomize_cast=True, rng=random.Random(123))
        b = new_state(1, True, randomize_cast=True, rng=random.Random(123))
        self.assertEqual(a, b)
        for shuffle in (False, True):
            for seed in range(12):
                state = new_state(3, shuffle, randomize_cast=True, rng=random.Random(seed))
                self.assertEqual({c["home"] for c in state["cast"].values()}, set(BEDROOMS))
                for cid, agent in state["agents"].items():
                    self.assertEqual(agent["room"], state["cast"][cid]["home"])
                    self.assertEqual(set(agent["aff"]), set(state["agents"]) - {cid})
                    self.assertTrue(all(v == 0 for v in agent["aff"].values()))
                    self.assertEqual(agent["memory"]["diary"], [])

    def test_legacy_fixtures_and_castless_saves_do_not_gain_new_participants(self):
        state = new_state(3)
        self.assertEqual(tuple(state["cast"]), LEGACY_CAST_IDS)
        old = copy.deepcopy(state)
        del old["cast"]
        restored = upgrade_state(old)
        self.assertEqual(set(restored["cast"]), set(state["cast"]))
        randomized = new_state(1, randomize_cast=True, rng=random.Random(8))
        before = list(randomized["cast"])
        for _ in range(5):
            randomized = World(json.loads(json.dumps(randomized))).dump()
            self.assertEqual(list(randomized["cast"]), before)

    def test_cast_profiles_are_independent_of_roster_templates(self):
        state = new_state(1, randomize_cast=True, rng=random.Random(8))
        cid = next(cid for cid in state["cast"] if cid in FEMALE_ADDITIONS)
        original = copy.deepcopy(CHARACTERS[cid])
        state["cast"][cid]["facets"]["anger"] = 1
        state["cast"][cid]["mock_lines"].append("local line")
        self.assertEqual(CHARACTERS[cid], original)

    def test_selection_can_accommodate_future_male_roster_additions(self):
        extra = dict(CHARACTERS["noah"], name="Future male", short="Future")
        with patch.dict(CHARACTERS, {"future_male": extra}):
            selections = [select_cast(random.Random(seed)) for seed in range(20)]
            self.assertTrue(any("future_male" in ids for ids in selections))
            self.assertTrue(all(sum(slot_for(CHARACTERS[c]) == "male" for c in ids) == 4 for ids in selections))

    def test_complete_days_cover_every_added_character_without_live_errors(self):
        remaining = set(FEMALE_ADDITIONS) | set(GUEST_ADDITIONS) | set(MALE_ADDITIONS)
        for seed in range(30):
            state = new_state(3, True, randomize_cast=True, rng=random.Random(seed))
            selected = set(state["cast"]) & remaining
            if not selected:
                continue
            with self.subTest(seed=seed, characters=selected):
                world = World(state)
                ticks = []
                runner = DayRunner(world, LLM("mock"), ticks.append, rule_mode="none", seed=seed + 500)
                count = runner.run()
                self.assertGreater(count, 0)
                self.assertTrue(ticks)
                self.assertFalse(any(t.get("live_error") for t in ticks))
                self.assertTrue(all("live" in t for t in ticks))
                for cid in selected:
                    self.assertIn(f"clothes_{cid}", world.state["custom_items"])
                    self.assertIn(f"swimsuit_{cid}", world.state["custom_items"])
                    self.assertIn(cid, ticks[0]["state"]["agents"])
            remaining -= selected
            if not remaining:
                break
        self.assertEqual(remaining, set())

    def test_childhood_friends_recognize_each_other_without_a_forced_romance(self):
        state = next(s for seed in range(100) if {"akira", "vincent"} <= set((s := new_state(1, randomize_cast=True, rng=random.Random(seed)))["cast"]))
        w = World(json.loads(json.dumps(state)))
        r = DayRunner(w, LLM("mock"), lambda tick: None, rule_mode="none", seed=20)
        for cid in ("akira", "vincent"):
            prompt = " ".join(r.intro_decision_lines(cid, 8))
            self.assertIn("childhood friends", prompt)
            self.assertNotIn("seven strangers", prompt)
            other = "vincent" if cid == "akira" else "akira"
            self.assertEqual(w.agents[cid]["aff"][other], 0)
        self.assertFalse(w.state.get("bonds"))

    def test_day_one_does_not_introduce_absent_childhood_friend(self):
        state = next(s for seed in range(100) if "akira" in (s := new_state(1, randomize_cast=True, rng=random.Random(seed)))["cast"] and "vincent" not in s["cast"])
        r = DayRunner(World(state), LLM("mock"), lambda tick: None, rule_mode="none", seed=20)
        self.assertNotIn("Vincent", " ".join(r.intro_decision_lines("akira", 8)))


class GuestChecks(unittest.TestCase):
    def setUp(self):
        self.state = next(s for seed in range(100) if "reiko" in (s := new_state(3, randomize_cast=True, rng=random.Random(seed)))["cast"])
        self.world = World(self.state)
        self.runner = DayRunner(self.world, LLM("mock"), lambda tick: None, rule_mode="none", seed=900)

    def test_reiko_identity_slot_and_blindness_survive_reload(self):
        w = World(json.loads(json.dumps(self.world.dump())))
        self.assertEqual(w.cast["reiko"]["pron"], "she")
        self.assertEqual(w.cast["reiko"]["gender"], "female")
        self.assertEqual(w.casting_slot("reiko"), "male")
        runner = DayRunner(w, LLM("mock"), lambda tick: None, rule_mode="none", seed=900)
        self.assertTrue(runner.blind("reiko"))
        self.assertFalse(runner.has_cond("reiko", "blinded"))
        self.assertEqual(w.cast["reiko"]["height_cm"], 167)

    def test_departure_and_replacement_use_casting_slot(self):
        self.runner.raft_away(self.runner.new_tick(12), ["reiko"], False)
        self.assertEqual(self.world.state["vacancies"][0]["gender"], "male")
        cid = self.world.add_newcomer({"name": "Guest", "gender": "female", "casting_slot": "male", "pron": "she"})
        self.assertEqual(self.world.state["vacancies"], [])
        self.assertEqual(self.world.casting_slot(cid), "male")
        self.assertEqual(self.world.cast[cid]["pron"], "she")

    def test_returning_reiko_consumes_the_male_vacancy(self):
        r, w = self.runner, self.world
        tick = r.new_tick(12)
        r.raft_away(tick, ["reiko"], False)
        crew = r.outside()["crews"][-1]
        r.raft_returns(tick, crew)
        self.assertIn("reiko", w.agents)
        self.assertEqual(w.state["vacancies"], [])

    def test_blind_observer_hears_without_visual_identification(self):
        r, w = self.runner, self.world
        actor = next(c for c in w.agents if c != "reiko")
        tile = r.perc().nav.nominal("library", actor, 3)
        self.assertEqual(r.perc().witnesses(tile, {"reiko": tile}, blind=["reiko"]), {"reiko": "heard"})
        self.assertEqual(r.perc().witnesses(tile, {actor: tile}), {actor: "saw"})
        self.assertIsNone(r.believe("reiko", {"k": "at", "s": actor, "r": "library", "t0": 84, "src": "seen"}))
        self.assertIsNotNone(r.believe("reiko", {"k": "at", "s": actor, "r": "library", "t0": 84, "src": "told", "c": .6}))
        for a in w.agents.values():
            a["room"] = "library"
        with patch.object(r, "event_witnesses", return_value=["reiko"]):
            r.log_event(r.new_tick(12), {"type": "attack", "vis": "public", "room": "library", "text": "A secretly named attacker uses a red knife."}, witnesses=["reiko"], actor=actor)
        self.assertFalse(any("red knife" in m for m in w.agents["reiko"]["memory"]["recent"]))
        self.assertFalse(any("reiko" in n["knows"] for n in w.state.get("news", [])))
        self.assertFalse(any(b["src"] == "seen" for b in r.beliefs("reiko")))
        w.agents[actor]["lit"] = True
        r.witness("reiko", {"who": actor, "type": "arrive", "hour": 12, "room": "library"})
        self.assertIn("without visual identification", w.agents["reiko"]["memory"]["recent"][-1])

    def test_reiko_is_not_a_visual_case_witness_or_clue_reader(self):
        r, w = self.runner, self.world
        killer, victim = [c for c in w.agents if c != "reiko"][:2]
        tick = r.new_tick(12)
        r.open_case(tick, "murder", victim, culprit=killer, wkind="hands", room="library", hour=12, witnesses=["reiko"])
        case = w.state["case"]
        self.assertNotIn("reiko", case["witnesses"])
        w.agents["reiko"]["room"] = "library"
        r.reveal_clues(tick, "reiko")
        self.assertFalse(any("reiko" in c["found_by"] for c in case["clues"]))
        self.assertFalse(r.fine_visible("reiko", {"kind": "trace"}))

    def test_death_opens_a_male_slot_and_no_visual_prompt_leaks(self):
        r, w = self.runner, self.world
        prompt = r.decision_prompt("reiko", 12)
        self.assertNotIn("VISIBLE ITEMS HERE:", prompt)
        self.assertIn("You are blind", prompt)
        w.agents["reiko"]["inv"]["binoculars"] = 1
        self.assertFalse(r.has_optics("reiko"))
        self.assertTrue(r.in_dark("reiko"))
        tick = r.new_tick(12)
        r.open_case(tick, "accident", "reiko", wkind="hands", room="library", hour=12, cause="an accident")
        r.announce_body(tick, 12, forced=True)
        self.assertEqual(w.state["vacancies"][-1]["gender"], "male")


class NewSeasonChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        state = str(Path(self.tmp.name) / "state")
        self.paths = patch.multiple(mod, STATE_DIR=state, RUNS_DIR=str(Path(self.tmp.name) / "runs"),
                                    CHECKPOINT=str(Path(state) / "checkpoint.json"), TUNING=str(Path(state) / "tuning.json"))
        self.paths.start()
        self.addCleanup(self.paths.stop)

    def test_initial_creation_and_each_new_season_request_random_casting(self):
        with patch.object(mod, "new_state", wraps=new_state) as build:
            game = mod.Game()
            self.assertTrue(build.call_args.kwargs["randomize_cast"])
            for day in (1, 3):
                game.new_game(day, False)
                self.assertTrue(build.call_args.kwargs["randomize_cast"])
                self.assertEqual(len(game.load_current()["cast"]), 8)
        cast = game.load_current()["cast"]
        with patch.object(mod, "new_state", wraps=new_state) as build:
            loaded = mod.Game()
            build.assert_not_called()
            self.assertEqual(loaded.load_current()["cast"], cast)

    def test_new_season_drops_scenario_cast_seeds_for_absent_characters(self):
        game = mod.Game()
        old = new_state(3)
        old["scenario"] = {"title": "Keep the premise", "premise": "A storm is coming.", "twist": None,
                           "rules": [], "relationships": [{"a": "seul", "b": "vixen", "kind": "friends", "value": 5, "text": "Old friends"}],
                           "secrets": [{"id": "seul", "text": "A seeded secret"}], "items": [], "events": []}
        game.save_current(old)
        replacement = next(s for seed in range(100) if "vixen" not in (s := new_state(1, randomize_cast=True, rng=random.Random(seed)))["cast"])
        self.assertNotIn("vixen", replacement["cast"])
        with patch.object(mod, "new_state", return_value=replacement):
            game.new_game(1, True)
        current = game.load_current()
        self.assertEqual(current["scenario"]["title"], "Keep the premise")
        self.assertEqual(current["scenario"]["relationships"], [])
        self.assertTrue(all(r["id"] in current["cast"] for r in current["scenario"]["secrets"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
