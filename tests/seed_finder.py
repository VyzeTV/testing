"""Find mock seasons worth watching, record one, and voice it again with the real model.

    python tests/seed_finder.py find --seeds 30            (30 seeds per configuration: rank them by how much happened; no model calls)
    python tests/seed_finder.py record 17 --violent --out DIR
                                                          (play that season again, keeping every day's record and the voicing prompts)
    python tests/seed_finder.py voice DIR --days 3-5 [--only trial,scene] [--backend cli]
                                                          (voice those days again with the real model; writes DIR_voiced)

A recording is a save slot: copy DIR (or DIR_voiced) into the viewer's data folder, under state/slots/<name>, load it from the Saves menu and
replay the days. The events are exactly the mock run's; voicing only changes the words (revoice.py).
"""
import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from multiprocessing import Pool

os.environ.setdefault("MC_DATA_DIR", tempfile.mkdtemp())
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import season  # noqa: E402

TWIST_PTS = {"confession": 5, "took_blame": 5, "neovi_names": 5, "death_pact": 6, "murder_suicide": 6, "raft_returned": 3, "hallucination_kill": 5,
             "killer_helps": 3, "neovi_defects": 4}


def score(r):
    """How much story a season has, and the reasons (for the shortlist)."""
    pts, why = 0, []
    for tr, m in zip(r["trials"], r["margins"] + [99] * len(r["trials"])):
        p = 3
        bits = []
        if not tr["found"]:
            p += 6
            bits.append("wrong verdict")
        if m <= 1:
            p += 4
            bits.append("vote decided by one")
        pts += p
        why.append(f"Day {tr['day']} trial" + (f" ({', '.join(bits)})" if bits else ""))
    for k, n in (r.get("twists") or {}).items():
        if n:
            pts += TWIST_PTS.get(k, 2) * n
            why.append(f"{k.replace('_', ' ')} x{n}")
    seg = r.get("segments") or {}
    for k in ("split", "climax", "crossexam"):
        if seg.get(k):
            pts += 1
    ev = r.get("events") or {}
    for k, p, cap in (("betrayal", 2, 4), ("fight", 1, 6), ("madness", 2, 3), ("assault", 1, 4), ("punish", 0, 0)):
        n = min(ev.get(k, 0), cap)
        if n:
            pts += p * n
    if ev.get("betrayal"):
        why.append(f"{ev['betrayal']} betrayals")
    nv = r.get("nv") or {}
    if nv.get("dead"):
        pts += 6
        why.append(f"NeoVi died ({nv['dead']})")
    if nv.get("kills"):
        pts += 5 * nv["kills"]
        why.append("NeoVi killed someone")
    if r.get("nv_joined"):
        pts += 2
        why.append(f"NeoVi joined the cast ({r['nv_joined']})")
    hows = Counter(g["how"] for g in r.get("cases") or [])
    for h, n in hows.items():
        if "wrongly" in h:
            pts += 2 * n
    aff = (r.get("intimacy") or {}).get("affairs_found", 0)
    if aff:
        pts += 3 * aff
        why.append(f"{aff} affairs found out")
    pts += {"good": 2, "bittersweet": 3, "bad": 1}.get(r.get("tier"), 0)
    days = max(1, r.get("day") or 1)
    return round(pts / (days ** 0.35), 1), why


def find(n):
    jobs = [(v, s) for v in (False, True) for s in range(1, n + 1)]
    with Pool(min(8, os.cpu_count() or 2), maxtasksperchild=1) as pool:       # a fresh process per season: nothing carries over from the last one
        res = pool.map(season.one_season, jobs, chunksize=1)
    ranked = sorted(((score(r), r) for r in res), key=lambda x: -x[0][0])
    out = []
    for (sc, why), r in ranked[:12]:
        out.append({"seed": r["seed"], "violent": r["violent"], "score": sc, "days": r["day"], "ending": r["title"], "tier": r["tier"],
                    "trials": len(r["trials"]), "why": why[:8]})
        print(f"{sc:6.1f}  seed {r['seed']:3d} {'violent' if r['violent'] else 'default'}  {r['day']:2d} days  {r['tier']:11s} {r['title']}")
        for w_ in why[:8]:
            print("          - " + w_)
    return out


