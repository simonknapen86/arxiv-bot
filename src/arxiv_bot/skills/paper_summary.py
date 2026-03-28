from __future__ import annotations

from arxiv_bot.models import PaperRecord


def _infer_focus(record: PaperRecord) -> str:
    """Infer a short focus phrase for summary text from record metadata."""
    if record.title.strip():
        return record.title.strip()
    if record.arxiv_id:
        return f"the arXiv work {record.arxiv_id}"
    if record.doi:
        return f"the DOI-indexed work {record.doi}"
    return "this paper"


def _summary_paragraph(record: PaperRecord) -> str:
    """Generate a single-paragraph summary for one paper record."""
    focus = _infer_focus(record)
    source_note = "arXiv" if record.arxiv_id else "DOI" if record.doi else "source URL"
    confidence_note = (
        "Its metadata and downloadable file were verified in the pipeline."
        if record.verified and record.local_pdf_path
        else "Its metadata was ingested, but file-level verification is pending."
    )

    return (
        f"{focus} is treated as a relevant contribution based on the seeded discovery criteria and "
        f"keyword ranking stage. The record is linked to a {source_note} identifier and assigned "
        f"citation key {record.bibtex_key or 'TBD'} for downstream referencing. "
        f"{confidence_note} This summary is a scaffold paragraph that will be replaced by a "
        f"model-generated technical synopsis in a later stage."
    )


def paper_summary_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    """Populate one-paragraph summaries for each record and mark as summarized."""
    for record in records:
        record.summary_paragraph = _summary_paragraph(record)
        record.status = "summarized"
    return records
