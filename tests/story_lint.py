"""Check seeded mock seasons or a saved recording. No model calls or save writes.

python tests/story_lint.py --seeds 1,11,13,28
python tests/story_lint.py --recording PATH --json REPORT.json
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MC_DATA_DIR", tempfile.mkdtemp(prefix="mc_story_"))

from murder.storylint import StoryLinter


def recording(path):
    base = Path(path)
    runs = base / "runs" if (base / "runs").is_dir() else base
    files = sorted(runs.glob("day_*/ticks.jsonl"))
    if not files:
        raise ValueError("No day_*/ticks.jsonl recordings found.")
    lint = StoryLinter()
    for file in files:
        day = int(file.parent.name[4:])
        starts = [base / "starts" / f"day_{day:02d}_start.json",
                  base / "state" / f"day_{day:02d}_start.json",
                  runs.parent / "state" / f"day_{day:02d}_start.json"]
        start = next((p for p in starts if p.is_file()), None)
        if start:
            lint.begin_day(json.loads(start.read_text(encoding="utf-8")))
        elif not lint.agents:
            raise ValueError(f"Starting state for Day {day} is missing; the check requires its cast and statuses.")
        with file.open(encoding="utf-8") as stream:
            for number, line in enumerate(stream, 1):
                if line.strip():
                    for issue in lint.feed(json.loads(line)):
                        issue.update(file=str(file), record_line=number)
    return {"recording": str(base), "story_issues": lint.issues, "story_checks": dict(lint.checks)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", default="1,11,13,28", help="comma-separated integer seeds; both cast configurations are checked")
    parser.add_argument("--recording", help="read a recording directory instead of simulating")
    parser.add_argument("--json", help="write full findings and coverage to this report")
    args = parser.parse_args()
    results = []
    if args.recording:
        results.append(recording(args.recording))
    else:
        from season import one_season
        seeds = list(dict.fromkeys(int(s) for s in args.seeds.split(",")))
        for seed in seeds:
            for violent in (False, True):
                result = one_season((violent, seed))
                results.append({k: result[k] for k in ("seed", "violent", "day", "story_issues", "story_checks")})
                print(f"Seed {seed}, {'violent' if violent else 'default'}: {len(result['story_issues'])} violations", flush=True)
    checks = Counter()
    for r in results:
        checks.update(r["story_checks"])
        for issue in r["story_issues"]:
            loc = f"Day {issue['day']}, hour {issue['hour']}, minute {issue['minute']}, {issue['source']}"
            print(f"{issue['code']}: {loc}: {issue['message']} {issue['text']}")
    count = sum(len(r["story_issues"]) for r in results)
    print(f"{len(results)} runs; {sum(checks.values())} checks; {count} violations. Coverage: {dict(sorted(checks.items()))}")
    if args.json:
        Path(args.json).write_text(json.dumps({"runs": results, "checks": dict(checks), "violations": count}, indent=2), encoding="utf-8")
    return 1 if count else 0


if __name__ == "__main__":
    sys.exit(main())
