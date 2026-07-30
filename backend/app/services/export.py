import json
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sqlalchemy.orm import Session

from app import config
from app.models import Interview, Summary
from app.services import orchestrator

# fpdf2's core "Helvetica" font only supports Latin-1, but real model output routinely
# uses smart quotes/dashes outside that range - transliterate the common ones, drop the rest.
_PDF_TRANSLITERATIONS = {
    "‘": "'", "’": "'",  # single smart quotes
    "“": '"', "”": '"',  # double smart quotes
    "–": "-", "—": "-",  # en/em dash
    "…": "...",  # ellipsis
    " ": " ",  # non-breaking space
}


def _sanitize_pdf_text(text: str) -> str:
    for unicode_char, ascii_equivalent in _PDF_TRANSLITERATIONS.items():
        text = text.replace(unicode_char, ascii_equivalent)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _interview_payload(session: Session, interview_id: int) -> dict:
    interview = session.get(Interview, interview_id)
    if interview is None:
        raise ValueError(f"No interview with id {interview_id}")

    summary = session.query(Summary).filter_by(interview_id=interview_id).one_or_none()
    history = orchestrator.get_history(session, interview_id)

    return {
        "interview_id": interview.id,
        "topic": interview.topic,
        "status": interview.status,
        "created_at": interview.created_at.isoformat(),
        "completed_at": interview.completed_at.isoformat() if interview.completed_at else None,
        "transcript": [{"role": m.role, "content": m.content} for m in history],
        "summary": {
            "themes": summary.themes,
            "key_points": summary.key_points,
            "keyword_extract": summary.keyword_extract,
            "sentiment_score": summary.sentiment_score,
        }
        if summary
        else None,
    }


def export_json(session: Session, interview_id: int) -> Path:
    payload = _interview_payload(session, interview_id)
    config.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.EXPORTS_DIR / f"{interview_id}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _line(pdf: FPDF, text: str, size: int = 11, bold: bool = False, height: int = 6) -> None:
    pdf.set_font("Helvetica", "B" if bold else "", size)
    pdf.multi_cell(0, height, _sanitize_pdf_text(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def export_pdf(session: Session, interview_id: int) -> Path:
    payload = _interview_payload(session, interview_id)
    config.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = config.EXPORTS_DIR / f"{interview_id}.pdf"

    pdf = FPDF()
    pdf.add_page()
    _line(pdf, f"Interview #{payload['interview_id']}: {payload['topic']}", size=16, bold=True, height=10)
    _line(pdf, f"Status: {payload['status']} | Created: {payload['created_at']}", size=10)
    pdf.ln(4)

    _line(pdf, "Transcript", size=12, bold=True, height=8)
    for message in payload["transcript"]:
        label = "Q" if message["role"] == "assistant" else "A"
        _line(pdf, f"{label}: {message['content']}")
        pdf.ln(1)

    if payload["summary"]:
        pdf.ln(4)
        _line(pdf, "Summary", size=12, bold=True, height=8)

        for theme in payload["summary"]["themes"]:
            _line(pdf, f"- {theme['name']} ({theme['sentiment']}): \"{theme['quote']}\"")

        pdf.ln(2)
        _line(pdf, "Key points", bold=True)
        for point in payload["summary"]["key_points"]:
            _line(pdf, f"- {point}")

        pdf.ln(2)
        _line(pdf, f"Keywords: {', '.join(payload['summary']['keyword_extract'])}", size=10)
        if payload["summary"]["sentiment_score"] is not None:
            _line(pdf, f"Overall sentiment score: {payload['summary']['sentiment_score']:.3f}", size=10)

    pdf.output(str(path))
    return path
