"""Contract-level API tests: real SQLite file, real HTTP handlers, simulated accounts."""
import json

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.sqlite3"))
    with TestClient(app) as testing_client:
        yield testing_client


def make_doc(client, title="My test document"):
    response = client.post("/api/documents", json={"title": title})
    assert response.status_code == 201, response.text
    return response.json()["document"]


def switch(client, user):
    response = client.post("/api/session", json={"user_id": user})
    assert response.status_code == 200, response.text


def test_seeded_dashboard_has_owned_and_shared_docs(client):
    result = client.get("/api/documents")
    assert result.status_code == 200
    docs = result.json()["documents"]
    assert any(d["role"] == "owner" for d in docs)
    assert any(d["role"] == "viewer" for d in docs)
    assert client.get("/healthz").json() == {"status": "ok", "storage": "sqlite"}


def test_create_rename_save_format_reopen_and_revision_conflict(client):
    doc = make_doc(client)
    delta = {"ops": [
        {"insert": "A formatted heading"},
        {"insert": "\n", "attributes": {"header": 1}},
        {"insert": "Important", "attributes": {"bold": True}},
        {"insert": " and normal text\n"},
        {"insert": "First item"},
        {"insert": "\n", "attributes": {"list": "bullet"}},
    ]}
    response = client.patch(f"/api/documents/{doc['id']}", json={"revision": 1, "title": "Renamed", "delta": delta})
    assert response.status_code == 200, response.text
    assert response.json()["document"]["revision"] == 2
    assert client.patch(f"/api/documents/{doc['id']}", json={"revision": 1, "title": "Overwriting stale version"}).status_code == 409
    reread = client.get(f"/api/documents/{doc['id']}").json()["document"]
    assert reread["title"] == "Renamed"
    assert reread["delta"] == delta
    # Persistence independent of in-process objects, backed by the SQLite file.
    assert client.app.state.db.one("SELECT title FROM documents WHERE id=?", doc["id"])["title"] == "Renamed"


def test_share_edit_revoke_enforces_backend_access(client):
    doc = make_doc(client)
    switch(client, "noah")
    assert client.get(f"/api/documents/{doc['id']}").status_code == 404
    assert client.patch(f"/api/documents/{doc['id']}",json={"revision":1,"title":"Forbidden"}).status_code == 404
    switch(client, "maya")
    share = client.post(f"/api/documents/{doc['id']}/shares", json={"email":"noah@demo.scribe", "role":"editor"})
    assert share.status_code == 200
    switch(client, "noah")
    assert client.get(f"/api/documents/{doc['id']}").json()["document"]["role"] == "editor"
    assert client.patch(f"/api/documents/{doc['id']}",json={"revision":1,"title":"Shared edit"}).status_code == 200
    assert client.post(f"/api/documents/{doc['id']}/shares",json={"email":"maya@demo.scribe","role":"viewer"}).status_code == 403
    assert client.delete(f"/api/documents/{doc['id']}").status_code == 403
    switch(client, "maya")
    assert client.delete(f"/api/documents/{doc['id']}/shares/noah").status_code == 204
    switch(client, "noah")
    assert client.get(f"/api/documents/{doc['id']}").status_code == 404


def test_viewer_cannot_edit_but_accesses_document(client):
    doc = make_doc(client)
    client.post(f"/api/documents/{doc['id']}/shares",json={"email":"noah@demo.scribe","role":"viewer"})
    switch(client, "noah")
    assert client.get(f"/api/documents/{doc['id']}").json()["document"]["role"] == "viewer"
    assert client.patch(f"/api/documents/{doc['id']}",json={"revision":1,"title":"No"}).status_code == 403
    assert any(x["id"]==doc["id"] and x["role"] == "viewer" for x in client.get("/api/documents").json()["documents"])


def test_import_markdown_and_plain_text(client):
    md = b"# Project plan\n- First **bold** item\n1. One more\n"
    response = client.post("/api/import", files={"file": ("plan.md", md, "text/markdown")})
    assert response.status_code == 201, response.text
    delta = response.json()["document"]["delta"]
    assert {"insert":"\n","attributes":{"header":1}} in delta["ops"]
    assert {"insert":"bold","attributes":{"bold":True}} in delta["ops"]
    assert {"insert":"\n","attributes":{"list":"bullet"}} in delta["ops"]
    response = client.post("/api/import",files={"file":("notes.txt",b"hello\nworld", "text/plain")})
    assert response.status_code == 201
    assert response.json()["document"]["title"] == "notes"
    assert client.post("/api/import",files={"file":("image.png",b"a","image/png")}).status_code == 422
    assert client.post("/api/import",files={"file":("big.txt",b"x" * (512 * 1024 + 1),"text/plain")}).status_code == 413


def test_validates_untrusted_editor_input(client):
    doc = make_doc(client)
    assert client.patch(f"/api/documents/{doc['id']}",json={"revision":1,"delta":{"ops":[{"insert":{"image":"evil"}}]}}).status_code == 422
    assert client.patch(f"/api/documents/{doc['id']}",json={"revision":1,"delta":{"ops":[{"insert":"hi", "attributes":{"link":"javascript:alert(1)"}}]}}).status_code == 422
    assert client.patch(f"/api/documents/{doc['id']}",json={"revision":1,"title":" "}).status_code == 422
    assert client.post(f"/api/documents/{doc['id']}/shares",json={"email":"unknown@example.com"}).status_code == 404
