from abc import ABC, abstractmethod

from app.schemas import AnalysisResult, ChecklistItem, HistoryMessage, InterviewTurnResult


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

    @abstractmethod
    def analyze(self, topic: str, history: list[HistoryMessage]) -> AnalysisResult:
        """Produce the final structured analysis over the full transcript."""
        raise NotImplementedError
