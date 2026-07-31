# AI Interviewer

Mini "AI Interviewer" — conducts a short AI-powered interview on a chosen topic via a
conversational agentic loop, then produces a themed summary. Built for the assignment in
[docs/AIAssignment.pdf](docs/AIAssignment.pdf).

## Status

Both phases working end-to-end against real providers:
- **Phase 1** — terminal CLI, fully hardened (adversarial testing, prompt-injection risk
  scoring, corruption guards)
- **Phase 2** — FastAPI HTTP layer + React frontend, same services layer as the CLI, no logic
  duplicated

See:
- [docs/decisions.md](docs/decisions.md) — architecture decisions and rationale
- [docs/edge-case-testing.md](docs/edge-case-testing.md) — adversarial/robustness test results, with real transcript evidence in [docs/test-evidence/](docs/test-evidence/)
- [backend/README.md](backend/README.md) — how to run the CLI and/or the API
- [frontend/README.md](frontend/README.md) — how to run the web UI
- [prompt_lab/](prompt_lab/) — standalone prompt-evaluation harness (separate from the shipped app)

## Stack

- Backend: FastAPI (Python), `uv` — terminal CLI and HTTP API, two entry points over one
  services layer
- Frontend: React + Vite + MUI (phase 2 — changed from an earlier Vue.js plan, see decisions.md)
- DB: SQLite via SQLAlchemy, plus JSON/PDF export per interview
- LLM providers: Gemini and OpenAI (implemented, real token streaming for OpenAI in the CLI),
  Mock (implemented), Claude (dropped for now, no API key — drop-in addition later via the same
  strategy pattern)

## Running it

**Terminal:**

```bash
cd backend
cp .env.example .env   # fill in GEMINI_API_KEY and/or OPENAI_API_KEY, or leave LLM_PROVIDER=mock
uv sync
uv run python -m app.cli
```

**Web UI** (two terminals):

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
```
```bash
cd frontend && npm install && npm run dev
```

Then open `http://localhost:5173`. See [backend/README.md](backend/README.md) and
[frontend/README.md](frontend/README.md) for details.

**Tests:**

```bash
cd backend && uv run pytest
```
```bash
cd frontend && npm run test
```
