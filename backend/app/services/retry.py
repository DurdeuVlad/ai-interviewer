import logging
import time
from typing import Callable, TypeVar

from app import config

logger = logging.getLogger(__name__)

T = TypeVar("T")


def call_with_retry(fn: Callable[[], T]) -> T:
    """Retry once with a fixed backoff, then let the exception propagate (fail loudly).

    Never silently falls back to a different provider - a visible failure during
    grading/demo is preferable to masking a real bug.
    """
    attempts = config.RETRY_ATTEMPTS + 1
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - provider calls can raise many exception types
            last_exc = exc
            if attempt < attempts - 1:
                logger.warning("Provider call failed (attempt %d/%d): %s", attempt + 1, attempts, exc)
                time.sleep(config.RETRY_BACKOFF_SECONDS)
    raise last_exc  # type: ignore[misc]
