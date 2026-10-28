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


def test_non_url_scan_is_persisted_without_fake_verdict():
    r = client.post("/api/v1/scans", json={"scan_type": "text", "input_value": "Please check this message"})
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


def test_url_result_is_persisted_with_evidence_not_probability():
    r = client.post("/api/v1/scans", json={"scan_type": "url", "input_value": "https://paypa1.com/login"})
    assert r.status_code == 201
    scan = r.json()
    assert scan["status"] == "completed"
    assert scan["verdict"] == "suspicious"
    assert scan["risk_score"] is None
    assert scan["details"]["detector"] == "url_rules"
    assert scan["details"]["findings"][0]["code"] == "brand_lookalike"
    assert client.get(f'/api/v1/scans/{scan["id"]}').json() == scan
    assert scan in client.get("/api/v1/scans").json()


def test_invalid_url_is_not_stored():
    r = client.post("/api/v1/scans", json={"scan_type": "url", "input_value": "javascript:alert(1)"})
    assert r.status_code == 422


def test_blank_message_is_rejected():
    assert client.post("/api/v1/scans", json={"scan_type": "text", "input_value": "   "}).status_code == 422


def test_missing_scan_returns_404():
    assert client.get("/api/v1/scans/00000000-0000-0000-0000-000000000000").status_code == 404
