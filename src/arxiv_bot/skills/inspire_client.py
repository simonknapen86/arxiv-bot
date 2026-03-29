from __future__ import annotations

from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from arxiv_bot.models import PaperRecord
from arxiv_bot.pipeline.errors import PermanentPipelineError, TransientPipelineError
from arxiv_bot.pipeline.retry import RetryPolicy, retry_call


@dataclass
class InspireClient:
    """Fetch BibTeX entries from INSPIRE-HEP identifier endpoints."""

    base_url: str = "https://inspirehep.net/api"
    timeout_seconds: int = 15
    retry_policy: RetryPolicy = field(
        default_factory=lambda: RetryPolicy(max_attempts=3, initial_delay_seconds=0.2)
    )

    def _is_retryable_error(self, error: Exception) -> bool:
        """Return True when an INSPIRE request error should be retried."""
        return isinstance(error, TransientPipelineError)

    def _fetch_text(self, url: str) -> str | None:
        """Fetch UTF-8 text from a URL and return None on transport errors."""
        def operation() -> str:
            """Perform one INSPIRE HTTP request attempt."""
            try:
                with urlopen(url, timeout=self.timeout_seconds) as response:  # nosec B310
                    return response.read().decode("utf-8", errors="replace")
            except HTTPError as exc:
                if exc.code == 429 or exc.code >= 500:
                    raise TransientPipelineError(str(exc)) from exc
                raise PermanentPipelineError(str(exc)) from exc
            except (URLError, TimeoutError) as exc:
                raise TransientPipelineError(str(exc)) from exc

        try:
            return retry_call(
                operation,
                is_retryable=self._is_retryable_error,
                policy=self.retry_policy,
            )
        except (TransientPipelineError, PermanentPipelineError):
            return None

    def _arxiv_url(self, arxiv_id: str) -> str:
        """Build an INSPIRE arXiv lookup URL that requests BibTeX format."""
        return f"{self.base_url}/arxiv/{quote(arxiv_id, safe='')}" + "?format=bibtex"

    def _doi_url(self, doi: str) -> str:
        """Build an INSPIRE DOI lookup URL that requests BibTeX format."""
        return f"{self.base_url}/doi/{quote(doi, safe='')}" + "?format=bibtex"

    def fetch_bibtex(self, record: PaperRecord) -> str | None:
        """Fetch BibTeX for a record by arXiv id first, then DOI."""
        if record.arxiv_id:
            arxiv_entry = self._fetch_text(self._arxiv_url(record.arxiv_id))
            if arxiv_entry and arxiv_entry.strip():
                return arxiv_entry.strip()

        if record.doi:
            doi_entry = self._fetch_text(self._doi_url(record.doi))
            if doi_entry and doi_entry.strip():
                return doi_entry.strip()

        return None
