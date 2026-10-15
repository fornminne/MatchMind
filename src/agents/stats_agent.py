"""Stats agent: aggregate raw events into football metrics."""
from collections import defaultdict


class StatsAgent:
    def __init__(self):
        self.state = {"HOME": defaultdict(float), "AWAY": defaultdict(float)}

    def handle(self, ev):
        t = ev.get("team")
        s = self.state.get(t)
        if s is None:
            return None
        et = ev["type"]
        if et == "pass":
            s["passes"] += 1
            s["passes_completed"] += 1 if ev.get("complete") else 0
        elif et in ("shot", "goal"):
            s["shots"] += 1
            s["xg"] += ev.get("xg", 0.0)
            if ev.get("goal"):
                s["goals"] += 1
        elif et == "tackle":
            s["tackles"] += 1
        return self.snapshot()

    def snapshot(self):
        out = {}
        for t, s in self.state.items():
            passes = s["passes"] or 1
            out[t] = {
                "passes": int(s["passes"]),
                "pass_accuracy": round(s["passes_completed"] / passes, 3),
                "shots": int(s["shots"]),
                "xg": round(s["xg"], 2),
                "goals": int(s["goals"]),
                "tackles": int(s["tackles"]),
            }
        return out
