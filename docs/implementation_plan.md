# Implementation Plan: Agentic Literature Pipeline

## Objective
Build a skills-first multi-agent workflow that takes seed paper links and a project description, discovers relevant literature, verifies existence, downloads PDFs, builds BibTeX, writes per-paper summaries, and produces a 1-2 page synthesis report with citations.

## Inputs
- Seed paper links (DOI/arXiv/journal URLs)
- Project description (scope, exclusions, timeframe, domain keywords)

## Required Outputs
- `artifacts/papers/` with verified PDF files
- `artifacts/references.bib` containing all BibTeX entries
- `artifacts/paper_summaries.tex` containing one paragraph per paper
- `artifacts/literature_review.tex` containing a 1-2 page synthesis with references

## Step-by-Step Build Plan

### 1. Define schemas and contracts
1. Create schema for run input (`input.json`)
2. Create schema for internal paper records (`paper_record.json`)
3. Define status lifecycle for each paper: `discovered -> verified -> downloaded -> summarized -> exported`

Tests:
1. Schema validation tests for valid and invalid payloads
2. Contract tests for required fields at each stage

### 2. Create skill modules with strict I/O boundaries
1. `seed_ingest_skill`: normalize and parse seed identifiers
2. `discovery_skill`: expand candidate set from APIs/search
3. `existence_verification_skill`: confirm metadata and source resolvability
4. `pdf_download_skill`: fetch and validate PDFs
5. `metadata_bibtex_skill`: generate canonical BibTeX entries
6. `paper_summary_skill`: create 1-paragraph per-paper summaries
7. `literature_synthesis_skill`: write 1-2 page synthesis with citations
8. `export_skill`: write output artifact files
9. `qa_audit_skill`: cross-check completeness and consistency

Tests:
1. Unit tests for each skill (happy path + failure path)
2. Mocked API tests for deterministic behavior
3. Parsing/BibTeX fixture tests

### 3. Build pipeline orchestrator and state store
1. Implement run coordinator with retry policy and stage transitions
2. Use SQLite for `papers` and `runs` tables
3. Add run manifest and per-stage structured logging

Tests:
1. Integration test for full run with fixtures
2. Retry and transient failure tests
3. Idempotency test for reruns

### 4. Enforce paper existence guarantee
1. Require trusted identifier (DOI/arXiv/PMID) or equivalent canonical source
2. Validate metadata consistency from trusted provider(s)
3. Validate PDF availability and content type
4. Only mark as verified when checks pass

Tests:
1. Reject invalid/broken links
2. Reject non-PDF payloads
3. Detect duplicate identifiers

### 5. Generate final artifacts
1. Save PDFs with deterministic naming convention
2. Generate deduplicated `references.bib`
3. Generate `paper_summaries.tex` with 1 paragraph per paper
4. Generate `literature_review.tex` with `\\cite{...}` references

Tests:
1. File existence and non-empty checks
2. BibTeX parse validation
3. TeX compile smoke test (optional in CI, required pre-release)

### 6. Add QA gates and audit report
1. Validate every citation key used in TeX exists in BibTeX
2. Validate every downloaded paper has summary + bib entry
3. Validate synthesis length target
4. Validate provenance metadata is present

Tests:
1. Cross-artifact consistency tests
2. End-to-end snapshot test with fixture corpus

### 7. CI and release hygiene
1. Add lint (`ruff`), types (`mypy`), tests (`pytest`)
2. Add CI workflow for unit/integration/e2e tiers
3. Publish architecture and runbook docs

Tests:
1. CI smoke run on pull requests
2. Nightly fixture run (optional)

## Non-Functional Requirements
- Reproducible runs via run IDs and manifests
- Deterministic file naming
- Explicit error handling and recovery
- Traceability for every output artifact to source metadata
