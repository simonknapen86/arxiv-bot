from __future__ import annotations

import re
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from arxiv_bot.models import PaperRecord
from arxiv_bot.pipeline.errors import PermanentPipelineError, TransientPipelineError
from arxiv_bot.pipeline.retry import RetryPolicy, retry_call


def _sanitize_token(value: str) -> str:
    """Convert a free-form token to a lowercase filename-safe slug."""
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "paper"


def _build_filename(record: PaperRecord) -> str:
    """Build a deterministic PDF filename from available record metadata."""
    if record.arxiv_id:
        token = _sanitize_token(record.arxiv_id)
    elif record.doi:
        token = _sanitize_token(record.doi)
    else:
        host = urlparse(record.source_link).netloc or "paper"
        token = _sanitize_token(host)
    return f"{token}.pdf"


def _resolve_pdf_url(record: PaperRecord) -> str | None:
    """Resolve the best PDF URL for a verified record."""
    if record.pdf_url:
        return record.pdf_url
    if record.arxiv_id:
        return f"https://arxiv.org/pdf/{record.arxiv_id}.pdf"
    if record.doi and record.source_link.startswith(("http://", "https://")):
        return record.source_link
    return None


def _is_retryable_download_error(error: Exception) -> bool:
    """Return True when a download error should be retried."""
    return isinstance(error, TransientPipelineError)


def _download_bytes(pdf_url: str) -> bytes:
    """Download binary content from a PDF URL."""
    def operation() -> bytes:
        """Perform one PDF download attempt."""
        try:
            with urlopen(pdf_url, timeout=30) as response:  # nosec B310
                return response.read()
        except HTTPError as exc:
            if exc.code == 429 or exc.code >= 500:
                raise TransientPipelineError(str(exc)) from exc
            raise PermanentPipelineError(str(exc)) from exc
        except (URLError, TimeoutError) as exc:
            raise TransientPipelineError(str(exc)) from exc

    return retry_call(
        operation,
        is_retryable=_is_retryable_download_error,
        policy=RetryPolicy(max_attempts=3, initial_delay_seconds=0.2),
    )


def _looks_like_pdf(payload: bytes) -> bool:
    """Return True when payload starts with the PDF file signature."""
    return payload.startswith(b"%PDF")


def pdf_download_skill(
    records: list[PaperRecord],
    output_dir: str | Path = "artifacts/papers",
    fetch_pdf: Callable[[str], bytes] | None = None,
) -> list[PaperRecord]:
    """Download PDFs for verified records and mark successful downloads."""
    fetch_pdf = fetch_pdf or _download_bytes
    papers_dir = Path(output_dir)
    papers_dir.mkdir(parents=True, exist_ok=True)

    downloaded: list[PaperRecord] = []
    for record in records:
        if not record.verified:
            continue

        pdf_url = _resolve_pdf_url(record)
        if not pdf_url:
            continue

        try:
            payload = fetch_pdf(pdf_url)
        except Exception:
            continue

        if not _looks_like_pdf(payload):
            continue

        filename = _build_filename(record)
        target = papers_dir / filename
        target.write_bytes(payload)

        record.pdf_url = pdf_url
        record.local_pdf_path = str(target)
        record.status = "downloaded"
        downloaded.append(record)

    return downloaded
