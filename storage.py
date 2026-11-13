"""Minimal SQLite-compatible persistence: local SQLite or remote Turso Hrana HTTP.

All queries use parameter binding. Production database credentials stay server-side.
"""
from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class StorageError(RuntimeError):
    pass


class Storage:
    def __init__(self, local_path: str | None = None):
        self.remote_url = os.getenv("TURSO_DATABASE_URL", "").strip()
        self.token = os.getenv("TURSO_AUTH_TOKEN", "").strip()
        self.local_path = Path(local_path or os.getenv("DATABASE_PATH", "data/scribe.sqlite3"))
        if self.remote_url:
            if not self.token:
                raise StorageError("TURSO_AUTH_TOKEN is required with TURSO_DATABASE_URL")
            if self.remote_url.startswith("libsql://"):
                self.remote_url = "https://" + self.remote_url.removeprefix("libsql://")
            if not self.remote_url.startswith("https://"):
                raise StorageError("TURSO_DATABASE_URL must be https:// or libsql://")
            self.remote_url = self.remote_url.rstrip("/")
        else:
            self.local_path.parent.mkdir(parents=True, exist_ok=True)

    def _local(self, sql: str, params: tuple[Any, ...]) -> tuple[list[dict], int]:
        with sqlite3.connect(self.local_path, timeout=20) as con:
            con.row_factory = sqlite3.Row
            con.execute("PRAGMA foreign_keys=ON")
            cursor = con.execute(sql, params)
            rows = [dict(row) for row in cursor.fetchall()] if cursor.description else []
            count = cursor.rowcount
            con.commit()
            return rows, count

    @staticmethod
    def _param(value: Any) -> dict[str, str]:
        if value is None:
            return {"type": "null"}
        if isinstance(value, bool):
            return {"type": "integer", "value": str(int(value))}
        if isinstance(value, int):
            return {"type": "integer", "value": str(value)}
        if isinstance(value, float):
            return {"type": "float", "value": repr(value)}
        return {"type": "text", "value": str(value)}

    def _remote(self, sql: str, params: tuple[Any, ...]) -> tuple[list[dict], int]:
        request_body = {
            "baton": None,
            "requests": [
                {"type": "execute", "stmt": {"sql": sql, "args": [self._param(v) for v in params], "want_rows": True}},
                {"type": "close"},
            ],
        }
        request = urllib.request.Request(
            self.remote_url + "/v2/pipeline",
            data=json.dumps(request_body).encode("utf-8"),
            method="POST",
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                result = json.load(response)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise StorageError("Unable to reach the hosted database") from exc
        item = result["results"][0]
        if item["type"] != "ok":
            raise StorageError(item.get("error", {}).get("message", "Database query failed"))
        payload = item["response"]["result"]
        cols = [col["name"] for col in payload.get("cols", [])]
        rows = [
            {name: (None if cell["type"] == "null" else int(cell["value"]) if cell["type"] == "integer" else float(cell["value"]) if cell["type"] == "float" else cell.get("value")) for name, cell in zip(cols, cells)}
            for cells in payload.get("rows", [])
        ]
        return rows, payload.get("affected_row_count", 0)

    def run(self, sql: str, *params: Any) -> tuple[list[dict], int]:
        if self.remote_url:
            return self._remote(sql, params)
        return self._local(sql, params)

    def all(self, sql: str, *params: Any) -> list[dict]:
        return self.run(sql, *params)[0]

    def one(self, sql: str, *params: Any) -> dict | None:
        rows = self.all(sql, *params)
        return rows[0] if rows else None

    def change(self, sql: str, *params: Any) -> int:
        return self.run(sql, *params)[1]


SCHEMA = [
    """CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE
    )""",
    """CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        owner_id TEXT NOT NULL REFERENCES users(id),
        title TEXT NOT NULL,
        delta_json TEXT NOT NULL,
        revision INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS shares (
        doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        user_id TEXT NOT NULL REFERENCES users(id),
        role TEXT NOT NULL CHECK (role IN ('viewer', 'editor')),
        PRIMARY KEY (doc_id, user_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_documents_owner ON documents(owner_id)",
    "CREATE INDEX IF NOT EXISTS idx_shares_user ON shares(user_id)",
    """CREATE TABLE IF NOT EXISTS document_versions (
        doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        revision INTEGER NOT NULL,
        title TEXT NOT NULL,
        delta_json TEXT NOT NULL,
        saved_at TEXT NOT NULL,
        PRIMARY KEY(doc_id, revision)
    )""",
    # A trigger keeps the document and its version in the same SQLite statement/transaction.
    """CREATE TRIGGER IF NOT EXISTS document_versions_on_insert
        AFTER INSERT ON documents
        BEGIN
            INSERT INTO document_versions(doc_id,revision,title,delta_json,saved_at)
            VALUES(NEW.id,NEW.revision,NEW.title,NEW.delta_json,NEW.updated_at);
        END""",
    """CREATE TRIGGER IF NOT EXISTS document_versions_on_update
        AFTER UPDATE ON documents
        BEGIN
            INSERT INTO document_versions(doc_id,revision,title,delta_json,saved_at)
            VALUES(NEW.id,NEW.revision,NEW.title,NEW.delta_json,NEW.updated_at);
            DELETE FROM document_versions
            WHERE doc_id=NEW.id AND revision < NEW.revision-29;
        END""",
]



def initialize(db: Storage) -> None:
    from datetime import datetime, timezone
    from uuid import uuid4

    for statement in SCHEMA:
        db.change(statement)
    # Zero-downtime upgrade of an existing SQLite or Turso database: its current
    # documents become the first available snapshot; earlier states cannot be recovered.
    db.change("""INSERT OR IGNORE INTO document_versions(doc_id,revision,title,delta_json,saved_at)
                 SELECT id,revision,title,delta_json,updated_at FROM documents""")
    db.change("INSERT OR IGNORE INTO users(id,name,email) VALUES(?,?,?)", "maya", "Maya Chen", "maya@demo.scribe")
    db.change("INSERT OR IGNORE INTO users(id,name,email) VALUES(?,?,?)", "noah", "Noah Patel", "noah@demo.scribe")
    if not db.one("SELECT id FROM documents LIMIT 1"):
        now = datetime.now(timezone.utc).isoformat()
        own_id, shared_id = str(uuid4()), str(uuid4())
        welcome_delta = {"ops": [
            {"insert": "Welcome to Scribe\n", "attributes": {"header": 1}},
            {"insert": "A calmer place to write, organize, and share work.\n"},
            {"insert": "Try creating a document, importing Markdown, or sharing this page with Noah.\n"},
            {"insert": "Tip: ", "attributes": {"bold": True}},
            {"insert": "Formatting is preserved when you reopen your document.\n"},
        ]}
        shared_delta = {"ops": [
            {"insert": "Team weekly planning\n", "attributes": {"header": 1}},
            {"insert": "This document belongs to Noah and is shared with Maya as a viewer.\n"},
            {"insert": "Switch accounts from the top-right to explore access permissions.\n"},
        ]}
        db.change("INSERT INTO documents(id,owner_id,title,delta_json,revision,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                  own_id, "maya", "Welcome to Scribe", json.dumps(welcome_delta), 1, now, now)
        db.change("INSERT INTO documents(id,owner_id,title,delta_json,revision,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                  shared_id, "noah", "Team weekly planning", json.dumps(shared_delta), 1, now, now)
        db.change("INSERT INTO shares(doc_id,user_id,role) VALUES(?,?,?)", shared_id, "maya", "viewer")
