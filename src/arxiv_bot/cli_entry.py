from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from arxiv_bot.models import PipelineInput
from arxiv_bot.orchestrator import PipelineOrchestrator
from arxiv_bot.skills.literature_regenerate import regenerate_literature_review


def _help_text() -> str:
    """Return CLI help text describing the supported invocation modes."""
    return (
        "Usage:\n"
        "  ./arxiv_bot.py -run settings.json   Run full pipeline using settings file\n"
        "  ./arxiv_bot.py -litreview           Regenerate only literature review from summaries\n"
        "  ./arxiv_bot.py -start               Create a template settings.json in current directory\n"
        "  ./arxiv_bot.py -help                Show this help text\n"
    )


def _parser() -> argparse.ArgumentParser:
    """Build argument parser for the top-level arxiv_bot command interface."""
    parser = argparse.ArgumentParser(add_help=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-run", dest="run_settings", metavar="SETTINGS_JSON")
    group.add_argument("-litreview", action="store_true")
    group.add_argument("-start", action="store_true")
    group.add_argument("-help", action="store_true")
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    """Load JSON settings from disk and validate root shape."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("settings file must contain a JSON object")
    return payload


def _target_dir(settings: dict[str, Any], cwd: Path) -> Path:
    """Resolve target directory from settings with current directory fallback."""
    configured = settings.get("target_dir")
    if isinstance(configured, str) and configured.strip():
        return Path(configured).expanduser().resolve()
    return cwd


def _artifacts_dir(settings: dict[str, Any], cwd: Path) -> Path:
    """Resolve artifacts directory rooted in target directory by default."""
    target_dir = _target_dir(settings, cwd=cwd)
    subdir = settings.get("artifacts_subdir")
    if isinstance(subdir, str) and subdir.strip():
        return target_dir / subdir.strip()
    return target_dir / "artifacts"


def _pipeline_input(settings: dict[str, Any]) -> PipelineInput:
    """Build PipelineInput from user settings with sensible defaults."""
    seed_links = settings.get("seed_links", [])
    if not isinstance(seed_links, list) or not all(isinstance(item, str) for item in seed_links):
        raise ValueError("settings.seed_links must be a list of strings")

    description = settings.get("project_description", "")
    if not isinstance(description, str):
        raise ValueError("settings.project_description must be a string")

    include_keywords = settings.get("include_keywords", [])
    exclude_keywords = settings.get("exclude_keywords", [])
    if not isinstance(include_keywords, list) or not all(isinstance(item, str) for item in include_keywords):
        raise ValueError("settings.include_keywords must be a list of strings")
    if not isinstance(exclude_keywords, list) or not all(isinstance(item, str) for item in exclude_keywords):
        raise ValueError("settings.exclude_keywords must be a list of strings")

    return PipelineInput(
        seed_links=seed_links,
        project_description=description,
        include_keywords=include_keywords,
        exclude_keywords=exclude_keywords,
        related_min_relevance_score=float(settings.get("related_min_relevance_score", 0.8)),
        related_min_keyword_overlap=float(settings.get("related_min_keyword_overlap", 0.05)),
    )


def _run_mode(settings_path: Path, cwd: Path) -> int:
    """Execute full pipeline using a settings JSON file."""
    settings = _load_json(settings_path)
    artifacts_dir = _artifacts_dir(settings, cwd=cwd)
    payload = _pipeline_input(settings)

    orchestrator = PipelineOrchestrator(
        use_fixture_pdf_fetcher=bool(settings.get("use_fixture_pdf_fetcher", False)),
        use_inspire_bibtex=bool(settings.get("use_inspire_bibtex", True)),
        use_inspire_related_discovery=bool(settings.get("use_inspire_related_discovery", True)),
        artifacts_dir=artifacts_dir,
    )
    records = orchestrator.run(payload)
    print(f"Pipeline completed. Records exported: {len(records)}")
    print(f"Artifacts directory: {artifacts_dir}")
    return 0


def _litreview_mode(cwd: Path) -> int:
    """Regenerate only literature review using local summaries and optional settings."""
    default_settings_path = cwd / "settings.json"
    settings: dict[str, Any] = {}
    if default_settings_path.exists():
        settings = _load_json(default_settings_path)

    artifacts_dir = _artifacts_dir(settings, cwd=cwd)
    project_description = ""
    raw_description = settings.get("project_description")
    if isinstance(raw_description, str):
        project_description = raw_description
    use_llm = bool(settings.get("litreview_use_llm", True))

    output_path = regenerate_literature_review(
        artifacts_dir=artifacts_dir,
        project_description=project_description,
        use_llm=use_llm,
    )
    print(f"Literature review regenerated: {output_path}")
    return 0


def _template_settings(cwd: Path) -> dict[str, Any]:
    """Return starter settings template for first-time users."""
    return {
        "seed_links": [
            "https://arxiv.org/abs/2506.11191",
            "https://arxiv.org/abs/1706.03762",
        ],
        "project_description": "Describe your project scope here.",
        "include_keywords": ["dark matter", "direct detection"],
        "exclude_keywords": [],
        "target_dir": str(cwd),
        "artifacts_subdir": "artifacts",
        "use_fixture_pdf_fetcher": False,
        "use_inspire_bibtex": True,
        "use_inspire_related_discovery": True,
        "related_min_relevance_score": 0.8,
        "related_min_keyword_overlap": 0.05,
        "litreview_use_llm": True,
    }


def _start_mode(cwd: Path) -> int:
    """Create template settings.json in current directory for user editing."""
    target = cwd / "settings.json"
    if target.exists():
        print(f"settings.json already exists: {target}")
        return 0
    target.write_text(json.dumps(_template_settings(cwd), indent=2), encoding="utf-8")
    print(f"Created template settings file: {target}")
    return 0


def main(argv: list[str] | None = None, cwd: Path | None = None) -> int:
    """Dispatch CLI execution modes for arxiv_bot top-level command."""
    resolved_cwd = (cwd or Path.cwd()).resolve()
    args = _parser().parse_args(argv)

    if args.help:
        print(_help_text())
        return 0
    if args.start:
        return _start_mode(resolved_cwd)
    if args.litreview:
        return _litreview_mode(resolved_cwd)
    if args.run_settings:
        settings_path = Path(args.run_settings).expanduser()
        if not settings_path.is_absolute():
            settings_path = (resolved_cwd / settings_path).resolve()
        if not settings_path.exists():
            raise FileNotFoundError(f"settings file not found: {settings_path}")
        return _run_mode(settings_path, cwd=resolved_cwd)

    print(_help_text())
    return 1
