import json
import re

from openai import OpenAI

from app import config
from app.providers.base import OnDelta
from app.providers.base import LLMProvider
from app.schemas import AnalysisResult, ChecklistItem, HistoryMessage, InterviewTurnResult, Theme

_INTERVIEW_TOOL = {
    "type": "function",
    "name": "interview_turn",
    "description": "Report the current checklist state and the next question to ask (or signal the interview is done).",
    "parameters": {
        "type": "object",
        "properties": {
            "checklist": {
                "type": "array",
                "description": "The full checklist of 3-5 things to learn about the person's view on the topic. On the first turn, invent this list. On later turns, return it updated.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "text": {"type": "string"},
                        "covered": {"type": "boolean"},
                    },
                    "required": ["id", "text", "covered"],
                },
            },
            "next_question": {
                "type": ["string", "null"],
                "description": "The next question to ask the person. Null if done is true.",
            },
            "done": {
                "type": "boolean",
                "description": "True if the checklist is fully covered and the interview should end.",
            },
        },
        "required": ["checklist", "next_question", "done"],
    },
}

_ANALYSIS_TOOL = {
    "type": "function",
    "name": "analysis_result",
    "description": "Report the structured analysis of a completed interview transcript.",
    "parameters": {
        "type": "object",
        "properties": {
            "themes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "sentiment": {
                            "type": "string",
                            "enum": ["positive", "negative", "mixed", "neutral"],
                        },
                        "quote": {"type": "string"},
                    },
                    "required": ["name", "sentiment", "quote"],
                },
            },
            "key_points": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["themes", "key_points"],
    },
}

# Best-effort partial extraction of the "next_question" string value out of a
# streaming (possibly incomplete) JSON arguments buffer, for live token display.
# The authoritative parse always happens on the complete response afterwards -
# this is cosmetic only, never used for the actual InterviewTurnResult.
_PARTIAL_QUESTION_RE = re.compile(r'"next_question"\s*:\s*"((?:[^"\\]|\\.)*)')


def _extract_partial_question(buffer: str) -> str | None:
    match = _PARTIAL_QUESTION_RE.search(buffer)
    if not match:
        return None
    raw = match.group(1)
    return raw.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def _load_prompt(name: str) -> str:
    return (config.PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _history_to_input(history: list[HistoryMessage]) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in history]


def _extract_tool_call(response, tool_name: str) -> dict:
    for item in response.output:
        if getattr(item, "type", None) == "function_call" and item.name == tool_name:
            return json.loads(item.arguments)
    text = getattr(response, "output_text", "") or ""
    raise RuntimeError(f"OpenAI did not call tool '{tool_name}'; got text instead: {text!r}")


class OpenAIProvider(LLMProvider):
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set - add it to backend/.env")
        self._client = OpenAI(api_key=config.OPENAI_API_KEY)
        self._model = config.OPENAI_MODEL
        self._interviewer_prompt = _load_prompt("interviewer")
        self._analyst_prompt = _load_prompt("analyst")

    def next_turn(
        self,
        topic: str,
        checklist: list[ChecklistItem],
        history: list[HistoryMessage],
    ) -> InterviewTurnResult:
        system_prompt = self._interviewer_prompt.format(topic=topic)
        input_ = _history_to_input(history) or [
            {"role": "user", "content": "(interview is starting, ask your first question)"}
        ]

        response = self._client.responses.create(
            model=self._model,
            instructions=system_prompt,
            input=input_,
            tools=[_INTERVIEW_TOOL],
        )
        data = _extract_tool_call(response, "interview_turn")
        return InterviewTurnResult(
            checklist=[ChecklistItem(**item) for item in data.get("checklist", [])],
            next_question=data.get("next_question") or None,
            done=bool(data.get("done", False)),
        )

    def next_turn_stream(
        self,
        topic: str,
        checklist: list[ChecklistItem],
        history: list[HistoryMessage],
        on_delta: OnDelta,
    ) -> InterviewTurnResult:
        system_prompt = self._interviewer_prompt.format(topic=topic)
        input_ = _history_to_input(history) or [
            {"role": "user", "content": "(interview is starting, ask your first question)"}
        ]

        stream = self._client.responses.create(
            model=self._model,
            instructions=system_prompt,
            input=input_,
            tools=[_INTERVIEW_TOOL],
            stream=True,
        )

        buffer = ""
        printed_len = 0
        final_response = None

        for event in stream:
            if event.type == "response.function_call_arguments.delta":
                buffer += event.delta
                partial = _extract_partial_question(buffer)
                if partial is not None and len(partial) > printed_len:
                    on_delta(partial[printed_len:])
                    printed_len = len(partial)
            elif event.type == "response.completed":
                final_response = event.response

        if final_response is None:
            raise RuntimeError("OpenAI stream ended without a completed response")

        data = _extract_tool_call(final_response, "interview_turn")
        final_question = data.get("next_question") or None

        # Correct the terminal display if our best-effort partial parse missed a
        # tail (e.g. trailing escape sequence never resolved mid-stream).
        if final_question and len(final_question) > printed_len:
            on_delta(final_question[printed_len:])

        return InterviewTurnResult(
            checklist=[ChecklistItem(**item) for item in data.get("checklist", [])],
            next_question=final_question,
            done=bool(data.get("done", False)),
        )

    def analyze(self, topic: str, history: list[HistoryMessage]) -> AnalysisResult:
        system_prompt = self._analyst_prompt.format(topic=topic)
        transcript_text = "\n".join(f"{m.role}: {m.content}" for m in history)

        response = self._client.responses.create(
            model=self._model,
            instructions=system_prompt,
            input=[{"role": "user", "content": f"Transcript:\n{transcript_text}"}],
            tools=[_ANALYSIS_TOOL],
        )
        data = _extract_tool_call(response, "analysis_result")
        return AnalysisResult(
            themes=[Theme(**theme) for theme in data.get("themes", [])],
            key_points=data.get("key_points", []),
        )
