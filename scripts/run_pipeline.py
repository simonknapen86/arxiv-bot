from arxiv_bot.models import PipelineInput
from arxiv_bot.orchestrator import PipelineOrchestrator


def main() -> None:
    """Run a minimal scaffold pipeline invocation from the command line."""
    payload = PipelineInput(
        seed_links=["https://arxiv.org/abs/1706.03762"],
        project_description="Example query",
    )
    records = PipelineOrchestrator().run(payload)
    print(f"Scaffold run complete. Records: {len(records)}")


if __name__ == "__main__":
    main()
