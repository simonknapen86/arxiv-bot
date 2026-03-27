from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PipelineInput:
    seed_links: list[str]
    project_description: str
    include_keywords: list[str] = field(default_factory=list)
    exclude_keywords: list[str] = field(default_factory=list)


@dataclass
class PaperRecord:
    source_link: str
    title: str = ""
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    local_pdf_path: Optional[str] = None
    bibtex_key: Optional[str] = None
    bibtex_entry: Optional[str] = None
    summary_paragraph: Optional[str] = None
    verified: bool = False
    status: str = "discovered"
