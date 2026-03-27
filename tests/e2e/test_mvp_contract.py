from arxiv_bot.models import PipelineInput
from arxiv_bot.orchestrator import PipelineOrchestrator


def test_mvp_contract_seed_to_records() -> None:
    payload = PipelineInput(seed_links=["seed"], project_description="desc")
    records = PipelineOrchestrator().run(payload)
    assert len(records) == 1
