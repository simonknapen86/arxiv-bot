from __future__ import annotations

from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from arxiv_bot.models import PaperRecord


@dataclass
class InspireClient:
    """Fetch BibTeX entries from INSPIRE-HEP identifier endpoints."""

    base_url: str = "https://inspirehep.net/api"
    timeout_seconds: int = 15

    def _fetch_text(self, url: str) -> str | None:
        """Fetch UTF-8 text from a URL and return None on transport errors."""
        try:
            with urlopen(url, timeout=self.timeout_seconds) as response:  # nosec B310
                return response.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError):
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
