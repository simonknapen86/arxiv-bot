from __future__ import annotations

from pathlib import Path

from arxiv_bot.storage.sqlite_store import SQLiteStore


def _make_store(tmp_path: Path) -> SQLiteStore:
    """Create a SQLiteStore instance pointed at a temporary database file."""
    db_path = tmp_path / "test_store.sqlite"
    store = SQLiteStore(db_path)
    store.init_schema()
    return store


def test_init_schema_creates_tables(tmp_path: Path) -> None:
    """Initialize schema and assert runs/papers tables exist."""
    store = _make_store(tmp_path)

    with store.connect() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()

    names = {row["name"] for row in rows}
    assert "runs" in names
    assert "papers" in names


def test_run_crud_round_trip(tmp_path: Path) -> None:
    """Create and update a run row, then verify stored values."""
    store = _make_store(tmp_path)
    store.create_run(
        {
            "run_id": "run-001",
            "status": "created",
            "query": "transformers",
            "created_at": "2026-03-28T00:00:00Z",
            "updated_at": "2026-03-28T00:00:00Z",
        }
    )

    created = store.get_run("run-001")
    assert created is not None
    assert created["status"] == "created"

    store.update_run_status("run-001", "running", "2026-03-28T00:10:00Z")
    updated = store.get_run("run-001")
    assert updated is not None
    assert updated["status"] == "running"
    assert updated["updated_at"] == "2026-03-28T00:10:00Z"


def test_paper_upsert_and_list(tmp_path: Path) -> None:
    """Insert and upsert a paper row, then verify latest values are returned."""
    store = _make_store(tmp_path)
    store.create_run(
        {
            "run_id": "run-002",
            "status": "created",
            "query": "attention",
            "created_at": "2026-03-28T00:00:00Z",
            "updated_at": "2026-03-28T00:00:00Z",
        }
    )

    base = {
        "run_id": "run-002",
        "source_link": "https://arxiv.org/abs/1706.03762",
        "title": "Attention Is All You Need",
        "year": 2017,
        "doi": None,
        "arxiv_id": "1706.03762",
        "status": "verified",
        "verified": 1,
        "local_pdf_path": None,
        "bibtex_key": None,
        "summary_paragraph": None,
        "created_at": "2026-03-28T00:00:00Z",
        "updated_at": "2026-03-28T00:00:00Z",
    }
    store.upsert_paper(base)

    updated = dict(base)
    updated["status"] = "downloaded"
    updated["local_pdf_path"] = "artifacts/papers/vaswani_2017_attention.pdf"
    updated["updated_at"] = "2026-03-28T00:15:00Z"
    store.upsert_paper(updated)

    papers = store.list_papers("run-002")
    assert len(papers) == 1
    assert papers[0]["status"] == "downloaded"
    assert papers[0]["local_pdf_path"] == "artifacts/papers/vaswani_2017_attention.pdf"


def test_delete_run_cascades_to_papers(tmp_path: Path) -> None:
    """Delete a run and confirm related papers are removed by cascade."""
    store = _make_store(tmp_path)
    store.create_run(
        {
            "run_id": "run-003",
            "status": "created",
            "query": "nlp",
            "created_at": "2026-03-28T00:00:00Z",
            "updated_at": "2026-03-28T00:00:00Z",
        }
    )
    store.upsert_paper(
        {
            "run_id": "run-003",
            "source_link": "https://example.org/paper",
            "title": "Paper",
            "year": 2020,
            "doi": None,
            "arxiv_id": None,
            "status": "verified",
            "verified": 1,
            "local_pdf_path": None,
            "bibtex_key": None,
            "summary_paragraph": None,
            "created_at": "2026-03-28T00:00:00Z",
            "updated_at": "2026-03-28T00:00:00Z",
        }
    )

    assert len(store.list_papers("run-003")) == 1
    store.delete_run("run-003")
    assert store.get_run("run-003") is None
    assert store.list_papers("run-003") == []
