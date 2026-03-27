from arxiv_bot.models import PaperRecord


def seed_ingest_skill(seed_links: list[str]) -> list[str]:
    return seed_links


def discovery_skill(links: list[str]) -> list[PaperRecord]:
    return [PaperRecord(source_link=link) for link in links]


def existence_verification_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    return records


def pdf_download_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    return records


def metadata_bibtex_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    return records


def paper_summary_skill(records: list[PaperRecord]) -> list[PaperRecord]:
    return records


def literature_synthesis_skill(records: list[PaperRecord]) -> str:
    return ""


def export_skill(records: list[PaperRecord]) -> None:
    return None


def qa_audit_skill(records: list[PaperRecord]) -> bool:
    return True
