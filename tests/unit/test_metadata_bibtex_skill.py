from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.metadata_bibtex import metadata_bibtex_skill


def test_metadata_bibtex_populates_key_and_entry() -> None:
    """Populate BibTeX key/entry fields for a downloaded record."""
    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            title="Attention Is All You Need",
            authors=["Ashish Vaswani", "Noam Shazeer"],
            year=2017,
            arxiv_id="1706.03762",
            status="downloaded",
        )
    ]

    enriched = metadata_bibtex_skill(records, use_inspire=False)
    assert len(enriched) == 1
    assert enriched[0].bibtex_key is not None
    assert enriched[0].bibtex_entry is not None
    assert "@article{" in enriched[0].bibtex_entry
    assert "archivePrefix = {arXiv}" in enriched[0].bibtex_entry


def test_metadata_bibtex_deduplicates_colliding_keys() -> None:
    """Assign unique keys when multiple papers generate the same base key."""
    records = [
        PaperRecord(
            source_link="https://example.org/paper-1",
            title="Same Title",
            authors=["A Smith"],
            year=2020,
            status="downloaded",
        ),
        PaperRecord(
            source_link="https://example.org/paper-2",
            title="Same Title",
            authors=["A Smith"],
            year=2020,
            status="downloaded",
        ),
    ]

    enriched = metadata_bibtex_skill(records, use_inspire=False)
    assert enriched[0].bibtex_key is not None
    assert enriched[1].bibtex_key is not None
    assert enriched[0].bibtex_key != enriched[1].bibtex_key


def test_metadata_bibtex_uses_fallback_fields_when_missing() -> None:
    """Render valid BibTeX when optional metadata like author/year are missing."""
    records = [
        PaperRecord(
            source_link="https://doi.org/10.1038/nature14539",
            doi="10.1038/nature14539",
            status="downloaded",
        )
    ]

    enriched = metadata_bibtex_skill(records, use_inspire=False)
    entry = enriched[0].bibtex_entry or ""
    assert "author = {Unknown}" in entry
    assert "year = {1900}" in entry
    assert "doi = {10.1038/nature14539}" in entry


def test_metadata_bibtex_uses_inspire_entry_when_available() -> None:
    """Use INSPIRE-provided BibTeX entry as the primary citation source."""
    class FakeInspireClient:
        """Return a fixed INSPIRE-style BibTeX entry for testing."""

        def fetch_bibtex(self, _: PaperRecord) -> str | None:
            """Return a deterministic INSPIRE BibTeX record."""
            return "@article{Vaswani:2017,\\n  title = {Attention Is All You Need}\\n}"

    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            arxiv_id="1706.03762",
            status="downloaded",
        )
    ]
    enriched = metadata_bibtex_skill(records, use_inspire=True, inspire_client=FakeInspireClient())
    assert enriched[0].bibtex_key == "Vaswani:2017"
    assert enriched[0].bibtex_entry is not None
    assert "Attention Is All You Need" in enriched[0].bibtex_entry


def test_metadata_bibtex_falls_back_when_inspire_invalid() -> None:
    """Fallback to local BibTeX generation when INSPIRE returns invalid payload."""
    class FakeInspireClient:
        """Return malformed data to force fallback behavior."""

        def fetch_bibtex(self, _: PaperRecord) -> str | None:
            """Return malformed non-BibTeX content."""
            return "not bibtex"

    records = [
        PaperRecord(
            source_link="https://doi.org/10.1038/nature14539",
            doi="10.1038/nature14539",
            status="downloaded",
        )
    ]
    enriched = metadata_bibtex_skill(records, use_inspire=True, inspire_client=FakeInspireClient())
    assert enriched[0].bibtex_entry is not None
    assert enriched[0].bibtex_entry.startswith("@article{")
