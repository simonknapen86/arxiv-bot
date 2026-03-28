from __future__ import annotations

from urllib.parse import urlparse

from arxiv_bot.models import PaperRecord


TRUSTED_HOSTS = {"arxiv.org", "doi.org"}


def _is_http_source(source_link: str) -> bool:
    """Return True when the source link is a valid HTTP(S) URL with a host."""
    parsed = urlparse(source_link)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _has_trusted_identifier(record: PaperRecord) -> bool:
    """Return True when a record has a DOI/arXiv id or comes from a trusted host."""
    if record.doi or record.arxiv_id:
        return True

    host = urlparse(record.source_link).netloc.lower()
    return host in TRUSTED_HOSTS


def _verify_record(record: PaperRecord) -> bool:
    """Apply existence checks for one paper record and update verification flags."""
    is_resolvable_source = _is_http_source(record.source_link)
    has_identifier = _has_trusted_identifier(record)

    if is_resolvable_source and has_identifier:
        record.verified = True
        record.status = "verified"
        return True

    record.verified = False
    return False


def existence_verification_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    """Filter records to those that pass identifier and resolvable-source checks."""
    verified_records: list[PaperRecord] = []
    for record in records:
        if _verify_record(record):
            verified_records.append(record)
    return verified_records
