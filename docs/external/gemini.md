# Google Gemini API Reference

Implementation reference for the `GeminiProvider` strategy. Verified against `ai.google.dev` docs (current as of this writing). Google's docs currently describe **two** API surfaces — the classic `generateContent` API and a newer `Interactions` API (server-side conversation state, similar in spirit to OpenAI's Responses API). This doc focuses on **`generateContent`**, since it's the stable, broadly-supported surface and best fit for a stateless backend that keeps its own conversation history in SQLite.

## Install & Auth

```bash
pip install -U google-genai
```

Auth is via API key, read from an env var by default:

```bash
export GEMINI_API_KEY="your-api-key"
```

```python
from google import genai
client = genai.Client()  # reads GEMINI_API_KEY from env
# or explicit: genai.Client(api_key="...")
```

Get a key from Google AI Studio: https://aistudio.google.com/apikey

## Endpoint (REST)

```
POST https://generativelanguage.googleapis.com/v1beta/{model=models/*}:generateContent
POST https://generativelanguage.googleapis.com/v1beta/{model=models/*}:streamGenerateContent
```

Auth via query param (raw HTTP) or header (SDK handles this):

```
?key=$GEMINI_API_KEY
```
or header `x-goog-api-key: $GEMINI_API_KEY`.

## Recommended model

Use **`gemini-2.5-flash`** for a general chat/text task — fast and cheap, good default for generating interview questions or evaluating answers. Use a `-pro` tier model if you need stronger reasoning and can tolerate more latency/cost. (Check https://ai.google.dev/gemini-api/docs/models for the current model list before committing to an ID — model names change over time and newer flash/pro generations are released periodically.)

## Minimal example (non-streaming)

```python
from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Ask me a question about Python generators.",
)
print(response.text)  # SDK convenience property — concatenates all text parts
```

With a system instruction:

```python
from google.genai import types

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Ask me a question about Python generators.",
    config=types.GenerateContentConfig(
        system_instruction="You are an expert technical interviewer conducting a live interview.",
    ),
)
print(response.text)
```

## Request shape (REST)

```json
{
  "contents": [
    {"role": "user", "parts": [{"text": "..."}]}
  ],
  "systemInstruction": {
    "parts": {"text": "You are an expert technical interviewer."}
  },
  "generationConfig": {
    "temperature": 1.0,
    "maxOutputTokens": 800,
    "topP": 0.8,
    "topK": 10
  }
}
```

- `systemInstruction` is a separate top-level field, like Anthropic's `system` — not a message in `contents`.
- Roles inside `contents` are `"user"` and `"model"` (not `"assistant"` — this is a Gemini-specific naming quirk to watch for when translating history between providers).
- No conversation/session ID for `generateContent` — stateless; resend full history each call, same pattern as Anthropic.

## Response shape (REST)

```json
{
  "candidates": [
    {
      "content": {
        "role": "model",
        "parts": [{"text": "..."}]
      },
      "finishReason": "STOP"
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 10,
    "candidatesTokenCount": 50,
    "totalTokenCount": 60
  }
}
```

`finishReason` values: `STOP` (normal), `MAX_TOKENS` (truncated), `SAFETY` (blocked — check `promptFeedback.blockReason` too), `RECITATION`.

In the Python SDK, `response.text` is a convenience that concatenates all text parts of the first candidate. For multi-candidate or multi-part responses, walk `response.candidates[0].content.parts`.

## Multi-turn conversation

Two options:

**1. Manage history yourself** (recommended for consistency with the Anthropic/OpenAI providers in a strategy pattern — same "replay full history" model):

```python
contents = [
    {"role": "user", "parts": [{"text": "Tell me about your SQL experience."}]},
    {"role": "model", "parts": [{"text": "Can you describe a project?"}]},
    {"role": "user", "parts": [{"text": "I built a reporting pipeline..."}]},
]

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=contents,
    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
)
```

**2. Use the SDK's chat session helper** (keeps history client-side for you within the SDK object, still stateless server-side):

```python
chat = client.chats.create(model="gemini-2.5-flash")
response1 = chat.send_message("Tell me about your SQL experience.")
response2 = chat.send_message("I built a reporting pipeline...")
# chat.get_history() returns the accumulated turns
```

For a backend that persists conversations in SQLite across requests/processes, option 1 (build `contents` from your DB rows each request) is simpler and matches the other providers' pattern.

## System prompts

Pass via `config.system_instruction` (SDK) / top-level `systemInstruction` (REST). Keep it stable across turns in a conversation.

## Streaming vs non-streaming

```python
stream = client.models.generate_content_stream(
    model="gemini-2.5-flash",
    contents=contents,
)
for chunk in stream:
    print(chunk.text, end="")
```

REST streaming uses the `:streamGenerateContent` endpoint with `?alt=sse` for Server-Sent Events; without it, the endpoint returns a JSON array of `GenerateContentResponse` objects as they complete.

## Error handling & rate limits

The SDK raises `google.genai.errors.APIError` (and subclasses) on non-2xx responses; inspect `.code` for the HTTP status.

| HTTP code | Meaning |
|---|---|
| 400 | invalid request |
| 401/403 | bad/missing API key or insufficient permission |
| 429 | rate limited — back off and retry |
| 500/503 | server error / overloaded — retry with backoff |

Free-tier and paid-tier rate limits (requests/minute, tokens/minute) are model-specific — check https://ai.google.dev/gemini-api/docs/rate-limits for current values before sizing retry/backoff logic.

## Notes / gotchas for the provider strategy

- Role naming differs from Anthropic/OpenAI: Gemini uses `"model"` where they use `"assistant"`. Normalize this at the strategy-adapter boundary.
- `system_instruction` (Gemini) / `system` (Anthropic) / a `role: "system"` message (OpenAI) are three different mechanisms for the same concept — handle this in your provider abstraction layer.
- Check https://ai.google.dev/gemini-api/docs/models for the current model catalog before hardcoding a model ID long-term.
