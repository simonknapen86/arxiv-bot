from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from arxiv_bot.models import PaperRecord, PipelineInput
from arxiv_bot.skills.discovery import discovery_skill
from arxiv_bot.skills.export import export_skill
from arxiv_bot.skills.existence_verification import existence_verification_skill
from arxiv_bot.skills.literature_synthesis import literature_synthesis_skill
from arxiv_bot.skills.metadata_bibtex import metadata_bibtex_skill
from arxiv_bot.skills.paper_summary import paper_summary_skill
from arxiv_bot.skills.pdf_download import pdf_download_skill
from arxiv_bot.skills.qa_audit import qa_audit_skill
from arxiv_bot.skills.run_manifest import write_run_manifest
from arxiv_bot.skills.seed_ingest import seed_ingest_skill


@dataclass
class RunReport:
    """Capture stage order and status snapshots for a single pipeline run."""
    stage_history: list[str] = field(default_factory=list)
    transition_snapshots: dict[str, list[str]] = field(default_factory=dict)
    literature_synthesis: str = ""


class PipelineOrchestrator:
    """Coordinates stage execution across skill modules."""

    def __init__(
        self,
        use_fixture_pdf_fetcher: bool = True,
        use_inspire_bibtex: bool = False,
        use_inspire_related_discovery: bool = False,
        artifacts_dir: str | Path = "artifacts",
    ) -> None:
        """Initialize orchestrator stage order, run state, and external I/O modes."""
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
        self.use_fixture_pdf_fetcher = use_fixture_pdf_fetcher
        self.use_inspire_bibtex = use_inspire_bibtex
        self.use_inspire_related_discovery = use_inspire_related_discovery
        self.artifacts_dir = Path(artifacts_dir)

    def _seed_ingest(self, payload: PipelineInput) -> list[dict[str, str]]:
        """Normalize and classify seed links from pipeline input."""
        return seed_ingest_skill(payload.seed_links)

    def _discovery(self, payload: PipelineInput, ingested: list[dict[str, str]]) -> list[PaperRecord]:
        """Create ranked discovered paper records from ingested seed metadata."""
        return discovery_skill(
            ingested,
            include_keywords=payload.include_keywords,
            exclude_keywords=payload.exclude_keywords,
            expand_via_inspire=self.use_inspire_related_discovery,
            min_relevance_score=payload.related_min_relevance_score,
            min_keyword_overlap=payload.related_min_keyword_overlap,
        )

    def _existence_verification(self, records: list[PaperRecord]) -> list[PaperRecord]:
        """Verify discovered records and keep only records that pass checks."""
        return existence_verification_skill(records)

    def _pdf_download(self, records: list[PaperRecord]) -> list[PaperRecord]:
        """Download verified PDFs using fixture or network fetcher per mode."""
        papers_dir = self.artifacts_dir / "papers"
        if self.use_fixture_pdf_fetcher:
            return pdf_download_skill(records, output_dir=papers_dir, fetch_pdf=self._fixture_pdf_fetcher)
        return pdf_download_skill(records, output_dir=papers_dir)

    def _fixture_pdf_fetcher(self, pdf_url: str) -> bytes:
        """Return minimal deterministic PDF bytes for non-network scaffold runs."""
        _ = pdf_url
        return b"%PDF-1.4\n% scaffold file\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"

    def _metadata_bibtex(self, records: list[PaperRecord]) -> list[PaperRecord]:
        """Populate citation keys and BibTeX entries for downloaded records."""
        return metadata_bibtex_skill(records, use_inspire=self.use_inspire_bibtex)

    def _paper_summary(self, records: list[PaperRecord]) -> list[PaperRecord]:
        """Attach one-paragraph summaries to each metadata-enriched record."""
        return paper_summary_skill(records, use_llm=True)

    def _literature_synthesis(self, payload: PipelineInput, records: list[PaperRecord]) -> str:
        """Generate a TeX-ready synthesis summary from summarized paper records."""
        return literature_synthesis_skill(
            records,
            project_description=payload.project_description,
            use_llm=True,
        )

    def _export(self, records: list[PaperRecord], literature_synthesis_tex: str) -> list[PaperRecord]:
        """Write output artifacts and mark records as exported."""
        return export_skill(records, literature_synthesis_tex, artifacts_dir=self.artifacts_dir)

    def _qa_audit(self, records: list[PaperRecord]) -> None:
        """Run cross-artifact quality checks and raise on audit failures."""
        qa_audit_skill(records, artifacts_dir=self.artifacts_dir)

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

        report.literature_synthesis = self._literature_synthesis(payload, records)
        report.stage_history.append("literature_synthesis")
        report.transition_snapshots["literature_synthesis"] = [r.status for r in records]

        records = self._export(records, report.literature_synthesis)
        report.stage_history.append("export")
        report.transition_snapshots["export"] = [r.status for r in records]

        self._qa_audit(records)
        report.stage_history.append("qa_audit")
        report.transition_snapshots["qa_audit"] = [r.status for r in records]

        write_run_manifest(records, stage_history=report.stage_history, artifacts_dir=self.artifacts_dir)

        self.last_run_report = report
        return records
