"""SQLite metadata store for documents."""

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional


class DocumentStore:
    """SQLite-based metadata store for ingested documents."""

    def __init__(self, db_path: str):
        """Initialize the document store.

        Args:
            db_path: Path to the SQLite database file.
        """
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
        self._db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create the documents table if it doesn't exist."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT,
                    date TEXT,
                    doc_type TEXT,
                    local_path TEXT,
                    ingested_at TEXT NOT NULL,
                    chunk_count INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        """Create a database connection."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_document(
        self,
        source_name: str,
        url: str,
        title: str,
        date: Optional[str] = None,
        doc_type: str = "pdf",
        local_path: Optional[str] = None,
        chunk_count: int = 0,
    ) -> int:
        """Add a document record.

        Args:
            source_name: Name of the source.
            url: URL of the document.
            title: Document title.
            date: Document date.
            doc_type: Type of document.
            local_path: Local file path.
            chunk_count: Number of chunks created.

        Returns:
            The row ID of the inserted document.
        """
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO documents
                    (source_name, url, title, date, doc_type, local_path, ingested_at, chunk_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_name,
                    url,
                    title,
                    date,
                    doc_type,
                    local_path,
                    datetime.utcnow().isoformat(),
                    chunk_count,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def get_documents(self) -> List[Dict]:
        """Get all document records."""
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM documents ORDER BY ingested_at DESC").fetchall()
            return [dict(row) for row in rows]

    def get_documents_by_source(self, source_name: str) -> List[Dict]:
        """Get document records for a specific source."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE source_name = ? ORDER BY ingested_at DESC",
                (source_name,),
            ).fetchall()
            return [dict(row) for row in rows]

    def document_exists(self, url: str) -> bool:
        """Check if a document with the given URL already exists."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM documents WHERE url = ?", (url,)
            ).fetchone()
            return row is not None

    def get_total_count(self) -> int:
        """Get total number of documents."""
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()
            return row["cnt"]
