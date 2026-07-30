# AI Interviewer

Mini "AI Interviewer" — conducts a short AI-powered interview on a chosen topic via a
conversational agentic loop, then produces a themed summary. Built for the assignment in
[docs/AIAssignment.pdf](docs/AIAssignment.pdf).

## Status

Phase 1 (terminal CLI backend) working end-to-end against real providers. See:
- [docs/decisions.md](docs/decisions.md) — architecture decisions and rationale
- [docs/implementation-plan.md](docs/implementation-plan.md) — concrete build plan (DB schema, API/CLI contract, build order)
- [docs/edge-case-testing.md](docs/edge-case-testing.md) — adversarial/robustness test results
- [docs/external/](docs/external/) — reference docs for the stack (Gemini/OpenAI/Anthropic APIs, uv, FastAPI, SQLAlchemy, Vue)
- [backend/README.md](backend/README.md) — how to run it
- [prompt_lab/](prompt_lab/) — standalone prompt-evaluation harness (separate from the shipped app)

## Stack

- Backend: FastAPI (Python), `uv` — terminal CLI first (done), HTTP API second (not started, see build phasing in decisions.md)
- Frontend: Vue.js + Vite (phase 2, only if time allows — not started)
- DB: SQLite via SQLAlchemy, plus JSON/PDF export per interview
- LLM providers: Gemini and OpenAI (implemented, real token streaming for OpenAI), Mock (implemented), Claude (dropped for now, no API key — drop-in addition later via the same strategy pattern)

## Running it

```bash
cd backend
cp .env.example .env   # fill in GEMINI_API_KEY and/or OPENAI_API_KEY, or leave LLM_PROVIDER=mock
uv sync
uv run python -m app.cli
```

See [backend/README.md](backend/README.md) for details.
