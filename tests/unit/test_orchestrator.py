from arxiv_bot.models import PipelineInput
from arxiv_bot.orchestrator import PipelineOrchestrator


def test_stage_names_present() -> None:
    orchestrator = PipelineOrchestrator()
    assert "seed_ingest" in orchestrator.stage_names
    assert "qa_audit" in orchestrator.stage_names


def test_run_returns_record_per_seed_link() -> None:
    payload = PipelineInput(
        seed_links=["a", "b"],
        project_description="Test",
    )
    records = PipelineOrchestrator().run(payload)
    assert len(records) == 2
    assert records[0].source_link == "a"
