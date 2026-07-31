# Architecture Decisions

Source spec: [AIAssignment.pdf](AIAssignment.pdf)

## Stack
- Frontend: React + Vite + MUI (small SPA) - **changed from the original Vue.js choice** when
  phase 2 actually started, switching to Material UI (React-specific) for a cleaner Material
  Design look, and pivoting the whole frontend framework rather than reaching for a Vue
  equivalent (Vuetify). No backend impact - the API/schemas were designed framework-agnostic.
- Backend: FastAPI (Python), package manager: `uv`
- DB: SQLite (via SQLAlchemy) - stores interviews, questions, answers, summary
- LLM strategy pattern: pluggable providers, common interface
  - `GeminiProvider` (Google) - implemented
  - `OpenAIProvider` (GPT, Responses API - "codex pass" clarified as this, not the deprecated Codex model) - implemented, real token streaming
  - `MockProvider` (canned/deterministic responses - no network, for dev/demo/tests) - implemented
  - `ClaudeProvider` (Anthropic) - **dropped for now**, no API key available to test against. The
    strategy pattern makes this a drop-in addition later (implement `LLMProvider`, register in
    `providers/factory.py`) - not a design change, just deferred work.

## Repo layout
Monorepo: `backend/` (FastAPI + uv) and `frontend/` (React + Vite) in one repo.

## Flow - conversational agentic loop
Not a fixed question list generated upfront. Instead:
1. User submits topic (free text)
2. Backend seeds an internal **topic checklist** (3–5 things to find out about the user re: the topic) - generated once by the LLM from the topic, kept server-side, not shown verbatim to the user
3. Loop, each turn:
   - LLM sees: topic, checklist (with items marked covered/open), full transcript so far
   - LLM decides next question - targeting an open checklist item, and may follow up on the user's last answer before moving on (genuine conversational feel, not round-robin)
   - LLM also marks which checklist item(s) the previous answer resolved
   - Backend persists each turn (question, answer, checklist state) to SQLite
4. Loop ends when checklist fully covered (or a max-turns safety cap is hit)
5. Backend asks LLM for final summary (themes, sentiment, key points) over full transcript
6. Bonus: keyword extraction (regex/counter) + sentiment scoring (lib or LLM-scored) run alongside LLM summary, stored as separate analysis fields

Checklist updates are reported via structured output (tool-call/function-calling JSON each turn: `{checklist_updates, next_question}`), not parsed free text - reliable across all three real providers.

## Provider selection
Env-config default only (e.g. `LLM_PROVIDER=claude|gemini|openai|mock` in backend `.env`). No per-interview user-facing picker for MVP.

Open question: exact turn-loop max-turns safety cap value - decide during backend design.

## Storage & export
SQLite remains the durable store for running an interview across turns, but it's not the
deliverable format. Every completed interview is also exported to:
- **JSON** (`exports/{id}.json`) - required, directly satisfies the assignment's "store in
  JSON, text file, or database" line
- **PDF** (`exports/{id}.pdf`) - extra polish, rendered via `fpdf2` (lightweight, no headless
  browser dependency)

## Docker (optional, not the primary way to run this)
`backend/Dockerfile`, `frontend/Dockerfile` (multi-stage, nginx-served static build), and root
`docker-compose.yml` - added as a nice-to-have on top of the assignment's own requirements.
`uv sync`/`npm run dev` remain the primary, always-supported way to run the app; Docker is an
alternative, not a replacement.

Verified end-to-end, not just that the images build: `docker compose up --build`, then a full
interview (topic → 3 answers → summary with themes/sentiment/keywords/exports) driven through
the actual browser UI against the containerized frontend talking to the containerized backend,
console clean throughout. One environment-specific note: the dev sandbox's default `docker
compose` invocation hits a buildkit/cgroup permission error unrelated to these Dockerfiles;
`DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 docker compose up --build` (legacy builder) works
around it there. A normal Docker Desktop install shouldn't need that workaround.

## Non-goals (MVP)
- No auth / multi-user
- No Postgres/hosted DB - SQLite is enough for scope

## Build phasing
Terminal-first. The assignment explicitly allows a terminal UI, so that's the real MVP:
build and thoroughly test a CLI-driven backend (`cli.py` entry point over the same
`services`/`providers` layer) before touching FastAPI routes or a web frontend. This de-risked
the submission: a polished terminal tool was a complete, scoreable deliverable on its own before
phase 2 started.

Phase 2 (FastAPI HTTP layer + React frontend) is now built as a second entry point over the same
services - no business logic duplicated between the CLI and the API. See the "Frontend" stack
entry above for the Vue→React pivot.

## Quality bar priorities (from assignment's "what we're evaluating")
Ranked equally, all must be strong: code clarity/structure, prompt design/LLM interaction, UX (even terminal), overall polish.

- **Code structure**: thin FastAPI routes → fat service layer (interview orchestrator, checklist state machine) → dumb providers (pure `messages+tools in, response out`, no business logic). Strategy pattern isolated to the provider layer only.
- **Prompt design**: two distinct system prompts, not one reused - (1) interviewer persona (conversational pacing, one question at a time, follows up before moving on, never interrogates), (2) analyst (summary/theme extraction, grounded strictly in transcript, separate job/constraints from interviewing). Checklist updates via structured tool-call output (already decided), not free-text parsing.
- **UX**: give turn-by-turn feedback (streamed tokens or at least a visible "thinking" state) rather than a frozen prompt during LLM latency. Handle empty/low-effort answers with a natural follow-up instead of silently accepting them. Clear turn boundaries in terminal output.
- **Polish over breadth**: finish the core loop + summary fully before touching bonus sentiment/keyword analysis. Bonus sentiment can be a lightweight lexicon-based lib (e.g. VADER/TextBlob) rather than training/hosting a BERT model - out of scope to train anything.

## Prompt engineering method
Prompts are not hand-tuned by trial and error. A standalone eval harness (`prompt_lab/`, own `uv` project, not part of shipped app) tests candidate system prompts against scripted scenarios and scores them on a fixed rubric, judged by an LLM grader - transparent, repeatable, same rubric every time (see `prompt_lab/README.md`).

The shipped prompt was also tested directly against the real orchestrator + real providers with
adversarial scenarios (prompt injection, guardrail off-topic, adversarial pushback, low-effort
answers) - see [edge-case-testing.md](edge-case-testing.md). Found and fixed one real gap: the
same prompt produced different off-topic-request behavior across models (Gemini declined
correctly on its own, OpenAI didn't), fixed with an explicit guardrail rule rather than relying
on incidental model alignment.

## Open questions log
- (resolved) Include MockProvider - yes, for cost-free dev/demo/testing
- (resolved) "codex pass" = OpenAI GPT provider
- (resolved) "small SQL-like db" = SQLite
- (resolved) Min-turns floor = 3, max-turns cap = 8 - closes the
  gap where the model could otherwise end the interview after 1-2 turns, violating the
  assignment's "3-5 questions" requirement
- (resolved) Provider failure mid-interview: retry once, then fail loudly - no silent fallback
  to MockProvider, that would mask real bugs during grading/demo
- (resolved) Git history starts now, before backend scaffolding, for a clean commit trail
- (resolved) Claude provider dropped for now (no API key to test with) - `mock`, `gemini`,
  `openai` are the supported `LLM_PROVIDER` values; add Claude back later as a drop-in via the
  existing strategy pattern, no rework needed
