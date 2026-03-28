from arxiv_bot.models import PaperRecord
from arxiv_bot.skills.discovery import discovery_skill as implemented_discovery_skill
from arxiv_bot.skills.existence_verification import (
    existence_verification_skill as implemented_existence_verification_skill,
)
from arxiv_bot.skills.metadata_bibtex import (
    metadata_bibtex_skill as implemented_metadata_bibtex_skill,
)
from arxiv_bot.skills.pdf_download import pdf_download_skill as implemented_pdf_download_skill
from arxiv_bot.skills.seed_ingest import seed_ingest_skill as implemented_seed_ingest_skill


def seed_ingest_skill(seed_links: list[str]) -> list[str]:
    """Delegate seed ingestion to the concrete seed ingest implementation."""
    return [item["source_link"] for item in implemented_seed_ingest_skill(seed_links)]


def discovery_skill(links: list[str]) -> list[PaperRecord]:
    """Delegate discovery to the concrete implementation with default ranking inputs."""
    ingested = implemented_seed_ingest_skill(links)
    return implemented_discovery_skill(ingested)


def existence_verification_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    """Delegate verification to the concrete existence-verification implementation."""
    return implemented_existence_verification_skill(records)


def pdf_download_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    """Delegate PDF download to the concrete implementation."""
    return implemented_pdf_download_skill(records)


def metadata_bibtex_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    """Delegate metadata/BibTeX generation to the concrete implementation."""
    return implemented_metadata_bibtex_skill(records, use_inspire=False)


def paper_summary_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    """Return records unchanged as a placeholder summary step."""
    return records


def literature_synthesis_skill(records: list[PaperRecord]) -> str:
    """Return an empty string as a placeholder synthesis output."""
    return ""


def export_skill(records: list[PaperRecord]) -> None:
    """Perform no action as a placeholder export step."""
    return None


def qa_audit_skill(records: list[PaperRecord]) -> bool:
    """Return True as a placeholder QA result."""
    return True
