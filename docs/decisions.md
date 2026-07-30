# Architecture Decisions

Source spec: [AIAssignment.pdf](AIAssignment.pdf)

## Stack
- Frontend: Vue.js (small SPA)
- Backend: FastAPI (Python), package manager: `uv`
- DB: SQLite (via SQLAlchemy) — stores interviews, questions, answers, summary
- LLM strategy pattern: pluggable providers, common interface
  - `GeminiProvider` (Google) — implemented
  - `OpenAIProvider` (GPT, Responses API — "codex pass" clarified as this, not the deprecated Codex model) — implemented, real token streaming
  - `MockProvider` (canned/deterministic responses — no network, for dev/demo/tests) — implemented
  - `ClaudeProvider` (Anthropic) — **dropped for now**, no API key available to test against. The
    strategy pattern makes this a drop-in addition later (implement `LLMProvider`, register in
    `providers/factory.py`) — not a design change, just deferred work. `docs/external/anthropic.md`
    stays as the reference for whenever it's picked back up.

## Repo layout
Monorepo: `backend/` (FastAPI + uv) and `frontend/` (Vue + Vite) in one repo.

## Flow — conversational agentic loop
Not a fixed question list generated upfront. Instead:
1. User submits topic (free text)
2. Backend seeds an internal **topic checklist** (3–5 things to find out about the user re: the topic) — generated once by the LLM from the topic, kept server-side, not shown verbatim to the user
3. Loop, each turn:
   - LLM sees: topic, checklist (with items marked covered/open), full transcript so far
   - LLM decides next question — targeting an open checklist item, and may follow up on the user's last answer before moving on (genuine conversational feel, not round-robin)
   - LLM also marks which checklist item(s) the previous answer resolved
   - Backend persists each turn (question, answer, checklist state) to SQLite
4. Loop ends when checklist fully covered (or a max-turns safety cap is hit)
5. Backend asks LLM for final summary (themes, sentiment, key points) over full transcript
6. Bonus: keyword extraction (regex/counter) + sentiment scoring (lib or LLM-scored) run alongside LLM summary, stored as separate analysis fields

Checklist updates are reported via structured output (tool-call/function-calling JSON each turn: `{checklist_updates, next_question}`), not parsed free text — reliable across all three real providers.

## Provider selection
Env-config default only (e.g. `LLM_PROVIDER=claude|gemini|openai|mock` in backend `.env`). No per-interview user-facing picker for MVP.

Open question: exact turn-loop max-turns safety cap value — decide during backend design.

## Build phasing
Terminal-first. The assignment explicitly allows a terminal UI, so that's the real MVP:
build and thoroughly test a CLI-driven backend (`cli.py` entry point over the same
`services`/`providers` layer) before touching FastAPI routes or the Vue frontend. Web UI is
phase 2, only if time remains — see [implementation-plan.md](implementation-plan.md) for the
full build order. This de-risks the submission: a polished terminal tool is a complete,
scoreable deliverable on its own.

## Storage & export
SQLite remains the durable store for running an interview across turns, but it's not the
deliverable format. Every completed interview is also exported to:
- **JSON** (`exports/{id}.json`) — required, directly satisfies the assignment's "store in
  JSON, text file, or database" line
- **PDF** (`exports/{id}.pdf`) — extra polish, rendered via `fpdf2` (lightweight, no headless
  browser dependency)

## Non-goals (MVP)
- No auth / multi-user
- No Postgres/hosted DB — SQLite is enough for scope

## Quality bar priorities (from assignment's "what we're evaluating")
Ranked equally, all must be strong: code clarity/structure, prompt design/LLM interaction, UX (even terminal), overall polish.

- **Code structure**: thin FastAPI routes → fat service layer (interview orchestrator, checklist state machine) → dumb providers (pure `messages+tools in, response out`, no business logic). Strategy pattern isolated to the provider layer only.
- **Prompt design**: two distinct system prompts, not one reused — (1) interviewer persona (conversational pacing, one question at a time, follows up before moving on, never interrogates), (2) analyst (summary/theme extraction, grounded strictly in transcript, separate job/constraints from interviewing). Checklist updates via structured tool-call output (already decided), not free-text parsing.
- **UX**: give turn-by-turn feedback (streamed tokens or at least a visible "thinking" state) rather than a frozen prompt during LLM latency. Handle empty/low-effort answers with a natural follow-up instead of silently accepting them. Clear turn boundaries in terminal output.
- **Polish over breadth**: finish the core loop + summary fully before touching bonus sentiment/keyword analysis. Bonus sentiment can be a lightweight lexicon-based lib (e.g. VADER/TextBlob) rather than training/hosting a BERT model — out of scope to train anything.

## Prompt engineering method
Prompts are not hand-tuned by trial and error. A standalone eval harness (`prompt_lab/`, own `uv` project, not part of shipped app) tests candidate system prompts against scripted scenarios and scores them on a fixed rubric, judged by an LLM grader — transparent, repeatable, same rubric every time (see `prompt_lab/README.md` once built).

## Open questions log
- (resolved) Include MockProvider — yes, for cost-free dev/demo/testing
- (resolved) "codex pass" = OpenAI GPT provider
- (resolved) "small SQL-like db" = SQLite
- (resolved) Min-turns floor = 3, max-turns cap = 8 (see implementation-plan.md) — closes the
  gap where the model could otherwise end the interview after 1-2 turns, violating the
  assignment's "3-5 questions" requirement
- (resolved) Provider failure mid-interview: retry once, then fail loudly — no silent fallback
  to MockProvider, that would mask real bugs during grading/demo
- (resolved) Git history starts now, before backend scaffolding, for a clean commit trail
- (resolved) Claude provider dropped for now (no API key to test with) — `mock`, `gemini`,
  `openai` are the supported `LLM_PROVIDER` values; add Claude back later as a drop-in via the
  existing strategy pattern, no rework needed
