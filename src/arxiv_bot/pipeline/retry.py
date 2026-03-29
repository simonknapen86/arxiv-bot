from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


@dataclass
class RetryPolicy:
    """Define retry behavior for transient pipeline operations."""

    max_attempts: int = 3
    initial_delay_seconds: float = 0.2
    backoff_multiplier: float = 2.0


def retry_call(
    operation: Callable[[], T],
    is_retryable: Callable[[Exception], bool],
    policy: RetryPolicy | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> T:
    """Execute an operation with exponential-backoff retries for retryable errors."""
    active = policy or RetryPolicy()
    delay = active.initial_delay_seconds

    last_error: Exception | None = None
    for attempt in range(1, active.max_attempts + 1):
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if not is_retryable(exc) or attempt == active.max_attempts:
                raise
            sleep_fn(delay)
            delay *= active.backoff_multiplier

    if last_error is not None:
        raise last_error
    raise RuntimeError("retry_call failed without capturing an exception")
