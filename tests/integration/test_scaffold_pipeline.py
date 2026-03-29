from pathlib import Path

from arxiv_bot.models import PipelineInput
from arxiv_bot.orchestrator import PipelineOrchestrator


def test_scaffold_pipeline_integration(tmp_path: Path) -> None:
    payload = PipelineInput(
        seed_links=["https://arxiv.org/abs/1706.03762"],
        project_description="Transformers literature",
    )
    records = PipelineOrchestrator(artifacts_dir=tmp_path).run(payload)
    assert records
    assert all(record.status == "exported" for record in records)
    assert all(record.summary_paragraph for record in records)
