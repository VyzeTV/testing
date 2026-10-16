"""Headless mock weeks: sanity distribution by day and how many turns the engine decided itself, with the mind layer on or off.
Run:  python tests/week_metrics.py      (mock backend only; never touches your saves)"""
import os
import statistics
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_metrics_")

from murder.engine import DayRunner   # noqa: E402
from murder.llm import LLM            # noqa: E402
from murder.world import World, new_state   # noqa: E402


class Counting(LLM):
    """The mock LLM, counting every call the engine makes (decisions, conversations, reactions, host and summary calls)."""
    n = 0

    def decide(self, *a, **k):
        type(self).n += 1
        return super().decide(*a, **k)

    def converse(self, *a, **k):
        type(self).n += 1
        return super().converse(*a, **k)

    def react(self, *a, **k):
        type(self).n += 1
        return super().react(*a, **k)

    def host_json(self, *a, **k):
        type(self).n += 1
        return super().host_json(*a, **k)

    def summarize(self, *a, **k):
        type(self).n += 1
        return super().summarize(*a, **k)


def run_week(seed, mind=1, engine=1, days=7):
    w = World(new_state(3))
    ticks = []
    meds, low, calls = [], [], {"model": 0, "engine": 0}
    for d in range(3, 3 + days):
        w.state["day"] = d
        r = DayRunner(w, Counting(backend="mock"), ticks.append, step=2, murders=True, rule_mode="none", seed=seed + d)
        r.tuning_get = lambda: {"mind": mind, "engine_decisions": engine}
        r.run()
        san = [a["sanity"] for a in w.agents.values() if a.get("status", "alive") == "alive"]
        if not san or w.state.get("over"):
            break
        meds.append(statistics.median(san))
        low.append(sum(1 for x in san if x < 20) / len(san))
        t = w.state.get("telemetry", {}).get(str(d), {}).get("decision", {})
        calls["model"] += t.get("model", 0)
        calls["engine"] += t.get("engine", 0)
    for t in ticks:
        for e in t.get("events", []):
            if e["type"] in ("plot", "attack", "madness", "assault", "betrayal", "friction"):
                calls["ev_" + e["type"]] = calls.get("ev_" + e["type"], 0) + 1
    calls["all"] = Counting.n
    Counting.n = 0
    calls["days"] = len(meds)
    return meds, low, calls, len(w.state["graveyard"])


if __name__ == "__main__":
    for label, kw in (("old sanity, model decides everything", {"mind": 0, "engine": 0}), ("mind layer, model decides everything", {"mind": 1, "engine": 0}), ("mind layer + engine routine turns", {"mind": 1, "engine": 1})):
        M, L, C, D = [], [], {"model": 0, "engine": 0, "all": 0, "days": 0}, 0
        for seed in (10, 20, 30, 40):
            m, l, c, d = run_week(seed, **kw)
            M.append(m)
            L.append(l)
            C["model"] += c["model"]
            C["engine"] += c["engine"]
            C["all"] += c["all"]
            C["days"] += c["days"]
            for k_, v_ in c.items():
                if k_.startswith("ev_"):
                    C[k_] = C.get(k_, 0) + v_
            D += d
        n = max(len(x) for x in M)
        med = [round(statistics.mean(x[i] for x in M if len(x) > i)) for i in range(n)]
        lo = [round(100 * statistics.mean(x[i] for x in L if len(x) > i)) for i in range(n)]
        print(f"{label}: median sanity by day {med}; % of survivors under 20: {lo}; decisions model/engine {C['model']}/{C['engine']}; model calls per day {C['all'] / max(1, C['days']):.0f}; deaths {D}; " + ", ".join(f"{k_[3:]} {v_}" for k_, v_ in sorted(C.items()) if k_.startswith("ev_")))
