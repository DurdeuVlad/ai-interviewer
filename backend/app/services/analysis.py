import logging
import re
from collections import Counter

from sqlalchemy.orm import Session
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.models import Interview, Summary
from app.providers.base import LLMProvider
from app.schemas import AnalysisResult, HistoryMessage, InterviewFeedback, Theme
from app.services import orchestrator
from app.services.retry import call_with_retry

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "to", "of", "in",
    "on", "for", "with", "it", "i", "you", "that", "this", "my", "me", "so", "just",
    "not", "be", "at", "as", "if", "do", "does", "did", "have", "has", "had", "than",
    "then", "will", "would", "could", "can", "about", "its", "it's", "im", "i'm",
}

_analyzer = SentimentIntensityAnalyzer()

# Guards against a real failure mode observed from a live model: the tool-call arguments
# came back as syntactically valid JSON (so json.loads succeeded) but one string value
# had the model's own scratch/retry commentary pasted into it instead of real content,
# e.g. one key_point ending in: `...details.], "feedback":{...}} argh nope. Need valid
# JSON no weird. Retry.} ... assistant to=functions.analysis_result (commentary) ...`
# Valid syntax doesn't mean sane content - this catches that gap.
_MAX_FIELD_LEN = 300
_CORRUPTION_MARKERS = ("assistant to=", "function_call", "tool call", "\"}", "{\"")


def _looks_corrupted(text: str) -> bool:
    if len(text) > _MAX_FIELD_LEN:
        return True
    lowered = text.lower()
    return any(marker in lowered for marker in _CORRUPTION_MARKERS)


def _is_sane(result: AnalysisResult) -> bool:
    texts = (
        [t.name for t in result.themes]
        + [t.quote for t in result.themes]
        + result.key_points
        + result.feedback.positives
        + result.feedback.constructive
    )
    return not any(_looks_corrupted(t) for t in texts)


_FALLBACK_ANALYSIS = AnalysisResult(
    themes=[Theme(name="Analysis unavailable", sentiment="neutral", quote="(analysis could not be completed reliably)")],
    key_points=["The automated analysis did not return a reliable result for this interview."],
    feedback=InterviewFeedback(positives=[], constructive=[]),
)


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

    if not _is_sane(result):
        logger.warning("Analysis result looked corrupted, retrying once.")
        result = call_with_retry(lambda: provider.analyze(topic=interview.topic, history=history))
        if not _is_sane(result):
            logger.warning("Analysis result still corrupted after retry, using fallback.")
            result = _FALLBACK_ANALYSIS

    answers_text = " ".join(m.content for m in history if m.role == "user")

    summary = Summary(
        interview_id=interview_id,
        themes=[theme.model_dump() for theme in result.themes],
        key_points=result.key_points,
        feedback=result.feedback.model_dump(),
        keyword_extract=_extract_keywords(answers_text),
        sentiment_score=_score_sentiment(answers_text) if answers_text else None,
    )
    session.add(summary)
    session.commit()
    return summary
