from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from arxiv_bot.models import PaperRecord


def _paper_manifest(record: PaperRecord) -> dict[str, object]:
    """Convert one paper record into manifest-friendly provenance fields."""
    return {
        "source_link": record.source_link,
        "title": record.title,
        "abstract": record.abstract,
        "authors": record.authors,
        "year": record.year,
        "doi": record.doi,
        "arxiv_id": record.arxiv_id,
        "pdf_url": record.pdf_url,
        "local_pdf_path": record.local_pdf_path,
        "bibtex_key": record.bibtex_key,
        "status": record.status,
        "verified": record.verified,
        "relevance_score": record.relevance_score,
    }


def write_run_manifest(
    records: list[PaperRecord],
    stage_history: list[str],
    artifacts_dir: str | Path = "artifacts",
) -> Path:
    """Write a JSON run manifest with stage history and per-paper provenance."""
    artifacts_path = Path(artifacts_dir)
    artifacts_path.mkdir(parents=True, exist_ok=True)
    manifest_path = artifacts_path / "run_manifest.json"

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "paper_count": len(records),
        "stage_history": stage_history,
        "papers": [_paper_manifest(record) for record in records],
    }

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path
