from arxiv_bot.models import PipelineInput
from arxiv_bot.orchestrator import PipelineOrchestrator


def test_scaffold_pipeline_integration() -> None:
    payload = PipelineInput(
        seed_links=["https://arxiv.org/abs/1706.03762"],
        project_description="Transformers literature",
    )
    records = PipelineOrchestrator().run(payload)
    assert records
    assert records[0].status == "discovered"
