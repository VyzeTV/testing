"""Who kills and who dies: per-character counts over many mock weeks (for curiosity, not a gate).

    python tests/cast_stats.py            (prints the table)
    python tests/cast_stats.py --write    (also writes docs/CAST_STATS.md)

Runs the weeks of tests/balance.py for seeds 101-140 in both configurations (default and the violent mock cast), in parallel, and logs every case
as it opens (victim, culprit, kind) and every trial (accused, right or wrong). Takes a few minutes.
"""
import json
import os
import sys
import tempfile
from collections import Counter
from multiprocessing import Pool

os.environ.setdefault("MC_DATA_DIR", tempfile.mkdtemp())
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SEEDS = list(range(101, 141))


def one_week(job):
    violent, seed = job
    import balance
    from murder.engine import DayRunner
    log = []
    oc, em = DayRunner.open_case, DayRunner.emit

    def open_case(self, tick, kind, victim, culprit=None, **kw):
        r = oc(self, tick, kind, victim, culprit=culprit, **kw)
        log.append({"ev": "case", "kind": kind, "victim": victim, "killer": culprit})
        return r

    def emit(self, tick):
        t = tick.get("trial")
        if t:
            log.append({"ev": "trial", "victim": t["victim"], "killer": t["killer"], "accused": t["accused"], "found": bool(t["found"]), "wrongful": bool(t["wrongful"])})
        return em(self, tick)

    DayRunner.open_case, DayRunner.emit = open_case, emit
    balance.run_week(seed, violent)
    return log


def collect():
    jobs = [(v, s) for v in (False, True) for s in SEEDS]
    with Pool(min(8, os.cpu_count() or 2)) as pool:
        logs = pool.map(one_week, jobs)
    return [e for lg in logs for e in lg]


def markdown(log, cast_names=None):
    cases = [e for e in log if e["ev"] == "case"]
    trials = [e for e in log if e["ev"] == "trial"]
    nm = lambda c: (cast_names or {}).get(c, c.capitalize())
    vic = Counter(c["victim"] for c in cases)
    kil = Counter(c["killer"] for c in cases if c["killer"])
    kind = Counter((c["killer"], c["kind"]) for c in cases if c["killer"])
    caught = Counter(t["killer"] for t in trials if t["found"])
    away = Counter(t["killer"] for t in trials if not t["found"])
    wrong = Counter(t["accused"] for t in trials if t["wrongful"])
    people = sorted(set(vic) | set(kil), key=lambda p: (-kil[p], p))
    kinds = Counter(c["kind"] for c in cases)
    rows = "\n".join(f"| {nm(p)} | {vic[p]} | {kil[p]} ({kind[(p, 'murder')]} + {kind[(p, 'manslaughter')]}) | {caught[p]} | {away[p]} | {wrong[p]} |" for p in people)
    pairs = ", ".join(f"{nm(k)} killing {nm(v)} ({n})" for (k, v), n in Counter((c["killer"], c["victim"]) for c in cases if c["killer"]).most_common(5))
    return (
        "# Who kills and who dies\n\n"
        f"Per-character counts over {2 * len(SEEDS)} mock weeks (seeds {SEEDS[0]}-{SEEDS[-1]}, the default and the violent mock cast of `tests/balance.py`). "
        "For curiosity, not a gate. Regenerate with `python tests/cast_stats.py --write` (a few minutes).\n\n"
        f"{len(cases)} deaths opened a case: " + ", ".join(f"{k} {n}" for k, n in kinds.most_common()) + ". "
        f"{len(trials)} reached a trial: {sum(t['found'] for t in trials)} right verdicts, {sum(t['wrongful'] for t in trials)} wrong, "
        f"{len(trials) - sum(t['found'] for t in trials) - sum(t['wrongful'] for t in trials)} with no verdict.\n\n"
        "| Character | Victim | Killer (murder + manslaughter) | Caught at trial | Got away at trial | Executed in someone else's place |\n"
        "| --- | --- | --- | --- | --- | --- |\n" + rows + "\n\n"
        "\"Got away at trial\" means a wrong verdict or none, so the killer survived. Killings that never reached a trial (the mock week ended before the trial, or the killing happened during a frenzy, which has no trial) "
        "count only as kills.\n\n"
        f"Most frequent pairs: {pairs}.\n"
    )


if __name__ == "__main__":
    src = sys.argv[sys.argv.index("--from") + 1] if "--from" in sys.argv else None
    log = json.load(open(src)) if src else collect()
    md = markdown(log)
    print(md)
    if "--write" in sys.argv:
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "CAST_STATS.md"), "w") as f:
            f.write(md)
