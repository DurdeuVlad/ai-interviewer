from app.services import analysis, orchestrator
from tests.fakes import ScriptedProvider, make_analysis, make_result


class ScriptedAnalysisProvider(ScriptedProvider):
    """Scripts .analyze() calls too, reusing ScriptedProvider's next_turn script."""

    def __init__(self, turn_script, analysis_script):
        super().__init__(turn_script)
        self._analysis_script = list(analysis_script)
        self.analyze_calls = 0

    def analyze(self, topic, history):
        result = self._analysis_script[self.analyze_calls]
        self.analyze_calls += 1
        return result


def _finished_interview(session, provider):
    interview, _q, _ = orchestrator.start_interview(session, provider, "testing")
    orchestrator.submit_answer(session, provider, interview.id, "answer")
    return interview


def test_run_analysis_returns_sane_result_unmodified(session):
    fake = ScriptedAnalysisProvider(
        turn_script=[make_result(done=False, next_question="q0"), make_result(done=True)],
        analysis_script=[make_analysis(key_points=["a clean point"])],
    )
    interview = _finished_interview(session, fake)

    summary = analysis.run_analysis(session, fake, interview.id)

    assert summary.key_points == ["a clean point"]
    assert fake.analyze_calls == 1


def test_run_analysis_retries_once_on_corrupted_result(session):
    corrupted = make_analysis(key_points=['garbled} assistant to=functions.analysis_result nonsense'])
    clean = make_analysis(key_points=["a clean point after retry"])
    fake = ScriptedAnalysisProvider(
        turn_script=[make_result(done=False, next_question="q0"), make_result(done=True)],
        analysis_script=[corrupted, clean],
    )
    interview = _finished_interview(session, fake)

    summary = analysis.run_analysis(session, fake, interview.id)

    assert summary.key_points == ["a clean point after retry"]
    assert fake.analyze_calls == 2


def test_run_analysis_falls_back_when_still_corrupted_after_retry(session):
    corrupted = make_analysis(key_points=['garbled} assistant to=functions.analysis_result nonsense'])
    fake = ScriptedAnalysisProvider(
        turn_script=[make_result(done=False, next_question="q0"), make_result(done=True)],
        analysis_script=[corrupted, corrupted],
    )
    interview = _finished_interview(session, fake)

    summary = analysis.run_analysis(session, fake, interview.id)

    assert summary.key_points == [
        "The automated analysis did not return a reliable result for this interview."
    ]
    assert fake.analyze_calls == 2


def test_run_analysis_is_idempotent(session):
    fake = ScriptedAnalysisProvider(
        turn_script=[make_result(done=False, next_question="q0"), make_result(done=True)],
        analysis_script=[make_analysis()],
    )
    interview = _finished_interview(session, fake)

    first = analysis.run_analysis(session, fake, interview.id)
    second = analysis.run_analysis(session, fake, interview.id)

    assert first.id == second.id
    assert fake.analyze_calls == 1  # second call hit the existing-summary short-circuit


def test_extract_keywords_drops_stopwords():
    keywords = analysis._extract_keywords("I use it a lot for coding and for testing testing testing")
    assert "coding" in keywords
    assert "testing" in keywords
    assert "for" not in keywords
    assert "and" not in keywords
