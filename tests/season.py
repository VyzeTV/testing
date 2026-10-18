"""Whole mock seasons: from Day 1 (the introductions and the reveal) until the show ends, however it ends.

    python tests/season.py               (prints the summary)
    python tests/season.py --write       (also writes docs/SEASONS.md)
    python tests/season.py --seeds 20    (seasons per configuration, default 12)

A season ends when the engine says so: the Reckoning (nobody died by a deadline), TereVi's endgame when three or fewer are left (she crowns
them, makes them fight, or crowns one on a whim), a way out (the truth broadcast, TereVi shut down, the last raft, the show surrenders), or
nobody left. Dead characters are not replaced (only the GM adds newcomers), so every season ends. Two configurations as in balance.py: the
default mock cast and a violent one. Runs in parallel; a few minutes. For curiosity, not a gate.
"""
import json
import os
import statistics
import sys
import tempfile
from collections import Counter
from multiprocessing import Pool

os.environ.setdefault("MC_DATA_DIR", tempfile.mkdtemp())
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

MAX_DAYS = 80


def one_season(job):
    violent, seed = job
    from murder.engine import DayRunner
    from murder.llm import LLM
    from murder.world import World, new_state
    LLM.mock_plot_prob = 0.04 if violent else 0.0
    LLM.mock_murder_prob = 0.02 if violent else 0.0
    w = World(new_state(1))
    trials, finales = [], []

    def keep(t):
        if t.get("trial"):
            tr = t["trial"]
            trials.append({"day": t["day"], "victim": tr["victim"], "killer": tr["killer"], "accused": tr["accused"], "found": bool(tr["found"])})
        if t.get("type") == "finale" or (t.get("ending") and t["ending"]["kind"] in ("truth", "shutdown", "raft", "ultimatum")):
            finales.append({"day": t["day"], "ending": (t.get("ending") or {}).get("kind")})

    day = 1
    while day <= MAX_DAYS and not w.state.get("over") and w.agents:
        w.state["day"] = day
        DayRunner(w, LLM(backend="mock"), keep, step=2, murders=True, rule_mode="roulette", seed=seed * 1000 + day).run()
        day = w.state.get("day", day) + (1 if w.state.get("day", day) == day else 0)
    over = w.state.get("over") or {"kind": "unfinished", "title": f"still going after {MAX_DAYS} days", "day": day}
    names = {c: v["short"] for c, v in w.state["cast"].items()}
    return {"violent": violent, "seed": seed, "ending": over["kind"], "title": over.get("title"), "day": over.get("day", day),
            "survivors": sorted(c for c, a in w.state["agents"].items() if a.get("status", "alive") == "alive"),
            "graveyard": [{"id": g["id"], "day": g["day"], "how": g["how"]} for g in w.state.get("graveyard", [])],
            "trials": trials, "finales": finales, "saga": list(w.state.get("saga", [])), "names": names}


def collect(n):
    jobs = [(v, s) for v in (False, True) for s in range(1, n + 1)]
    with Pool(min(8, os.cpu_count() or 2)) as pool:
        return pool.map(one_season, jobs)


def markdown(seasons):
    out = ["# Whole mock seasons\n",
           f"{len(seasons)} seasons played from Day 1 until the show ended ({len(seasons) // 2} per configuration: the default mock cast and a violent one, as in "
           "`tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.\n"]
    nm = lambda s, c: s["names"].get(c, c)
    for label, violent in (("Default", False), ("Violent mock cast", True)):
        ss = [s for s in seasons if s["violent"] == violent]
        if not ss:
            continue
        ends = Counter(s["title"].split(":")[0] if s["ending"] in ("battle", "sole") else s["title"] for s in ss)
        days = [s["day"] for s in ss]
        tr = [t for s in ss for t in s["trials"]]
        hows = Counter(g["how"] for s in ss for g in s["graveyard"])
        winners = Counter(nm(s, c) for s in ss for c in s["survivors"])
        out.append(f"## {label}\n")
        out.append(f"- **Season length:** median {statistics.median(days)} days (shortest {min(days)}, longest {max(days)}).")
        out.append("- **How seasons ended:** " + ", ".join(f"{k} {n}" for k, n in ends.most_common()) + ".")
        out.append(f"- **Deaths per season:** {round(sum(len(s['graveyard']) for s in ss) / len(ss), 1)} on average. Causes: "
                   + ", ".join(f"{k} {n}" for k, n in hows.most_common(8)) + ".")
        out.append(f"- **Trials:** {len(tr)} in all, {sum(t['found'] for t in tr)} right verdicts.")
        out.append("- **Who walked out alive (seasons):** " + (", ".join(f"{k} {n}" for k, n in winners.most_common()) or "nobody") + ".\n")
        out.append("| Season | Days | Ending | Survivors | Deaths | Trials (right) |")
        out.append("| --- | --- | --- | --- | --- | --- |")
        for s in ss:
            out.append(f"| {s['seed']} | {s['day']} | {s['title']} | {', '.join(nm(s, c) for c in s['survivors']) or 'none'} | {len(s['graveyard'])} | "
                       f"{len(s['trials'])} ({sum(t['found'] for t in s['trials'])}) |")
        out.append("")
    best = max(seasons, key=lambda s: (len(s["graveyard"]) + 2 * len(s["trials"]), s["day"]))
    out.append(f"## One season, told by its saga (violent seed {best['seed']}" if best["violent"] else f"## One season, told by its saga (default seed {best['seed']}")
    out[-1] += f": {best['title']}, day {best['day']})\n"
    out += [f"- {line}" for line in best["saga"]]
    out.append("")
    out.append("Deaths in order: " + "; ".join(f"day {g['day']} {nm(best, g['id'])} ({g['how']})" for g in best["graveyard"]) + ".")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--seeds") + 1]) if "--seeds" in sys.argv else 12
    seasons = collect(n)
    md = markdown(seasons)
    print(md)
    if "--write" in sys.argv:
        open(os.path.join(ROOT, "docs", "SEASONS.md"), "w").write(md)
        json.dump(seasons, open(os.path.join(tempfile.gettempdir(), "mc_seasons.json"), "w"))
