import pytest

from arxiv_bot.contracts import validate_paper_record, validate_pipeline_input


def test_validate_pipeline_input_accepts_valid_payload() -> None:
    payload = {
        "seed_links": ["https://arxiv.org/abs/1706.03762"],
        "project_description": "Find transformer papers for NLP",
        "include_keywords": ["transformer", "attention"],
        "exclude_keywords": ["vision-only"],
    }

    model = validate_pipeline_input(payload)
    assert model.seed_links == payload["seed_links"]
    assert model.project_description == payload["project_description"]


def test_validate_pipeline_input_rejects_empty_seed_links() -> None:
    payload = {
        "seed_links": [],
        "project_description": "Find papers",
    }

    with pytest.raises(ValueError, match="seed_links"):
        validate_pipeline_input(payload)


def test_validate_pipeline_input_rejects_missing_description() -> None:
    payload = {
        "seed_links": ["https://arxiv.org/abs/1706.03762"],
        "project_description": "   ",
    }

    with pytest.raises(ValueError, match="project_description"):
        validate_pipeline_input(payload)


def test_validate_paper_record_accepts_valid_payload() -> None:
    payload = {
        "source_link": "https://arxiv.org/abs/1706.03762",
        "title": "Attention Is All You Need",
        "authors": ["Vaswani et al."],
        "year": 2017,
        "arxiv_id": "1706.03762",
        "status": "verified",
        "verified": True,
    }

    record = validate_paper_record(payload)
    assert record.source_link == payload["source_link"]
    assert record.status == "verified"
    assert record.verified is True


def test_validate_paper_record_rejects_invalid_status() -> None:
    payload = {
        "source_link": "https://arxiv.org/abs/1706.03762",
        "status": "done",
    }

    with pytest.raises(ValueError, match="status"):
        validate_paper_record(payload)


def test_validate_paper_record_rejects_year_type() -> None:
    payload = {
        "source_link": "https://arxiv.org/abs/1706.03762",
        "year": "2017",
    }

    with pytest.raises(ValueError, match="year"):
        validate_paper_record(payload)


def test_validate_paper_record_rejects_non_bool_verified() -> None:
    payload = {
        "source_link": "https://arxiv.org/abs/1706.03762",
        "verified": "yes",
    }

    with pytest.raises(ValueError, match="verified"):
        validate_paper_record(payload)
