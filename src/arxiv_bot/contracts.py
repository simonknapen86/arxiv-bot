from __future__ import annotations

from datetime import datetime
from typing import Any

from arxiv_bot.models import PaperRecord, PipelineInput


ALLOWED_STATUSES = {
    "discovered",
    "verified",
    "downloaded",
    "summarized",
    "exported",
}


def _require_non_empty_string(value: Any, field_name: str) -> str:
    """Validate and normalize a required non-empty string value."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_string_list(value: Any, field_name: str) -> list[str]:
    """Validate a list of strings and return stripped non-empty items."""
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{field_name} must be a list of strings")
    return [item.strip() for item in value if item.strip()]


def _optional_string(value: Any, field_name: str) -> str | None:
    """Validate an optional string and return None for empty input."""
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or null")
    stripped = value.strip()
    return stripped or None


def validate_pipeline_input(data: dict[str, Any]) -> PipelineInput:
    """Validate raw input payload and build a PipelineInput model."""
    if not isinstance(data, dict):
        raise ValueError("pipeline input must be an object")

    seed_links = _require_string_list(data.get("seed_links"), "seed_links")
    if not seed_links:
        raise ValueError("seed_links must include at least one link")

    project_description = _require_non_empty_string(
        data.get("project_description"), "project_description"
    )

    include_keywords = _require_string_list(data.get("include_keywords", []), "include_keywords")
    exclude_keywords = _require_string_list(data.get("exclude_keywords", []), "exclude_keywords")

    return PipelineInput(
        seed_links=seed_links,
        project_description=project_description,
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
    )


def validate_paper_record(data: dict[str, Any]) -> PaperRecord:
    """Validate raw paper payload and build a PaperRecord model."""
    if not isinstance(data, dict):
        raise ValueError("paper record must be an object")

    source_link = _require_non_empty_string(data.get("source_link"), "source_link")
    title = _optional_string(data.get("title"), "title") or ""

    authors_raw = data.get("authors", [])
    authors = _require_string_list(authors_raw, "authors")

    year_value = data.get("year")
    year = None
    if year_value is not None:
        if not isinstance(year_value, int):
            raise ValueError("year must be an integer or null")
        current_year = datetime.now().year
        if year_value < 1800 or year_value > current_year + 1:
            raise ValueError("year is out of supported range")
        year = year_value

    status = data.get("status", "discovered")
    if status not in ALLOWED_STATUSES:
        raise ValueError("status is not valid")

    verified = data.get("verified", False)
    if not isinstance(verified, bool):
        raise ValueError("verified must be a boolean")

    return PaperRecord(
        source_link=source_link,
        title=title,
        authors=authors,
        year=year,
        doi=_optional_string(data.get("doi"), "doi"),
        arxiv_id=_optional_string(data.get("arxiv_id"), "arxiv_id"),
        pdf_url=_optional_string(data.get("pdf_url"), "pdf_url"),
        local_pdf_path=_optional_string(data.get("local_pdf_path"), "local_pdf_path"),
        bibtex_key=_optional_string(data.get("bibtex_key"), "bibtex_key"),
        bibtex_entry=_optional_string(data.get("bibtex_entry"), "bibtex_entry"),
        summary_paragraph=_optional_string(data.get("summary_paragraph"), "summary_paragraph"),
        verified=verified,
        status=status,
    )
