"""Voice a finished run again with another model: the events stay exactly as they happened, only the words change.

With `keep_voice` on (the seed finder turns it on; the app leaves it off), every voicing call keeps its prompt in the day's record: a conversation's
(`entry["vp"]`, with its beats in `entry["vb"]`), a trial sequence's and a gathering's (`entry["vp"]`), and TereVi's broadcasts (`tick["vlog"]`). The
long system prompts are stored once per day, by hash, in `tick["vsys"]`.

`revoice_day` later sends those same prompts to a real model and puts the answers where the mock's words were. Nothing the engine decided changes:
not who spoke, when, where or about what. VoiceKeepMixin is mixed into DayRunner (engine.py).
"""
import hashlib
from concurrent.futures import ThreadPoolExecutor

from .voice import check_lines


class VoiceKeepMixin:
    def vkeep(self, sysm, user, ctx):
        """The prompt of a voicing call, kept for voicing it again later. None unless `keep_voice` is on."""
        if not self.__dict__.get("keep_voice"):
            return None
        h = hashlib.md5(sysm.encode("utf-8")).hexdigest()[:12]
        known = self.__dict__.setdefault("_vsys_all", set())
        if h not in known:
            known.add(h)
            self.__dict__.setdefault("_vsys_new", {})[h] = sysm
        return {"s": h, "u": user, "c": dict(ctx or {})}

    def vkeep_broadcast(self, sysm, user, ctx, text):
        vp = self.vkeep(sysm, user, ctx)
        if vp and isinstance(text, str):
            self.__dict__.setdefault("_vlog", []).append(dict(vp, k="broadcast", t=text))

    def vkeep_flush(self, tick):
        """At emit: the system prompts first used in this tick, and the broadcasts asked for since the last one."""
        new = self.__dict__.pop("_vsys_new", None)
        if new:
            tick["vsys"] = new
        log = self.__dict__.pop("_vlog", None)
        if log:
            tick["vlog"] = log


def _indexed(res, n):
    got = {}
    for ln in (res or {}).get("lines") or []:
        if isinstance(ln, dict) and isinstance(ln.get("i"), int) and 0 <= ln["i"] < n and str(ln.get("text", "")).strip():
            got[ln["i"]] = str(ln["text"]).strip()[:260]
    return got


def _swap_any(o, old, new):
    """Replace the first string equal to `old` anywhere in a tick (an execution or an escape keeps its broadcast in its own record). True if found."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("vlog", "vsys", "vp", "vb"):
                continue
            if v == old:
                o[k] = new
                return True
            if isinstance(v, (dict, list)) and _swap_any(v, old, new):
                return True
    elif isinstance(o, list):
        for i, v in enumerate(o):
            if v == old:
                o[i] = new
                return True
            if isinstance(v, (dict, list)) and _swap_any(v, old, new):
                return True
    return False


def revoice_day(days, runner, llm, workers=4, log=print, only=None, pick=None):
    """Voice the recorded days again. `days` is a list of tick lists (one per day; a system prompt may be first stored on an earlier day), changed in place.
    `runner` is a DayRunner on the season's state (for names and line tidying); `llm` the model to voice with. `only`: None, or a set of kinds
    ("conv", "trial", "scene", "broadcast"). `pick`: None, or the indexes of the days to voice (the others only lend their stored prompts). Returns counts."""
    sysd = {}
    for ticks in days:
        for t in ticks:
            sysd.update(t.get("vsys") or {})
    jobs = []
    for di, ticks in enumerate(days):
        if pick is not None and di not in pick:
            continue
        for t in ticks:
            for e in t.get("talk") or []:
                vp = e.get("vp")
                if not vp or vp["s"] not in sysd:
                    continue
                kind = "conv" if e.get("vb") is not None else "trial" if e.get("segment") else "scene"
                if only is None or kind in only:
                    jobs.append((kind, e, vp))
            for b in t.get("vlog") or []:
                if b["s"] in sysd and (only is None or "broadcast" in only):
                    jobs.append(("broadcast", dict(b, at=(ticks, ticks.index(t))), b))
    stats = {"asked": len(jobs), "voiced": 0, "failed": 0, "lines": 0, "broadcasts": 0}

    def ask(job):
        kind, e, vp = job
        fn = llm.broadcast if kind == "broadcast" else llm.voice
        return fn(sysd[vp["s"]], vp["u"], vp["c"])

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(ask, j) for j in jobs]
        answers = []
        for j, f in zip(jobs, futs):
            try:
                answers.append(f.result())
            except Exception as ex:  # noqa: BLE001
                answers.append(None)
                stats["failed"] += 1
                log(f"  {j[0]} failed: {str(ex)[:100]}")
    taken = set()
    for (kind, e, vp), res in zip(jobs, answers):
        if res is None:
            continue
        if kind == "broadcast":
            ticks, i = e["at"]
            spot = next(((ti, bi) for ti in range(i, min(len(ticks), i + 2)) for bi, b in enumerate(ticks[ti].get("broadcasts") or [])
                         if b.get("text") == e["t"] and (id(ticks), ti, bi) not in taken), None)       # its own block (or the next): the mock says the same thing every day
            if isinstance(res, str) and res.strip() and (spot or _swap_any(ticks[i], e["t"], res.strip())):
                if spot:
                    taken.add((id(ticks),) + spot)
                    ticks[spot[0]]["broadcasts"][spot[1]]["text"] = res.strip()
                stats["broadcasts"] += 1
                stats["voiced"] += 1
            continue
        lines = e["lines"]
        if kind == "conv":
            new, fixed = check_lines(runner, e["vb"], res, runner.rng)
            if fixed >= len(new):
                stats["failed"] += 1
                continue
            for ln in lines:
                b = ln.get("b")
                if isinstance(b, int) and 0 <= b < len(new) and new[b]["speaker"] == ln["speaker"]:
                    ln["text"] = runner.clean_line(ln["speaker"], new[b]["kind"], new[b]["text"]) or new[b]["text"]
                    ln["kind"] = new[b]["kind"]
                    stats["lines"] += 1
        else:
            got = _indexed(res, len(lines))
            if not got:
                stats["failed"] += 1
                continue
            for i, text in got.items():
                ln = lines[i]
                if ln.get("move") == "cry":
                    continue                                        # an objection cry is never reworded
                ln["text"] = (runner.clean_line(ln["speaker"], ln.get("kind", "say"), text) if ln["speaker"] in runner.world.cast else text) or text
                stats["lines"] += 1
        e["voiced"] = True
        stats["voiced"] += 1
    return stats


def strip_prompts(ticks):
    """Drop the kept prompts from a day's record (they are only needed for voicing again)."""
    for t in ticks:
        t.pop("vsys", None)
        t.pop("vlog", None)
        for e in t.get("talk") or []:
            e.pop("vp", None)
            e.pop("vb", None)
