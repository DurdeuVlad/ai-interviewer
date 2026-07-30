"""Terminal entry point for the AI Interviewer.

Usage:
    uv run python -m app.cli
"""

import os
import sys
import time

if os.name == "nt":
    os.system("chcp 65001 >NUL")
    sys.stdout.reconfigure(encoding="utf-8")

from colorama import Fore, Style, init as colorama_init

from app import config
from app.db import get_session, init_db
from app.providers.factory import get_provider
from app.services import analysis, export, orchestrator

colorama_init()


class _QuestionStreamer:
    """Shows a placeholder while waiting on the model, then types the question out
    character-by-character once real text starts arriving. Silences itself entirely
    if a turn ends with done=True and no question ever arrives."""

    def __init__(self, turn_number: int) -> None:
        self.started = False
        self._placeholder_shown = False
        self._turn_number = turn_number

    def show_waiting(self) -> None:
        print(Fore.YELLOW + "..." + Style.RESET_ALL, end="", flush=True)
        self._placeholder_shown = True

    def __call__(self, text: str) -> None:
        if not self.started:
            if self._placeholder_shown:
                print("\r" + " " * 3 + "\r", end="", flush=True)
            print(Fore.CYAN + f"[{self._turn_number}] Q: ", end="", flush=True)
            self.started = True
        for ch in text:
            print(ch, end="", flush=True)
            if config.TYPING_DELAY_SECONDS:
                time.sleep(config.TYPING_DELAY_SECONDS)

    def finish(self) -> None:
        if self.started:
            print(Style.RESET_ALL)
        elif self._placeholder_shown:
            print("\r" + " " * 3 + "\r", end="", flush=True)


def _print_debug(interview, reasoning: str | None) -> None:
    if not config.DEBUG_MODE:
        return
    checklist_state = ", ".join(
        f"{item['id']}:{'done' if item['covered'] else 'open'}" for item in interview.checklist
    )
    print(Fore.BLACK + Style.BRIGHT + f"  [debug] reasoning: {reasoning or '(none)'}" + Style.RESET_ALL)
    print(Fore.BLACK + Style.BRIGHT + f"  [debug] checklist: {checklist_state}" + Style.RESET_ALL)


def _sentiment_label(score: float) -> str:
    if score >= 0.5:
        return "very positive"
    if score >= 0.05:
        return "positive"
    if score <= -0.5:
        return "very negative"
    if score <= -0.05:
        return "negative"
    return "neutral"


def _sentiment_color(sentiment: str) -> str:
    return {
        "positive": Fore.GREEN,
        "negative": Fore.RED,
        "mixed": Fore.YELLOW,
        "neutral": Fore.WHITE,
    }.get(sentiment, Fore.WHITE)


def _print_summary(summary) -> None:
    rule = "=" * 60
    print(f"\n{rule}")
    print(Style.BRIGHT + "  SUMMARY" + Style.RESET_ALL)
    print(rule)

    print(Style.BRIGHT + "\nThemes:" + Style.RESET_ALL)
    if summary.themes:
        for theme in summary.themes:
            color = _sentiment_color(theme["sentiment"])
            print(f"- {theme['name']} ({color}{theme['sentiment']}{Style.RESET_ALL}): \"{theme['quote']}\"")
    else:
        print("No clear themes emerged from this conversation.")

    print(Style.BRIGHT + "\nKey points:" + Style.RESET_ALL)
    if summary.key_points:
        for point in summary.key_points:
            print(f"- {point}")
    else:
        print("No concrete points could be drawn from the responses given.")

    feedback = summary.feedback or {}
    if feedback.get("positives") or feedback.get("constructive"):
        print(Style.BRIGHT + "\nFeedback on the interview:" + Style.RESET_ALL)
        for point in feedback.get("positives", []):
            print(Fore.GREEN + f"+ {point}" + Style.RESET_ALL)
        for point in feedback.get("constructive", []):
            print(Fore.YELLOW + f"- {point}" + Style.RESET_ALL)

    print(Style.BRIGHT + "\nBonus analysis:" + Style.RESET_ALL)
    if summary.keyword_extract:
        print(f"Keywords: {', '.join(summary.keyword_extract)}")
    if summary.sentiment_score is not None:
        label = _sentiment_label(summary.sentiment_score)
        print(f"Overall sentiment: {summary.sentiment_score:+.3f} ({label})")

    print(f"\n{rule}")
    print("Thanks for taking part in this interview!")


def _handle_early_exit(session, interview) -> None:
    print(Fore.YELLOW + "\n\nInterview ended early." + Style.RESET_ALL)
    if interview is None:
        return
    json_path = export.export_json(session, interview.id)
    pdf_path = export.export_pdf(session, interview.id)
    print(f"What was captured is saved to:\n  {json_path}\n  {pdf_path}")


def main() -> None:
    init_db()
    session = get_session()
    provider = get_provider()
    interview = None

    try:
        print("=== AI Interviewer ===")
        topic = input("What topic would you like to be interviewed on? ").strip()
        while not topic:
            topic = input("Please enter a topic: ").strip()

        print()
        streamer = _QuestionStreamer(turn_number=1)
        streamer.show_waiting()
        interview, question, reasoning = orchestrator.start_interview(
            session, provider, topic, on_delta=streamer
        )
        streamer.finish()
        _print_debug(interview, reasoning)

        turn_number = 1
        while True:
            answer = input("> ")
            turn_number += 1
            streamer = _QuestionStreamer(turn_number=turn_number)
            streamer.show_waiting()
            question, done, reasoning = orchestrator.submit_answer(
                session, provider, interview.id, answer, on_delta=streamer
            )
            streamer.finish()
            _print_debug(interview, reasoning)
            if done:
                break

        print(Fore.YELLOW + "\nInterview complete. Generating summary..." + Style.RESET_ALL)
        summary = analysis.run_analysis(session, provider, interview.id)
        _print_summary(summary)

        json_path = export.export_json(session, interview.id)
        pdf_path = export.export_pdf(session, interview.id)
        print(f"\nSaved transcript + summary to:\n  {json_path}\n  {pdf_path}")

    except (KeyboardInterrupt, EOFError):
        _handle_early_exit(session, interview)
    finally:
        session.close()


if __name__ == "__main__":
    main()
