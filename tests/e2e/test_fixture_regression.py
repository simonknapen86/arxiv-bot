import json
from pathlib import Path

from arxiv_bot.models import PipelineInput
from arxiv_bot.orchestrator import PipelineOrchestrator
from arxiv_bot.skills.export import export_skill as real_export_skill
from arxiv_bot.skills.pdf_download import pdf_download_skill as real_pdf_download_skill
from arxiv_bot.skills.qa_audit import qa_audit_skill as real_qa_audit_skill
from arxiv_bot.skills.run_manifest import write_run_manifest as real_write_run_manifest


def _fixture_input(path: Path) -> PipelineInput:
    """Load a PipelineInput payload from a JSON fixture file."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return PipelineInput(**payload)


def test_e2e_fixture_regression_snapshot(tmp_path: Path, monkeypatch) -> None:
    """Run the full pipeline on a fixed fixture and compare output snapshots."""
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures"
    input_path = fixture_root / "corpus" / "transformers_minimal.json"
    snapshots_dir = fixture_root / "snapshots" / "transformers_minimal"
    artifacts_output_dir = tmp_path / "artifacts"
    pdf_dir = artifacts_output_dir / "papers"

    def _pdf_download(records, output_dir: str | Path = "artifacts/papers", fetch_pdf=None):
        """Route pdf download output to the test-local artifacts directory."""
        _ = output_dir
        return real_pdf_download_skill(records, output_dir=pdf_dir, fetch_pdf=fetch_pdf)

    def _export(records, literature_synthesis_tex, artifacts_dir: str | Path = "artifacts"):
        """Route export output to the test-local artifacts directory."""
        _ = artifacts_dir
        return real_export_skill(records, literature_synthesis_tex, artifacts_dir=artifacts_output_dir)

    def _manifest(records, stage_history, artifacts_dir: str | Path = "artifacts"):
        """Route run manifest output to the test-local artifacts directory."""
        _ = artifacts_dir
        return real_write_run_manifest(
            records,
            stage_history=stage_history,
            artifacts_dir=artifacts_output_dir,
        )

    def _qa_audit(records, artifacts_dir: str | Path = "artifacts"):
        """Route QA audit checks to the test-local artifacts directory."""
        _ = artifacts_dir
        real_qa_audit_skill(records, artifacts_dir=artifacts_output_dir)

    def _empty_generate(self, prompt: str, max_tokens: int = 400) -> str:
        """Force deterministic fallback summaries instead of live model output."""
        _ = (self, prompt, max_tokens)
        return ""

    monkeypatch.setattr("arxiv_bot.orchestrator.pdf_download_skill", _pdf_download)
    monkeypatch.setattr("arxiv_bot.orchestrator.export_skill", _export)
    monkeypatch.setattr("arxiv_bot.orchestrator.qa_audit_skill", _qa_audit)
    monkeypatch.setattr("arxiv_bot.orchestrator.write_run_manifest", _manifest)
    monkeypatch.setattr("arxiv_bot.skills.llm_client.LLMClient.generate", _empty_generate)

    orchestrator = PipelineOrchestrator(use_fixture_pdf_fetcher=True, use_inspire_bibtex=False)
    records = orchestrator.run(_fixture_input(input_path))

    assert records
    assert all(record.status == "exported" for record in records)

    references_actual = (artifacts_output_dir / "references.bib").read_text(encoding="utf-8")
    summaries_actual = (artifacts_output_dir / "paper_summaries.tex").read_text(encoding="utf-8")
    review_actual = (artifacts_output_dir / "literature_review.tex").read_text(encoding="utf-8")

    references_expected = (snapshots_dir / "references.bib").read_text(encoding="utf-8")
    summaries_expected = (snapshots_dir / "paper_summaries.tex").read_text(encoding="utf-8")
    review_expected = (snapshots_dir / "literature_review.tex").read_text(encoding="utf-8")

    assert references_actual == references_expected
    assert summaries_actual == summaries_expected
    assert review_actual == review_expected
