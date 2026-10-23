"""Generation status without prompts, credentials, or private game content."""
import time


def generation_status(session):
    if session is None:
        return {"state": "idle"}
    s = session
    llm = s.get("llm")
    calls = llm.call_activity() if llm and hasattr(llm, "call_activity") else {"active": 0}
    if s.get("error"):
        state = "error"
    elif s.get("done"):
        state = "complete"
    elif s.get("stop") or s.get("aborted"):
        state = "stopped"
    elif s.get("roll"):
        state = "waiting_on_gm"
    elif s.get("waiting_on_viewer"):
        state = "waiting_on_viewer"
    elif calls["active"]:
        state = "waiting_on_ai"
    else:
        state = "generating"
    return {"state": state, "ai": calls, "viewer_position": s.get("pos", -1),
            "generated_ticks": len(s.get("ticks", [])),
            "seconds_since_progress": round(max(0, time.monotonic() - s.get("progress_at", time.monotonic())), 1),
            "error_type": s.get("error_type")}
