from __future__ import annotations

import re

from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.inspire_client import InspireClient


def _tokenize(text: str) -> set[str]:
    """Convert free text into a lowercase token set for keyword matching."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _score_candidate(
    source_type: str,
    candidate_text: str,
    include_keywords: list[str],
    exclude_keywords: list[str],
) -> float:
    """Compute a heuristic relevance score for one candidate paper."""
    include_tokens = _tokenize(" ".join(include_keywords))
    exclude_tokens = _tokenize(" ".join(exclude_keywords))
    candidate_tokens = _tokenize(candidate_text)

    base = 1.0 if source_type in {"arxiv", "doi"} else 0.6
    include_hits = len(include_tokens.intersection(candidate_tokens))
    exclude_hits = len(exclude_tokens.intersection(candidate_tokens))

    score = base + 0.1 * include_hits - 0.3 * exclude_hits
    return round(score, 4)


def _extract_keywords(text: str, min_len: int = 4) -> set[str]:
    """Extract simple lowercase keywords from free-form text."""
    stopwords = {
        "this",
        "that",
        "with",
        "from",
        "have",
        "their",
        "using",
        "used",
        "also",
        "into",
        "between",
        "through",
        "which",
        "where",
        "while",
        "these",
        "those",
        "show",
        "shows",
        "paper",
        "study",
        "results",
        "analysis",
    }
    keywords: set[str] = set()
    for token in _tokenize(text):
        if len(token) < min_len:
            continue
        if token in stopwords:
            continue
        keywords.add(token)
    return keywords


def _keyword_overlap(seed_keywords: set[str], candidate_keywords: set[str]) -> float:
    """Compute Jaccard overlap between seed and candidate keyword sets."""
    if not seed_keywords or not candidate_keywords:
        return 0.0
    union = seed_keywords.union(candidate_keywords)
    if not union:
        return 0.0
    return len(seed_keywords.intersection(candidate_keywords)) / len(union)


def _record_identity(record: PaperRecord) -> str:
    """Build a stable deduplication identity for a discovered record."""
    if record.arxiv_id:
        return f"arxiv:{record.arxiv_id.lower()}"
    if record.doi:
        return f"doi:{record.doi.lower()}"
    return f"url:{record.source_link.lower()}"


def _seed_record(seed: dict[str, str], include_keywords: list[str], exclude_keywords: list[str]) -> PaperRecord:
    """Construct one PaperRecord from ingested seed metadata."""
    source_link = seed["source_link"]
    source_type = seed.get("source_type", "url")
    identifier = seed.get("identifier", source_link)
    score = _score_candidate(source_type, f"{source_link} {identifier}", include_keywords, exclude_keywords)

    return PaperRecord(
        source_link=source_link,
        title=identifier,
        doi=identifier if source_type == "doi" else None,
        arxiv_id=identifier if source_type == "arxiv" else None,
        relevance_score=score,
        status="discovered",
    )


def _aggregate_seed_keywords(seed_records: list[PaperRecord], include_keywords: list[str]) -> set[str]:
    """Build the seed keyword set from seed abstracts and include-keyword hints."""
    abstract_keywords: set[str] = set()
    for record in seed_records:
        if record.abstract:
            abstract_keywords.update(_extract_keywords(record.abstract))

    if abstract_keywords:
        return abstract_keywords
    return _extract_keywords(" ".join(include_keywords))


def _related_score(
    record: PaperRecord,
    seed_keywords: set[str],
    include_keywords: list[str],
    exclude_keywords: list[str],
) -> float:
    """Score a related-paper candidate using abstract keyword overlap and hints."""
    include_token_set = _tokenize(" ".join(include_keywords))
    exclude_token_set = _tokenize(" ".join(exclude_keywords))
    candidate_text = f"{record.title} {record.abstract or ''} {record.source_link}"
    candidate_tokens = _tokenize(candidate_text)
    overlap = _keyword_overlap(seed_keywords, _extract_keywords(record.abstract or ""))
    include_hits = len(include_token_set.intersection(candidate_tokens))
    exclude_hits = len(exclude_token_set.intersection(candidate_tokens))

    score = 0.7 + overlap + (0.1 * include_hits) - (0.3 * exclude_hits)
    return round(score, 4)


def _should_keep_related(
    score: float,
    overlap: float,
    min_relevance_score: float,
    min_keyword_overlap: float,
) -> bool:
    """Return True when a related paper passes relevance thresholds."""
    return score >= min_relevance_score and overlap >= min_keyword_overlap


def _expand_via_inspire(
    seed_records: list[PaperRecord],
    include_keywords: list[str],
    exclude_keywords: list[str],
    inspire_client: InspireClient,
    min_relevance_score: float,
    min_keyword_overlap: float,
) -> list[PaperRecord]:
    """Expand discovery with INSPIRE citing/cited papers filtered by relevance."""
    expanded: dict[str, PaperRecord] = {_record_identity(record): record for record in seed_records}

    for seed_record in seed_records:
        seed_abstract = inspire_client.fetch_abstract(seed_record)
        if seed_abstract and seed_abstract.strip():
            seed_record.abstract = seed_abstract.strip()

    seed_keywords = _aggregate_seed_keywords(seed_records, include_keywords)

    for seed_record in seed_records:
        related_records = inspire_client.fetch_related_papers(seed_record)
        for candidate in related_records:
            candidate_identity = _record_identity(candidate)
            if candidate_identity in expanded:
                continue

            candidate_keywords = _extract_keywords(candidate.abstract or "")
            overlap = _keyword_overlap(seed_keywords, candidate_keywords)
            candidate_score = _related_score(
                candidate,
                seed_keywords=seed_keywords,
                include_keywords=include_keywords,
                exclude_keywords=exclude_keywords,
            )
            if not _should_keep_related(
                score=candidate_score,
                overlap=overlap,
                min_relevance_score=min_relevance_score,
                min_keyword_overlap=min_keyword_overlap,
            ):
                continue

            candidate.relevance_score = candidate_score
            candidate.status = "discovered"
            expanded[candidate_identity] = candidate

    return list(expanded.values())


def discovery_skill(
    ingested_seeds: list[dict[str, str]],
    include_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
    expand_via_inspire: bool = False,
    inspire_client: InspireClient | None = None,
    min_relevance_score: float = 0.8,
    min_keyword_overlap: float = 0.05,
) -> list[PaperRecord]:
    """Convert ingested seeds into ranked records with optional INSPIRE expansion."""
    include_keywords = include_keywords or []
    exclude_keywords = exclude_keywords or []

    records = [_seed_record(seed, include_keywords, exclude_keywords) for seed in ingested_seeds]

    if expand_via_inspire and records:
        records = _expand_via_inspire(
            records,
            include_keywords=include_keywords,
            exclude_keywords=exclude_keywords,
            inspire_client=inspire_client or InspireClient(),
            min_relevance_score=min_relevance_score,
            min_keyword_overlap=min_keyword_overlap,
        )

    records.sort(
        key=lambda record: (
            -(record.relevance_score if record.relevance_score is not None else 0.0),
            record.source_link,
        )
    )
    return records
