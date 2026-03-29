import json
from pathlib import Path

from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.run_manifest import write_run_manifest


def test_write_run_manifest_creates_expected_json(tmp_path: Path) -> None:
    """Write a manifest JSON with stage history and paper provenance fields."""
    records = [
        PaperRecord(
            source_link="https://arxiv.org/abs/1706.03762",
            title="Attention Is All You Need",
            arxiv_id="1706.03762",
            bibtex_key="Vaswani:2017lxt",
            local_pdf_path="artifacts/papers/1706_03762.pdf",
            status="exported",
            verified=True,
            relevance_score=1.2,
        )
    ]

    manifest_path = write_run_manifest(
        records,
        stage_history=["seed_ingest", "discovery", "export", "qa_audit"],
        artifacts_dir=tmp_path,
    )

    assert manifest_path.exists()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["paper_count"] == 1
    assert payload["stage_history"][-1] == "qa_audit"
    assert payload["papers"][0]["bibtex_key"] == "Vaswani:2017lxt"
    assert payload["papers"][0]["verified"] is True
