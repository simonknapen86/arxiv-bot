# Runbook

## Goal
Run the project locally from a fresh checkout in under 15 minutes.

## Prerequisites
1. Python 3.11+ available (`openai311` is recommended in this repo).
2. `git` installed.
3. Optional for live summaries: `OPENAI_API_KEY` set.

## 15-Minute Quickstart
1. Clone and enter the repo.
```bash
git clone <repo-url>
cd arxiv_bot
```
2. Install in editable mode with dev tools.
```bash
/opt/anaconda3/envs/openai311/bin/python3 -m pip install -e .[dev]
```
3. Run the full test suite.
```bash
/opt/anaconda3/envs/openai311/bin/python3 -m pytest -q -W error
```
4. Run the sample pipeline script.
```bash
/opt/anaconda3/envs/openai311/bin/python3 scripts/run_pipeline.py
```
5. Confirm artifacts were produced.
```bash
ls -lah artifacts
ls -lah artifacts/papers
```

## What To Expect After A Run
1. `artifacts/papers/` contains downloaded PDFs.
2. `artifacts/references.bib` contains BibTeX entries.
3. `artifacts/paper_summaries.tex` contains one subsection per paper.
4. `artifacts/literature_review.tex` contains the synthesis report.
5. `artifacts/run_manifest.json` records stage history and provenance.

## Deterministic Development Workflow
1. Use the fixture-based e2e test for stable regression checks.
```bash
/opt/anaconda3/envs/openai311/bin/python3 -m pytest -q tests/e2e/test_fixture_regression.py -W error
```
2. Keep unit tests green while iterating on one skill at a time.
```bash
/opt/anaconda3/envs/openai311/bin/python3 -m pytest -q tests/unit -W error
```

## Troubleshooting
1. If summaries fall back to scaffold text, verify `OPENAI_API_KEY` and model access.
2. If PDFs fail to download in live runs, retry with a known-valid arXiv seed.
3. If TeX output does not compile, inspect for non-LaTeX-safe model output in `artifacts/*.tex`.

## Related Docs
1. `docs/architecture.md`
2. `docs/implementation_plan.md`
3. `docs/task_board.md`
4. `docs/usage_examples.md`
