import re
from collections import Counter

from sqlalchemy.orm import Session
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app import config
from app.models import Interview, Summary
from app.providers.base import LLMProvider
from app.schemas import AnalysisResult, HistoryMessage
from app.services import orchestrator
from app.services.retry import call_with_retry

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "to", "of", "in",
    "on", "for", "with", "it", "i", "you", "that", "this", "my", "me", "so", "just",
    "not", "be", "at", "as", "if", "do", "does", "did", "have", "has", "had", "than",
    "then", "will", "would", "could", "can", "about", "its", "it's", "im", "i'm",
}

_analyzer = SentimentIntensityAnalyzer()


def _extract_keywords(text: str, top_n: int = 8) -> list[str]:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    words = [w for w in words if w not in _STOPWORDS and len(w) > 2]
    return [word for word, _count in Counter(words).most_common(top_n)]


def _score_sentiment(text: str) -> float:
    return _analyzer.polarity_scores(text)["compound"]


def run_analysis(session: Session, provider: LLMProvider, interview_id: int) -> Summary:
    existing = session.query(Summary).filter_by(interview_id=interview_id).one_or_none()
    if existing is not None:
        return existing

    interview = session.get(Interview, interview_id)
    if interview is None:
        raise ValueError(f"No interview with id {interview_id}")

    history: list[HistoryMessage] = orchestrator.get_history(session, interview_id)
    result: AnalysisResult = call_with_retry(
        lambda: provider.analyze(topic=interview.topic, history=history)
    )

    answers_text = " ".join(m.content for m in history if m.role == "user")

    summary = Summary(
        interview_id=interview_id,
        themes=[theme.model_dump() for theme in result.themes],
        key_points=result.key_points,
        keyword_extract=_extract_keywords(answers_text),
        sentiment_score=_score_sentiment(answers_text) if answers_text else None,
    )
    session.add(summary)
    session.commit()
    return summary
