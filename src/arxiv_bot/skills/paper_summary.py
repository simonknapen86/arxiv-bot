from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.llm_client import LLMClient


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
    """Generate a fallback one-paragraph summary from available record metadata."""
    if record.abstract and record.abstract.strip():
        cleaned = re.sub(r"\s+", " ", record.abstract.strip())
        trimmed = cleaned[:900].rstrip()
        if not trimmed.endswith("."):
            trimmed += "."
        return (
            f"{trimmed} This fallback summary was derived from metadata-level abstract text "
            f"for citation key {record.bibtex_key or 'TBD'}."
        )

    focus = _infer_focus(record)
    source_note = "arXiv" if record.arxiv_id else "DOI" if record.doi else "source URL"
    confidence_note = (
        "Its metadata and downloadable file were verified in the pipeline."
        if record.verified and record.local_pdf_path
        else "Its metadata was ingested, but file-level verification is pending."
    )

    return (
        f"{focus} was retained by the discovery and verification workflow as a relevant source. "
        f"The record is linked to a {source_note} identifier and assigned citation key "
        f"{record.bibtex_key or 'TBD'} for downstream referencing. {confidence_note}"
    )


def _extract_pdf_text(pdf_path: str | None, max_chars: int = 12000) -> str:
    """Extract text from a local PDF path for grounded summarization prompts."""
    if not pdf_path:
        return ""

    path = Path(pdf_path)
    if not path.exists():
        return ""

    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return ""

    try:
        reader = PdfReader(str(path))
        chunks: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                chunks.append(text.strip())
            if sum(len(chunk) for chunk in chunks) >= max_chars:
                break
        combined = "\n\n".join(chunks)
        return combined[:max_chars]
    except Exception:
        return ""


def _summary_prompt(record: PaperRecord, paper_text: str) -> str:
    """Build a grounded prompt for LLM-based one-paragraph paper summarization."""
    text_block = paper_text if paper_text.strip() else "No PDF text could be extracted."
    return (
        "Write exactly one concise paragraph summarizing the paper for a literature review. "
        "Use only the provided metadata and extracted PDF text, and avoid fabricating results. "
        "Output must be LaTeX-safe plain text (no markdown code fences), and escape literal "
        "special characters such as %, &, _, #, $, {, and } unless used as valid LaTeX syntax. "
        f"Title: {record.title or 'Unknown'}. "
        f"Source: {record.source_link}. "
        f"Local PDF path: {record.local_pdf_path or 'N/A'}. "
        f"arXiv: {record.arxiv_id or 'N/A'}. DOI: {record.doi or 'N/A'}. "
        f"BibTeX key: {record.bibtex_key or 'TBD'}. "
        "Extracted paper text begins below:\n"
        f"{text_block}"
    )


def paper_summary_skill(
    records: list[PaperRecord],
    use_llm: bool = False,
    llm_client: LLMClient | None = None,
    pdf_text_extractor: Callable[[str | None], str] | None = None,
) -> list[PaperRecord]:
    """Populate one-paragraph summaries with optional LLM generation and safe fallback."""
    client = llm_client or LLMClient()
    extractor = pdf_text_extractor or _extract_pdf_text

    for record in records:
        summary = ""
        if use_llm:
            paper_text = extractor(record.local_pdf_path)
            summary = client.generate(_summary_prompt(record, paper_text), max_tokens=300).strip()
        record.summary_paragraph = summary or _summary_paragraph(record)
        record.status = "summarized"
    return records
