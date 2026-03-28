from __future__ import annotations

from pathlib import Path

from arxiv_bot.models import PaperRecord


def _write_text(path: Path, content: str) -> None:
    """Write UTF-8 text content to disk, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _references_bib(records: list[PaperRecord]) -> str:
    """Build a combined BibTeX document from record entries."""
    entries: list[str] = []
    for record in records:
        if record.bibtex_entry and record.bibtex_entry.strip():
            entries.append(record.bibtex_entry.strip())
    return "\n\n".join(entries) + ("\n" if entries else "")


def _paper_summaries_tex(records: list[PaperRecord]) -> str:
    """Build a TeX document containing one summary paragraph per paper."""
    sections: list[str] = ["\\section*{Paper Summaries}"]
    for index, record in enumerate(records, start=1):
        cite = record.bibtex_key or f"paper{index}"
        title = record.title.strip() or record.source_link
        summary = record.summary_paragraph or "Summary unavailable."
        sections.append(f"\\subsection*{{{title}}}")
        sections.append(f"{summary} \\cite{{{cite}}}.")
    return "\n\n".join(sections) + "\n"


def export_skill(
    records: list[PaperRecord],
    literature_synthesis_tex: str,
    artifacts_dir: str | Path = "artifacts",
) -> list[PaperRecord]:
    """Write BibTeX and TeX artifacts to disk and mark records as exported."""
    artifacts_path = Path(artifacts_dir)
    references_path = artifacts_path / "references.bib"
    summaries_path = artifacts_path / "paper_summaries.tex"
    review_path = artifacts_path / "literature_review.tex"

    _write_text(references_path, _references_bib(records))
    _write_text(summaries_path, _paper_summaries_tex(records))
    _write_text(review_path, literature_synthesis_tex)

    for record in records:
        record.status = "exported"

    return records
