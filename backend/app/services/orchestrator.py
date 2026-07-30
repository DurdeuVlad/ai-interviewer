import logging
from datetime import datetime, timezone

from sqlalchemy import select
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
) -> tuple[Interview, str]:
    on_delta = on_delta or _noop
    result = call_with_retry(
        lambda: provider.next_turn_stream(topic=topic, checklist=[], history=[], on_delta=on_delta)
    )

    next_question = result.next_question
    if not next_question:
        # Backend invariant: turn 0 always asks something, regardless of what the provider claims.
        logger.warning("Provider returned no question on interview start - using fallback.")
        open_items = [c for c in result.checklist if not c.covered]
        next_question = (
            f"To start, can you tell me about {open_items[0].text}?"
            if open_items
            else f"To start, what's your general take on {topic}?"
        )
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

    return interview, next_question


def submit_answer(
    session: Session,
    provider: LLMProvider,
    interview_id: int,
    answer: str,
    on_delta: OnDelta | None = None,
) -> tuple[str | None, bool]:
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
    current_turn.answer = answer
    session.flush()

    completed_turns = len(turns)  # all turns now have an answer, including current_turn

    if completed_turns >= config.MAX_TURNS:
        # Cap already reached - skip the provider call, the question would just be discarded.
        interview.status = "completed"
        interview.completed_at = datetime.now(timezone.utc)
        session.commit()
        return None, True

    history = _build_history(turns)
    checklist = [ChecklistItem(**item) for item in interview.checklist]

    result = call_with_retry(
        lambda: provider.next_turn_stream(
            topic=interview.topic, checklist=checklist, history=history, on_delta=on_delta
        )
    )

    done = result.done
    next_question = result.next_question

    if completed_turns < config.MIN_TURNS and done:
        # Backend invariant: the model never needs to know about this floor.
        logger.info(
            "Provider signaled done at turn %d, below MIN_TURNS=%d - overriding.",
            completed_turns,
            config.MIN_TURNS,
        )
        done = False
        if not next_question:
            open_items = [c for c in result.checklist if not c.covered]
            next_question = (
                f"Can you tell me more about {open_items[0].text}?"
                if open_items
                else f"Is there anything else about {interview.topic} you'd like to share?"
            )
            on_delta(next_question)

    interview.checklist = [item.model_dump() for item in result.checklist]

    if done:
        interview.status = "completed"
        interview.completed_at = datetime.now(timezone.utc)
    else:
        new_turn = Turn(interview_id=interview_id, turn_index=completed_turns, question=next_question)
        session.add(new_turn)

    session.commit()
    return next_question, done


def get_history(session: Session, interview_id: int) -> list[HistoryMessage]:
    turns = list(
        session.scalars(
            select(Turn).where(Turn.interview_id == interview_id).order_by(Turn.turn_index)
        )
    )
    return _build_history(turns)
