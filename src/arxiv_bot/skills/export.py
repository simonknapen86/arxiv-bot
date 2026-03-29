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


def _wrap_latex_document(body_tex: str) -> str:
    """Wrap TeX body content in a compilable LaTeX document preamble."""
    body = _strip_markdown_fences(body_tex).strip() + "\n"
    return (
        "\\documentclass[11pt]{article}\n"
        "\\usepackage[T1]{fontenc}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage[margin=1in]{geometry}\n"
        "\\usepackage[hidelinks]{hyperref}\n"
        "\\usepackage[numbers]{natbib}\n"
        "\\begin{document}\n\n"
        f"{body}\n"
        "\\bibliographystyle{unsrtnat}\n"
        "\\bibliography{references}\n"
        "\\end{document}\n"
    )


def _strip_markdown_fences(text: str) -> str:
    """Remove optional markdown code fences from model-generated TeX text."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines)
    return _strip_embedded_bibliography(stripped)


def _strip_embedded_bibliography(text: str) -> str:
    """Remove bibliography directives from body text to avoid duplicate footers."""
    kept: list[str] = []
    for line in text.splitlines():
        normalized = line.strip().lower()
        if normalized.startswith("\\bibliographystyle"):
            continue
        if normalized.startswith("\\bibliography"):
            continue
        kept.append(line)
    return "\n".join(kept)


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
    _write_text(summaries_path, _wrap_latex_document(_paper_summaries_tex(records)))
    _write_text(review_path, _wrap_latex_document(literature_synthesis_tex))

    for record in records:
        record.status = "exported"

    return records
