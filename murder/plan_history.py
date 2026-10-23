"""Record plan changes without depending on the engine's mixin hierarchy."""
import copy


def record_change(state, plot, who, day, hour, action, reason, replacement=None):
    entry = {"who": who, "target": plot["target"], "day": day, "hour": hour,
             "action": action, "reason": reason,
             "from": copy.deepcopy(plot.get("scheme")), "to": copy.deepcopy(replacement)}
    plot.setdefault("changes", []).append(entry)
    del plot["changes"][:-12]
    state.setdefault("plot_history", []).append(entry)
    del state["plot_history"][:-80]
    return entry
