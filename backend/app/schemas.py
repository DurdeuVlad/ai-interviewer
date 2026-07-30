from pydantic import BaseModel


class ChecklistItem(BaseModel):
    id: str
    text: str
    covered: bool


class InterviewTurnResult(BaseModel):
    checklist: list[ChecklistItem]
    next_question: str | None
    done: bool
    reasoning: str | None = None  # debug-only: model's one-line rationale for this turn


class Theme(BaseModel):
    name: str
    sentiment: str
    quote: str


class InterviewFeedback(BaseModel):
    positives: list[str]
    constructive: list[str]


class AnalysisResult(BaseModel):
    themes: list[Theme]
    key_points: list[str]
    feedback: InterviewFeedback


class HistoryMessage(BaseModel):
    role: str  # "assistant" | "user"
    content: str
