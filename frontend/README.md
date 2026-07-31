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
vars at runtime), so it must be passed as a `--build-arg`, not `-e`. Or `docker compose up
--build` from the repo root — see [../docker-compose.yml](../docker-compose.yml).

## Layout

Full-screen, two-pane messaging-app layout: a conversation sidebar plus one chat panel, two
routes (`/` and `/interview/:id`) both rendered by the same `ChatPanel` — no Redux/Context, each
piece fetches its own data.

- `src/App.jsx` — full-viewport shell; responsive `Drawer` (permanent above the `md` breakpoint,
  a temporary overlay below it) wrapping `Sidebar`, routes to `ChatPanel`
- `src/api/client.js` — thin fetch wrapper, one function per backend endpoint, normalizes non-2xx
  responses into an `ApiError { status, detail }`
- `src/views/`
  - `TopicEntryView` — the "new chat" form (topic input), rendered inside `ChatPanel` when there's
    no interview id yet
  - `ChatPanel` — the whole conversation thread for `/` and `/interview/:id`: loads/streams the
    transcript, renders `ChatBubble`s and the live question, and once the interview completes,
    fetches and appends the summary inline in the same thread (no separate summary route)
- `src/components/`
  - `Sidebar` — list of past interviews (topic, status, date), "New chat" button, refetches on
    route change and on a custom `interviews-changed` window event (see `interviewEvents.js`)
  - `ChatHeader` — sticky top bar per conversation, with the mobile hamburger menu button
  - `ChatBubble` — left/right-aligned message bubble (assistant vs. user)
  - `InterviewSummaryCard` — themes/key points/feedback/keyword-extract/sentiment + export links,
    rendered as the last item in the thread once an interview is done
  - `TypewriterText` — client-side fake-streaming effect over the full question text (the backend
    returns one response, not a real token stream)
  - `ThinkingIndicator`, `ThemeBadge` (sentiment-colored chip), `ErrorBanner` (shared error
    presentation — distinguishes an already-ended interview, which gets a "View summary" link,
    from a duplicate-answer race, which gets "Try again", both are HTTP 409 but mean different
    things)
- `src/utils/sentiment.js` — ports the CLI's `_sentiment_label` bucketing to JS, so the sentiment
  score reads the same "+0.128 (positive)" way in both places
- `src/utils/interviewEvents.js` — tiny `window`-event bridge so the sidebar refreshes when an
  interview completes in place (no navigation happens on completion, so route-change-based
  refetching alone would miss it)

## Notes

- No real SSE/streaming — a deliberate choice, see `docs/decisions.md`. The backend's real
  OpenAI token streaming (used by the CLI) isn't exposed over HTTP; the typewriter effect here is
  a client-side animation over an already-complete response.
- `npm audit` flags `react-router` advisories that only apply to its SSR/RSC/server-action
  features — this app is a plain client-side SPA (`BrowserRouter`, no server rendering, no server
  actions), so that attack surface doesn't apply here.
