from typing import Iterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import config
from app.api_schemas import (
    AnswerRequest,
    AnswerResponse,
    DebugInfo,
    ExportLinks,
    InterviewDetailResponse,
    StartInterviewResponse,
    SummaryResponse,
    TopicRequest,
    TranscriptMessage,
)
from app.db import get_session
from app.models import Interview
from app.providers.factory import get_provider
from app.services import analysis, export, orchestrator

router = APIRouter(prefix="/interviews", tags=["interviews"])

# Constructed once per process, mirrors cli.py's single provider for the process lifetime.
_provider = get_provider()


def get_db() -> Iterator[Session]:
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def get_interview_or_404(interview_id: int, session: Session = Depends(get_db)) -> Interview:
    interview = session.get(Interview, interview_id)
    if interview is None:
        raise HTTPException(status_code=404, detail="Interview not found")
    return interview


def _debug_info(interview: Interview, reasoning: str | None) -> DebugInfo | None:
    if not config.DEBUG_MODE:
        return None
    return DebugInfo(reasoning=reasoning, checklist=interview.checklist, risk_score=interview.risk_score)


@router.post("", status_code=201, response_model=StartInterviewResponse)
def start_interview(body: TopicRequest, session: Session = Depends(get_db)) -> StartInterviewResponse:
    interview, question, reasoning = orchestrator.start_interview(session, _provider, body.topic)
    return StartInterviewResponse(
        interview_id=interview.id,
        status=interview.status,
        question=question,
        debug=_debug_info(interview, reasoning),
    )


@router.post("/{interview_id}/answer", response_model=AnswerResponse)
def submit_answer(
    interview_id: int,
    body: AnswerRequest,
    session: Session = Depends(get_db),
    interview: Interview = Depends(get_interview_or_404),
) -> AnswerResponse:
    if interview.status == "completed":
        raise HTTPException(status_code=409, detail="This interview has already ended.")

    question, done, reasoning = orchestrator.submit_answer(session, _provider, interview_id, body.answer)
    session.refresh(interview)
    return AnswerResponse(
        question=question,
        done=done,
        status=interview.status,
        debug=_debug_info(interview, reasoning),
    )


@router.get("/{interview_id}", response_model=InterviewDetailResponse)
def get_interview(
    interview_id: int,
    session: Session = Depends(get_db),
    interview: Interview = Depends(get_interview_or_404),
) -> InterviewDetailResponse:
    history = orchestrator.get_history(session, interview_id)
    return InterviewDetailResponse(
        interview_id=interview.id,
        topic=interview.topic,
        status=interview.status,
        created_at=interview.created_at.isoformat(),
        completed_at=interview.completed_at.isoformat() if interview.completed_at else None,
        transcript=[TranscriptMessage(role=m.role, content=m.content) for m in history],
    )


@router.get("/{interview_id}/summary", response_model=SummaryResponse)
def get_summary(
    interview_id: int,
    session: Session = Depends(get_db),
    interview: Interview = Depends(get_interview_or_404),
) -> SummaryResponse:
    summary = analysis.run_analysis(session, _provider, interview_id)
    return SummaryResponse(
        interview_id=interview.id,
        themes=summary.themes,
        key_points=summary.key_points,
        feedback=summary.feedback,
        keyword_extract=summary.keyword_extract,
        sentiment_score=summary.sentiment_score,
        exports=ExportLinks(
            json_url=f"/interviews/{interview_id}/export/json",
            pdf_url=f"/interviews/{interview_id}/export/pdf",
        ),
    )


@router.get("/{interview_id}/export/json")
def download_json(
    interview_id: int,
    session: Session = Depends(get_db),
    interview: Interview = Depends(get_interview_or_404),
) -> FileResponse:
    analysis.run_analysis(session, _provider, interview_id)
    path = export.export_json(session, interview_id)
    return FileResponse(path, media_type="application/json", filename=f"interview-{interview_id}.json")


@router.get("/{interview_id}/export/pdf")
def download_pdf(
    interview_id: int,
    session: Session = Depends(get_db),
    interview: Interview = Depends(get_interview_or_404),
) -> FileResponse:
    analysis.run_analysis(session, _provider, interview_id)
    path = export.export_pdf(session, interview_id)
    return FileResponse(path, media_type="application/pdf", filename=f"interview-{interview_id}.pdf")
