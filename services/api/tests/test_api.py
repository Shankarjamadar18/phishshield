"""Integration tests. Require DATABASE_URL pointing at a migrated PostgreSQL database."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_is_liveness_only():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert "dependencies" not in r.json()


def test_ready_reports_database_up():
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json() == {"status": "ready", "dependencies": {"database": {"status": "up", "error": None}}}


def test_ready_returns_503_when_database_down(monkeypatch):
    from app.api import routes

    def boom():
        raise ConnectionError("db down")

    monkeypatch.setattr(routes, "check_db", boom)
    r = client.get("/ready")
    assert r.status_code == 503
    assert r.json()["status"] == "not_ready"
    assert r.json()["dependencies"]["database"]["status"] == "down"


def test_create_scan_is_persisted_without_fake_verdict():
    r = client.post("/api/v1/scans", json={"scan_type": "url", "input_value": "http://example.com"})
    assert r.status_code == 201
    created = r.json()
    assert created["status"] == "pending"
    assert created["verdict"] is None and created["risk_score"] is None
    ids = [s["id"] for s in client.get("/api/v1/scans").json()]
    assert created["id"] in ids


def test_rejects_unknown_scan_type():
    r = client.post("/api/v1/scans", json={"scan_type": "fax", "input_value": "x"})
    assert r.status_code == 422


def test_rejects_empty_input():
    r = client.post("/api/v1/scans", json={"scan_type": "url", "input_value": ""})
    assert r.status_code == 422
