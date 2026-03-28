# Runbook (Draft)

## Local Development
1. Use the pinned `openai311` interpreter by default (reliable in this repo shell context).
2. Run tests and keep the suite green after each milestone.
3. Implement one skill at a time with fixtures.

## Environment Commands
```bash
# Default path (pinned openai311 interpreter)
/opt/anaconda3/envs/openai311/bin/python --version
/opt/anaconda3/envs/openai311/bin/python -m pytest -q

# Optional: if your shell resolves a newer base python3
python3 --version
python3 -m pytest -q
```

## Suggested Milestone Order
1. Contracts and schema validation
2. Verification and downloader
3. BibTeX generation
4. Per-paper summaries
5. Literature synthesis
6. QA audit and manifests

## Definition of Done (MVP)
- All required artifacts are generated.
- Every included paper is verified and has a local PDF.
- CI checks pass.
