"""Minimal offline orchestrator wiring the five agents over an event stream.

Replace the direct calls with Microsoft Agent Framework handoffs + Foundry models.
"""
import json
import sys
sys.path.insert(0, "src")
from agents import StatsAgent, ExplainabilityAgent, NarrativeAgent, PersonalizationAgent


def run(path, persona="casual", favorite_team="HOME", lang="en"):
    stats = StatsAgent()
    explain = ExplainabilityAgent()
    narrate = NarrativeAgent(lang=lang)
    personalize = PersonalizationAgent()
    feed = []
    with open(path) as f:
        for raw in f:
            ev = json.loads(raw)
            snap = stats.handle(ev)
            why = explain.explain(ev, snap)
            if why:
                line = narrate.line(ev, why)
                feed.append(personalize.view(line, persona, favorite_team))
    return {"highlights": feed, "final_stats": stats.snapshot()}


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "data/sample_match.jsonl"
    out = run(p)
    for h in out["highlights"][:15]:
        print(h["text"])
    print("FINAL STATS:", json.dumps(out["final_stats"]))
