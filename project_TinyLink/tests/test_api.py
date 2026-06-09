import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("TINYLINK_DB", str(db_file))
    # re-import after env is set so DB path picks up the fixture
    import importlib

    import backend.db as db_module
    importlib.reload(db_module)
    import backend.main as main_module
    importlib.reload(main_module)

    return TestClient(main_module.app)


def test_shorten_returns_code(client):
    res = client.post("/api/shorten", json={"long": "https://example.com/"})
    assert res.status_code == 200
    data = res.json()
    assert data["code"]
    assert data["long"] == "https://example.com/"
    assert data["short"].endswith("/" + data["code"])


def test_redirect_returns_302(client):
    res = client.post("/api/shorten", json={"long": "https://example.com/x"})
    code = res.json()["code"]
    follow = client.get(f"/{code}", follow_redirects=False)
    assert follow.status_code == 302
    assert follow.headers["location"] == "https://example.com/x"


def test_unknown_code_404(client):
    res = client.get("/zzzzz", follow_redirects=False)
    assert res.status_code == 404


def test_bad_url_rejected(client):
    res = client.post("/api/shorten", json={"long": "not a url"})
    assert res.status_code == 422


def test_meta_lookup(client):
    code = client.post("/api/shorten", json={"long": "https://example.com/m"}).json()["code"]
    meta = client.get(f"/api/links/{code}")
    assert meta.status_code == 200
    assert meta.json()["long"] == "https://example.com/m"
