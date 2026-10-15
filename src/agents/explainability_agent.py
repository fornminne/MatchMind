"""Explainability agent: say WHY a moment matters (rule stubs; swap for Foundry model)."""


class ExplainabilityAgent:
    def explain(self, ev, stats):
        et = ev["type"]
        if et == "goal":
            return (f"Goal for {ev['team']} ({ev['minute']}'): shifts the score to "
                    f"{ev['score']['HOME']}-{ev['score']['AWAY']}. High-leverage moment.")
        if et == "shot" and ev.get("xg", 0) >= 0.3:
            return f"Big chance for {ev['team']} (xG {ev['xg']}) at {ev['minute']}'."
        if et == "pressure" and ev.get("intensity", 0) >= 0.8:
            return f"Intense press by {ev['team']} — control tilting."
        return None
