from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class SQLiteStore:
    """Provide schema management and CRUD operations for run and paper state."""

    def __init__(self, db_path: str | Path) -> None:
        """Create a SQLite store bound to the provided database path."""
        self.db_path = str(db_path)

    def connect(self) -> sqlite3.Connection:
        """Open a SQLite connection with row access by column name."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_schema(self) -> None:
        """Create runs and papers tables plus indexes if they do not exist."""
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    query TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS papers (
                    paper_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    source_link TEXT NOT NULL,
                    title TEXT,
                    year INTEGER,
                    doi TEXT,
                    arxiv_id TEXT,
                    status TEXT NOT NULL,
                    verified INTEGER NOT NULL DEFAULT 0,
                    local_pdf_path TEXT,
                    bibtex_key TEXT,
                    summary_paragraph TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES runs(run_id) ON DELETE CASCADE,
                    UNIQUE(run_id, source_link)
                );

                CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
                CREATE INDEX IF NOT EXISTS idx_papers_run_id ON papers(run_id);
                CREATE INDEX IF NOT EXISTS idx_papers_status ON papers(status);
                """
            )

    def create_run(self, run: dict[str, Any]) -> None:
        """Insert a run row into storage."""
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (run_id, status, query, created_at, updated_at)
                VALUES (:run_id, :status, :query, :created_at, :updated_at)
                """,
                run,
            )

    def update_run_status(self, run_id: str, status: str, updated_at: str) -> None:
        """Update status metadata for an existing run."""
        with self.connect() as conn:
            conn.execute(
                """
                UPDATE runs
                SET status = :status, updated_at = :updated_at
                WHERE run_id = :run_id
                """,
                {"run_id": run_id, "status": status, "updated_at": updated_at},
            )

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Fetch a run by id and return it as a plain dictionary."""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        return dict(row) if row else None

    def upsert_paper(self, paper: dict[str, Any]) -> None:
        """Insert or update a paper row keyed by run_id and source_link."""
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO papers (
                    run_id,
                    source_link,
                    title,
                    year,
                    doi,
                    arxiv_id,
                    status,
                    verified,
                    local_pdf_path,
                    bibtex_key,
                    summary_paragraph,
                    created_at,
                    updated_at
                )
                VALUES (
                    :run_id,
                    :source_link,
                    :title,
                    :year,
                    :doi,
                    :arxiv_id,
                    :status,
                    :verified,
                    :local_pdf_path,
                    :bibtex_key,
                    :summary_paragraph,
                    :created_at,
                    :updated_at
                )
                ON CONFLICT(run_id, source_link)
                DO UPDATE SET
                    title = excluded.title,
                    year = excluded.year,
                    doi = excluded.doi,
                    arxiv_id = excluded.arxiv_id,
                    status = excluded.status,
                    verified = excluded.verified,
                    local_pdf_path = excluded.local_pdf_path,
                    bibtex_key = excluded.bibtex_key,
                    summary_paragraph = excluded.summary_paragraph,
                    updated_at = excluded.updated_at
                """,
                paper,
            )

    def list_papers(self, run_id: str) -> list[dict[str, Any]]:
        """List papers for a run ordered by insertion id."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM papers WHERE run_id = ? ORDER BY paper_id ASC",
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_run(self, run_id: str) -> None:
        """Delete a run and cascade-delete associated papers."""
        with self.connect() as conn:
            conn.execute("DELETE FROM runs WHERE run_id = ?", (run_id,))
