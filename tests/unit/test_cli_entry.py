import json
from pathlib import Path

from arxiv_bot import cli_entry


def test_help_mode_prints_usage(capsys) -> None:
    """Print supported command modes in help output."""
    exit_code = cli_entry.main(["-help"])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "./arxiv_bot.py -run settings.json" in captured
    assert "./arxiv_bot.py -litreview" in captured
    assert "./arxiv_bot.py -start" in captured


def test_start_mode_creates_settings_template(tmp_path: Path) -> None:
    """Create settings.json template in current working directory."""
    exit_code = cli_entry.main(["-start"], cwd=tmp_path)
    assert exit_code == 0
    settings_path = tmp_path / "settings.json"
    assert settings_path.exists()
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "seed_links" in payload
    assert "project_description" in payload
    assert payload["target_dir"] == str(tmp_path)


def test_litreview_mode_uses_local_settings(monkeypatch, tmp_path: Path) -> None:
    """Read project settings and regenerate literature review from summaries."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "project_description": "Regenerate from edited summaries",
                "target_dir": str(tmp_path),
                "artifacts_subdir": "my_artifacts",
                "litreview_use_llm": False,
            }
        ),
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    def _fake_regenerate(
        artifacts_dir: str | Path = "artifacts",
        project_description: str = "",
        use_llm: bool = True,
        llm_client=None,
    ) -> Path:
        """Capture regeneration invocation and return deterministic output path."""
        _ = llm_client
        captured["artifacts_dir"] = Path(artifacts_dir)
        captured["project_description"] = project_description
        captured["use_llm"] = use_llm
        return Path(artifacts_dir) / "literature_review.tex"

    monkeypatch.setattr(cli_entry, "regenerate_literature_review", _fake_regenerate)
    exit_code = cli_entry.main(["-litreview"], cwd=tmp_path)
    assert exit_code == 0
    assert captured["artifacts_dir"] == tmp_path / "my_artifacts"
    assert captured["project_description"] == "Regenerate from edited summaries"
    assert captured["use_llm"] is False


def test_run_mode_builds_pipeline_from_settings(monkeypatch, tmp_path: Path) -> None:
    """Build PipelineInput and orchestrator flags from settings JSON."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "seed_links": ["https://arxiv.org/abs/1706.03762"],
                "project_description": "Test project",
                "include_keywords": ["transformer"],
                "target_dir": str(tmp_path),
                "artifacts_subdir": "outputs",
                "use_fixture_pdf_fetcher": True,
                "use_inspire_bibtex": False,
                "use_inspire_related_discovery": False,
            }
        ),
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    class FakeOrchestrator:
        """Capture init args and run payload for CLI run-mode tests."""

        def __init__(
            self,
            use_fixture_pdf_fetcher: bool,
            use_inspire_bibtex: bool,
            use_inspire_related_discovery: bool,
            artifacts_dir: str | Path,
        ) -> None:
            """Capture constructor options passed by CLI."""
            captured["fixture"] = use_fixture_pdf_fetcher
            captured["inspire_bibtex"] = use_inspire_bibtex
            captured["related"] = use_inspire_related_discovery
            captured["artifacts_dir"] = Path(artifacts_dir)

        def run(self, payload) -> list[object]:
            """Capture run payload and return one fake record."""
            captured["payload_seed_links"] = payload.seed_links
            captured["payload_description"] = payload.project_description
            captured["payload_keywords"] = payload.include_keywords
            return [object()]

    monkeypatch.setattr(cli_entry, "PipelineOrchestrator", FakeOrchestrator)
    exit_code = cli_entry.main(["-run", "settings.json"], cwd=tmp_path)
    assert exit_code == 0
    assert captured["fixture"] is True
    assert captured["inspire_bibtex"] is False
    assert captured["related"] is False
    assert captured["artifacts_dir"] == tmp_path / "outputs"
    assert captured["payload_seed_links"] == ["https://arxiv.org/abs/1706.03762"]
    assert captured["payload_description"] == "Test project"
    assert captured["payload_keywords"] == ["transformer"]
