# Anthropic Claude — Messages API Reference

Implementation reference for the `AnthropicProvider` strategy. Verified against the `anthropic` Python SDK docs (current as of this writing).

## Install & Auth

```bash
pip install anthropic
```

Auth is via API key header, resolved automatically by the SDK from `ANTHROPIC_API_KEY`:

```python
import anthropic
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
# or explicit: anthropic.Anthropic(api_key="sk-ant-...")
```

Raw HTTP headers (if not using the SDK):

| Header | Value |
|---|---|
| `x-api-key` | your API key |
| `anthropic-version` | `2023-06-01` |
| `content-type` | `application/json` |

## Endpoint

```
POST https://api.anthropic.com/v1/messages
```

## Recommended model

Use **`claude-sonnet-5`** for a general chat/interview-question-generation task — best balance of quality, speed, and cost for this tier. (`claude-opus-5` if you want the strongest reasoning and don't mind higher cost/latency; `claude-haiku-4-5` for cheap/fast simple tasks.)

## Minimal example (non-streaming)

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    system="You are an expert technical interviewer conducting a live interview.",
    messages=[
        {"role": "user", "content": "Ask me a question about Python generators."}
    ],
)

# content is a list of blocks; find the text block(s)
reply = "".join(b.text for b in response.content if b.type == "text")
print(reply)
```

## Request shape

```json
{
  "model": "claude-sonnet-5",
  "max_tokens": 1024,
  "system": "You are an expert technical interviewer.",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."},
    {"role": "user", "content": "..."}
  ]
}
```

- `system` is a **top-level string (or list of text blocks)** — not a message with `role: "system"`. This is different from OpenAI/Gemini.
- `messages` must start with `role: "user"` and strictly alternate `user`/`assistant` (consecutive same-role messages get merged, not rejected).
- No separate "conversation ID" — the API is stateless. Your app must resend the full message history each turn (this is why you have a SQLite DB: store the turns and replay them).

## Response shape

```json
{
  "id": "msg_01...",
  "type": "message",
  "role": "assistant",
  "model": "claude-sonnet-5",
  "content": [
    {"type": "text", "text": "..."}
  ],
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 25,
    "output_tokens": 138
  }
}
```

`content` is a **list of blocks** (not a single string) because a response can include `text`, `thinking`, or `tool_use` blocks. For plain text generation, filter for `block.type == "text"`.

`stop_reason` values you'll see: `end_turn` (done), `max_tokens` (truncated — raise `max_tokens` or stream), `tool_use`, `refusal` (safety decline — check before reading `content`).

## Multi-turn conversation

Build the `messages` array yourself from your stored interview transcript each request:

```python
history = [
    {"role": "user", "content": "Tell me about your experience with SQL."},
    {"role": "assistant", "content": "Sure — can you describe a project where you used it?"},
    {"role": "user", "content": "I built a reporting pipeline..."},
]

response = client.messages.create(
    model="claude-sonnet-5",
    max_tokens=1024,
    system=SYSTEM_PROMPT,  # stays constant across turns
    messages=history,
)
```

Append the assistant's reply (as a plain string, or as `response.content` if you need to preserve block structure) to `history` before the next call.

## System prompts

- Pass once per request as the top-level `system` field; it is **not** part of `messages`.
- Keep it stable across turns — this both simplifies your code and enables prompt caching (see below).

## Streaming vs non-streaming

Non-streaming (`client.messages.create(...)`) is fine for short replies. For longer generations (`max_tokens` above ~16000), the SDK requires streaming to avoid HTTP timeouts.

```python
with client.messages.stream(
    model="claude-sonnet-5",
    max_tokens=1024,
    system=SYSTEM_PROMPT,
    messages=history,
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    final_message = stream.get_final_message()  # full Message object, same shape as non-streaming
```

Use `stream.get_final_message()` to get the complete response object (with `usage`, `stop_reason`, etc.) even when streaming token-by-token to a UI.

## Error handling

Use typed exceptions, not string matching:

```python
try:
    response = client.messages.create(...)
except anthropic.RateLimitError as e:
    retry_after = int(e.response.headers.get("retry-after", "60"))
except anthropic.AuthenticationError:
    ...  # bad API key
except anthropic.APIStatusError as e:
    if e.status_code >= 500:
        ...  # retry with backoff
except anthropic.APIConnectionError:
    ...  # network error
```

| HTTP code | Meaning |
|---|---|
| 400 | invalid request (bad params, non-alternating roles) |
| 401 | bad/missing API key |
| 403 | key lacks permission for this model/feature |
| 404 | bad model ID or endpoint |
| 429 | rate limited — retry with backoff, respect `retry-after` header |
| 500 | Anthropic-side error — retry |
| 529 | overloaded — retry with backoff |

The SDK auto-retries 429/5xx/connection errors twice by default (`max_retries`).

## Rate limits

Per-organization limits on requests-per-minute, input-tokens-per-minute, output-tokens-per-minute — tier-dependent. Check response headers `x-ratelimit-remaining-*` / `x-ratelimit-limit-*` and the `retry-after` header on a 429.

## Pricing

Do not hardcode prices in code/config comments that need upkeep — check current per-model pricing at **https://platform.claude.com/docs/en/pricing** (also surfaced via `https://platform.claude.com/docs/en/about-claude/models/overview`) before estimating cost, since rates and intro discounts change.
