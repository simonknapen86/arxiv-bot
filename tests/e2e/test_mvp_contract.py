from pathlib import Path

from arxiv_bot.models import PipelineInput
from arxiv_bot.orchestrator import PipelineOrchestrator


def test_mvp_contract_seed_to_records(tmp_path: Path) -> None:
    """Run the MVP contract using a resolvable and identifiable seed link."""
    payload = PipelineInput(
        seed_links=["https://arxiv.org/abs/1706.03762"],
        project_description="desc",
    )
    records = PipelineOrchestrator(artifacts_dir=tmp_path).run(payload)
    assert len(records) == 1
