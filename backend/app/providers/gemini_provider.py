from google import genai
from google.genai import types

from app import config
from app.providers.base import LLMProvider
from app.schemas import AnalysisResult, ChecklistItem, HistoryMessage, InterviewTurnResult, Theme

_INTERVIEW_FUNCTION = types.FunctionDeclaration(
    name="interview_turn",
    description="Report the current checklist state and the next question to ask (or signal the interview is done).",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "checklist": types.Schema(
                type="ARRAY",
                description="The full checklist of 3-5 things to learn about the person's view on the topic. On the first turn, invent this list. On later turns, return it updated.",
                items=types.Schema(
                    type="OBJECT",
                    properties={
                        "id": types.Schema(type="STRING"),
                        "text": types.Schema(type="STRING"),
                        "covered": types.Schema(type="BOOLEAN"),
                    },
                    required=["id", "text", "covered"],
                ),
            ),
            "next_question": types.Schema(
                type="STRING",
                description="The next question to ask the person. Empty string if done is true.",
            ),
            "done": types.Schema(
                type="BOOLEAN",
                description="True if the checklist is fully covered and the interview should end.",
            ),
            "reasoning": types.Schema(
                type="STRING",
                description="One short sentence, for internal debugging only, never shown to the person: what you picked up on in their last answer and why you're asking this next question.",
            ),
        },
        required=["checklist", "next_question", "done", "reasoning"],
    ),
)

_ANALYSIS_FUNCTION = types.FunctionDeclaration(
    name="analysis_result",
    description="Report the structured analysis of a completed interview transcript.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "themes": types.Schema(
                type="ARRAY",
                items=types.Schema(
                    type="OBJECT",
                    properties={
                        "name": types.Schema(type="STRING"),
                        "sentiment": types.Schema(
                            type="STRING",
                            enum=["positive", "negative", "mixed", "neutral"],
                        ),
                        "quote": types.Schema(type="STRING"),
                    },
                    required=["name", "sentiment", "quote"],
                ),
            ),
            "key_points": types.Schema(
                type="ARRAY",
                items=types.Schema(type="STRING"),
            ),
        },
        required=["themes", "key_points"],
    ),
)


def _load_prompt(name: str) -> str:
    return (config.PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _history_to_contents(history: list[HistoryMessage]) -> list[dict]:
    return [
        {"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
        for m in history
    ]


def _checklist_state_block(checklist: list[ChecklistItem]) -> str:
    # The model has no memory between calls - without resending its own prior
    # checklist as authoritative state, it reinvents item ids/wording each turn.
    if not checklist:
        return ""
    lines = "\n".join(f"- {c.id}: {c.text} [{'covered' if c.covered else 'open'}]" for c in checklist)
    return (
        "\n\nCurrent checklist state (this is your own prior state, build on it):\n"
        f"{lines}\n"
        "Keep ids stable for items that still apply. You may add, remove, or reword items if "
        "the conversation genuinely calls for it - but don't discard and reinvent the whole "
        "list from scratch without reason."
    )


def _extract_function_call(response, fn_name: str) -> dict:
    candidate = response.candidates[0]
    for part in candidate.content.parts:
        fc = getattr(part, "function_call", None)
        if fc and fc.name == fn_name:
            return dict(fc.args)
    text = getattr(response, "text", "") or ""
    raise RuntimeError(f"Gemini did not call function '{fn_name}'; got text instead: {text!r}")


class GeminiProvider(LLMProvider):
    def __init__(self):
        if not config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set - add it to backend/.env")
        self._client = genai.Client(api_key=config.GEMINI_API_KEY)
        self._model = config.GEMINI_MODEL
        self._interviewer_prompt = _load_prompt("interviewer")
        self._analyst_prompt = _load_prompt("analyst")

    def next_turn(
        self,
        topic: str,
        checklist: list[ChecklistItem],
        history: list[HistoryMessage],
    ) -> InterviewTurnResult:
        system_prompt = self._interviewer_prompt.format(topic=topic) + _checklist_state_block(checklist)
        contents = _history_to_contents(history) or [
            {"role": "user", "parts": [{"text": "(interview is starting, ask your first question)"}]}
        ]

        response = self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[types.Tool(function_declarations=[_INTERVIEW_FUNCTION])],
            ),
        )
        data = _extract_function_call(response, "interview_turn")

        return InterviewTurnResult(
            checklist=[ChecklistItem(**item) for item in data.get("checklist", [])],
            next_question=data.get("next_question") or None,
            done=bool(data.get("done", False)),
            reasoning=data.get("reasoning") or None,
        )

    def analyze(self, topic: str, history: list[HistoryMessage]) -> AnalysisResult:
        system_prompt = self._analyst_prompt.format(topic=topic)
        transcript_text = "\n".join(f"{m.role}: {m.content}" for m in history)

        response = self._client.models.generate_content(
            model=self._model,
            contents=[{"role": "user", "parts": [{"text": f"Transcript:\n{transcript_text}"}]}],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[types.Tool(function_declarations=[_ANALYSIS_FUNCTION])],
            ),
        )
        data = _extract_function_call(response, "analysis_result")

        return AnalysisResult(
            themes=[Theme(**theme) for theme in data.get("themes", [])],
            key_points=data.get("key_points", []),
        )
