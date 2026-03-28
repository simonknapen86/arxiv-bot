from arxiv_bot.models import PaperRecord


def seed_ingest_skill(seed_links: list[str]) -> list[str]:
    """Return seed links unchanged as a placeholder ingest implementation."""
    return seed_links


def discovery_skill(links: list[str]) -> list[PaperRecord]:
    """Convert links into placeholder discovered paper records."""
    return [PaperRecord(source_link=link) for link in links]


def existence_verification_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    """Return records unchanged as a placeholder verification step."""
    return records


def pdf_download_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    """Return records unchanged as a placeholder download step."""
    return records


def metadata_bibtex_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    """Return records unchanged as a placeholder metadata/BibTeX step."""
    return records


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
