# Architecture

## Runtime Overview
```mermaid
flowchart TD
    U[User] --> CLI["./arxiv_bot.py / arxiv-bot"]

    CLI -->|"-run settings.json"| O["PipelineOrchestrator.run()"]
    CLI -->|"-litreview"| LR["regenerate_literature_review()"]
    CLI -->|"-start"| ST["settings.json template"]
    CLI -->|"-help"| HP["usage text"]

    O --> S1[seed_ingest_skill]
    S1 --> S2[discovery_skill<br/>+ optional INSPIRE citing/cited expansion]
    S2 --> S3[existence_verification_skill]
    S3 --> S4[pdf_download_skill]
    S4 --> S5[metadata_bibtex_skill<br/>+ INSPIRE BibTeX]
    S5 --> S6[paper_summary_skill<br/>+ optional LLM]
    S6 --> S7[literature_synthesis_skill<br/>+ optional LLM]
    S7 --> S8[export_skill]
    S8 --> S9[qa_audit_skill]
    S9 --> S10[run_manifest]

    S8 --> A1["artifacts/papers/*.pdf"]
    S8 --> A2["artifacts/references.bib"]
    S8 --> A3["artifacts/paper_summaries.tex"]
    S8 --> A4["artifacts/literature_review.tex"]
    S10 --> A5["artifacts/run_manifest.json"]

    LR --> A3
    LR --> S7
    S7 --> A4
```

## Main Components
- `CLI entry`: supports `-run`, `-litreview`, `-start`, and `-help`.
- `PipelineOrchestrator`: executes stage order, emits progress logs, and routes artifacts to configured output directory.
- `Skills`: pure-ish task modules for ingest, discovery, verification, download, metadata, summary, synthesis, export, QA, and manifest.
- `InspireClient`: INSPIRE API access for BibTeX, seed abstracts, and related-paper discovery.
- `LLMClient`: optional model-backed generation for per-paper summaries and synthesis with deterministic fallbacks.

## Data Contracts
- `PipelineInput`: seed links, project description, include/exclude keywords, related-paper relevance thresholds.
- `PaperRecord`: canonical per-paper state record through lifecycle:
  `discovered -> verified -> downloaded -> metadata_enriched -> summarized -> exported`.

## Output Guarantees
- Verified outputs are written under `<target_dir>/artifacts` by default.
- QA gate validates:
  - artifact existence and non-empty content
  - citation keys in TeX exist in `references.bib`
  - each exported paper is cited and has a local PDF
- Manifest captures stage history and per-paper provenance.
