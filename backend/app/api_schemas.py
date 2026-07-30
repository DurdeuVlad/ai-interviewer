"""HTTP request/response DTOs for the FastAPI layer.

Distinct from app/schemas.py, which holds internal models used between the
orchestrator and providers. ChecklistItem/Theme/InterviewFeedback are pure
output shapes with no provider-specific mechanics, so they're reused directly
rather than duplicated here.
"""

from pydantic import BaseModel

from app.schemas import ChecklistItem, InterviewFeedback, Theme


class TopicRequest(BaseModel):
    topic: str


class AnswerRequest(BaseModel):
    answer: str


class DebugInfo(BaseModel):
    reasoning: str | None
    checklist: list[ChecklistItem]
    risk_score: float


class StartInterviewResponse(BaseModel):
    interview_id: int
    status: str
    question: str
    debug: DebugInfo | None = None


class AnswerResponse(BaseModel):
    question: str | None
    done: bool
    status: str
    debug: DebugInfo | None = None


class TranscriptMessage(BaseModel):
    role: str
    content: str


class InterviewDetailResponse(BaseModel):
    interview_id: int
    topic: str
    status: str
    created_at: str
    completed_at: str | None
    transcript: list[TranscriptMessage]


class ExportLinks(BaseModel):
    json_url: str
    pdf_url: str


class SummaryResponse(BaseModel):
    interview_id: int
    themes: list[Theme]
    key_points: list[str]
    feedback: InterviewFeedback
    keyword_extract: list[str]
    sentiment_score: float | None
    exports: ExportLinks
