from pydantic import BaseModel


class ChecklistItem(BaseModel):
    id: str
    text: str
    covered: bool


class InterviewTurnResult(BaseModel):
    checklist: list[ChecklistItem]
    next_question: str | None
    done: bool


class Theme(BaseModel):
    name: str
    sentiment: str
    quote: str


class AnalysisResult(BaseModel):
    themes: list[Theme]
    key_points: list[str]


class HistoryMessage(BaseModel):
    role: str  # "assistant" | "user"
    content: str
