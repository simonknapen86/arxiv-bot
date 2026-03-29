from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.paper_summary import paper_summary_skill


def test_paper_summary_skill_generates_single_paragraph() -> None:
    """Generate one non-empty paragraph per paper and set summarized status."""
    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            title="Attention Is All You Need",
            arxiv_id="1706.03762",
            bibtex_key="vaswani2017attention",
            verified=True,
            local_pdf_path="artifacts/papers/1706_03762.pdf",
            status="metadata_enriched",
        )
    ]

    summarized = paper_summary_skill(records, use_llm=False)
    assert len(summarized) == 1
    assert summarized[0].status == "summarized"
    assert summarized[0].summary_paragraph is not None
    assert summarized[0].summary_paragraph.strip() != ""
    assert "\n" not in summarized[0].summary_paragraph


def test_paper_summary_skill_handles_missing_title_and_bibkey() -> None:
    """Fallback gracefully when title and citation key are missing."""
    records = [
        PaperRecord(
            source_link="https://doi.org/10.1038/nature14539",
            doi="10.1038/nature14539",
            verified=False,
            status="metadata_enriched",
        )
    ]

    summarized = paper_summary_skill(records, use_llm=False)
    paragraph = summarized[0].summary_paragraph or ""
    assert "DOI-indexed work 10.1038/nature14539" in paragraph
    assert "citation key TBD" in paragraph
    assert summarized[0].status == "summarized"


def test_paper_summary_skill_uses_llm_output_when_enabled() -> None:
    """Use injected LLM client output when LLM mode is enabled."""
    captured_prompts: list[str] = []

    class FakeLLMClient:
        """Return deterministic text for summary generation tests."""

        def generate(self, prompt: str, max_tokens: int = 400) -> str:
            """Return a one-line synthetic summary payload."""
            captured_prompts.append(prompt)
            _ = max_tokens
            return "Model summary paragraph."

    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            title="Attention Is All You Need",
            local_pdf_path="artifacts/papers/1706_03762.pdf",
            status="metadata_enriched",
        )
    ]
    summarized = paper_summary_skill(
        records,
        use_llm=True,
        llm_client=FakeLLMClient(),
        pdf_text_extractor=lambda _: "Paper body text.",
    )
    assert summarized[0].summary_paragraph == "Model summary paragraph."
    assert summarized[0].status == "summarized"
    assert captured_prompts
    assert "Paper body text." in captured_prompts[0]
    assert "Local PDF path: artifacts/papers/1706_03762.pdf." in captured_prompts[0]
