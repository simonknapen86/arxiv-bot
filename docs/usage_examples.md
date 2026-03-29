# Usage Examples

## 1) Run The Included Pipeline Script
Use this for a quick smoke run that writes artifacts.
```bash
/opt/anaconda3/envs/openai311/bin/python3 scripts/run_pipeline.py
```

## 2) Run A Deterministic Local Pipeline (No Live LLM Needed)
This uses fixture PDF fetching and local BibTeX fallback for stable behavior.
```bash
/opt/anaconda3/envs/openai311/bin/python3 - <<'PY'
from arxiv_bot.models import PipelineInput
from arxiv_bot.orchestrator import PipelineOrchestrator

payload = PipelineInput(
    seed_links=["https://arxiv.org/abs/1706.03762"],
    project_description="Transformer methods overview",
    include_keywords=["transformer", "attention"],
)

records = PipelineOrchestrator(
    use_fixture_pdf_fetcher=True,
    use_inspire_bibtex=False,
).run(payload)

print(f"records={len(records)}")
PY
```

## 3) Run With INSPIRE BibTeX + Live LLM Summaries
Set your OpenAI key first, then use live mode.
```bash
export OPENAI_API_KEY="<your-key>"
/opt/anaconda3/envs/openai311/bin/python3 - <<'PY'
from arxiv_bot.models import PipelineInput
from arxiv_bot.orchestrator import PipelineOrchestrator

payload = PipelineInput(
    seed_links=["https://arxiv.org/abs/1706.03762"],
    project_description="Technical synthesis of transformer scaling trends",
)

records = PipelineOrchestrator(
    use_fixture_pdf_fetcher=False,
    use_inspire_bibtex=True,
).run(payload)

print(f"records={len(records)}")
PY
```

## 4) Inspect Produced Artifacts
```bash
ls -lah artifacts
sed -n '1,80p' artifacts/references.bib
sed -n '1,120p' artifacts/paper_summaries.tex
sed -n '1,120p' artifacts/literature_review.tex
```

## 5) Run Regression Guardrails Before Committing
```bash
/opt/anaconda3/envs/openai311/bin/python3 -m pytest -q -W error
```
