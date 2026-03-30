from pathlib import Path

from arxiv_bot.skills.literature_regenerate import (
    records_from_paper_summaries_tex,
    regenerate_literature_review,
)


def test_records_from_paper_summaries_tex_parses_sections() -> None:
    """Parse subsection headers and cite keys into synthesis-ready records."""
    summaries_tex = r"""
\documentclass{article}
\begin{document}
\section*{Paper Summaries}
\subsection*{Paper A | Alice, Bob | \href{https://arxiv.org/abs/1234.56789}{arXiv:1234.56789}}
Paper A summary sentence. \cite{keyA}.

\subsection*{Paper B | Carol | \href{https://arxiv.org/abs/2345.67890}{arXiv:2345.67890}}
Paper B summary sentence. \cite{keyB}.
\bibliographystyle{unsrtnat}
\end{document}
"""
    records = records_from_paper_summaries_tex(summaries_tex)
    assert len(records) == 2
    assert records[0].title == "Paper A"
    assert records[0].authors == ["Alice", "Bob"]
    assert records[0].arxiv_id == "1234.56789"
    assert records[0].bibtex_key == "keyA"
    assert "Paper A summary sentence." in (records[0].summary_paragraph or "")


def test_regenerate_literature_review_writes_tex(tmp_path: Path) -> None:
    """Regenerate literature review TeX from edited paper summaries file."""
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / "paper_summaries.tex").write_text(
        r"""
\documentclass{article}
\begin{document}
\section*{Paper Summaries}
\subsection*{Paper A | Alice | \href{https://arxiv.org/abs/1234.56789}{arXiv:1234.56789}}
Edited summary content for paper A. \cite{keyA}.
\bibliographystyle{unsrtnat}
\end{document}
""",
        encoding="utf-8",
    )

    output = regenerate_literature_review(
        artifacts_dir=artifacts_dir,
        project_description="Edited summary based synthesis",
        use_llm=False,
    )

    assert output == artifacts_dir / "literature_review.tex"
    content = output.read_text(encoding="utf-8")
    assert "\\section*{Literature Synthesis}" in content
    assert "\\cite{keyA}" in content
