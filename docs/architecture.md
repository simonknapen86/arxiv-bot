# Architecture

```mermaid
flowchart TD
    A[User Input: seed links + topic description] --> B[seed_ingest_skill]
    B --> C[discovery_skill]
    C --> D[existence_verification_skill]
    D -->|verified| E[pdf_download_skill]
    D -->|rejected| X[Reject and Log]
    E --> F[metadata_bibtex_skill]
    E --> G[paper_summary_skill]
    F --> H[export_skill]
    G --> H
    H --> I[paper_summaries.tex]
    H --> J[literature_synthesis_skill]
    J --> K[literature_review.tex]
    H --> L[references.bib]
    H --> M[papers folder with PDFs]
    I --> N[qa_audit_skill]
    K --> N
    L --> N
    M --> N
    N --> O[Run Manifest + Pass or Fail]

    subgraph DB[SQLite]
      P[papers table]
      Q[runs table]
    end

    C --> P
    D --> P
    E --> P
    N --> Q
```

## Core Components
- Skills layer: modular task implementations with strict inputs/outputs.
- Orchestrator: stage sequencing, retries, state transitions, and logging.
- Storage: SQLite for run/paper lifecycle.
- Exporters: deterministic generation of PDF, BibTeX, and TeX artifacts.
- QA/Audit: cross-file consistency and citation integrity checks.
