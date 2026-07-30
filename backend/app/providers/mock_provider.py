from app.providers.base import LLMProvider
from app.schemas import (
    AnalysisResult,
    ChecklistItem,
    HistoryMessage,
    InterviewFeedback,
    InterviewTurnResult,
    Theme,
)

_ASPECTS = ["how they use it day to day", "what worries them about it", "what they'd change about it"]


class MockProvider(LLMProvider):
    """Deterministic, no-network provider for dev/demo/tests.

    Mirrors the real providers' contract exactly (3-item checklist, one question
    per turn, structured done/covered signaling) without ever calling out.
    """

    def next_turn(
        self,
        topic: str,
        checklist: list[ChecklistItem],
        history: list[HistoryMessage],
    ) -> InterviewTurnResult:
        if not checklist:
            checklist = [
                ChecklistItem(id=f"c{i + 1}", text=aspect, covered=False)
                for i, aspect in enumerate(_ASPECTS)
            ]
        else:
            checklist = [item.model_copy() for item in checklist]

        answered_count = sum(1 for m in history if m.role == "user")
        covered_so_far = min(answered_count, len(checklist))
        for i in range(covered_so_far):
            checklist[i].covered = True

        if all(item.covered for item in checklist):
            return InterviewTurnResult(
                checklist=checklist, next_question=None, done=True, reasoning="Checklist fully covered."
            )

        next_item = checklist[covered_so_far]
        question = f"[mock] Regarding {topic}, {next_item.text} - what's your take?"
        reasoning = f"Moving to checklist item '{next_item.id}' ({next_item.text})."
        return InterviewTurnResult(
            checklist=checklist, next_question=question, done=False, reasoning=reasoning
        )

    def analyze(self, topic: str, history: list[HistoryMessage]) -> AnalysisResult:
        answers = [m.content for m in history if m.role == "user"]
        quote = answers[0] if answers else "(no answers given)"
        return AnalysisResult(
            themes=[
                Theme(name=f"General view on {topic}", sentiment="neutral", quote=quote),
            ],
            key_points=answers,
            feedback=InterviewFeedback(
                positives=["[mock] Answered every question without skipping."],
                constructive=["[mock] Some answers could have included more concrete detail."],
            ),
        )
