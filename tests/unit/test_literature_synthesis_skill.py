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

    synthesis = literature_synthesis_skill(
        records,
        project_description="Transformer model search",
        use_llm=False,
    )
    assert "Transformer model search" in synthesis
    assert "\\cite{vaswani2017attention}" in synthesis
    assert "\\cite{doi2015paper}" in synthesis


def test_literature_synthesis_uses_fallback_citation_keys() -> None:
    """Fallback to deterministic citation keys when bibtex keys are missing."""
    records = [
        PaperRecord(source_link="https://example.org/one", title="Paper One"),
        PaperRecord(source_link="https://example.org/two", title="Paper Two"),
    ]

    synthesis = literature_synthesis_skill(records, use_llm=False)
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

    synthesis = literature_synthesis_skill(records, use_llm=False)
    assert len([token for token in synthesis.split() if token.strip()]) >= 320


def test_literature_synthesis_uses_llm_output_when_valid() -> None:
    """Use LLM output when required citations and section header are present."""
    class FakeLLMClient:
        """Return deterministic synthesis text for testing."""

        def generate(self, prompt: str, max_tokens: int = 400) -> str:
            """Return a valid TeX synthesis that includes required citations."""
            _ = prompt
            _ = max_tokens
            return (
                "\\section*{Literature Synthesis}\n\n"
                "A synthesized review text \\cite{vaswani2017attention}."
            )

    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            title="Attention Is All You Need",
            bibtex_key="vaswani2017attention",
        )
    ]
    synthesis = literature_synthesis_skill(records, use_llm=True, llm_client=FakeLLMClient())
    assert "A synthesized review text" in synthesis
    assert "\\cite{vaswani2017attention}" in synthesis


def test_literature_synthesis_appends_missing_citations_for_llm_output() -> None:
    """Append missing required citations instead of dropping to deterministic fallback."""

    class FakeLLMClient:
        """Return LLM text with section header but missing one required cite."""

        def generate(self, prompt: str, max_tokens: int = 400) -> str:
            """Return synthesis body containing only one citation."""
            _ = prompt
            _ = max_tokens
            return (
                "\\section*{Literature Synthesis}\n\n"
                "A synthesized review text \\cite{vaswani2017attention}."
            )

    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            title="Attention Is All You Need",
            bibtex_key="vaswani2017attention",
        ),
        PaperRecord(
            source_link="https://doi.org/10.1038/nature14539",
            title="A DOI paper",
            bibtex_key="doi2015paper",
        ),
    ]
    synthesis = literature_synthesis_skill(records, use_llm=True, llm_client=FakeLLMClient())
    assert "A synthesized review text" in synthesis
    assert "\\cite{vaswani2017attention}" in synthesis
    assert "\\cite{doi2015paper}" in synthesis
