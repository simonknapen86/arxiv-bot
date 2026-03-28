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
