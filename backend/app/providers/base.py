from abc import ABC, abstractmethod
from typing import Callable

from app.schemas import AnalysisResult, ChecklistItem, HistoryMessage, InterviewTurnResult

OnDelta = Callable[[str], None]


class LLMProvider(ABC):
    """Strategy interface every provider (Claude, Gemini, OpenAI, Mock) implements.

    Providers are deliberately dumb: given topic/checklist/history in, structured
    result out. No orchestration logic, no persistence, no turn-counting — that
    all lives in services/orchestrator.py.
    """

    @abstractmethod
    def next_turn(
        self,
        topic: str,
        checklist: list[ChecklistItem],
        history: list[HistoryMessage],
    ) -> InterviewTurnResult:
        """Decide the next interview question and updated checklist state.

        `checklist` is empty on the very first call — the provider must invent
        3-5 items itself based on the topic.
        """
        raise NotImplementedError

    def next_turn_stream(
        self,
        topic: str,
        checklist: list[ChecklistItem],
        history: list[HistoryMessage],
        on_delta: OnDelta,
    ) -> InterviewTurnResult:
        """Same as next_turn, but calls on_delta with question text as it's generated.

        Default implementation has no real incremental streaming - it just calls
        next_turn and emits the whole question in one burst. Providers whose API
        genuinely supports streaming structured/tool-call output (OpenAI's
        Responses API does, reliably) should override this for real token-by-token
        UX. Providers that don't (or where it isn't well-supported, e.g. Gemini's
        SDK doesn't reliably expose partial function-call argument deltas) can
        just rely on this default rather than faking it.
        """
        result = self.next_turn(topic, checklist, history)
        if result.next_question:
            on_delta(result.next_question)
        return result

    @abstractmethod
    def analyze(self, topic: str, history: list[HistoryMessage]) -> AnalysisResult:
        """Produce the final structured analysis over the full transcript."""
        raise NotImplementedError
