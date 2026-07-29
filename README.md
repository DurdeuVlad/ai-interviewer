# AI Interviewer

Mini "AI Interviewer" — conducts a short AI-powered interview on a chosen topic via a
conversational agentic loop, then produces a themed summary. Built for the assignment in
[docs/AIAssignment.pdf](docs/AIAssignment.pdf).

## Status

Planning complete, backend not yet scaffolded. See:
- [docs/decisions.md](docs/decisions.md) — architecture decisions and rationale
- [docs/implementation-plan.md](docs/implementation-plan.md) — concrete build plan (DB schema, API/CLI contract, build order)
- [docs/external/](docs/external/) — reference docs for the stack (Claude/Gemini/OpenAI APIs, uv, FastAPI, SQLAlchemy, Vue)
- [prompt_lab/](prompt_lab/) — standalone prompt-evaluation harness (separate from the shipped app)

## Stack

- Backend: FastAPI (Python), `uv` — terminal CLI first, HTTP API second (see build phasing in decisions.md)
- Frontend: Vue.js + Vite (phase 2, only if time allows)
- DB: SQLite via SQLAlchemy, plus JSON/PDF export per interview
- LLM providers: Claude, Gemini, OpenAI, and a Mock provider — pluggable via a strategy pattern

## Running it

Not yet available — backend scaffolding hasn't started.
