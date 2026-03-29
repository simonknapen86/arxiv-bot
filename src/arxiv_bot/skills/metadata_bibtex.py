from __future__ import annotations

import re
from collections import defaultdict

from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.inspire_client import InspireClient


def _slug(text: str) -> str:
    """Convert free text into an alphanumeric lowercase slug."""
    return re.sub(r"[^a-z0-9]+", "", text.lower()) or "paper"


def _infer_year(record: PaperRecord) -> int:
    """Return a valid year for BibTeX output, defaulting to 1900 when missing."""
    return record.year if record.year is not None else 1900


def _infer_title(record: PaperRecord) -> str:
    """Return a usable title for BibTeX output."""
    if record.title.strip():
        return record.title.strip()
    if record.arxiv_id:
        return f"arXiv preprint {record.arxiv_id}"
    if record.doi:
        return f"DOI preprint {record.doi}"
    return record.source_link


def _infer_author(record: PaperRecord) -> str:
    """Return a BibTeX-formatted author string with a safe fallback."""
    if record.authors:
        return " and ".join(record.authors)
    return "Unknown"


def _base_bibtex_key(record: PaperRecord) -> str:
    """Build a deterministic base citation key from record metadata."""
    if record.authors:
        author_token = _slug(record.authors[0].split()[-1])
    elif record.arxiv_id:
        author_token = "arxiv"
    elif record.doi:
        author_token = "doi"
    else:
        author_token = _slug(record.source_link)

    year_token = str(_infer_year(record))
    title_token = _slug(_infer_title(record))[:20]
    return f"{author_token}{year_token}{title_token}"


def _assign_unique_key(base_key: str, seen: dict[str, int]) -> str:
    """Assign a unique citation key by suffixing collisions."""
    seen[base_key] += 1
    if seen[base_key] == 1:
        return base_key
    return f"{base_key}{seen[base_key]}"


def _build_bibtex_entry(record: PaperRecord) -> str:
    """Render a BibTeX entry string from a populated paper record."""
    fields = [
        f"  title = {{{_infer_title(record)}}}",
        f"  author = {{{_infer_author(record)}}}",
        f"  year = {{{_infer_year(record)}}}",
        f"  url = {{{record.source_link}}}",
    ]
    if record.doi:
        fields.append(f"  doi = {{{record.doi}}}")
    if record.arxiv_id:
        fields.append(f"  eprint = {{{record.arxiv_id}}}")
        fields.append("  archivePrefix = {arXiv}")

    joined = ",\n".join(fields)
    return f"@article{{{record.bibtex_key},\n{joined}\n}}"


def _extract_bibtex_key(entry: str) -> str | None:
    """Extract the citation key from a BibTeX entry header."""
    match = re.search(r"@\w+\{([^,]+),", entry)
    if not match:
        return None
    return match.group(1).strip()


def _rewrite_bibtex_key(entry: str, new_key: str) -> str:
    """Rewrite the citation key in a BibTeX entry header."""
    return re.sub(r"(@\w+\{)[^,]+(,)", rf"\1{new_key}\2", entry, count=1)


def _looks_like_bibtex(entry: str) -> bool:
    """Return True when text appears to be a minimally valid BibTeX entry."""
    return entry.lstrip().startswith("@") and "{" in entry and "}" in entry


def _extract_bibtex_field(entry: str, field: str) -> str | None:
    """Extract a BibTeX field value from a single entry string."""
    normalized = entry.replace("\\n", "\n")
    brace_pattern = rf"{field}\s*=\s*\{{(.*?)\}}\s*,?\s*(?:\n|$)"
    quote_pattern = rf'{field}\s*=\s*"(.*?)"\s*,?\s*(?:\n|$)'

    match = re.search(brace_pattern, normalized, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        match = re.search(quote_pattern, normalized, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    value = match.group(1).strip()
    while len(value) >= 2 and value.startswith("{") and value.endswith("}"):
        value = value[1:-1].strip()
    return value or None


def _populate_record_from_bibtex(record: PaperRecord, entry: str) -> None:
    """Populate record metadata fields from a BibTeX entry when available."""
    title = _extract_bibtex_field(entry, "title")
    if title:
        record.title = title

    author_field = _extract_bibtex_field(entry, "author")
    if author_field:
        parsed_authors = [a.strip() for a in author_field.split(" and ") if a.strip()]
        if parsed_authors:
            record.authors = parsed_authors

    year_field = _extract_bibtex_field(entry, "year")
    if year_field:
        try:
            record.year = int(re.sub(r"[^0-9]", "", year_field))
        except ValueError:
            pass


def metadata_bibtex_skill(
    records: list[PaperRecord],
    use_inspire: bool = True,
    inspire_client: InspireClient | None = None,
) -> list[PaperRecord]:
    """Populate BibTeX keys/entries, preferring INSPIRE output when available."""
    seen: dict[str, int] = defaultdict(int)
    client = inspire_client or InspireClient()

    for record in records:
        inspire_entry: str | None = None
        if use_inspire:
            inspire_entry = client.fetch_bibtex(record)
            if inspire_entry and not _looks_like_bibtex(inspire_entry):
                inspire_entry = None

        if inspire_entry:
            parsed_key = _extract_bibtex_key(inspire_entry) or _base_bibtex_key(record)
            final_key = _assign_unique_key(parsed_key, seen)
            record.bibtex_key = final_key
            rewritten_entry = _rewrite_bibtex_key(inspire_entry, final_key)
            record.bibtex_entry = rewritten_entry
            _populate_record_from_bibtex(record, rewritten_entry)
            record.status = "metadata_enriched"
            continue

        base_key = _base_bibtex_key(record)
        final_key = _assign_unique_key(base_key, seen)
        record.bibtex_key = final_key
        fallback_entry = _build_bibtex_entry(record)
        record.bibtex_entry = fallback_entry
        _populate_record_from_bibtex(record, fallback_entry)
        record.status = "metadata_enriched"

    return records
