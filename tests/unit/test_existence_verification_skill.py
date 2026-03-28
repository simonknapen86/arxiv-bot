from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.existence_verification import existence_verification_skill


def test_existence_verification_accepts_arxiv_record() -> None:
    """Verify that arXiv-linked records with identifiers pass verification."""
    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            arxiv_id="1706.03762",
            status="discovered",
        )
    ]

    verified = existence_verification_skill(records)
    assert len(verified) == 1
    assert verified[0].verified is True
    assert verified[0].status == "verified"


def test_existence_verification_accepts_doi_record() -> None:
    """Verify that DOI-linked records with identifiers pass verification."""
    records = [
        PaperRecord(
            source_link="https://doi.org/10.1038/nature14539",
            doi="10.1038/nature14539",
            status="discovered",
        )
    ]

    verified = existence_verification_skill(records)
    assert len(verified) == 1
    assert verified[0].verified is True


def test_existence_verification_rejects_missing_identifier() -> None:
    """Reject records without DOI/arXiv identifiers from untrusted hosts."""
    records = [
        PaperRecord(
            source_link="https://example.org/paper/123",
            status="discovered",
        )
    ]

    verified = existence_verification_skill(records)
    assert verified == []
    assert records[0].verified is False


def test_existence_verification_rejects_non_http_source() -> None:
    """Reject records with non-HTTP sources even if an identifier is present."""
    records = [
        PaperRecord(
            source_link="ftp://arxiv.org/abs/1706.03762",
            arxiv_id="1706.03762",
            status="discovered",
        )
    ]

    verified = existence_verification_skill(records)
    assert verified == []


def test_existence_verification_filters_mixed_inputs() -> None:
    """Keep only verified records when given a mix of valid and invalid papers."""
    records = [
        PaperRecord(source_link="https://arxiv.org/abs/1706.03762", arxiv_id="1706.03762"),
        PaperRecord(source_link="https://example.org/paper/no-id"),
        PaperRecord(source_link="https://doi.org/10.1038/nature14539", doi="10.1038/nature14539"),
    ]

    verified = existence_verification_skill(records)
    assert len(verified) == 2
    assert all(record.verified for record in verified)
