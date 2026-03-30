from __future__ import annotations

import re
from pathlib import Path

from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.export import _wrap_latex_document
from arxiv_bot.skills.literature_synthesis import literature_synthesis_skill
from arxiv_bot.skills.llm_client import LLMClient


def _matching_brace_index(text: str, open_brace_index: int) -> int:
    """Return closing-brace index for a TeX command argument with nested braces."""
    depth = 0
    for index in range(open_brace_index, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
    return -1


def _parse_subsections(summaries_tex: str) -> list[tuple[str, str]]:
    """Extract subsection header/body pairs from paper summaries TeX content."""
    marker = r"\subsection*{"
    positions: list[tuple[int, int, str]] = []
    cursor = 0
    while True:
        start = summaries_tex.find(marker, cursor)
        if start == -1:
            break
        open_brace = start + len(marker) - 1
        close_brace = _matching_brace_index(summaries_tex, open_brace)
        if close_brace == -1:
            break
        header = summaries_tex[open_brace + 1 : close_brace].strip()
        body_start = close_brace + 1
        positions.append((start, body_start, header))
        cursor = close_brace + 1

    pairs: list[tuple[str, str]] = []
    for index, (_, body_start, header) in enumerate(positions):
        if index + 1 < len(positions):
            body_end = positions[index + 1][0]
        else:
            bibliography_index = summaries_tex.find(r"\bibliographystyle", body_start)
            end_document_index = summaries_tex.find(r"\end{document}", body_start)
            candidates = [position for position in [bibliography_index, end_document_index] if position != -1]
            body_end = min(candidates) if candidates else len(summaries_tex)

        body = summaries_tex[body_start:body_end].strip()
        if header and body:
            pairs.append((header, body))
    return pairs


def _extract_cite_key(text: str, index: int) -> str:
    """Extract first citation key from TeX text with deterministic fallback."""
    match = re.search(r"\\cite\{([^}]+)\}", text)
    if not match:
        return f"paper{index + 1}"
    keys = [token.strip() for token in match.group(1).split(",") if token.strip()]
    if not keys:
        return f"paper{index + 1}"
    return keys[0]


def _strip_citations(text: str) -> str:
    """Remove citation commands from TeX text while preserving sentence prose."""
    without_cites = re.sub(r"\\cite\{[^}]+\}", "", text)
    return re.sub(r"\s+", " ", without_cites).strip()


def _header_parts(header: str) -> tuple[str, list[str], str | None]:
    """Parse summary subsection header into title, authors, and arXiv id."""
    parts = [part.strip() for part in header.split("|")]
    title = parts[0] if parts else "Unknown"
    authors_raw = parts[1] if len(parts) > 1 else "Unknown"
    authors = [token.strip() for token in authors_raw.split(",") if token.strip()] if authors_raw else []
    arxiv_match = re.search(r"arXiv:([A-Za-z0-9.\-v]+)", header)
    arxiv_id = arxiv_match.group(1) if arxiv_match else None
    return title, authors, arxiv_id


def records_from_paper_summaries_tex(summaries_tex: str) -> list[PaperRecord]:
    """Build PaperRecord inputs for synthesis from a paper summaries TeX document."""
    records: list[PaperRecord] = []
    for index, (header, body) in enumerate(_parse_subsections(summaries_tex)):
        title, authors, arxiv_id = _header_parts(header)
        cite_key = _extract_cite_key(body, index=index)
        summary_paragraph = _strip_citations(body)
        source_link = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else title
        records.append(
            PaperRecord(
                source_link=source_link,
                title=title,
                authors=authors,
                arxiv_id=arxiv_id,
                bibtex_key=cite_key,
                summary_paragraph=summary_paragraph,
                status="summarized",
            )
        )
    return records


def regenerate_literature_review(
    artifacts_dir: str | Path = "artifacts",
    project_description: str = "",
    use_llm: bool = True,
    llm_client: LLMClient | None = None,
) -> Path:
    """Regenerate only literature_review.tex using existing paper_summaries.tex input."""
    artifacts_path = Path(artifacts_dir)
    summaries_path = artifacts_path / "paper_summaries.tex"
    if not summaries_path.exists():
        raise FileNotFoundError(f"paper summaries file not found: {summaries_path}")

    summaries_tex = summaries_path.read_text(encoding="utf-8")
    records = records_from_paper_summaries_tex(summaries_tex)
    if not records:
        raise ValueError("no paper summaries found in paper_summaries.tex")

    synthesis_body = literature_synthesis_skill(
        records,
        project_description=project_description,
        use_llm=use_llm,
        llm_client=llm_client,
    )
    literature_review_path = artifacts_path / "literature_review.tex"
    literature_review_path.write_text(_wrap_latex_document(synthesis_body), encoding="utf-8")
    return literature_review_path
