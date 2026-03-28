from __future__ import annotations

from dataclasses import dataclass, field

from arxiv_bot.models import PaperRecord, PipelineInput
from arxiv_bot.skills.discovery import discovery_skill
from arxiv_bot.skills.existence_verification import existence_verification_skill
from arxiv_bot.skills.pdf_download import pdf_download_skill
from arxiv_bot.skills.seed_ingest import seed_ingest_skill


@dataclass
class RunReport:
    """Capture stage order and status snapshots for a single pipeline run."""
    stage_history: list[str] = field(default_factory=list)
    transition_snapshots: dict[str, list[str]] = field(default_factory=dict)
    literature_synthesis: str = ""


class PipelineOrchestrator:
    """Coordinates stage execution across skill modules."""

    def __init__(self) -> None:
        """Initialize orchestrator stage order and run report state."""
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
        self.last_run_report: RunReport | None = None

    def _seed_ingest(self, payload: PipelineInput) -> list[dict[str, str]]:
        """Normalize and classify seed links from pipeline input."""
        return seed_ingest_skill(payload.seed_links)

    def _discovery(self, payload: PipelineInput, ingested: list[dict[str, str]]) -> list[PaperRecord]:
        """Create ranked discovered paper records from ingested seed metadata."""
        return discovery_skill(
            ingested,
            include_keywords=payload.include_keywords,
            exclude_keywords=payload.exclude_keywords,
        )

    def _existence_verification(self, records: list[PaperRecord]) -> list[PaperRecord]:
        """Verify discovered records and keep only records that pass checks."""
        return existence_verification_skill(records)

    def _pdf_download(self, records: list[PaperRecord]) -> list[PaperRecord]:
        """Download verified PDFs using a deterministic test-safe fetcher."""
        return pdf_download_skill(records, fetch_pdf=self._fixture_pdf_fetcher)

    def _fixture_pdf_fetcher(self, pdf_url: str) -> bytes:
        """Return minimal deterministic PDF bytes for non-network scaffold runs."""
        _ = pdf_url
        return b"%PDF-1.4\n% scaffold file\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"

    def _metadata_bibtex(self, records: list[PaperRecord]) -> list[PaperRecord]:
        """Pass records through the metadata and BibTeX stage placeholder."""
        return records

    def _paper_summary(self, records: list[PaperRecord]) -> list[PaperRecord]:
        """Attach a placeholder summary paragraph to each record."""
        for record in records:
            record.summary_paragraph = (
                f"Placeholder summary for {record.source_link}. "
                "Replace with model-based summarization."
            )
            record.status = "summarized"
        return records

    def _literature_synthesis(self, records: list[PaperRecord]) -> str:
        """Generate a placeholder synthesis string for the current run."""
        return (
            "Placeholder literature synthesis. "
            f"Includes {len(records)} paper(s)."
        )

    def _export(self, records: list[PaperRecord]) -> list[PaperRecord]:
        """Mark records as exported in the current no-op scaffold."""
        for record in records:
            record.status = "exported"
        return records

    def _qa_audit(self, records: list[PaperRecord]) -> None:
        """Ensure records exist and have reached the exported stage."""
        if not records:
            raise ValueError("qa_audit failed: no records to audit")
        non_exported = [record.source_link for record in records if record.status != "exported"]
        if non_exported:
            raise ValueError(f"qa_audit failed: non-exported records found: {non_exported}")

    def run(self, payload: PipelineInput) -> list[PaperRecord]:
        """Execute the no-op stage pipeline with explicit transitions."""
        report = RunReport()

        ingested = self._seed_ingest(payload)
        report.stage_history.append("seed_ingest")
        report.transition_snapshots["seed_ingest"] = [item["source_link"] for item in ingested]

        records = self._discovery(payload, ingested)
        report.stage_history.append("discovery")
        report.transition_snapshots["discovery"] = [r.status for r in records]

        records = self._existence_verification(records)
        report.stage_history.append("existence_verification")
        report.transition_snapshots["existence_verification"] = [r.status for r in records]

        records = self._pdf_download(records)
        report.stage_history.append("pdf_download")
        report.transition_snapshots["pdf_download"] = [r.status for r in records]

        records = self._metadata_bibtex(records)
        report.stage_history.append("metadata_bibtex")
        report.transition_snapshots["metadata_bibtex"] = [r.status for r in records]

        records = self._paper_summary(records)
        report.stage_history.append("paper_summary")
        report.transition_snapshots["paper_summary"] = [r.status for r in records]

        report.literature_synthesis = self._literature_synthesis(records)
        report.stage_history.append("literature_synthesis")
        report.transition_snapshots["literature_synthesis"] = [r.status for r in records]

        records = self._export(records)
        report.stage_history.append("export")
        report.transition_snapshots["export"] = [r.status for r in records]

        self._qa_audit(records)
        report.stage_history.append("qa_audit")
        report.transition_snapshots["qa_audit"] = [r.status for r in records]

        self.last_run_report = report
        return records
