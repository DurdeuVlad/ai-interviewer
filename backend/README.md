# backend

FastAPI + `uv` backend for the AI Interviewer. Two entry points over the same services layer:
a terminal CLI (phase 1) and an HTTP API (phase 2, for the [`../frontend`](../frontend) React
app). Neither duplicates business logic — both drive `app/services/orchestrator.py` etc. See
[../docs/implementation-plan.md](../docs/implementation-plan.md) for the full build plan.

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
`LLM_PROVIDER=gemini` or `LLM_PROVIDER=openai` in `.env` (with the matching API key) for a real
interview. `claude` is dropped for now (no API key to test against) — the strategy pattern
makes it a drop-in addition later.

## Run the API (for the frontend)

```bash
uv run uvicorn app.main:app --reload --port 8000
```

CORS is controlled by `CORS_ORIGIN` in `.env` (defaults to `http://localhost:5173`, matching
Vite's default port) — update it if the frontend runs on a different port. Interactive API docs
(Swagger UI) are available at `http://localhost:8000/docs` once running.

Endpoints: `POST /interviews`, `POST /interviews/{id}/answer`, `GET /interviews/{id}`,
`GET /interviews/{id}/summary`, `GET /interviews/{id}/export/{json,pdf}`. `DEBUG_MODE=true`
includes a `debug` block (reasoning, checklist, injection risk score) in responses, same as the
CLI's debug printing — omitted entirely otherwise.

## Tests

```bash
uv sync --dev
uv run pytest
```

17 tests, MockProvider only (no network calls, no real API key needed) — orchestrator's
MIN_TURNS/MAX_TURNS floor/cap, injection-risk immediate/cumulative bail-out, the atomic
answer-race guard, analysis.py's corruption-retry/fallback, and the HTTP routes end-to-end via
FastAPI's `TestClient`.

## Layout

- `app/models.py` / `app/db.py` — SQLAlchemy models + session (`interviews`, `turns`, `summaries`)
- `app/providers/` — strategy pattern: `base.py` interface, `mock_provider.py` / `gemini_provider.py` /
  `openai_provider.py` (all implemented; `claude_provider.py` not built, see decisions.md)
- `app/services/orchestrator.py` — checklist state machine, enforces the 3-turn floor / 8-turn cap
- `app/services/analysis.py` — final summary + bonus keyword extraction / VADER sentiment
- `app/services/export.py` — JSON + PDF export per interview, written to `exports/`
- `app/prompts/` — the two system prompts (interviewer, analyst), copied from the graded
  `prompt_lab/` variants
- `app/cli.py` — terminal entry point (phase 1)
- `app/main.py` / `app/routes/interviews.py` / `app/api_schemas.py` — HTTP entry point (phase 2),
  thin routes over the same services, distinct request/response DTOs from the internal
  `app/schemas.py` used by the orchestrator/providers

## Output

Every completed interview writes `exports/{id}.json` and `exports/{id}.pdf` (both gitignored —
they're generated user data, not repo content).
