# arxiv_bot

Agentic literature pipeline for finding, verifying, downloading, and summarizing research papers.

## Goals
- Input: seed paper links + project description.
- Output:
  - `artifacts/papers/` with verified PDFs
  - `artifacts/references.bib`
  - `artifacts/paper_summaries.tex`
  - `artifacts/literature_review.tex`
- Quality gates: every suggested paper must be verified and downloadable.

## Project Layout
- `docs/` architecture, implementation plan, and task board
- `docs/skills/` skill contracts and definitions
- `src/arxiv_bot/` implementation
- `tests/` unit, integration, and e2e tests
- `scripts/` runnable entry points for local pipeline execution

## Quickstart
```bash
./scripts/install_with_pip.sh --dev
/opt/anaconda3/envs/openai311/bin/python3 -m pytest -q -W error
./arxiv_bot.py -start
./arxiv_bot.py -run settings.json
```

## CLI Modes
- `./arxiv_bot.py -run settings.json` runs the full pipeline.
- `./arxiv_bot.py -litreview` regenerates only `literature_review.tex` from `paper_summaries.tex`.
- `./arxiv_bot.py -start` creates a template `settings.json`.
- `./arxiv_bot.py -help` prints command usage.
- If installed via pip, `arxiv-bot` is also available.

## Docs
- `docs/runbook.md` for setup, troubleshooting, and expected outputs
- `docs/usage_examples.md` for deterministic and live run examples
