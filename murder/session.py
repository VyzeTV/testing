"""Game session manager: persistence, live generation with gating, replay, fast-forward."""
import copy
import glob
import json
import os
import shutil
import threading
import time

from .engine import DayRunner, Stop
from .llm import LLM, LLMError
from .world import World, new_state, upgrade_state, week_of
from . import export as exportlib
from . import scenario as scn
from . import settings as settings_mod

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("MC_DATA_DIR") or BASE      # tests point this at a scratch copy so real saves are never touched
STATE_DIR = os.path.join(DATA, "state")
RUNS_DIR = os.path.join(DATA, "runs")
CHECKPOINT = os.path.join(STATE_DIR, "checkpoint.json")
TUNING = os.path.join(STATE_DIR, "tuning.json")
BUFFER = 2  # live generation stays this many ticks ahead of the viewer's playback cursor (two, so a heavy block of model calls is usually ready before it is due)


def day_dir(day):
    return os.path.join(RUNS_DIR, f"day_{day:02d}")



CHECKPOINT_V = 2          # 2: the night is bedtime (22), blocks 23/25/27/29 and dawn (31)


def resume_hour(cp):
    """The hour a saved day picks up after. An old checkpoint (no version) at 23 was the old single night turn, which ran before bedtime: replay from bedtime."""
    if cp.get("v") is None and cp.get("hour") == 23:
        return 21
    return cp["hour"]

