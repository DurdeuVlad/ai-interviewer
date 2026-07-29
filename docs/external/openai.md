# OpenAI GPT — Responses API Reference

Implementation reference for the `OpenAIProvider` strategy. OpenAI now recommends the **Responses API** (`/v1/responses`) over the older Chat Completions API (`/v1/chat/completions`) for new text-generation apps — verified against `developers.openai.com` docs (current as of this writing). Chat Completions still works and is documented below as a fallback/alternative since a lot of existing example code and tutorials use it.

## Install & Auth

```bash
pip install openai
```

```python
from openai import OpenAI
client = OpenAI()  # reads OPENAI_API_KEY from env
# or explicit: OpenAI(api_key="sk-...")
```

Raw HTTP header:

```
Authorization: Bearer $OPENAI_API_KEY
```

## Endpoint

```
POST https://api.openai.com/v1/responses
```

(Chat Completions equivalent: `POST https://api.openai.com/v1/chat/completions`.)

## Recommended model

Use the current **`gpt-5`**-family model for a general chat/text task (check https://platform.openai.com/docs/models for the exact current default — OpenAI iterates model names/versions; as of this writing examples in the docs use `gpt-5.6`). For cost-sensitive high-volume use, look for a `-mini`/`-nano` variant of the same family.

## Minimal example (Responses API, non-streaming)

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5.6",
    instructions="You are an expert technical interviewer conducting a live interview.",
    input="Ask me a question about Python generators.",
)
print(response.output_text)  # SDK convenience property
```

## Request shape

```json
{
  "model": "gpt-5.6",
  "instructions": "You are an expert technical interviewer.",
  "input": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
    {"role": "user", "content": "..."}
  ]
}
```

- `input` accepts either a plain string (single user turn) or a list of message objects with `role`/`content` — this is how you pass multi-turn history explicitly.
- `instructions` is the system-prompt-equivalent field, separate from `input` (comparable to Anthropic's `system` and Gemini's `system_instruction`). Note: `instructions` from a *previous* turn do **not** automatically carry forward if you use `previous_response_id` — pass them fresh each call.
- Optional: `max_output_tokens`, `store` (whether OpenAI retains response state server-side, default true), `stream`.

## Response shape

```json
{
  "id": "resp_...",
  "status": "completed",
  "output": [
    {
      "type": "message",
      "role": "assistant",
      "content": [
        {"type": "output_text", "text": "..."}
      ]
    }
  ],
  "usage": {
    "input_tokens": 25,
    "output_tokens": 138,
    "total_tokens": 163
  }
}
```

`output` is a list of items (message, tool call, reasoning, etc.) — for plain text, use the `response.output_text` convenience property (SDK) or walk `output[].content[].text` where `type == "output_text"`.

`status` values: `completed`, `in_progress`, `incomplete` (e.g. hit `max_output_tokens`).

## Multi-turn conversation

Two options, same tradeoff as the other providers:

**1. Manage history yourself (recommended for parity with the Anthropic/Gemini providers)** — build the `input` list from your stored transcript each call:

```python
history = [
    {"role": "user", "content": "Tell me about your SQL experience."},
    {"role": "assistant", "content": "Can you describe a project?"},
    {"role": "user", "content": "I built a reporting pipeline..."},
]

response = client.responses.create(
    model="gpt-5.6",
    instructions=SYSTEM_PROMPT,
    input=history,
)
```

**2. Use OpenAI's server-side conversation state** via `previous_response_id`, chaining calls without resending full history:

```python
r1 = client.responses.create(model="gpt-5.6", input="Tell me about your SQL experience.")
r2 = client.responses.create(
    model="gpt-5.6",
    input="I built a reporting pipeline...",
    previous_response_id=r1.id,
)
```

Since this app already persists conversations in SQLite (and needs provider-agnostic history to swap strategies), option 1 is the better fit — it keeps the "source of truth" for conversation state in your own DB rather than split across providers.

## System prompts

Pass via top-level `instructions` (Responses API) — comparable to Anthropic's `system` param and distinct from a `role: "system"` message in the older Chat Completions API. Keep it stable/identical across turns of the same conversation.

## Streaming vs non-streaming

```python
stream = client.responses.create(
    model="gpt-5.6",
    input=history,
    stream=True,
)
for event in stream:
    if event.type == "response.output_text.delta":
        print(event.delta, end="", flush=True)
    elif event.type == "response.completed":
        final = event.response  # full Response object, same shape as non-streaming
```

Streaming events are discriminated by `type` (e.g. `response.output_text.delta`, `response.completed`, tool-call events). Non-streaming is fine for short replies; use streaming for longer generations or to show incremental output in a UI.

## Chat Completions API (legacy alternative)

Still supported; simpler mental model if you've used it before (`messages` list with `role: "system"/"user"/"assistant"`):

```python
response = client.chat.completions.create(
    model="gpt-5.6",
    messages=[
        {"role": "system", "content": "You are an expert technical interviewer."},
        {"role": "user", "content": "Ask me a question about Python generators."},
    ],
)
print(response.choices[0].message.content)
```

Endpoint: `POST https://api.openai.com/v1/chat/completions`. Response shape uses `choices[0].message.content` instead of `output_text`. Prefer the Responses API for new code per OpenAI's current guidance.

## Error handling & rate limits

The SDK raises typed exceptions (`openai.AuthenticationError`, `openai.RateLimitError`, `openai.APIStatusError`, `openai.APIConnectionError`) — catch most-specific first, same pattern as the Anthropic SDK.

| HTTP code | Meaning |
|---|---|
| 401 | invalid/revoked API key or wrong org |
| 429 | rate limit exceeded **or** quota/credits exhausted (two distinct causes under the same code) |
| 500 | OpenAI server error — retry after a brief wait |
| 503 | overloaded / "slow down" throttling — back off |

Rate-limit handling: implement exponential backoff, respect any `retry-after`-style guidance in response headers, and if throttled, reduce request rate and hold it steady for at least ~15 minutes before ramping back up. Limits apply per-organization, not per-user.

## Pricing

Do not hardcode prices — check current per-model pricing at **https://platform.openai.com/docs/pricing** before estimating cost, since rates change and vary by model tier (`gpt-5.6` vs `-mini`/`-nano` variants).
