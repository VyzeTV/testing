"""Whole mock seasons: from Day 1 (the introductions and the reveal) until the show ends, however it ends.

    python tests/season.py               (prints the summary)
    python tests/season.py --write       (also writes docs/SEASONS.md)
    python tests/season.py --seeds 20    (seasons per configuration, default 12)

A season ends when the engine says so: the Reckoning (nobody died by a deadline), TereVi's endgame when three or fewer are left (she crowns
them, makes them fight, or crowns one on a whim), a way out (the truth broadcast, TereVi shut down, the last raft, the show surrenders), or
nobody left. As in the viewer, every empty place is filled with a newcomer when a new week starts (from a pool of producer sketches here). Two configurations as in balance.py: the
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

MAX_DAYS = 120
FIRST = {"female": ["Nadia", "Elsa", "Priya", "Lena", "Yuki", "Carmen", "Ines", "Zoe", "Tamsin", "Greta", "Ama", "Sofia"],
         "male": ["Felix", "Omar", "Kenji", "Lucas", "Ravi", "Anton", "Malik", "Emil", "Tomas", "Joon", "Pavel", "Hugo"]}
# Newcomers for the weekly refill, as a producer might sketch them (the viewer asks for them before a new week starts if anyone is missing).
NEWCOMERS = [
    {"name": "Mara Voss", "gender": "female", "role": "Stunt Driver", "persona": "Fearless, impatient and hot-headed; quick to anger and quick to forgive. Built a fan base crashing cars for movies.",
     "speech": "Blunt and fast, swears casually.", "likes": "speed, engines", "dislikes": "cowards, waiting", "drive": "thrill"},
    {"name": "Ilya Petrov", "gender": "male", "role": "Chess Grandmaster", "persona": "Calm, calculating and cold; patient to a fault, trusts nobody, plans every move. Never lost his temper on camera.",
     "speech": "Measured and precise, few words.", "likes": "strategy, silence", "dislikes": "noise, chaos", "drive": "schemer"},
    {"name": "June Okafor", "gender": "female", "role": "Nurse", "persona": "Gentle, caring and selfless; altruistic and brave in a crisis, loyal to anyone hurt. Went viral for a hospital vlog.",
     "speech": "Warm and steady.", "likes": "helping, tea", "dislikes": "cruelty, lies", "drive": "protector"},
    {"name": "Dario Quint", "gender": "male", "role": "Prank Streamer", "persona": "Loud, reckless and cruel in his jokes; vain, impulsive and attention-hungry. Banned from three platforms.",
     "speech": "Shouty, laughs at his own jokes.", "likes": "pranks, attention", "dislikes": "being ignored", "drive": "thrill"},
    {"name": "Hana Sato", "gender": "female", "role": "Detective Novelist", "persona": "Curious, sharp and suspicious; notices everything, trusts little, loves a puzzle. Writes bestselling mysteries.",
     "speech": "Questions everything.", "likes": "mysteries, coffee", "dislikes": "sloppy thinking", "drive": "seeker"},
    {"name": "Bram de Wit", "gender": "male", "role": "Mountain Guide", "persona": "Steady, brave and protective; gregarious and kind, a natural leader who keeps people calm in storms.",
     "speech": "Plain and reassuring.", "likes": "climbing, campfires", "dislikes": "panic, bullies", "drive": "protector"},
    {"name": "Rosa Lind", "gender": "female", "role": "Opera Singer", "persona": "Dramatic, vain and romantic; ambitious, jealous of rivals, holds grudges and craves the spotlight.",
     "speech": "Grand and theatrical.", "likes": "applause, roses", "dislikes": "rivals, ugliness", "drive": "romantic"},
    {"name": "Teo Marsh", "gender": "male", "role": "Ex-Soldier", "persona": "Quiet, disciplined and dangerous; cold under pressure, vengeful when betrayed, haunted by a war he never talks about.",
     "speech": "Short, clipped sentences.", "likes": "order, routine", "dislikes": "liars, disorder", "drive": "survivor"},
]


def one_season(job):
    """job: (violent, seed) or (violent, seed, opts); opts {"record": True} also keeps every day's ticks and starting state, with the voicing prompts (revoice.py)."""
    violent, seed = job[0], job[1]
    opts = job[2] if len(job) > 2 else {}
    from murder.storylint import StoryLinter
    from murder.engine import DayRunner
    from murder.llm import LLM
    from murder.world import World, new_state
    LLM.mock_plot_prob = 0.04 if violent else 0.0
    LLM.mock_murder_prob = 0.02 if violent else 0.0
    w = World(new_state(1))
    lint = StoryLinter(w.dump())
    trials, finales = [], []
    evc, margins, segs = Counter(), [], Counter()
    rec = {"days": [], "starts": []} if opts.get("record") else None

    def keep(t):
        lint.feed(t)
        if rec is not None:
            rec["days"][-1].append(t)
        for e in t.get("events") or []:
            evc[e.get("type")] += 1
        for sg in t.get("segments") or []:
            segs[sg.get("kind")] += 1
        if t.get("trial"):
            tr = t["trial"]
            trials.append({"day": t["day"], "victim": tr["victim"], "killer": tr["killer"], "accused": tr["accused"], "found": bool(tr["found"])})
            tl = sorted((tr.get("tally") or {}).values(), reverse=True)
            margins.append((tl[0] - (tl[1] if len(tl) > 1 else 0)) if tl else 99)
        if t.get("type") == "finale" or (t.get("ending") and t["ending"]["kind"] in ("truth", "shutdown", "raft", "ultimatum")):
            finales.append({"day": t["day"], "ending": (t.get("ending") or {}).get("kind")})

    day, arrivals = 1, []
    pool = list(NEWCOMERS)
    while day <= MAX_DAYS and not w.state.get("over") and w.agents:
        w.state["day"] = day
        if (day - 1) % w.state.get("week_len", 7) == 0 and w.state.get("vacancies") and not w.state.get("no_newcomers"):
            for v in list(w.state["vacancies"]):                       # a new week: the producer fills every empty place, as the viewer requires
                spec = next((x for x in pool if x["gender"] == v["gender"]), None)
                if spec:
                    pool.remove(spec)
                else:                                                   # the sketches ran out: an old personality under a new name
                    base = [x for x in NEWCOMERS if x["gender"] == v["gender"]][len(arrivals) % 4]
                    used = {c["short"] for c in w.state["cast"].values()}
                    first = next((f for f in FIRST[v["gender"]] if f not in used), None) or f"{FIRST[v['gender']][len(arrivals) % 12]}-{len(arrivals) + 1}"
                    spec = dict(base, name=f"{first} {base['name'].split()[-1]}")
                arrivals.append({"id": w.add_newcomer(spec), "day": day})
        lint.begin_day(w.dump())
        dr = DayRunner(w, LLM(backend="mock"), keep, step=2, murders=True, rule_mode="roulette", seed=seed * 1000 + day)
        if rec is not None:
            dr.keep_voice = True
            rec["starts"].append(json.loads(json.dumps(w.dump())))
            rec["days"].append([])
        dr.run()
        day = w.state.get("day", day) + (1 if w.state.get("day", day) == day else 0)
    if not w.state.get("over") and not w.agents:                         # the island emptied at the end of a day: the endgame decides
        lint.begin_day(w.dump())
        dr = DayRunner(w, LLM(backend="mock"), keep, step=2, murders=True, rule_mode="roulette", seed=seed * 1000 + day)
        dr.keep_voice = rec is not None
        if rec is not None and not rec["days"]:
            rec["starts"].append(json.loads(json.dumps(w.dump())))
            rec["days"].append([])
        dr.run_endgame(8)
    over = w.state.get("over") or {"kind": "unfinished", "title": f"still going after {MAX_DAYS} days", "day": day}
    names = {c: v["short"] for c, v in w.state["cast"].items()}
    nv = (w.state.get("npcs") or {}).get("neovi") or {}
    return {"story_issues": lint.issues, "story_checks": dict(lint.checks), "violent": violent, "seed": seed, "ending": over["kind"], "title": over.get("title"), "day": over.get("day", day), "tier": over.get("tier", "unfinished"), "costs": over.get("costs") or [], "epilogues": over.get("epilogues") or [],
            "neovi": ((nv.get("arc") or {}).get("fate") or "none"), "romances": sum(1 for b in w.state.get("bonds", []) if b.get("kind") == "romance"),
            "minds": dict(w.state.get("mind_stats") or {}), "stories": [e["kind"] for e in (w.state.get("stories") or {}).values()], "twists": dict(w.state.get("twists") or {}), "intimacy": dict(w.state.get("intimacy") or {}),
            "nv": {"helped": nv.get("helped", 0), "punished": [p["kind"] for p in nv.get("punished", [])], "named": sum(1 for v in (nv.get("told") or {}).values() if "name" in v),
                   "lover": bool(nv.get("lovers")), "fights": len(nv.get("fights") or []), "kills": len(nv.get("kills") or []), "dead": (nv.get("dead") or {}).get("how"),
                   "sanity": nv.get("sanity", 70), "sabotaged": nv.get("sabotaged", 0)},
            "survivors": sorted(c for c, a in w.state["agents"].items() if a.get("status", "alive") == "alive"),
            "graveyard": [{"id": g["id"], "day": g["day"], "how": g["how"]} for g in w.state.get("graveyard", [])],
            "trials": trials, "finales": finales, "saga": list(w.state.get("saga", [])), "names": names, "arrivals": arrivals,
            "rafts": [{"ids": c["ids"], "stage": c["stage"], "day": c["day"]} for c in (w.state.get("outside") or {}).get("crews", []) if c.get("kind") != "killer"],
            "killers_out": [{"id": c["ids"][0], "stage": c["stage"]} for c in (w.state.get("outside") or {}).get("crews", []) if c.get("kind") == "killer"],
            "nv_joined": nv.get("joined_for"), "capped": bool(w.state.get("_capped")), "rescue": w.state.get("rescue"),
            "truths": [e["text"] for e in w.state.get("chronicle", []) if str(e.get("text", "")).startswith("TRUTH")],
            "nights": len([n for n in w.state.get("nights") or []]), "nv_lover": bool(nv.get("lovers")),
            "events": dict(evc), "margins": margins, "segments": dict(segs), "cases": [dict(g) for g in w.state.get("graveyard", [])],
            "record": rec, "final": json.loads(json.dumps(w.dump())) if rec is not None else None,
            "escape": {rid: int(round(sum(r["plan"].values()) / len(r["plan"]))) for rid, r in (w.state.get("escape") or {}).get("routes", {}).items()}}


