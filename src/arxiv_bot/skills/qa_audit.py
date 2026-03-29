from __future__ import annotations

import re
from pathlib import Path

from arxiv_bot.models import PaperRecord


def _read_text(path: Path) -> str:
    """Read UTF-8 text from a file path."""
    return path.read_text(encoding="utf-8")


def _extract_cite_keys(tex_text: str) -> set[str]:
    """Extract citation keys from TeX \\cite{...} commands."""
    keys: set[str] = set()
    for raw in re.findall(r"\\cite\{([^}]+)\}", tex_text):
        for key in raw.split(","):
            cleaned = key.strip()
            if cleaned:
                keys.add(cleaned)
    return keys


def _extract_bib_keys(bib_text: str) -> set[str]:
    """Extract BibTeX entry keys from a combined .bib string."""
    keys = re.findall(r"@\w+\{([^,]+),", bib_text)
    return {key.strip() for key in keys if key.strip()}


def qa_audit_skill(records: list[PaperRecord], artifacts_dir: str | Path = "artifacts") -> None:
    """Validate cross-artifact consistency and raise clear errors on failures."""
    if not records:
        raise ValueError("qa_audit failed: no records to audit")

    non_exported = [record.source_link for record in records if record.status != "exported"]
    if non_exported:
        raise ValueError(f"qa_audit failed: non-exported records found: {non_exported}")

    missing_pdf = [record.source_link for record in records if not record.local_pdf_path or not Path(record.local_pdf_path).exists()]
    if missing_pdf:
        raise ValueError(f"qa_audit failed: missing downloaded PDFs for records: {missing_pdf}")

    artifacts_path = Path(artifacts_dir)
    references_path = artifacts_path / "references.bib"
    summaries_path = artifacts_path / "paper_summaries.tex"
    review_path = artifacts_path / "literature_review.tex"

    for path in [references_path, summaries_path, review_path]:
        if not path.exists() or path.stat().st_size == 0:
            raise ValueError(f"qa_audit failed: missing or empty artifact file: {path}")

    bib_text = _read_text(references_path)
    summary_text = _read_text(summaries_path)
    review_text = _read_text(review_path)

    bib_keys = _extract_bib_keys(bib_text)
    if not bib_keys:
        raise ValueError("qa_audit failed: references.bib has no BibTeX keys")

    summary_cites = _extract_cite_keys(summary_text)
    review_cites = _extract_cite_keys(review_text)
    all_cites = summary_cites.union(review_cites)

    unknown_cites = sorted(all_cites - bib_keys)
    if unknown_cites:
        raise ValueError(f"qa_audit failed: citation keys missing from references.bib: {unknown_cites}")

    missing_record_keys = [record.source_link for record in records if not record.bibtex_key or record.bibtex_key not in bib_keys]
    if missing_record_keys:
        raise ValueError(f"qa_audit failed: record bibtex keys missing in references.bib for: {missing_record_keys}")

    uncited_records = [record.source_link for record in records if record.bibtex_key not in all_cites]
    if uncited_records:
        raise ValueError(f"qa_audit failed: records not cited in TeX outputs: {uncited_records}")
