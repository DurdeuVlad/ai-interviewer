# frontend

React + Vite + MUI frontend for the AI Interviewer — phase 2, a browser UI over the FastAPI
backend in [`../backend`](../backend). Not required for the assignment (the terminal CLI is a
complete deliverable on its own), built for a nicer interactive experience.

## Setup

```bash
npm install
```

`.env.development` sets `VITE_API_BASE=http://localhost:8000` — update it if the backend runs
on a different port.

## Run it

The backend must already be running (see [../backend/README.md](../backend/README.md), "Run the
API" section) before this will do anything useful:

```bash
npm run dev
```

Opens on `http://localhost:5173` by default.

## Tests

```bash
npm run test
```

20 tests via Vitest + Testing Library — sentiment bucketing, the api client's error
normalization, `ErrorBanner`'s 409-reason distinction (already-ended vs. duplicate-answer),
`ChatBubble` alignment, and the `interviewEvents` window bridge.

## Docker

```bash
docker build -t ai-interviewer-frontend --build-arg VITE_API_BASE=http://localhost:8000 .
docker run -p 5173:80 ai-interviewer-frontend
```

`VITE_API_BASE` is baked into the static build at image-build time (Vite doesn't read `VITE_*`
vars at runtime), so it must be passed as a `--build-arg`, not `-e`. Or use
`docker compose up --build` from the repo root — see
[../docker-compose.yml](../docker-compose.yml).

## Layout

- `src/api/client.js` — thin fetch wrapper, one function per backend endpoint, normalizes non-2xx
  responses into an `ApiError { status, detail }`
- `src/views/` — `TopicEntryView` (`/`), `InterviewView` (`/interview/:id`),
  `SummaryView` (`/interview/:id/summary`) — no Redux/Context, each view holds its own local state
- `src/components/` — `TypewriterText` (client-side fake-streaming effect over the full question
  text — the backend returns one response, not a real token stream), `ThinkingIndicator`,
  `ThemeBadge` (sentiment-colored chip), `ErrorBanner` (shared error presentation, with a
  "View summary" link instead of "Try again" for the 409 already-completed case)
- `src/utils/sentiment.js` — ports the CLI's `_sentiment_label` bucketing to JS, so the sentiment
  score reads the same "+0.128 (positive)" way in both places

## Notes

- No real SSE/streaming — a deliberate choice, see `docs/decisions.md`. The backend's real
  OpenAI token streaming (used by the CLI) isn't exposed over HTTP; the typewriter effect here is
  a client-side animation over an already-complete response.
- `npm audit` flags `react-router` advisories that only apply to its SSR/RSC/server-action
  features — this app is a plain client-side SPA (`BrowserRouter`, no server rendering, no server
  actions), so that attack surface doesn't apply here.
