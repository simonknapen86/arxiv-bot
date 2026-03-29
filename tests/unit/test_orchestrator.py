from pathlib import Path

from arxiv_bot.models import PipelineInput
from arxiv_bot.orchestrator import PipelineOrchestrator


def test_stage_names_present() -> None:
    orchestrator = PipelineOrchestrator()
    assert "seed_ingest" in orchestrator.stage_names
    assert "qa_audit" in orchestrator.stage_names


def test_run_returns_record_per_seed_link(tmp_path: Path) -> None:
    """Run the pipeline on valid seed links and return one record per unique seed."""
    payload = PipelineInput(
        seed_links=[
            "https://arxiv.org/abs/1706.03762",
            "https://doi.org/10.1038/nature14539",
        ],
        project_description="Test",
    )
    records = PipelineOrchestrator(artifacts_dir=tmp_path).run(payload)
    assert len(records) == 2
    assert records[0].source_link in payload.seed_links
    assert all(record.status == "exported" for record in records)
    assert all(record.verified for record in records)


def test_run_tracks_stage_history_end_to_end(tmp_path: Path) -> None:
    """Track stage history and expose synthesis text in the final run report."""
    payload = PipelineInput(
        seed_links=["https://arxiv.org/abs/1706.03762"],
        project_description="Test",
    )
    orchestrator = PipelineOrchestrator(artifacts_dir=tmp_path)
    orchestrator.run(payload)

    assert orchestrator.last_run_report is not None
    assert orchestrator.last_run_report.stage_history == orchestrator.stage_names
    assert orchestrator.last_run_report.transition_snapshots["discovery"] == ["discovered"]
    assert orchestrator.last_run_report.transition_snapshots["export"] == ["exported"]
    assert "\\section*{Literature Synthesis}" in orchestrator.last_run_report.literature_synthesis
    assert (tmp_path / "run_manifest.json").exists()
