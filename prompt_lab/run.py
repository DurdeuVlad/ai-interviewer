"""
Prompt evaluation harness (Gemini).

Runs each (interviewer prompt variant x model x scenario) combination through
a full scripted interview, then runs the analyst prompt over the resulting
transcript. Saves one JSON file per combination to results/raw/ for later
grading (grading is a separate, manual step against rubric.md — this script
only produces raw transcripts, it does not score anything).

Usage:
    uv run run.py
"""

import json
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from google import genai
from google.genai import types

import config

load_dotenv()
client = genai.Client()

INTERVIEW_FUNCTION = types.FunctionDeclaration(
    name="interview_turn",
    description="Report the current checklist state and the next question to ask (or signal the interview is done).",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "checklist": types.Schema(
                type="ARRAY",
                description="The full checklist of 3-5 things to learn about the person's view on the topic. On the first turn, invent this list. On later turns, return it updated.",
                items=types.Schema(
                    type="OBJECT",
                    properties={
                        "id": types.Schema(type="STRING"),
                        "text": types.Schema(type="STRING"),
                        "covered": types.Schema(type="BOOLEAN"),
                    },
                    required=["id", "text", "covered"],
                ),
            ),
            "next_question": types.Schema(
                type="STRING",
                description="The next question to ask the person. Empty string if done is true.",
            ),
            "done": types.Schema(
                type="BOOLEAN",
                description="True if the checklist is fully covered and the interview should end.",
            ),
        },
        required=["checklist", "next_question", "done"],
    ),
)

ANALYSIS_FUNCTION = types.FunctionDeclaration(
    name="analysis_result",
    description="Report the structured analysis of a completed interview transcript.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "themes": types.Schema(
                type="ARRAY",
                items=types.Schema(
                    type="OBJECT",
                    properties={
                        "name": types.Schema(type="STRING"),
                        "sentiment": types.Schema(
                            type="STRING",
                            enum=["positive", "negative", "mixed", "neutral"],
                        ),
                        "quote": types.Schema(type="STRING"),
                    },
                    required=["name", "sentiment", "quote"],
                ),
            ),
            "key_points": types.Schema(
                type="ARRAY",
                items=types.Schema(type="STRING"),
            ),
        },
        required=["themes", "key_points"],
    ),
)


def load_prompt(name: str) -> str:
    return (config.PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def extract_function_call(response, fn_name: str) -> dict:
    candidate = response.candidates[0]
    for part in candidate.content.parts:
        fc = getattr(part, "function_call", None)
        if fc and fc.name == fn_name:
            return dict(fc.args)
    # Fallback: some models may emit plain JSON text instead of a function call.
    text = getattr(response, "text", "") or ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError(
            f"Model did not call function '{fn_name}' and text was not JSON: {text!r}"
        )


def run_interview(model: str, interviewer_prompt_name: str, scenario: dict) -> dict:
    system_prompt = load_prompt(interviewer_prompt_name).format(topic=scenario["topic"])
    tool = types.Tool(function_declarations=[INTERVIEW_FUNCTION])
    gen_config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[tool],
    )

    contents = []
    transcript = []
    scripted_answers = list(scenario["scripted_answers"])

    for turn in range(config.MAX_TURNS):
        if not contents:
            contents.append(
                {"role": "user", "parts": [{"text": "(interview is starting, ask your first question)"}]}
            )

        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=gen_config,
        )
        state = extract_function_call(response, "interview_turn")

        transcript.append(
            {
                "turn": turn,
                "question": state.get("next_question"),
                "checklist": state.get("checklist"),
                "done": state.get("done"),
            }
        )

        if state.get("done") or not state.get("next_question"):
            break

        contents.append({"role": "model", "parts": [{"text": state["next_question"]}]})

        if turn < len(scripted_answers):
            answer = scripted_answers[turn]
        else:
            answer = "That's all I have to say on this."
        contents.append({"role": "user", "parts": [{"text": answer}]})
        transcript[-1]["answer"] = answer

    # Return conversation in a provider-neutral shape for downstream grading/analysis.
    conversation = [
        {"role": "assistant" if c["role"] == "model" else "user", "content": c["parts"][0]["text"]}
        for c in contents
        if c["parts"][0]["text"] != "(interview is starting, ask your first question)"
    ]
    return {"conversation": conversation, "turns": transcript}


def run_analysis(model: str, scenario: dict, conversation: list) -> dict:
    system_prompt = load_prompt(config.ANALYST_PROMPT_VARIANT).format(topic=scenario["topic"])
    tool = types.Tool(function_declarations=[ANALYSIS_FUNCTION])
    gen_config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[tool],
    )
    transcript_text = "\n".join(f"{m['role']}: {m['content']}" for m in conversation)

    response = client.models.generate_content(
        model=model,
        contents=[{"role": "user", "parts": [{"text": f"Transcript:\n{transcript_text}"}]}],
        config=gen_config,
    )
    return extract_function_call(response, "analysis_result")


def main():
    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    scenarios = json.loads(config.SCENARIOS_FILE.read_text(encoding="utf-8"))

    combos = [
        (interviewer_variant, model, scenario)
        for interviewer_variant in config.INTERVIEWER_PROMPT_VARIANTS
        for model in config.MODELS
        for scenario in scenarios
    ]

    print(f"Running {len(combos)} combinations...")

    for interviewer_variant, model, scenario in combos:
        out_name = f"{interviewer_variant}__{model}__{scenario['id']}.json"
        out_path = config.RESULTS_DIR / out_name
        print(f"  -> {out_name}")

        try:
            interview_result = run_interview(model, interviewer_variant, scenario)
            analysis_result = run_analysis(model, scenario, interview_result["conversation"])
        except Exception as exc:  # noqa: BLE001 - lab script, surface everything to the log
            out_path.write_text(
                json.dumps(
                    {
                        "interviewer_prompt": interviewer_variant,
                        "model": model,
                        "scenario_id": scenario["id"],
                        "category": scenario.get("category"),
                        "error": str(exc),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"     ERROR: {exc}")
            continue

        out_path.write_text(
            json.dumps(
                {
                    "interviewer_prompt": interviewer_variant,
                    "analyst_prompt": config.ANALYST_PROMPT_VARIANT,
                    "model": model,
                    "scenario_id": scenario["id"],
                    "category": scenario.get("category"),
                    "topic": scenario["topic"],
                    "persona": scenario["persona"],
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "interview": interview_result,
                    "analysis": analysis_result,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    print(f"Done. Raw transcripts in {config.RESULTS_DIR}")


if __name__ == "__main__":
    if not config.SCENARIOS_FILE.exists():
        print(f"Missing scenarios file: {config.SCENARIOS_FILE}", file=sys.stderr)
        sys.exit(1)
    main()
