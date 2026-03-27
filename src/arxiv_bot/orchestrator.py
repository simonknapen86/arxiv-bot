from arxiv_bot.models import PaperRecord, PipelineInput


class PipelineOrchestrator:
    """Coordinates stage execution across skill modules."""

    def __init__(self) -> None:
        self.stage_names = [
            "seed_ingest",
            "discovery",
            "existence_verification",
            "pdf_download",
            "metadata_bibtex",
            "paper_summary",
            "literature_synthesis",
            "export",
            "qa_audit",
        ]

    def run(self, payload: PipelineInput) -> list[PaperRecord]:
        """Placeholder pipeline execution.

        Returns discovered records as a scaffold for implementation.
        """
        return [PaperRecord(source_link=link) for link in payload.seed_links]
