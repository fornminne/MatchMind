# MatchMind

AI multi-agent system for the Microsoft x Premier League **Inside the Game: Developer Hackathon**.
Turns synthetic, football-realistic event data into explainable match intelligence:
**ingest → interpret → explain → render → personalize**.

## Architecture (5-agent pipeline)

| Agent | Role |
|---|---|
| Ingest | Consume synthetic event stream, normalize, land raw events |
| Stats | Compute football metrics (xG-ish, pass accuracy/difficulty, speed, momentum) |
| Explainability | Reason over patterns — control vs chaos, tactical shifts, rhythm; say *why* a moment matters |
| Narrative | Generate recaps / live commentary, multi-language |
| Personalization | Reshape the same intelligence per persona (analyst vs casual; favorite club/player modes) |

Agents coordinate through shared match state and handoffs (target: **Microsoft Agent Framework** +
**Azure AI Foundry** models). This repo ships a runnable synthetic data layer and agent stubs so the
pipeline runs end-to-end offline before wiring real models.

## Tech stack (target)
GitHub Copilot, Azure AI Foundry + Foundry Agents, Microsoft Agent Framework / A2A,
Azure Container Apps + Functions (event-driven ingest), Microsoft Fabric (data), FastAPI overlay UI.

## Quick start
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Generate a sample match event stream:
python src/generate_events.py --match-id DEMO-001 --out data/sample_match.jsonl
# Stream it in real time (2x speed):
python src/generate_events.py --match-id DEMO-001 --speed 2 --stream
```

## Layout
```
data/                 generated match event streams (jsonl)
src/generate_events.py  synthetic football event generator (CLI)
src/ingest/           ingest adapters
src/agents/           stats / explainability / narrative / personalization agents
src/orchestration/    multi-agent orchestrator
ui/                   overlay / dashboard placeholder
```

## Overlay UI
```bash
source .venv/bin/activate
uvicorn ui.app:app --reload   # http://127.0.0.1:8000
```
`GET /api/match?persona=analyst&team=HOME` returns highlights + final stats as JSON.

## Foundry wiring
The narrative agent auto-detects Azure AI Foundry creds and falls back to offline
rules otherwise. Set `FOUNDRY_ENDPOINT`, `FOUNDRY_API_KEY`, `FOUNDRY_DEPLOYMENT`
to switch it on — no code change.
