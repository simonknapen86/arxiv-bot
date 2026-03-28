from __future__ import annotations

import re
from urllib.parse import urlparse


_ARXIV_ABS_RE = re.compile(r"arxiv\.org/abs/([A-Za-z0-9.\-v]+)")
_ARXIV_PDF_RE = re.compile(r"arxiv\.org/pdf/([^/?#]+?)(?:\.pdf)?(?:[?#]|$)")
_DOI_URL_RE = re.compile(r"doi\.org/(10\.[^\s]+)")
_DOI_RAW_RE = re.compile(r"^(10\.[^\s]+)$")


def normalize_seed_link(seed_link: str) -> str:
    """Normalize a seed link by trimming whitespace and removing URL fragments."""
    stripped = seed_link.strip()
    if not stripped:
        return ""

    parsed = urlparse(stripped)
    if parsed.scheme and parsed.netloc:
        cleaned = parsed._replace(fragment="")
        return cleaned.geturl()
    return stripped


def extract_identifier(seed_link: str) -> dict[str, str]:
    """Extract canonical identifier metadata from a normalized seed link."""
    arxiv_abs = _ARXIV_ABS_RE.search(seed_link)
    if arxiv_abs:
        return {
            "source_link": seed_link,
            "source_type": "arxiv",
            "identifier": arxiv_abs.group(1),
        }

    arxiv_pdf = _ARXIV_PDF_RE.search(seed_link)
    if arxiv_pdf:
        return {
            "source_link": seed_link,
            "source_type": "arxiv",
            "identifier": arxiv_pdf.group(1),
        }

    doi_url = _DOI_URL_RE.search(seed_link)
    if doi_url:
        return {
            "source_link": seed_link,
            "source_type": "doi",
            "identifier": doi_url.group(1),
        }

    doi_raw = _DOI_RAW_RE.search(seed_link)
    if doi_raw:
        return {
            "source_link": f"https://doi.org/{doi_raw.group(1)}",
            "source_type": "doi",
            "identifier": doi_raw.group(1),
        }

    return {
        "source_link": seed_link,
        "source_type": "url",
        "identifier": seed_link,
    }


def seed_ingest_skill(seed_links: list[str]) -> list[dict[str, str]]:
    """Normalize, classify, and deduplicate seed links for downstream discovery."""
    normalized = [normalize_seed_link(link) for link in seed_links]
    non_empty = [link for link in normalized if link]

    unique_links: list[str] = []
    seen: set[str] = set()
    for link in non_empty:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    return [extract_identifier(link) for link in unique_links]