def collect(n):
    jobs = [(v, s) for v in (False, True) for s in range(1, n + 1)]
    with Pool(min(8, os.cpu_count() or 2)) as pool:
        return pool.map(one_season, jobs)


def markdown(seasons):
    out = ["# Whole mock seasons\n",
           f"{len(seasons)} seasons played from Day 1 until the show ended, with every empty place filled by a newcomer at the start of each week ({len(seasons) // 2} per configuration: the default mock cast and a violent one, as in "
           "`tests/balance.py`). Regenerate with `python tests/season.py --write` (a few minutes). For curiosity, not a gate.\n"]
    nm = lambda s, c: s["names"].get(c, c)
    out.append("Story checks: " + str(sum(sum(s.get("story_checks", {}).values()) for s in seasons)) +
               "; violations: " + str(sum(len(s.get("story_issues", [])) for s in seasons)) + ". Run `python tests/story_lint.py` for locations and details.\n")
    tiers = Counter(s["tier"] for s in seasons)
    out.append("**Ending tiers, all seasons:** " + ", ".join(f"{t} {tiers.get(t, 0)} ({round(100 * tiers.get(t, 0) / len(seasons))}%)" for t in ("good", "bittersweet", "bad"))
               + (f", unfinished {tiers['unfinished']}" if tiers.get("unfinished") else "") + ". Target: good 40%, bittersweet 30%, bad 30% (plan doc, phase 7b).\n")
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
        tt = Counter(s["tier"] for s in ss)
        out.append("- **Ending tiers:** " + ", ".join(f"{t} {tt.get(t, 0)}" for t in ("good", "bittersweet", "bad")) + ".")
        out.append("- **NeoVi's fate:** " + ", ".join(f"{k} {n}" for k, n in Counter(s["neovi"] for s in ss).most_common()) + f". Romances at the end: {sum(s['romances'] for s in ss)} in all.")
        pun = Counter(k for s in ss for k in s["nv"]["punished"])
        out.append(f"- **Kumiko:** helped the cast {sum(s['nv']['helped'] for s in ss)} times; told someone her real name in {sum(1 for s in ss if s['nv']['named'])} seasons; "
                   f"a romance with someone in {sum(1 for s in ss if s['nv']['lover'])}; punished: " + (", ".join(f"{k} {n}" for k, n in pun.most_common()) or "never") + ".")
        mi = Counter()
        for s in ss:
            mi.update(s["minds"])
        out.append(f"- **Minds:** {mi['thoughts']} thoughts shown; {mi['warped']} beliefs warped by fear, {mi['hallucinations']} hallucinations, "
                   f"{mi['false_memories']} false memories of a crime scene, {mi['seen_through']} seen through later; acted on: {mi['paranoid_plots']} paranoid plots, "
                   f"{mi['hid']} hid; {mi['plots_overheard']} plotters overheard muttering; {mi['mind_testimony']} trials heard testimony from a broken mind.")
        tw, im = Counter(), Counter()
        for s in ss:
            tw.update(s["twists"])
            im.update(s["intimacy"])
        out.append("- **Rare turns:** " + (", ".join(f"{k.replace('_', ' ')} {n}" for k, n in tw.most_common()) or "none") + ".")
        out.append(f"- **Love life:** {im['nights']} nights together, {im['affairs']} affairs ({im['affairs_found']} found out), {im['jealousy']} pangs of jealousy.")
        costs = Counter(c.split(" took ")[0] + " took someone with her" if c.startswith("TereVi took") else (c.split(" never came out")[0] and "someone never came out of the house" if "never came out" in c else c)
                        for s in ss for c in s["costs"])
        out.append("- **Wins at a price** (good endings made bittersweet): " + (", ".join(f"{k} {n}" for k, n in costs.most_common()) or "none") + ".")
        ko = [k for s in ss for k in s["killers_out"]]
        out.append(f"- **Killers the show let go:** {len(ko)}; {sum(s['twists'].get('killer_helps', 0) for s in ss)} tried to help from outside "
                   f"(believed {sum(1 for k in ko if k['stage'] == 'believed')}, dismissed {sum(1 for k in ko if k['stage'] == 'dismissed')}), the rest kept quiet or gave up.")
        out.append(f"- **NeoVi's body and mind:** fights {sum(s['nv'].get('fights', 0) for s in ss)}, people she killed {sum(s['nv'].get('kills', 0) for s in ss)}, "
                   f"sabotage of TereVi {sum(s['nv'].get('sabotaged', 0) for s in ss)}; she died in {sum(1 for s in ss if s['nv'].get('dead'))} seasons "
                   f"({', '.join(f'{k} {n}' for k, n in Counter(s['nv']['dead'] for s in ss if s['nv'].get('dead')).most_common()) or 'none'}); "
                   f"her sanity at the end: median {sorted(s['nv'].get('sanity', 70) for s in ss)[len(ss) // 2]}.")
        out.append(f"- **NeoVi joined the cast** after the fourth trial in {sum(1 for s in ss if s['nv_joined'] == 'fourth trial')} seasons, as a punishment in "
                   f"{sum(1 for s in ss if s['nv_joined'] == 'punishment')}. Seasons that ran the full 28 days: {sum(1 for s in ss if s['capped'])}.")
        sk = Counter(k for s in ss for k in s["stories"])
        out.append("- **Stories that formed** (story sifting): " + (", ".join(f"{k.replace('_', ' ')} {n}" for k, n in sk.most_common()) or "none") + ".")
        out.append(f"- **Season length:** median {statistics.median(days)} days (shortest {min(days)}, longest {max(days)}).")
        out.append("- **How seasons ended:** " + ", ".join(f"{k} {n}" for k, n in ends.most_common()) + ".")
        out.append(f"- **Deaths per season:** {round(sum(len(s['graveyard']) for s in ss) / len(ss), 1)} on average. Causes: "
                   + ", ".join(f"{k} {n}" for k, n in hows.most_common(8)) + ".")
        out.append(f"- **Trials:** {len(tr)} in all, {sum(t['found'] for t in tr)} right verdicts.")
        out.append(f"- **Newcomers:** {round(sum(len(s['arrivals']) for s in ss) / len(ss), 1)} per season on average; "
                   f"{sum(1 for s in ss for c in s['survivors'] if c in {a['id'] for a in s['arrivals']})} of the survivors were newcomers.")
        rafts = [c for s in ss for c in s["rafts"]]
        out.append(f"- **Rafts launched:** {len(rafts)}" + (" (" + ", ".join(f"{k} {n}" for k, n in Counter(c['stage'] for c in rafts).most_common()) + ")" if rafts else "")
                   + f". Rescue countdowns started: {sum(1 for s in ss if s['rescue'])}.")
        out.append(f"- **Ways out at the end:** the furthest route reached {round(statistics.mean(max(s['escape'].values() or [0]) for s in ss))}% on average "
                   f"(best {max(max(s['escape'].values() or [0]) for s in ss)}%).")
        out.append("- **Who walked out alive (seasons):** " + (", ".join(f"{k} {n}" for k, n in winners.most_common()) or "nobody") + ".\n")
        out.append("| Season | Days | Ending | Tier | Survivors | Deaths | Newcomers | Trials (right) |")
        out.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for s in ss:
            out.append(f"| {s['seed']} | {s['day']} | {s['title']} | {s['tier']} | {', '.join(nm(s, c) for c in s['survivors']) or 'none'} | {len(s['graveyard'])} | {len(s['arrivals'])} | "
                       f"{len(s['trials'])} ({sum(t['found'] for t in s['trials'])}) |")
        out.append("")
    best = max(seasons, key=lambda s: (len(s["graveyard"]) + 2 * len(s["trials"]), s["day"]))
    out.append(f"## One season, told by its saga (violent seed {best['seed']}" if best["violent"] else f"## One season, told by its saga (default seed {best['seed']}")
    out[-1] += f": {best['title']}, day {best['day']})\n"
    out += [f"- {line}" for line in best["saga"]]
    out.append("")
    out.append("Deaths in order: " + "; ".join(f"day {g['day']} {nm(best, g['id'])} ({g['how']})" for g in best["graveyard"]) + ".")
    withep = [s for s in seasons if len(s["epilogues"]) >= 2]
    if withep:
        ep = max(withep, key=lambda s: (len(s["epilogues"]), s["seed"]))
        out.append(f"\n## Epilogues from one season ({'violent' if ep['violent'] else 'default'} seed {ep['seed']}: {ep['title']}, {ep['tier']})\n")
        out += [f"- **{nm(ep, e['id']) if e['id'] != 'neovi' else 'NeoVi'}**: {e['text']}" for e in ep["epilogues"]]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--seeds") + 1]) if "--seeds" in sys.argv else 12
    seasons = collect(n)
    md = markdown(seasons)
    print(md)
    if "--write" in sys.argv:
        open(os.path.join(ROOT, "docs", "SEASONS.md"), "w").write(md)
        json.dump(seasons, open(os.path.join(tempfile.gettempdir(), "mc_seasons.json"), "w"))