class Game:
    def __init__(self):
        self.cv = threading.Condition()
        self.session = None
        self.tuning = {}
        os.makedirs(STATE_DIR, exist_ok=True)
        self.load_tuning()
        os.makedirs(RUNS_DIR, exist_ok=True)
        if not os.path.exists(self.current_path()):
            self.save_current(new_state(3))

    # ---------- persistence ----------
    def current_path(self):
        return os.path.join(STATE_DIR, "current.json")

    def save_current(self, state):
        with open(self.current_path(), "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=1)

    def load_current(self):
        with open(self.current_path(), "r", encoding="utf-8") as f:
            return upgrade_state(json.load(f))

    def recorded_days(self):
        out = []
        for p in sorted(glob.glob(os.path.join(RUNS_DIR, "day_*", "meta.json"))):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    out.append(json.load(f))
            except Exception:
                pass
        return sorted(out, key=lambda m: m["day"])

    # ---------- status ----------
    def status(self):
        with self.cv:
            s = self.session
            sess = None
            if s:
                sess = {"day": s["day"], "mode": s["mode"], "backend": s["backend"], "step": s["step"],
                        "done": s["done"], "error": s["error"], "aborted": s["aborted"], "ff": s["ff"],
                        "known": len(s["ticks"]), "usage": s.get("usage")}
        from .llm import find_api_key
        import shutil as _sh
        cur = self.load_current()
        alive = [k for k, v in cur["agents"].items() if v.get("status", "alive") == "alive"]
        return {
            "next_day": cur["day"],
            "new_week": (cur["day"] - 1) % cur.get("week_len", 7) == 0,
            "week_len": cur.get("week_len", 7),
            "deadline_day": cur.get("deadline_day"),
            "vacancies": cur.get("vacancies", []),
            "alive": len(alive),
            "case_open": bool(cur.get("case")),
            "over": cur.get("over"),
            "scenario": ((cur.get("scenario") or {}).get("title") or "custom") if cur.get("scenario") else None,
            "revealed": cur.get("revealed", True),
            "checkpoint": (lambda cp: cp if cp and cp["day"] == cur["day"] else None)(self.checkpoint_info()),
            "gm_pending": len(cur.get("gm_pending", [])),
            "season_calls": sum(((m.get("usage") or {}).get("calls", 0)) for m in self.recorded_days()),
            "can_rewind": self.can_rewind(),
            "slots": self.list_slots(),
            "autodir": bool(self.session["autodir"]) if (self.session and self.session.get("mode") == "live") else getattr(self, "pref_autodir", False),
            "day_starts": sorted(int(os.path.basename(p)[4:6]) for p in glob.glob(os.path.join(STATE_DIR, "day_*_start.json"))),
            "recorded": [{"day": m["day"], "ticks": m["ticks"], "backend": m.get("backend"), "step": m.get("step"),
                          "usage": m.get("usage")} for m in self.recorded_days()],
            "session": sess,
            "backends": {"cli": bool(_sh.which("claude")), "api": bool(find_api_key()), "mock": True},
        }

    # ---------- newcomers ----------
    def add_newcomer(self, spec):
        with self.cv:
            s = self.session
            if s and s["mode"] == "live" and not s["done"] and not s["aborted"] and not s["error"]:
                raise ValueError("Stop or finish the live day before adding a newcomer.")
        state = self.load_current()
        w = World(state)
        if w.state.get("no_newcomers"):
            raise ValueError("No newcomers can arrive: with NeoVi made a contestant, nobody is left to keep the house.")
        if not w.state["vacancies"]:
            raise ValueError("There are no vacancies: the island already has 8 participants.")
        if spec.get("ai"):
            spec = dict(spec, **self.develop_newcomer(spec, spec.get("backend") or "cli"))
        if not (spec.get("name") or "").strip():
            raise ValueError("A name is required.")
        gender = spec.get("gender")
        if gender not in ("male", "female"):
            raise ValueError("Choose male or female.")
        if gender not in [v["gender"] for v in w.state["vacancies"]]:
            need = ", ".join(sorted({v["gender"] for v in w.state["vacancies"]}))
            raise ValueError(f"The show needs a newcomer who is: {need}.")
        cid = w.add_newcomer(spec)
        portrait = spec.get("portrait")
        if portrait and "," in portrait:
            import base64, io
            from PIL import Image
            raw = base64.b64decode(portrait.split(",", 1)[1])
            im = Image.open(io.BytesIO(raw)).convert("RGB")
            side = min(im.size)
            left, top = (im.width - side) // 2, (im.height - side) // 4
            im = im.crop((left, max(0, top), left + side, max(0, top) + side)).resize((200, 200))
            im.save(os.path.join(BASE, "static", "portraits", f"{cid}.png"))
        self.save_current(w.dump())
        return cid

    NEWCOMER_FIELDS = ("role", "age", "origin", "items", "persona", "secret", "likes", "dislikes", "speech", "candor", "goals")

    def develop_newcomer(self, spec, backend="cli"):
        """Let the AI fill in the blanks of a newcomer the user has sketched. Anything the user wrote is kept untouched."""
        cur = self.load_current()
        name = (spec.get("name") or "").strip()
        if not name:
            raise ValueError("A name is required.")
        if spec.get("gender") not in ("male", "female"):
            raise ValueError("Choose male or female.")
        given = {k: str(spec.get(k)).strip() for k in self.NEWCOMER_FIELDS if str(spec.get(k) or "").strip()}
        llm = LLM(backend=backend)
        alive = [f"{c['name']} ({c['role']}; {c['persona'][:90]})" for k, c in cur["cast"].items() if cur["agents"].get(k, {}).get("status") == "alive"]
        system = ("You are the casting writer of a dark reality-TV drama called Murder Channel (a deadly game show on a sealed island). A producer has sketched a new participant; "
                  "you flesh out ONLY the blanks, in the same style as the existing cast sheets. Never change or contradict what the producer wrote, and never invent a different person. "
                  "Reply with a single JSON object and nothing else.")
        user = (f"New participant: {name}, {spec.get('gender')}. What the producer has decided: {json.dumps(given, ensure_ascii=False) or 'nothing else'}.\n"
                f"Current cast (for contrast, do not copy them): {'; '.join(alive)}.\n"
                "Fill every missing field. persona = personality AND backstory (what made them famous, how they act, a vivid specific history, 3-5 sentences). "
                "secret = something they hide that could be used against them. candor = how they behave under stress. goals = what they want on the island. "
                "items = up to 5 starting items, comma separated. drive = their hidden drive, one of survivor, protector, saboteur, schemer, avenger, thrill, romantic, seeker, nihilist, martyr.\n"
                'Reply as JSON: {"role": "", "age": 0, "origin": "", "items": "", "persona": "", "secret": "", "likes": "", "dislikes": "", "speech": "", "candor": "", "goals": "", "drive": ""}')
        r = llm.host_json(system, user, {"kind": "develop"})
        out = {}
        for k in self.NEWCOMER_FIELDS:
            if k not in given and r.get(k) not in (None, "", 0):
                out[k] = str(r[k]).strip()[:700] if k != "age" else r[k]
        if r.get("drive"):
            out["drive"] = str(r["drive"]).strip().lower()
        return out

    # ---------- the director (game master) ----------
    GM_TYPES = ("rumor", "item", "whisper", "announce", "twist", "event", "schedule", "goal", "propose")

    def gm_action(self, act):
        if act.get("type") not in self.GM_TYPES:
            raise ValueError("Unknown director action.")
        act = {k: v for k, v in act.items() if k in ("type", "about", "claim", "to", "tone", "lie", "room", "name", "text", "id", "op", "at", "kind", "a", "b", "days")}
        with self.cv:
            s = self.session
            if s and s["mode"] == "live" and not s["done"] and not s["aborted"] and not s["error"]:
                s["gm"].append(act)
                return "queued for the next turn"
        cur = self.load_current()
        cur.setdefault("gm_pending", []).append(act)
        self.save_current(cur)
        return "queued for the start of the next day"

    # ---------- save slots ----------
    @staticmethod
    def _slot_name(name):
        import re
        n = re.sub(r"[^A-Za-z0-9 _.-]", "", str(name or "")).strip()[:40]
        if not n:
            raise ValueError("Give the save a name.")
        return n

    def _busy(self):
        with self.cv:
            s = self.session
            return bool(s and s["mode"] == "live" and not s["done"] and not s["aborted"] and not s["error"])

    def list_slots(self):
        out = []
        base = os.path.join(STATE_DIR, "slots")
        for d in sorted(glob.glob(os.path.join(base, "*", "meta.json"))):
            try:
                with open(d, "r", encoding="utf-8") as f:
                    out.append(json.load(f))
            except Exception:
                pass
        return out

    def save_slot(self, name):
        n = self._slot_name(name)
        if self._busy():
            raise ValueError("Stop or finish the live day first.")
        dst = os.path.join(STATE_DIR, "slots", n)
        shutil.rmtree(dst, ignore_errors=True)
        os.makedirs(dst, exist_ok=True)
        shutil.copyfile(self.current_path(), os.path.join(dst, "current.json"))
        if os.path.isdir(RUNS_DIR):
            shutil.copytree(RUNS_DIR, os.path.join(dst, "runs"), ignore=shutil.ignore_patterns("_rewound"))
        os.makedirs(os.path.join(dst, "starts"), exist_ok=True)
        for p in glob.glob(os.path.join(STATE_DIR, "day_*_start.json")):
            shutil.copyfile(p, os.path.join(dst, "starts", os.path.basename(p)))
        cur = self.load_current()
        meta = {"name": n, "day": cur["day"], "alive": sum(1 for v in cur["agents"].values() if v.get("status", "alive") == "alive"),
                "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        with open(os.path.join(dst, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f)
        return meta

    def load_slot(self, name):
        n = self._slot_name(name)
        src = os.path.join(STATE_DIR, "slots", n)
        if not os.path.exists(os.path.join(src, "current.json")):
            raise ValueError("No such save.")
        if self._busy():
            raise ValueError("Stop or finish the live day first.")
        with self.cv:
            self.session = None
        shutil.rmtree(RUNS_DIR, ignore_errors=True)
        if os.path.isdir(os.path.join(src, "runs")):
            shutil.copytree(os.path.join(src, "runs"), RUNS_DIR)
        else:
            os.makedirs(RUNS_DIR, exist_ok=True)
        for p in glob.glob(os.path.join(STATE_DIR, "day_*_start.json")):
            os.remove(p)
        for p in glob.glob(os.path.join(src, "starts", "*.json")):
            shutil.copyfile(p, os.path.join(STATE_DIR, os.path.basename(p)))
        shutil.copyfile(os.path.join(src, "current.json"), self.current_path())
        return n

    def delete_slot(self, name):
        n = self._slot_name(name)
        shutil.rmtree(os.path.join(STATE_DIR, "slots", n), ignore_errors=True)

    def goto_day_start(self, day):
        """Go back to the start of any earlier day (not only the last): later recordings are set aside."""
        if self._busy():
            raise ValueError("Stop or finish the live day first.")
        day = int(day)
        src = os.path.join(STATE_DIR, f"day_{day:02d}_start.json")
        if not os.path.exists(src):
            raise ValueError(f"No saved starting state for Day {day}.")
        stamp = time.strftime("%Y%m%d_%H%M%S")
        aside = os.path.join(RUNS_DIR, "_rewound")
        os.makedirs(aside, exist_ok=True)
        for m in self.recorded_days():
            if m["day"] >= day:
                shutil.move(day_dir(m["day"]), os.path.join(aside, f"day_{m['day']:02d}_{stamp}"))
        shutil.copyfile(src, self.current_path())
        with self.cv:
            self.session = None
        return day

    # ---------- scenario ----------
    def get_scenario(self):
        from .data_cast import CHARACTERS
        from .data_world import ROOMS
        cur = self.load_current()
        return {"scenario": cur.get("scenario") or {}, "templates": scn.template_list(), "kinds": list(scn.KINDS),
                "cast": {k: c["name"] for k, c in cur["cast"].items()}, "rooms": {k: v[0] for k, v in ROOMS.items()}}

    def generate_scenario(self, seed, difficulty, allow_secrets=False):
        """A procedurally composed scenario (not saved: the caller previews it and then applies it with set_scenario)."""
        from . import scengen
        cur = self.load_current()
        out = scengen.generate(seed, difficulty, start_day=cur.get("day", 3), allow_secrets=allow_secrets, cast_ids=set(cur["cast"]))
        out["scenario"]["_meta"] = out["meta"]
        return out

    def set_scenario(self, raw):
        if self._busy():
            raise ValueError("Stop or finish the live day first.")
        cur = self.load_current()
        from .data_world import ROOMS
        sc = scn.clean(raw, set(cur["cast"]), set(ROOMS))
        old = cur.get("scenario") or {}
        if old.get("twist") and sc.get("twist") and old["twist"]["text"] == sc["twist"]["text"]:
            sc["twist"]["done"] = old["twist"].get("done", False)
        sc["_placed"] = list(old.get("_placed", []))
        cur["scenario"] = None if scn.is_empty(sc) else sc
        scn.apply_seeds(cur)
        self.save_current(cur)
        return cur["scenario"]

    # ---------- rewind and export ----------
    def can_rewind(self):
        days = self.recorded_days()
        if not days:
            return False
        last = days[-1]["day"]
        return os.path.exists(os.path.join(STATE_DIR, f"day_{last:02d}_start.json"))

    def rewind(self):
        """Undo the last recorded day: restore the state from before it and set the recording aside."""
        with self.cv:
            s = self.session
            if s and s["mode"] == "live" and not s["done"] and not s["aborted"] and not s["error"]:
                raise ValueError("Stop the live day first.")
        days = self.recorded_days()
        if not days:
            raise ValueError("There is nothing to rewind.")
        last = days[-1]["day"]
        src = os.path.join(STATE_DIR, f"day_{last:02d}_start.json")
        if not os.path.exists(src):
            raise ValueError(f"No saved starting state for Day {last}.")
        stamp = time.strftime("%Y%m%d_%H%M%S")
        aside = os.path.join(RUNS_DIR, "_rewound")
        os.makedirs(aside, exist_ok=True)
        shutil.move(day_dir(last), os.path.join(aside, f"day_{last:02d}_{stamp}"))
        shutil.copyfile(src, self.current_path())
        with self.cv:
            self.session = None
        return last

    def export(self, day=None):
        names = {k: c["name"] for k, c in self.load_current().get("cast", {}).items()}
        return exportlib.story_markdown(RUNS_DIR, names, day)

    # ---------- control ----------
    def start(self, day, mode, backend="cli", step=2, murders=True, motive="", rule="roulette", rule_text="", mischief="occasional", confessionals=True, chaos="normal", variation=0, lean=False, call_cap=0, autodir=False, week_len=None, resume=False):
        with self.cv:
            if self.session and not self.session["done"] and not self.session["aborted"] and not self.session["error"]:
                self._stop_locked()
        if mode == "replay":
            path = os.path.join(day_dir(day), "ticks.jsonl")
            if not os.path.exists(path):
                raise ValueError(f"Day {day} has not been recorded yet.")
            with open(path, "r", encoding="utf-8") as f:
                ticks = [json.loads(line) for line in f if line.strip()]
            with self.cv:
                self.session = {"day": day, "mode": "replay", "backend": "replay", "step": step, "ticks": ticks,
                                "done": True, "error": None, "aborted": False, "ff": False, "stop": False,
                                "pos": -1, "thread": None, "usage": None}
            return
        cur = self.load_current()
        if cur.get("over"):
            raise ValueError("The season is over (" + cur["over"]["title"].title() + "). Start a new game.")
        nxt = cur["day"]
        if day != nxt:
            raise ValueError(f"Only Day {nxt} can be played live next. Use replay for recorded days.")
        if (day - 1) % cur.get("week_len", 7) == 0 and cur.get("vacancies") and not cur.get("no_newcomers"):
            need = ", ".join(f"{sum(1 for v in cur['vacancies'] if v['gender'] == g)} {g}" for g in ("female", "male")
                             if any(v["gender"] == g for v in cur["vacancies"]))
            raise ValueError(f"A new week starts on Day {day}. Add newcomers first (needed: {need}).")
        if resume:
            cp = self.checkpoint_info()
            if not cp or cp["day"] != day:
                raise ValueError("There is no unfinished Day " + str(day) + " to resume.")
        if week_len and not resume:
            n = max(3, min(14, int(week_len)))
            if n != cur.get("week_len", 7):
                cur["week_len"] = n
                if cur.get("revealed", True) and not cur.get("case") and not (cur.get("scenario") or {}).get("deadline_days"):
                    cur["deadline_day"] = max(day, n * week_of(day, n))
                self.save_current(cur)
        llm = LLM(backend=backend)
        llm.cap = int(call_cap) if call_cap and int(call_cap) > 0 else None
        sess = {"day": day, "mode": "live", "backend": backend, "step": step, "ticks": [], "done": False,
                "error": None, "aborted": False, "ff": False, "stop": False, "pos": -1, "thread": None,
                "usage": dict(llm.usage), "llm": llm, "murders": murders, "motive": motive, "rule": rule, "rule_text": rule_text, "mischief": mischief, "confessionals": confessionals, "chaos": chaos,
                "variation": int(variation or 0), "gm": [], "lean": bool(lean), "autodir": bool(autodir), "resume": bool(resume)}
        with self.cv:
            self.session = sess
        t = threading.Thread(target=self._run_live, args=(sess,), daemon=True)
        sess["thread"] = t
        t.start()

    def load_tuning(self):
        try:
            with open(TUNING, "r", encoding="utf-8") as f:
                self.tuning = settings_mod.clean(json.load(f))
        except (OSError, ValueError):
            self.tuning = {}

    def get_tuning(self):
        return {"settings": settings_mod.meta(), "values": {**settings_mod.DEFAULTS, **self.tuning}}

    def set_tuning(self, values):
        """Saved to disk and read by the running day on its next turn."""
        self.tuning = settings_mod.clean(values)
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(TUNING, "w", encoding="utf-8") as f:
            json.dump(self.tuning, f)
        return self.get_tuning()

    def checkpoint_info(self):
        """An unfinished day that can be resumed: written after every tick, removed when the day completes."""
        try:
            with open(CHECKPOINT, "r", encoding="utf-8") as f:
                cp = json.load(f)
            return {"day": cp["day"], "hour": cp["hour"], "idx": cp["idx"]}
        except (OSError, ValueError, KeyError):
            return None

    def _run_live(self, sess):
        day = sess["day"]
        os.makedirs(day_dir(day), exist_ok=True)
        tmp = os.path.join(day_dir(day), "ticks.partial.jsonl")
        resume_after, start_idx = None, 0
        if sess.get("resume"):
            with open(CHECKPOINT, "r", encoding="utf-8") as f:
                cp = json.load(f)
            start_state = cp["state"]
            resume_after, start_idx = resume_hour(cp), cp["idx"] + 1
            with open(tmp, "r", encoding="utf-8") as f:
                sess["ticks"] = [json.loads(line) for line in f if line.strip()][:start_idx]
            fh = open(tmp, "w", encoding="utf-8")
            for t_ in sess["ticks"]:
                fh.write(json.dumps(t_, ensure_ascii=False) + "\n")
            fh.flush()
        else:
            start_state = self.load_current()
            with open(os.path.join(STATE_DIR, f"day_{day:02d}_start.json"), "w", encoding="utf-8") as f:
                json.dump(start_state, f, ensure_ascii=False)
            fh = open(tmp, "w", encoding="utf-8")
        world = World(copy.deepcopy(start_state))
        llm = sess["llm"]

        def on_tick(tick):
            fh.write(json.dumps(tick, ensure_ascii=False) + "\n")
            fh.flush()
            try:
                with open(CHECKPOINT + ".tmp", "w", encoding="utf-8") as cf:
                    json.dump({"day": day, "hour": tick["hour"], "idx": tick["idx"], "v": CHECKPOINT_V, "state": world.dump()}, cf, ensure_ascii=False)
                os.replace(CHECKPOINT + ".tmp", CHECKPOINT)
            except OSError:
                pass
            with self.cv:
                sess["ticks"].append(tick)
                sess["usage"] = dict(llm.usage)
                self.cv.notify_all()

        def gate(idx):
            with self.cv:
                while not (sess["ff"] or sess["stop"] or idx <= sess["pos"] + BUFFER):
                    self.cv.wait(timeout=1.0)

        runner = DayRunner(world, llm, on_tick, gate=gate, should_stop=lambda: sess["stop"], step=sess["step"],
                           murders=sess["murders"], motive=sess["motive"], rule_mode=sess["rule"], rule_text=sess["rule_text"],
                           mischief=sess["mischief"], confessionals=sess["confessionals"],
                           chaos=sess["chaos"], variation=sess["variation"], gm_pull=lambda: self._pull_gm(sess), lean=sess["lean"], call_cap=0, autodir=sess["autodir"], autodir_get=lambda: sess["autodir"], tuning_get=lambda: self.tuning,
                           ask_gm=lambda q: self._ask_gm(sess, q))
        try:
            n = runner.run(resume_after=resume_after, start_idx=start_idx)
            fh.close()
            final = os.path.join(day_dir(day), "ticks.jsonl")
            if os.path.exists(final):
                os.remove(final)
            os.replace(tmp, final)
            meta = {"day": day, "ticks": n, "step": sess["step"], "backend": sess["backend"],
                    "usage": dict(llm.usage), "notable": runner.day_notable[-30:], "diaries": runner.diary_added,
                    "telemetry": world.state.get("telemetry", {}).get(str(day), {}),
                    "rule": ({"id": runner.rule_final["id"], "title": runner.rule_final["title"],
                              "short": runner.rule_final["short"], "strikes": runner.rule_final["strikes"]}
                             if runner.rule_final else None),
                    "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            with open(os.path.join(day_dir(day), "meta.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=1)
            self.save_current(world.dump())
            try:
                os.remove(CHECKPOINT)
            except OSError:
                pass
            with self.cv:
                sess["done"] = True
                self.cv.notify_all()
        except Stop:
            fh.close()
            with self.cv:
                sess["aborted"] = True
                self.cv.notify_all()
        except LLMError as e:
            fh.close()
            with self.cv:
                sess["error"] = f"{e}" + ("  (usage limit or login problem: wait and try again)" if e.fatal else "")
                self.cv.notify_all()
        except Exception as e:  # engine bug: surface it instead of dying silently
            fh.close()
            import traceback
            traceback.print_exc()
            with self.cv:
                sess["error"] = f"Engine error: {type(e).__name__}: {e}"
                self.cv.notify_all()

    # ---------- GM pause hooks (pauses.py) ----------
    def set_roll_prefs(self, kinds, timeout=None):
        from .pauses import ROLL_KINDS
        self.roll_prefs = {"kinds": [k for k in (kinds or []) if k in ROLL_KINDS],
                           "timeout": max(5, min(300, int(timeout or getattr(self, "roll_prefs", {}).get("timeout", 45))))}
        return self.roll_prefs

    def _ask_gm(self, sess, q):
        """Called on the engine's thread at a deciding roll: if the GM wants this kind of roll paused, publish the question and wait for an
        answer (or the timeout, a stop or a fast-forward). Returns "encourage", "discourage" or None (let the dice decide)."""
        prefs = getattr(self, "roll_prefs", None) or {}
        if q.get("kind") not in prefs.get("kinds", []) or sess.get("mode") != "live":
            return None
        deadline = time.time() + prefs.get("timeout", 45)
        with self.cv:
            if sess["ff"] or sess["stop"]:
                return None
            sess["roll_seq"] = sess.get("roll_seq", 0) + 1
            rid = sess["roll_seq"]
            sess["roll"] = {**q, "id": rid, "timeout": prefs.get("timeout", 45)}
            sess["roll_answer"] = None
            self.cv.notify_all()
            while sess.get("roll_answer") is None and not (sess["stop"] or sess["ff"]) and time.time() < deadline:
                self.cv.wait(timeout=0.5)
            ans = sess.get("roll_answer")
            sess["roll"] = None
            sess["roll_answer"] = None
        return ans if ans in ("encourage", "discourage") else None

    def answer_roll(self, rid, answer):
        with self.cv:
            s = self.session
            if not s or not s.get("roll") or s["roll"]["id"] != int(rid):
                return False
            s["roll_answer"] = answer if answer in ("encourage", "discourage") else "dice"
            self.cv.notify_all()
            return True

    def set_autodir(self, on):
        self.pref_autodir = bool(on)
        with self.cv:
            if self.session and self.session.get("mode") == "live":
                self.session["autodir"] = bool(on)

    def chronicle(self, **kw):
        """The committed season's chronicle (finished days), filtered. The live day arrives through the tick stream."""
        from .chronicle import query_chronicle
        try:
            st = self.load_current()
        except Exception:
            return []
        return query_chronicle(st.get("chronicle", []), **kw)

    def previously(self, day):
        """'Previously on...': a recap of the day before, built from what was recorded (no AI calls)."""
        prev = int(day) - 1
        d = day_dir(prev)
        mp = os.path.join(d, "meta.json")
        if prev < 1 or not os.path.exists(mp):
            return None
        with open(mp, "r", encoding="utf-8") as f:
            meta = json.load(f)
        recap = None
        tp = os.path.join(d, "ticks.jsonl")
        if os.path.exists(tp):
            with open(tp, "r", encoding="utf-8") as f:
                for line in f:
                    if '"recap"' in line:
                        try:
                            t = json.loads(line)
                            if t.get("recap"):
                                recap = t["recap"]
                        except Exception:
                            pass
        sp = os.path.join(STATE_DIR, f"day_{int(day):02d}_start.json")
        try:
            with open(sp if os.path.exists(sp) else self.current_path(), "r", encoding="utf-8") as f:
                st = upgrade_state(json.load(f))
        except Exception:
            st = None
        names = {k: c["name"] for k, c in (st or {}).get("cast", {}).items()}
        skip = ("In the ", "TereVi meddled", "The auto-director")
        notable = [n for n in meta.get("notable", []) if not n.startswith(skip)]
        deaths = []
        if st:
            deaths = [{"id": g["id"], "name": names.get(g["id"], g["id"]), "how": g.get("how", g["status"])} for g in st["graveyard"] if g.get("day") == prev]
        return {"day": prev, "recap": recap, "highlights": notable[:7], "deaths": deaths,
                "alive": sum(1 for a in (st or {"agents": {}})["agents"].values() if a.get("status", "alive") == "alive") if st else None,
                "deadline": st["deadline_day"] if st else None, "over": st.get("over") if st else None,
                "saga": [x for x in (st or {}).get("saga", [])][-4:]}

    def _pull_gm(self, sess):
        with self.cv:
            out, sess["gm"] = sess["gm"], []
        return out

    def ticks(self, since, pos):
        with self.cv:
            s = self.session
            if not s:
                return {"ticks": [], "done": True, "error": None, "aborted": False, "ff": False, "known": 0}
            if pos is not None and pos > s["pos"]:
                s["pos"] = pos
                self.cv.notify_all()
            return {"ticks": s["ticks"][since:], "done": s["done"], "error": s["error"], "aborted": s["aborted"],
                    "ff": s["ff"], "known": len(s["ticks"]), "usage": s.get("usage"), "mode": s["mode"], "day": s["day"], "roll": s.get("roll")}

    def fast_forward(self):
        with self.cv:
            if self.session:
                self.session["ff"] = True
                self.cv.notify_all()

    def _stop_locked(self):
        s = self.session
        if s:
            s["stop"] = True
            self.cv.notify_all()

    def stop(self):
        with self.cv:
            self._stop_locked()

    def new_game(self, start_day=3, keep_scenario=True):
        old_sc = None
        if keep_scenario:
            try:
                old_sc = self.load_current().get("scenario")
            except Exception:
                old_sc = None
        self.stop()
        t = self.session["thread"] if self.session else None
        if t:
            t.join(timeout=5)
        with self.cv:
            self.session = None
        shutil.rmtree(RUNS_DIR, ignore_errors=True)
        os.makedirs(RUNS_DIR, exist_ok=True)
        for p in glob.glob(os.path.join(STATE_DIR, "day_*_start.json")):
            os.remove(p)
        st = new_state(start_day, shuffle_rooms=True)
        if old_sc:
            old_sc = dict(old_sc, _placed=[])
            if old_sc.get("twist"):
                old_sc["twist"] = dict(old_sc["twist"], done=False)
            st["scenario"] = old_sc
            scn.apply_seeds(st)
        self.save_current(st)
