"""Turn recorded days into a readable story (Markdown). No AI calls."""
import glob
import json
import os

HOST_NAMES = {"terevi": "TereVi", "neovi": "NeoVi"}


def _load(path):
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def story_markdown(runs_dir, names, day=None):
    nm = lambda i: names.get(i) or HOST_NAMES.get(i) or str(i)
    parts = ["# Murder Channel: the story so far\n"]
    paths = sorted(glob.glob(os.path.join(runs_dir, "day_*", "ticks.jsonl")))
    if day is not None:
        paths = [p for p in paths if os.path.basename(os.path.dirname(p)) == f"day_{int(day):02d}"]
    if not paths:
        raise ValueError("No recorded days to export.")
    for p in paths:
        ticks = _load(p)
        if not ticks:
            continue
        parts.append(f"\n## Day {ticks[0]['day']}\n")
        for t in ticks:
            parts.append(f"\n### {t['time']}" + (f" ({t['type']})" if t.get("type") else "") + "\n")
            for b in t.get("broadcasts", []) or ([t["broadcast"]] if t.get("broadcast") else []):
                parts.append(f"> **TereVi:** {b['text']}\n")
            if t.get("rule_announce"):
                parts.append(f"> **Rule of the day, {t['rule_announce']['title']}:** {t['rule_announce']['text']}\n")
            for e in t.get("events", []):
                if e.get("vis") == "gm" or e.get("type") in ("arrive", "move", "stat"):
                    continue
                parts.append(f"- {e['text']}")
            for g in t.get("talk", []):
                parts.append(f"\n*{g['room'].replace('_', ' ').title()}*\n")
                for l in g["lines"]:
                    parts.append((f"- *{nm(l['speaker'])} {l['text']}*" if l["kind"] == "act" else f"- **{nm(l['speaker'])}:** {l['text']}"))
            for c in t.get("confessionals", []) or []:
                parts.append(f"\n> *Confessional, {nm(c['id'])}:* {c['text']}\n")
            tr = t.get("trial")
            if tr:
                parts.append("\n**Class trial votes**\n")
                for v in tr["votes"]:
                    parts.append(f"- {nm(v['voter'])} votes for {nm(v['target']) if v['target'] != 'nobody' else 'nobody'}: {v.get('reason', '')}")
            if t.get("execution"):
                parts.append(f"\n> **Execution of {nm(t['execution']['id'])}:** {t['execution']['scene']}\n")
            if t.get("escape"):
                parts.append(f"\n> **{nm(t['escape']['id'])} escapes:** {t['escape']['text']}\n")
            if t.get("ending"):
                parts.append(f"\n## {t['ending']['title']}\n\n{t['ending']['text']}\n")
            if t.get("recap"):
                r = t["recap"]
                parts.append(f"\n**Episode recap, {r['title']}:** {r['recap']}")
                for a in r.get("awards", []):
                    parts.append(f"- {a['title']}: {nm(a['who'])} ({a['why']})")
    return "\n".join(parts) + "\n"