def record(seed, violent, out):
    r = season.one_season((violent, seed, {"record": True}))
    rec = r["record"]
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(os.path.join(out, "starts"), exist_ok=True)
    total = 0
    for i, (ticks, start) in enumerate(zip(rec["days"], rec["starts"])):
        day = start["day"]
        d = os.path.join(out, "runs", f"day_{day:02d}")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "ticks.jsonl"), "w", encoding="utf-8") as f:
            for t in ticks:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
        with open(os.path.join(d, "meta.json"), "w", encoding="utf-8") as f:
            json.dump({"day": day, "ticks": len(ticks), "step": 2, "backend": "mock", "usage": {}}, f)
        with open(os.path.join(out, "starts", f"day_{day:02d}_start.json"), "w", encoding="utf-8") as f:
            json.dump(start, f, ensure_ascii=False)
        total += len(ticks)
    with open(os.path.join(out, "current.json"), "w", encoding="utf-8") as f:
        json.dump(r["final"], f, ensure_ascii=False)
    name = os.path.basename(os.path.normpath(out))
    with open(os.path.join(out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump({"name": name, "day": r["final"]["day"], "alive": len(r["survivors"]), "saved_at": "seed finder",
                   "seed": seed, "violent": violent, "ending": r["title"], "tier": r["tier"]}, f)
    print(f"recorded seed {seed} ({'violent' if violent else 'default'}): {len(rec['days'])} days, {total} ticks, ended {r['title']} ({r['tier']}) -> {out}")
    return r


def load_days(slot):
    days = []
    for d in sorted(os.listdir(os.path.join(slot, "runs"))):
        with open(os.path.join(slot, "runs", d, "ticks.jsonl"), "r", encoding="utf-8") as f:
            days.append((int(d[4:6]), [json.loads(line) for line in f if line.strip()]))
    return days


def voice(slot, day_range=None, only=None, backend="cli", workers=4):
    from murder.engine import DayRunner
    from murder.llm import LLM
    from murder.revoice import revoice_day, strip_prompts
    from murder.world import World
    days = load_days(slot)
    with open(os.path.join(slot, "current.json"), "r", encoding="utf-8") as f:
        final = json.load(f)
    runner = DayRunner(World(final), LLM(backend="mock"), lambda t: None, step=2, seed=1)
    llm = LLM(backend=backend)
    lo, hi = day_range or (0, 10 ** 6)
    pick = {i for i, (d, _) in enumerate(days) if lo <= d <= hi}
    st = revoice_day([t for _, t in days], runner, llm, workers=workers, only=only, pick=pick)
    out = os.path.normpath(slot) + "_voiced"
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(slot, out)
    for d, ticks in days:
        strip_prompts(ticks)
        with open(os.path.join(out, "runs", f"day_{d:02d}", "ticks.jsonl"), "w", encoding="utf-8") as f:
            for t in ticks:
                f.write(json.dumps(t, ensure_ascii=False) + "\n")
    with open(os.path.join(out, "meta.json"), "r", encoding="utf-8") as f:
        meta = json.load(f)
    meta.update(name=os.path.basename(out), voiced={"days": [d for i, (d, _) in enumerate(days) if i in pick], "backend": backend, **st, "usage": dict(llm.usage)})
    with open(os.path.join(out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f)
    print(f"voiced {out}: {st}, model usage {llm.usage}")
    return st


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("find", "record", "voice"):
        print(__doc__)
        sys.exit(1)
    opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    if a[0] == "find":
        res = find(int(opt("--seeds", 20)))
        if opt("--json"):
            with open(opt("--json"), "w", encoding="utf-8") as f:
                json.dump(res, f, indent=1)
    elif a[0] == "record":
        record(int(a[1]), "--violent" in a, opt("--out", os.path.join(tempfile.gettempdir(), f"mc_seed_{a[1]}")))
    else:
        rng = opt("--days")
        dr = tuple(int(x) for x in rng.split("-")) if rng and "-" in rng else ((int(rng), int(rng)) if rng else None)
        voice(a[1], dr, set(opt("--only").split(",")) if opt("--only") else None, opt("--backend", "cli"), int(opt("--workers", 4)))
