"""Narrative agent: commentary / recaps.

Uses an Azure AI Foundry (OpenAI-compatible) model when credentials are present,
otherwise falls back to a deterministic rule-based line so the pipeline always runs.

Env vars (set at build/deploy time):
  FOUNDRY_ENDPOINT   e.g. https://<resource>.openai.azure.com
  FOUNDRY_API_KEY
  FOUNDRY_DEPLOYMENT e.g. gpt-4o-mini  (your Foundry model deployment name)
"""
import os


class NarrativeAgent:
    def __init__(self, lang="en"):
        self.lang = lang
        self._client = None
        self._deployment = os.getenv("FOUNDRY_DEPLOYMENT")
        endpoint = os.getenv("FOUNDRY_ENDPOINT")
        key = os.getenv("FOUNDRY_API_KEY")
        if endpoint and key and self._deployment:
            try:
                from openai import AzureOpenAI
                self._client = AzureOpenAI(
                    azure_endpoint=endpoint,
                    api_key=key,
                    api_version="2024-06-01",
                )
            except Exception:
                self._client = None

    @property
    def mode(self):
        return "foundry" if self._client else "offline-stub"

    def line(self, ev, explanation=None):
        base = explanation or f"{ev['minute']}' {ev['type']} — {ev.get('team','')}"
        if not self._client:
            return base
        try:
            resp = self._client.chat.completions.create(
                model=self._deployment,
                temperature=0.6,
                max_tokens=60,
                messages=[
                    {"role": "system", "content":
                        f"You are a football commentator. One vivid sentence, language={self.lang}."},
                    {"role": "user", "content":
                        f"Event: {ev}. Context: {base}. Give one broadcast-style line."},
                ],
            )
            return resp.choices[0].message.content.strip()
        except Exception:
            return base
