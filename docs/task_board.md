# First-Pass Task Board

## P0 - Foundation
1. `P0-01` Initialize package skeleton and test harness
- Owner: Core
- Acceptance criteria: project installs, pytest runs

2. `P0-02` Define input and paper record schemas [DONE]
- Owner: Contracts
- Acceptance criteria: schema validation tests pass for fixtures

3. `P0-03` Implement run orchestrator state machine [DONE]
- Owner: Pipeline
- Acceptance criteria: can execute no-op stages end-to-end

4. `P0-04` Set up SQLite storage (`papers`, `runs`, indexes) [DONE]
- Owner: Storage
- Acceptance criteria: migration + CRUD tests pass

## P1 - Core Skills
1. `P1-01` Implement `seed_ingest_skill` [DONE]
- Acceptance criteria: seed links normalized into identifiers

2. `P1-02` Implement `discovery_skill` [DONE]
- Acceptance criteria: returns ranked candidate paper list

3. `P1-03` Implement `existence_verification_skill` [DONE]
- Acceptance criteria: metadata + resolvable source check enforced

4. `P1-04` Implement `pdf_download_skill` [DONE]
- Acceptance criteria: verified PDFs stored under deterministic names

5. `P1-05` Implement `metadata_bibtex_skill` [DONE]
- Acceptance criteria: valid deduplicated BibTeX keys produced

## P2 - Summaries and Exports
1. `P2-01` Implement `paper_summary_skill` [DONE]
- Acceptance criteria: one paragraph per paper generated

2. `P2-02` Implement `literature_synthesis_skill` [DONE]
- Acceptance criteria: 1-2 page draft with citation keys

3. `P2-03` Implement `export_skill` [DONE]
- Acceptance criteria: all required artifact files produced

4. `P2-04` Add LLM-backed `paper_summary_skill` [DONE]
- Acceptance criteria: one model-generated paragraph per paper with source-grounded content

5. `P2-05` Add LLM-backed `literature_synthesis_skill` [DONE]
- Acceptance criteria: model-generated 1-2 page synthesis with valid `\cite{...}` keys

## P3 - QA and Reliability
1. `P3-01` Implement `qa_audit_skill`
- Acceptance criteria: citation and cross-artifact checks pass/fail clearly

2. `P3-02` Add retry policies and error taxonomy
- Acceptance criteria: transient errors retried, permanent errors classified

3. `P3-03` Add run manifests and provenance logging
- Acceptance criteria: every run emits machine-readable manifest

## P4 - DevEx and CI
1. `P4-01` Add lint/type/test CI workflow
- Acceptance criteria: CI gate on PRs

2. `P4-02` Add fixture-driven e2e regression suite
- Acceptance criteria: stable snapshots on fixture corpus

3. `P4-03` Add runbook and usage examples
- Acceptance criteria: new contributor can run local pipeline in < 15 minutes
