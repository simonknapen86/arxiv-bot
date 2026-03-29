from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PipelineInput:
    """Describe the high-level request that drives one literature pipeline run."""
    seed_links: list[str]
    project_description: str
    include_keywords: list[str] = field(default_factory=list)
    exclude_keywords: list[str] = field(default_factory=list)
    related_min_relevance_score: float = 0.8
    related_min_keyword_overlap: float = 0.05


@dataclass
class PaperRecord:
    """Represent a candidate paper and its processing state through the pipeline."""
    source_link: str
    title: str = ""
    abstract: Optional[str] = None
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pdf_url: Optional[str] = None
    local_pdf_path: Optional[str] = None
    bibtex_key: Optional[str] = None
    bibtex_entry: Optional[str] = None
    summary_paragraph: Optional[str] = None
    relevance_score: Optional[float] = None
    verified: bool = False
    status: str = "discovered"
