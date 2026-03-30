from __future__ import annotations

import argparse

from arxiv_bot.skills.literature_regenerate import regenerate_literature_review


def _build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for literature-review-only regeneration."""
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate artifacts/literature_review.tex from an existing "
            "artifacts/paper_summaries.tex file."
        )
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Directory containing paper_summaries.tex and references.bib (default: artifacts).",
    )
    parser.add_argument(
        "--project-description",
        default="",
        help="Optional project description passed into synthesis generation.",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM synthesis and force deterministic synthesis from summaries.",
    )
    return parser


def main() -> None:
    """Run literature-synthesis-only regeneration from existing summary artifacts."""
    args = _build_parser().parse_args()
    print(
        "Regenerating literature review "
        f"(artifacts_dir={args.artifacts_dir}, use_llm={not args.no_llm})...",
        flush=True,
    )
    output_path = regenerate_literature_review(
        artifacts_dir=args.artifacts_dir,
        project_description=args.project_description,
        use_llm=not args.no_llm,
    )
    print(f"Literature survey regenerated: {output_path}")


if __name__ == "__main__":
    main()
