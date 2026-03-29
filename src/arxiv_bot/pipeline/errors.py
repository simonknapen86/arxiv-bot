from __future__ import annotations


class PipelineError(Exception):
    """Base exception for pipeline-level failures."""


class TransientPipelineError(PipelineError):
    """Exception class for retryable transient failures."""


class PermanentPipelineError(PipelineError):
    """Exception class for non-retryable permanent failures."""
