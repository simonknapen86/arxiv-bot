from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.literature_synthesis import literature_synthesis_skill


def test_literature_synthesis_includes_project_description_and_citations() -> None:
    """Include project scope text and cite each referenced paper key."""
    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            title="Attention Is All You Need",
            bibtex_key="vaswani2017attention",
            relevance_score=1.2,
        ),
        PaperRecord(
            source_link="https://doi.org/10.1038/nature14539",
            title="A DOI paper",
            bibtex_key="doi2015paper",
            relevance_score=0.9,
        ),
    ]

    synthesis = literature_synthesis_skill(records, project_description="Transformer model search")
    assert "Transformer model search" in synthesis
    assert "\\cite{vaswani2017attention}" in synthesis
    assert "\\cite{doi2015paper}" in synthesis


def test_literature_synthesis_uses_fallback_citation_keys() -> None:
    """Fallback to deterministic citation keys when bibtex keys are missing."""
    records = [
        PaperRecord(source_link="https://example.org/one", title="Paper One"),
        PaperRecord(source_link="https://example.org/two", title="Paper Two"),
    ]

    synthesis = literature_synthesis_skill(records)
    assert "\\cite{paper1}" in synthesis
    assert "\\cite{paper2}" in synthesis


def test_literature_synthesis_targets_minimum_length() -> None:
    """Generate synthesis text long enough to approximate a short literature section."""
    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            title="Attention Is All You Need",
            bibtex_key="vaswani2017attention",
        )
    ]

    synthesis = literature_synthesis_skill(records)
    assert len([token for token in synthesis.split() if token.strip()]) >= 320
