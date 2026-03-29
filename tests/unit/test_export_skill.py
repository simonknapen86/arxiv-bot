from pathlib import Path

from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.export import export_skill


def test_export_skill_writes_required_artifacts(tmp_path: Path) -> None:
    """Write bibtex and TeX outputs to the artifacts directory."""
    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            title="Attention Is All You Need",
            authors=["Ashish Vaswani", "Noam Shazeer"],
            arxiv_id="1706.03762",
            bibtex_key="vaswani2017attention",
            bibtex_entry="@article{vaswani2017attention,\\n  title={Attention Is All You Need}\\n}",
            summary_paragraph="A summary paragraph.",
            status="summarized",
        )
    ]

    synthesis = "\\section*{Literature Synthesis}\\nSome synthesis text with \\cite{vaswani2017attention}."
    exported = export_skill(records, synthesis, artifacts_dir=tmp_path)

    references = tmp_path / "references.bib"
    summaries = tmp_path / "paper_summaries.tex"
    review = tmp_path / "literature_review.tex"

    assert references.exists()
    assert summaries.exists()
    assert review.exists()

    assert "@article{vaswani2017attention" in references.read_text(encoding="utf-8")
    summary_text = summaries.read_text(encoding="utf-8")
    review_text = review.read_text(encoding="utf-8")
    assert "\\documentclass[11pt]{article}" in summary_text
    assert "\\begin{document}" in summary_text
    assert "\\cite{vaswani2017attention}" in summary_text
    assert "Ashish Vaswani, Noam Shazeer" in summary_text
    assert "\\href{https://arxiv.org/abs/1706.03762}{arXiv:1706.03762}" in summary_text
    assert "\\bibliography{references}" in summary_text
    assert "\\section*{Literature Synthesis}" in review_text
    assert "\\documentclass[11pt]{article}" in review_text
    assert "\\bibliography{references}" in review_text
    assert all(record.status == "exported" for record in exported)


def test_export_skill_handles_missing_optional_fields(tmp_path: Path) -> None:
    """Export minimal placeholder output when bibtex and summary fields are missing."""
    records = [
        PaperRecord(
            source_link="https://example.org/paper",
            title="",
            status="summarized",
        )
    ]

    export_skill(records, "", artifacts_dir=tmp_path)
    summaries = (tmp_path / "paper_summaries.tex").read_text(encoding="utf-8")
    assert "Summary unavailable." in summaries
    assert "arXiv:N/A" in summaries


def test_export_skill_escapes_summary_special_characters(tmp_path: Path) -> None:
    """Escape summary characters that would otherwise break LaTeX compilation."""
    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1910.10716",
            title="Target comparison",
            arxiv_id="1910.10716",
            bibtex_key="griffin2019target",
            summary_paragraph="Compares CaWO_4 and Al_2O_3 channels with 5% error and L ⊗ S terms.",
            status="summarized",
        )
    ]

    export_skill(records, "", artifacts_dir=tmp_path)
    summaries = (tmp_path / "paper_summaries.tex").read_text(encoding="utf-8")
    assert "CaWO\\_4" in summaries
    assert "Al\\_2O\\_3" in summaries
    assert "5\\% error" in summaries
    assert "L x S terms" in summaries
