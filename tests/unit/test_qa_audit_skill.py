from pathlib import Path

import pytest

from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.qa_audit import qa_audit_skill


def _write(path: Path, text: str) -> None:
    """Write UTF-8 text to disk and create parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_record(tmp_path: Path, key: str = "key1") -> PaperRecord:
    """Create an exported record with a local PDF path for audit tests."""
    pdf_path = tmp_path / "papers" / "paper.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"%PDF-1.4\n%fake\n")
    return PaperRecord(
        source_link="https://arxiv.org/abs/1706.03762",
        local_pdf_path=str(pdf_path),
        bibtex_key=key,
        status="exported",
    )


def test_qa_audit_skill_passes_with_consistent_artifacts(tmp_path: Path) -> None:
    """Pass audit when artifact files and citations are mutually consistent."""
    record = _make_record(tmp_path, key="goodkey")
    _write(tmp_path / "references.bib", "@article{goodkey,\\n  title={X}\\n}\\n")
    _write(tmp_path / "paper_summaries.tex", "Summary \\cite{goodkey}.")
    _write(tmp_path / "literature_review.tex", "Review \\cite{goodkey}.")

    qa_audit_skill([record], artifacts_dir=tmp_path)


def test_qa_audit_skill_fails_when_citation_missing_from_bib(tmp_path: Path) -> None:
    """Fail audit when TeX cites keys absent from references.bib."""
    record = _make_record(tmp_path, key="goodkey")
    _write(tmp_path / "references.bib", "@article{goodkey,\\n  title={X}\\n}\\n")
    _write(tmp_path / "paper_summaries.tex", "Summary \\cite{missingkey}.")
    _write(tmp_path / "literature_review.tex", "Review \\cite{goodkey}.")

    with pytest.raises(ValueError, match=r"missing from references\.bib"):
        qa_audit_skill([record], artifacts_dir=tmp_path)


def test_qa_audit_skill_fails_when_record_not_cited(tmp_path: Path) -> None:
    """Fail audit when an exported record key is never cited in TeX outputs."""
    record = _make_record(tmp_path, key="uncitedkey")
    _write(tmp_path / "references.bib", "@article{uncitedkey,\\n  title={X}\\n}\\n")
    _write(tmp_path / "paper_summaries.tex", "Summary text.")
    _write(tmp_path / "literature_review.tex", "Review text.")

    with pytest.raises(ValueError, match="records not cited"):
        qa_audit_skill([record], artifacts_dir=tmp_path)
