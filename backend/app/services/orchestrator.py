import logging
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import config
from app.models import Interview, Turn
from app.providers.base import LLMProvider, OnDelta
from app.schemas import ChecklistItem, HistoryMessage
from app.services.retry import call_with_retry

logger = logging.getLogger(__name__)


def _noop(_text: str) -> None:
    pass


def _build_history(turns: list[Turn]) -> list[HistoryMessage]:
    history: list[HistoryMessage] = []
    for turn in turns:
        history.append(HistoryMessage(role="assistant", content=turn.question))
        if turn.answer is not None:
            history.append(HistoryMessage(role="user", content=turn.answer))
    return history


def start_interview(
    session: Session, provider: LLMProvider, topic: str, on_delta: OnDelta | None = None
) -> tuple[Interview, str, str | None]:
    on_delta = on_delta or _noop
    result = call_with_retry(
        lambda: provider.next_turn_stream(topic=topic, checklist=[], history=[], on_delta=on_delta)
    )

    next_question = result.next_question
    reasoning = result.reasoning
    if not next_question:
        # Backend invariant: turn 0 always asks something, regardless of what the provider claims.
        # Deliberately generic wording, not built from checklist item text: that text is internal
        # state the model writes in whatever grammatical person it likes, not a sentence fragment
        # meant to be embedded directly - doing so risks producing something ungrammatical.
        logger.warning("Provider returned no question on interview start - using fallback.")
        next_question = f"To start, what's your own experience with {topic}?"
        reasoning = "Backend fallback: provider returned no question on turn 0."
        on_delta(next_question)

    interview = Interview(
        topic=topic,
        status="in_progress",
        checklist=[item.model_dump() for item in result.checklist],
    )
    session.add(interview)
    session.flush()

    turn = Turn(interview_id=interview.id, turn_index=0, question=next_question)
    session.add(turn)
    session.commit()

    return interview, next_question, reasoning


def submit_answer(
    session: Session,
    provider: LLMProvider,
    interview_id: int,
    answer: str,
    on_delta: OnDelta | None = None,
) -> tuple[str | None, bool, str | None]:
    on_delta = on_delta or _noop
    interview = session.get(Interview, interview_id)
    if interview is None:
        raise ValueError(f"No interview with id {interview_id}")

    turns = list(
        session.scalars(
            select(Turn).where(Turn.interview_id == interview_id).order_by(Turn.turn_index)
        )
    )
    current_turn = turns[-1]

    # Atomic conditional update, not a read-then-write: defends against genuinely concurrent
    # submit_answer calls for the same turn (a rapid double-click racing past the client-side
    # guard, a retried request, two tabs on the same interview). A plain "if current_turn.answer
    # is not None: raise" check-then-set is NOT sufficient here - two concurrent requests can
    # both read answer=None before either commits (verified: it let 3 truly concurrent raw HTTP
    # requests all succeed and each independently call the provider, producing 3 duplicate
    # questions for one answer). WHERE answer IS NULL makes the write itself the check - only
    # one concurrent UPDATE can ever affect a row, and SQLite's file-level write locking
    # serializes the competing statements, so exactly one succeeds.
    updated = session.execute(
        update(Turn)
        .where(Turn.id == current_turn.id, Turn.answer.is_(None))
        .values(answer=answer)
    )
    if updated.rowcount == 0:
        raise ValueError("This question has already been answered.")
    session.flush()
    session.refresh(current_turn)

    completed_turns = len(turns)  # all turns now have an answer, including current_turn

    if completed_turns >= config.MAX_TURNS:
        # Cap already reached - skip the provider call, the question would just be discarded.
        interview.status = "completed"
        interview.completed_at = datetime.now(timezone.utc)
        session.commit()
        return None, True, "Backend cap: MAX_TURNS reached, ending without another provider call."

    history = _build_history(turns)
    checklist = [ChecklistItem(**item) for item in interview.checklist]

    result = call_with_retry(
        lambda: provider.next_turn_stream(
            topic=interview.topic, checklist=checklist, history=history, on_delta=on_delta
        )
    )

    done = result.done
    next_question = result.next_question
    reasoning = result.reasoning

    # Injection risk accumulates across turns regardless of anything else below - even a
    # bail the model doesn't act on should still count toward the cumulative backstop.
    interview.risk_score = min(1.0, interview.risk_score + result.injection_risk)

    confident_injection_bail = done and result.injection_risk >= config.INJECTION_IMMEDIATE_BAILOUT
    if confident_injection_bail:
        logger.warning(
            "Provider confidently flagged prompt injection (risk=%.2f) at turn %d - bailing immediately, MIN_TURNS not enforced for security bails.",
            result.injection_risk,
            completed_turns,
        )

    if completed_turns < config.MIN_TURNS and done and not confident_injection_bail:
        # Backend invariant: the model never needs to know about this floor. Doesn't apply
        # to a confident injection bail above - forcing 3 questions on an actively
        # malicious user defeats the point of ending quickly.
        logger.info(
            "Provider signaled done at turn %d, below MIN_TURNS=%d - overriding.",
            completed_turns,
            config.MIN_TURNS,
        )
        done = False
        if not next_question:
            # Same reasoning as the turn-0 fallback above: don't embed raw checklist item
            # text into a sentence, its grammatical person isn't guaranteed to fit.
            next_question = f"Is there anything else about {interview.topic} you'd like to share?"
            on_delta(next_question)
        reasoning = f"Backend floor override (model signaled done at turn {completed_turns} < MIN_TURNS={config.MIN_TURNS}). {reasoning or ''}".strip()

    if not done and interview.risk_score >= config.INJECTION_CUMULATIVE_BAILOUT:
        # Defense in depth: even if no single turn was scored confidently enough to bail on
        # its own, repeated smaller flags accumulate here and the backend enforces the stop
        # itself rather than trusting the model's per-turn judgment alone.
        logger.warning(
            "Cumulative injection risk %.2f >= %.2f - backend forcing bail.",
            interview.risk_score,
            config.INJECTION_CUMULATIVE_BAILOUT,
        )
        done = True
        next_question = None
        reasoning = f"Backend security bailout: cumulative injection risk {interview.risk_score:.2f} >= {config.INJECTION_CUMULATIVE_BAILOUT}. {reasoning or ''}".strip()

    interview.checklist = [item.model_dump() for item in result.checklist]

    if done:
        interview.status = "completed"
        interview.completed_at = datetime.now(timezone.utc)
    else:
        new_turn = Turn(interview_id=interview_id, turn_index=completed_turns, question=next_question)
        session.add(new_turn)

    session.commit()
    return next_question, done, reasoning


def get_history(session: Session, interview_id: int) -> list[HistoryMessage]:
    turns = list(
        session.scalars(
            select(Turn).where(Turn.interview_id == interview_id).order_by(Turn.turn_index)
        )
    )
    return _build_history(turns)


def list_interviews(session: Session) -> list[Interview]:
    return list(session.scalars(select(Interview).order_by(Interview.created_at.desc())))
