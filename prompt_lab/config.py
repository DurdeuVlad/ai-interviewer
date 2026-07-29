from pathlib import Path

ROOT = Path(__file__).parent
PROMPTS_DIR = ROOT / "prompts"
SCENARIOS_FILE = ROOT / "scenarios" / "scenarios.json"
RESULTS_DIR = ROOT / "results" / "raw"

# Edit this list to whatever Gemini models you want to compare.
# Check https://ai.google.dev/gemini-api/docs/models for the current catalog.
MODELS = [
    "gemini-2.5-flash",
]

INTERVIEWER_PROMPT_VARIANTS = ["interviewer_v1", "interviewer_v2"]
ANALYST_PROMPT_VARIANT = "analyst_v1"

MAX_TURNS = 6
