from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from urllib.parse import urlencode
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

    def _fetch_json(self, url: str) -> dict[str, object] | None:
        """Fetch JSON payload from INSPIRE and return None on transport/parse errors."""
        payload = self._fetch_text(url)
        if not payload:
            return None
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return None
        if isinstance(data, dict):
            return data
        return None

    def _arxiv_url(self, arxiv_id: str) -> str:
        """Build an INSPIRE arXiv lookup URL that requests BibTeX format."""
        return f"{self.base_url}/arxiv/{quote(arxiv_id, safe='')}" + "?format=bibtex"

    def _doi_url(self, doi: str) -> str:
        """Build an INSPIRE DOI lookup URL that requests BibTeX format."""
        return f"{self.base_url}/doi/{quote(doi, safe='')}" + "?format=bibtex"

    def _arxiv_json_url(self, arxiv_id: str) -> str:
        """Build an INSPIRE arXiv lookup URL that returns JSON metadata."""
        return f"{self.base_url}/arxiv/{quote(arxiv_id, safe='')}"

    def _doi_json_url(self, doi: str) -> str:
        """Build an INSPIRE DOI lookup URL that returns JSON metadata."""
        return f"{self.base_url}/doi/{quote(doi, safe='')}"

    def _literature_by_recid_url(self, recid: str) -> str:
        """Build a literature endpoint URL for one INSPIRE record id."""
        return f"{self.base_url}/literature/{quote(recid, safe='')}"

    def _literature_search_url(self, query: str, size: int) -> str:
        """Build an INSPIRE literature search URL."""
        params = urlencode({"q": query, "size": str(size)})
        return f"{self.base_url}/literature?{params}"

    def _lookup_seed_record(self, record: PaperRecord) -> dict[str, object] | None:
        """Lookup one seed record in INSPIRE using arXiv id first, then DOI."""
        if record.arxiv_id:
            arxiv_payload = self._fetch_json(self._arxiv_json_url(record.arxiv_id))
            if arxiv_payload:
                return arxiv_payload

        if record.doi:
            doi_payload = self._fetch_json(self._doi_json_url(record.doi))
            if doi_payload:
                return doi_payload

        return None

    def _metadata(self, payload: dict[str, object]) -> dict[str, object]:
        """Extract metadata object from INSPIRE payload."""
        metadata = payload.get("metadata")
        if isinstance(metadata, dict):
            return metadata
        return {}

    def _extract_first_text(self, values: object, key: str) -> str | None:
        """Extract first text value from a list[dict] INSPIRE metadata field."""
        if not isinstance(values, list):
            return None
        for item in values:
            if isinstance(item, dict):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    def _extract_authors(self, metadata: dict[str, object]) -> list[str]:
        """Extract normalized author names from INSPIRE metadata."""
        raw_authors = metadata.get("authors")
        if not isinstance(raw_authors, list):
            return []
        authors: list[str] = []
        for item in raw_authors:
            if not isinstance(item, dict):
                continue
            full_name = item.get("full_name")
            if isinstance(full_name, str) and full_name.strip():
                authors.append(full_name.strip())
        return authors

    def _extract_year(self, metadata: dict[str, object]) -> int | None:
        """Extract a publication year from INSPIRE date metadata."""
        raw_date = metadata.get("earliest_date")
        if not isinstance(raw_date, str):
            return None
        match = re.match(r"(\d{4})", raw_date.strip())
        if not match:
            return None
        return int(match.group(1))

    def _extract_recid(self, payload: dict[str, object]) -> str | None:
        """Extract INSPIRE record id from payload."""
        recid = payload.get("id")
        if isinstance(recid, str) and recid.strip():
            return recid.strip()
        if isinstance(recid, int):
            return str(recid)
        return None

    def _extract_reference_recids(self, metadata: dict[str, object]) -> list[str]:
        """Extract referenced literature ids from INSPIRE metadata."""
        raw_references = metadata.get("references")
        if not isinstance(raw_references, list):
            return []
        recids: list[str] = []
        for item in raw_references:
            if not isinstance(item, dict):
                continue
            record = item.get("record")
            if not isinstance(record, dict):
                continue
            raw_ref = record.get("$ref")
            if not isinstance(raw_ref, str):
                continue
            match = re.search(r"/literature/([^/?#]+)", raw_ref)
            if not match:
                continue
            recids.append(match.group(1))
        return recids

    def _record_from_payload(self, payload: dict[str, object]) -> PaperRecord | None:
        """Convert one INSPIRE literature payload into a PaperRecord candidate."""
        metadata = self._metadata(payload)

        title = self._extract_first_text(metadata.get("titles"), "title") or ""
        abstract = self._extract_first_text(metadata.get("abstracts"), "value")
        arxiv_id = self._extract_first_text(metadata.get("arxiv_eprints"), "value")
        doi = self._extract_first_text(metadata.get("dois"), "value")

        if arxiv_id:
            source_link = f"https://arxiv.org/abs/{arxiv_id}"
        elif doi:
            source_link = f"https://doi.org/{doi}"
        else:
            recid = self._extract_recid(payload)
            if not recid:
                return None
            source_link = self._literature_by_recid_url(recid)

        return PaperRecord(
            source_link=source_link,
            title=title or source_link,
            abstract=abstract,
            authors=self._extract_authors(metadata),
            year=self._extract_year(metadata),
            doi=doi,
            arxiv_id=arxiv_id,
            status="discovered",
        )

    def _records_from_search_payload(self, payload: dict[str, object]) -> list[PaperRecord]:
        """Convert an INSPIRE literature search response into PaperRecord candidates."""
        hits_container = payload.get("hits")
        if not isinstance(hits_container, dict):
            return []
        hits = hits_container.get("hits")
        if not isinstance(hits, list):
            return []

        records: list[PaperRecord] = []
        for item in hits:
            if not isinstance(item, dict):
                continue
            record = self._record_from_payload(item)
            if record:
                records.append(record)
        return records

    def fetch_abstract(self, record: PaperRecord) -> str | None:
        """Fetch abstract text for a seed record by arXiv/DOI identifier."""
        payload = self._lookup_seed_record(record)
        if not payload:
            return None
        metadata = self._metadata(payload)
        return self._extract_first_text(metadata.get("abstracts"), "value")

    def fetch_related_papers(
        self,
        record: PaperRecord,
        max_citing: int = 20,
        max_references: int = 20,
    ) -> list[PaperRecord]:
        """Fetch papers citing and cited by a seed INSPIRE record."""
        seed_payload = self._lookup_seed_record(record)
        if not seed_payload:
            return []

        seed_recid = self._extract_recid(seed_payload)
        metadata = self._metadata(seed_payload)
        if not seed_recid:
            return []

        related: list[PaperRecord] = []

        citing_query = f"refersto recid:{seed_recid}"
        citing_url = self._literature_search_url(citing_query, max_citing)
        citing_payload = self._fetch_json(citing_url)
        if citing_payload:
            related.extend(self._records_from_search_payload(citing_payload))

        for ref_recid in self._extract_reference_recids(metadata)[:max_references]:
            reference_payload = self._fetch_json(self._literature_by_recid_url(ref_recid))
            if not reference_payload:
                continue
            candidate = self._record_from_payload(reference_payload)
            if candidate:
                related.append(candidate)

        return related

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
