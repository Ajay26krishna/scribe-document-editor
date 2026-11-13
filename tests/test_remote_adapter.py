"""Unit-test the remote protocol serialization without requiring a Turso account."""
import io
import json

from storage import Storage


def test_turso_http_adapter_binds_parameters_and_decodes_rows(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://demo-example.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "test-secret-token")
    seen = {}

    class FakeResponse(io.BytesIO):
        pass

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        seen["headers"] = dict(req.header_items())
        seen["body"] = json.loads(req.data)
        return FakeResponse(json.dumps({
            "results": [
                {"type": "ok", "response": {"type": "execute", "result": {
                    "cols": [{"name": "id"}, {"name": "name"}],
                    "rows": [[{"type": "integer", "value": "7"}, {"type": "text", "value": "Maya"}]],
                    "affected_row_count": 0,
                }}},
                {"type": "ok", "response": {"type": "close"}},
            ],
        }).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    db = Storage()
    result = db.all("SELECT id,name FROM users WHERE id=? AND name=?", 7, "Maya")
    assert result == [{"id": 7, "name": "Maya"}]
    assert seen["url"] == "https://demo-example.turso.io/v2/pipeline"
    assert seen["headers"]["Authorization"] == "Bearer test-secret-token"
    statement = seen["body"]["requests"][0]["stmt"]
    assert statement["sql"].endswith("id=? AND name=?")
    assert statement["args"] == [{"type":"integer", "value":"7"}, {"type":"text", "value":"Maya"}]
