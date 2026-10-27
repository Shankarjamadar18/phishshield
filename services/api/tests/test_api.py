"""Integration tests. Require DATABASE_URL pointing at a migrated PostgreSQL database."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_liveness():
    assert client.get("/health/live").json() == {"status": "ok"}


def test_health_reports_database_up():
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["database"] == "up"


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
