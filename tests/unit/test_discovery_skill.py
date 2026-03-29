from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.discovery import discovery_skill


def test_discovery_skill_builds_records_with_ids() -> None:
    """Build discovered records and map identifiers into doi/arxiv fields."""
    records = discovery_skill(
        [
            {
                "source_link": "https://arxiv.org/abs/1706.03762",
                "source_type": "arxiv",
                "identifier": "1706.03762",
            },
            {
                "source_link": "https://doi.org/10.1038/nature14539",
                "source_type": "doi",
                "identifier": "10.1038/nature14539",
            },
        ]
    )

    assert len(records) == 2
    assert records[0].status == "discovered"
    assert any(record.arxiv_id == "1706.03762" for record in records)
    assert any(record.doi == "10.1038/nature14539" for record in records)


def test_discovery_skill_ranks_by_keyword_match() -> None:
    """Rank papers higher when include keywords appear in candidate text."""
    records = discovery_skill(
        [
            {
                "source_link": "https://example.org/graph-paper",
                "source_type": "url",
                "identifier": "graph neural",
            },
            {
                "source_link": "https://example.org/misc-paper",
                "source_type": "url",
                "identifier": "misc",
            },
        ],
        include_keywords=["graph", "neural"],
    )

    assert len(records) == 2
    assert records[0].source_link == "https://example.org/graph-paper"
    assert records[0].relevance_score is not None
    assert records[1].relevance_score is not None
    assert records[0].relevance_score > records[1].relevance_score


def test_discovery_skill_penalizes_excluded_terms() -> None:
    """Lower candidate scores when excluded terms appear in candidate text."""
    records = discovery_skill(
        [
            {
                "source_link": "https://example.org/keep-paper",
                "source_type": "url",
                "identifier": "language model",
            },
            {
                "source_link": "https://example.org/drop-paper",
                "source_type": "url",
                "identifier": "vision benchmark",
            },
        ],
        include_keywords=["model"],
        exclude_keywords=["vision"],
    )

    assert len(records) == 2
    assert records[0].source_link == "https://example.org/keep-paper"


def test_discovery_skill_expands_with_related_inspire_papers() -> None:
    """Add citing/cited records when INSPIRE expansion and relevance checks pass."""

    class FakeInspireClient:
        """Provide deterministic seed abstract and related candidate records."""

        def fetch_abstract(self, record: PaperRecord) -> str | None:
            """Return an abstract for the seed record."""
            _ = record
            return "Transformer attention model for sequence representation learning."

        def fetch_related_papers(self, record: PaperRecord) -> list[PaperRecord]:
            """Return one relevant and one irrelevant related paper."""
            _ = record
            return [
                PaperRecord(
                    source_link="https://arxiv.org/abs/2001.00001",
                    arxiv_id="2001.00001",
                    title="Sparse attention transformer variants",
                    abstract="We introduce transformer attention sparsity for long-context language modeling.",
                    status="discovered",
                ),
                PaperRecord(
                    source_link="https://arxiv.org/abs/2001.00002",
                    arxiv_id="2001.00002",
                    title="Protein folding benchmark",
                    abstract="Protein structure prediction in structural biology.",
                    status="discovered",
                ),
            ]

    records = discovery_skill(
        [
            {
                "source_link": "https://arxiv.org/abs/1706.03762",
                "source_type": "arxiv",
                "identifier": "1706.03762",
            }
        ],
        include_keywords=["transformer", "attention"],
        expand_via_inspire=True,
        inspire_client=FakeInspireClient(),
        min_relevance_score=0.8,
        min_keyword_overlap=0.05,
    )

    source_links = {record.source_link for record in records}
    assert "https://arxiv.org/abs/1706.03762" in source_links
    assert "https://arxiv.org/abs/2001.00001" in source_links
    assert "https://arxiv.org/abs/2001.00002" not in source_links


def test_discovery_skill_deduplicates_seed_from_related_expansion() -> None:
    """Avoid duplicating records when related results include the seed paper."""

    class FakeInspireClient:
        """Return a duplicate of the seed plus one genuinely new related paper."""

        def fetch_abstract(self, record: PaperRecord) -> str | None:
            """Return deterministic seed abstract text."""
            _ = record
            return "Attention-based sequence models."

        def fetch_related_papers(self, record: PaperRecord) -> list[PaperRecord]:
            """Return records including a duplicate seed arXiv id."""
            _ = record
            return [
                PaperRecord(
                    source_link="https://arxiv.org/abs/1706.03762",
                    arxiv_id="1706.03762",
                    title="Attention Is All You Need",
                    abstract="Attention mechanisms in sequence transduction.",
                    status="discovered",
                ),
                PaperRecord(
                    source_link="https://arxiv.org/abs/1910.00001",
                    arxiv_id="1910.00001",
                    title="Extended attention architecture",
                    abstract="Attention architecture for sequence learning tasks.",
                    status="discovered",
                ),
            ]

    records = discovery_skill(
        [
            {
                "source_link": "https://arxiv.org/abs/1706.03762",
                "source_type": "arxiv",
                "identifier": "1706.03762",
            }
        ],
        expand_via_inspire=True,
        inspire_client=FakeInspireClient(),
        min_relevance_score=0.6,
        min_keyword_overlap=0.0,
    )

    assert sum(1 for record in records if record.arxiv_id == "1706.03762") == 1
