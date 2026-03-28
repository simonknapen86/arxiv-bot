from arxiv_bot.skills.seed_ingest import extract_identifier, normalize_seed_link, seed_ingest_skill


def test_normalize_seed_link_trims_and_strips_fragment() -> None:
    """Trim whitespace and remove URL fragments from seed links."""
    link = "  https://arxiv.org/abs/1706.03762#section  "
    assert normalize_seed_link(link) == "https://arxiv.org/abs/1706.03762"


def test_extract_identifier_handles_arxiv_abs() -> None:
    """Extract arXiv identifiers from abs URLs."""
    parsed = extract_identifier("https://arxiv.org/abs/1706.03762")
    assert parsed["source_type"] == "arxiv"
    assert parsed["identifier"] == "1706.03762"


def test_extract_identifier_handles_arxiv_pdf() -> None:
    """Extract arXiv identifiers from pdf URLs."""
    parsed = extract_identifier("https://arxiv.org/pdf/1706.03762.pdf")
    assert parsed["source_type"] == "arxiv"
    assert parsed["identifier"] == "1706.03762"


def test_extract_identifier_handles_doi_url() -> None:
    """Extract DOI identifiers from doi.org URLs."""
    parsed = extract_identifier("https://doi.org/10.1038/nature14539")
    assert parsed["source_type"] == "doi"
    assert parsed["identifier"] == "10.1038/nature14539"


def test_extract_identifier_handles_raw_doi() -> None:
    """Convert raw DOI strings into canonical doi.org links."""
    parsed = extract_identifier("10.1126/science.169.3946.635")
    assert parsed["source_type"] == "doi"
    assert parsed["source_link"] == "https://doi.org/10.1126/science.169.3946.635"


def test_seed_ingest_skill_deduplicates_and_drops_empty_links() -> None:
    """Deduplicate normalized links and skip empty inputs."""
    results = seed_ingest_skill(
        [
            " https://arxiv.org/abs/1706.03762 ",
            "https://arxiv.org/abs/1706.03762#v1",
            "",
            "10.1038/nature14539",
            "10.1038/nature14539",
        ]
    )

    assert len(results) == 2
    assert results[0]["source_link"] == "https://arxiv.org/abs/1706.03762"
    assert results[1]["source_link"] == "https://doi.org/10.1038/nature14539"
