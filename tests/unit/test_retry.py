import pytest

from arxiv_bot.pipeline.errors import PermanentPipelineError, TransientPipelineError
from arxiv_bot.pipeline.retry import RetryPolicy, retry_call


def test_retry_call_retries_transient_errors_then_succeeds() -> None:
    """Retry transient failures until operation succeeds within attempt budget."""
    attempts = {"count": 0}

    def operation() -> str:
        """Fail twice with transient error, then return success payload."""
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise TransientPipelineError("temporary")
        return "ok"

    sleeps: list[float] = []
    result = retry_call(
        operation,
        is_retryable=lambda exc: isinstance(exc, TransientPipelineError),
        policy=RetryPolicy(max_attempts=4, initial_delay_seconds=0.1, backoff_multiplier=2.0),
        sleep_fn=sleeps.append,
    )

    assert result == "ok"
    assert attempts["count"] == 3
    assert sleeps == [0.1, 0.2]


def test_retry_call_stops_on_permanent_error() -> None:
    """Do not retry when the error is classified as permanent."""

    def operation() -> str:
        """Raise permanent pipeline error on first attempt."""
        raise PermanentPipelineError("bad request")

    with pytest.raises(PermanentPipelineError):
        retry_call(
            operation,
            is_retryable=lambda exc: isinstance(exc, TransientPipelineError),
            policy=RetryPolicy(max_attempts=5),
            sleep_fn=lambda _: None,
        )


def test_retry_call_raises_after_max_attempts() -> None:
    """Raise the last transient error when retry budget is exhausted."""
    attempts = {"count": 0}

    def operation() -> str:
        """Always raise transient error to exhaust retries."""
        attempts["count"] += 1
        raise TransientPipelineError("flaky")

    with pytest.raises(TransientPipelineError):
        retry_call(
            operation,
            is_retryable=lambda exc: isinstance(exc, TransientPipelineError),
            policy=RetryPolicy(max_attempts=3, initial_delay_seconds=0.0),
            sleep_fn=lambda _: None,
        )

    assert attempts["count"] == 3
