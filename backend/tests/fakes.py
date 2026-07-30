from app.providers.base import LLMProvider
from app.schemas import AnalysisResult, ChecklistItem, HistoryMessage, InterviewFeedback, InterviewTurnResult, Theme


class ScriptedProvider(LLMProvider):
    """Returns a pre-scripted sequence of InterviewTurnResult, one per call.

    Lets orchestrator tests pin down exact `done`/`injection_risk` combinations
    that MockProvider's own checklist-covering heuristic can't easily produce
    (e.g. "done=True below MIN_TURNS with no injection risk").
    """

    def __init__(self, script: list[InterviewTurnResult]):
        self._script = list(script)
        self.calls = 0

    def next_turn(self, topic, checklist, history) -> InterviewTurnResult:
        result = self._script[self.calls]
        self.calls += 1
        return result

    def analyze(self, topic, history) -> AnalysisResult:
        raise NotImplementedError


def make_result(done: bool, next_question: str | None = None, injection_risk: float = 0.0) -> InterviewTurnResult:
    return InterviewTurnResult(
        checklist=[ChecklistItem(id="c1", text="something", covered=done)],
        next_question=next_question,
        done=done,
        reasoning=None,
        injection_risk=injection_risk,
    )


def make_analysis(themes=None, key_points=None, positives=None, constructive=None) -> AnalysisResult:
    return AnalysisResult(
        themes=themes or [Theme(name="Theme", sentiment="neutral", quote="quote")],
        key_points=key_points if key_points is not None else ["point one"],
        feedback=InterviewFeedback(positives=positives or [], constructive=constructive or []),
    )
