import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
PROMPTS_DIR = Path(__file__).parent / "prompts"
EXPORTS_DIR = BASE_DIR / "exports"

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")

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

RETRY_ATTEMPTS = 1
RETRY_BACKOFF_SECONDS = 2
