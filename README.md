# AI Interviewer

**v1.0.0** — submission snapshot.

Mini "AI Interviewer" — conducts a short AI-powered interview on a chosen topic via a
conversational agentic loop, then produces a themed summary. Built for the assignment in
[docs/AIAssignment.pdf](docs/AIAssignment.pdf).

## Requirements

- Python 3.12+ and [`uv`](https://docs.astral.sh/uv/) (backend)
- Node 18+ and npm (frontend, only if you want the web UI)
- Docker + Docker Compose (optional, only for the Docker path below)
- No API key is required to try it — it runs out of the box against a deterministic mock
  provider (`LLM_PROVIDER=mock`, the default in `.env.example`). Add a `GEMINI_API_KEY` or
  `OPENAI_API_KEY` only if you want a real LLM-driven interview.

## Running it

**Terminal** (the core deliverable — no API key needed to try it):

```bash
cd backend
cp .env.example .env
uv sync
uv run python -m app.cli
```

**Web UI** — needs the backend running first (two terminals):

```bash
cd backend
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```
```bash
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173` in a browser. See [backend/README.md](backend/README.md) and
[frontend/README.md](frontend/README.md) for more detail on each half.

**Docker** (optional, both services in one command, no local Python/Node setup needed):

```bash
docker compose up --build
```

Backend on `http://localhost:8000`, frontend on `http://localhost:5173`. Defaults to
`LLM_PROVIDER=mock` — set real provider vars in a `.env` file at the repo root (read
automatically by `docker compose`, e.g. `LLM_PROVIDER=openai`, `OPENAI_API_KEY=...`) for a real
interview. DB and exports persist in named volumes (`backend_db`, `backend_exports`) across
restarts. Verified end-to-end (full interview through the browser against the containerized
stack, see [docs/decisions.md](docs/decisions.md)). See [docker-compose.yml](docker-compose.yml).

**Tests:**

```bash
cd backend && uv run pytest
```
```bash
cd frontend && npm run test
```

## Status

Both phases working end-to-end against real providers:
- **Phase 1** — terminal CLI, fully hardened (adversarial testing, prompt-injection risk
  scoring, corruption guards)
- **Phase 2** — FastAPI HTTP layer + React frontend, same services layer as the CLI, no logic
  duplicated

## Stack

- Backend: FastAPI (Python), `uv` — terminal CLI and HTTP API, two entry points over one
  services layer
- Frontend: React + Vite + MUI (phase 2 — changed from an earlier Vue.js plan, see decisions.md)
- DB: SQLite via SQLAlchemy, plus JSON/PDF export per interview
- LLM providers: Gemini and OpenAI (implemented, real token streaming for OpenAI in the CLI),
  Mock (implemented), Claude (dropped for now, no API key — drop-in addition later via the same
  strategy pattern)

## Further documentation

- [docs/decisions.md](docs/decisions.md) — architecture decisions and rationale
- [docs/edge-case-testing.md](docs/edge-case-testing.md) — adversarial/robustness test results, with real transcript evidence in [docs/test-evidence/](docs/test-evidence/)
- [backend/README.md](backend/README.md) — how to run the CLI and/or the API
- [frontend/README.md](frontend/README.md) — how to run the web UI
- [prompt_lab/](prompt_lab/) — standalone prompt-evaluation harness (separate from the shipped app)
