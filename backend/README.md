# backend

FastAPI + `uv` backend for the AI Interviewer. Phase 1 (current): terminal CLI only, driven by
`MockProvider`. See [../docs/implementation-plan.md](../docs/implementation-plan.md) for the
full build plan.

## Setup

```bash
cp .env.example .env
uv sync
```

## Run the interview (terminal)

```bash
uv run python -m app.cli
```

Defaults to `LLM_PROVIDER=mock` (no API key needed, deterministic responses) — set
`LLM_PROVIDER=claude` etc. in `.env` once a real provider is implemented.

## Layout

- `app/models.py` / `app/db.py` — SQLAlchemy models + session (`interviews`, `turns`, `summaries`)
- `app/providers/` — strategy pattern: `base.py` interface, `mock_provider.py` (implemented),
  `claude_provider.py` / `gemini_provider.py` / `openai_provider.py` (not yet built)
- `app/services/orchestrator.py` — checklist state machine, enforces the 3-turn floor / 8-turn cap
- `app/services/analysis.py` — final summary + bonus keyword extraction / VADER sentiment
- `app/services/export.py` — JSON + PDF export per interview, written to `exports/`
- `app/prompts/` — the two system prompts (interviewer, analyst), copied from the graded
  `prompt_lab/` variants
- `app/cli.py` — terminal entry point

## Output

Every completed interview writes `exports/{id}.json` and `exports/{id}.pdf` (both gitignored —
they're generated user data, not repo content).
