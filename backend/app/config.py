import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
PROMPTS_DIR = Path(__file__).parent / "prompts"
EXPORTS_DIR = BASE_DIR / "exports"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("1", "true", "yes")

# Claude dropped for now, no API key to test against - see docs/decisions.md.

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")

DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "interviews.db"))
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")

MIN_TURNS = 3
MAX_TURNS = 8

# Prompt injection handling: the model reports a per-turn injection_risk (0.0-1.0).
# If it's confident (>= IMMEDIATE) AND itself signals done, bail right away, bypassing
# MIN_TURNS - forcing 3 questions on an actively malicious user defeats the point of a
# fast bail. If it's not confident but still elevated, we don't act on a single turn -
# instead risk accumulates turn over turn on the interview record, and once the running
# total crosses CUMULATIVE, the backend forces a bail itself regardless of what the
# model says, as a defense-in-depth backstop against under-scoring any single turn.
INJECTION_IMMEDIATE_BAILOUT = 0.85
INJECTION_CUMULATIVE_BAILOUT = 0.8

RETRY_ATTEMPTS = 1
RETRY_BACKOFF_SECONDS = 2

# Terminal UX: per-character delay while "typing" streamed question text, seconds.
TYPING_DELAY_SECONDS = float(os.getenv("TYPING_DELAY_SECONDS", "0.015"))
