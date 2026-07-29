"""Terminal entry point for the AI Interviewer.

Usage:
    uv run python -m app.cli
"""

from app import config
from app.db import get_session, init_db
from app.providers.factory import get_provider
from app.services import analysis, export, orchestrator


def _print_summary(summary) -> None:
    print("\n=== Summary ===")
    for theme in summary.themes:
        print(f"- {theme['name']} ({theme['sentiment']}): \"{theme['quote']}\"")
    print("\nKey points:")
    for point in summary.key_points:
        print(f"- {point}")
    if summary.keyword_extract:
        print(f"\nKeywords: {', '.join(summary.keyword_extract)}")
    if summary.sentiment_score is not None:
        print(f"Overall sentiment score: {summary.sentiment_score:.3f}")


def main() -> None:
    init_db()
    session = get_session()
    provider = get_provider()

    print("=== AI Interviewer ===")
    topic = input("What topic would you like to be interviewed on? ").strip()
    while not topic:
        topic = input("Please enter a topic: ").strip()

    interview, question = orchestrator.start_interview(session, provider, topic)

    while True:
        print(f"\nQ: {question}")
        answer = input("> ")
        print("[thinking...]")
        question, done = orchestrator.submit_answer(session, provider, interview.id, answer)
        if done:
            break

    print("\nInterview complete. Generating summary...")
    summary = analysis.run_analysis(session, provider, interview.id)
    _print_summary(summary)

    json_path = export.export_json(session, interview.id)
    pdf_path = export.export_pdf(session, interview.id)
    print(f"\nSaved transcript + summary to:\n  {json_path}\n  {pdf_path}")

    session.close()


if __name__ == "__main__":
    main()
