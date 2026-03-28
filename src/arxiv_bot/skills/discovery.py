from __future__ import annotations

import re

from arxiv_bot.models import PaperRecord


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


def discovery_skill(
    ingested_seeds: list[dict[str, str]],
    include_keywords: list[str] | None = None,
    exclude_keywords: list[str] | None = None,
) -> list[PaperRecord]:
    """Convert ingested seeds into ranked discovered paper records."""
    include_keywords = include_keywords or []
    exclude_keywords = exclude_keywords or []

    records: list[PaperRecord] = []
    for seed in ingested_seeds:
        source_link = seed["source_link"]
        source_type = seed.get("source_type", "url")
        identifier = seed.get("identifier", source_link)
        score = _score_candidate(source_type, f"{source_link} {identifier}", include_keywords, exclude_keywords)

        records.append(
            PaperRecord(
                source_link=source_link,
                title=identifier,
                doi=identifier if source_type == "doi" else None,
                arxiv_id=identifier if source_type == "arxiv" else None,
                relevance_score=score,
                status="discovered",
            )
        )

    records.sort(
        key=lambda record: (
            -(record.relevance_score if record.relevance_score is not None else 0.0),
            record.source_link,
        )
    )
    return records
