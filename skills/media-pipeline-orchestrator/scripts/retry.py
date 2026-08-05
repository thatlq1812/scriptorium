"""Exponential-backoff retry decorator for Gemini API calls (image/video/audio
generation) -- transient rate-limit/5xx errors are common across all 3
skills this orchestrator drives. Pattern observed for real in
youtube-shorts-pipeline (MIT, data/references/e2e-pipeline/NOTES.md #1) --
reimplemented independently here (a generic decorator, not their specific
file), applied uniformly to every Gemini call this orchestrator makes."""
from __future__ import annotations

import functools
import time
from typing import Callable, TypeVar

T = TypeVar("T")


def with_retry(max_retries: int = 3, base_delay: float = 2.0, exceptions: tuple = (Exception,)) -> Callable:
    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            last_exc: Exception | None = None
            for attempt in range(1, max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        break
                    delay = base_delay * (2 ** (attempt - 1))
                    print(f"    (attempt {attempt}/{max_retries} failed: {exc}; retrying in {delay:.0f}s)")
                    time.sleep(delay)
            assert last_exc is not None
            raise last_exc
        return wrapper
    return decorator
