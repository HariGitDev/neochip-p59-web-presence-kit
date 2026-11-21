import hashlib
import json
import time
from datetime import datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

import app as contact_api


@pytest.fixture
def client(tmp_path, monkeypatch):
    for key in (*contact_api.SMTP_SETTINGS, "NTFY_URL", "ALLOWED_ORIGINS"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SALT", "test-salt")
    with TestClient(contact_api.create_app()) as instance:
        yield instance


@pytest.fixture
def submission():
    return {
        "name": "Sample Visitor",
        "company": "Sample Company",
        "email": "visitor@example.com",
        "part_number": "NC-100",
        "quantity": "20",
        "message": "Please send a quote.",
        "website": "",
        "t": time.time_ns() // 1_000_000 - 10_000,
    }


def test_success(client, submission, tmp_path):
    assert client.get("/healthz").json() == {"ok": True}
    ip = "203.0.113.42"
    origin = "https://neochipsolutions.com"
    response = client.post(
        "/api/contact", json=submission, headers={"CF-Connecting-IP": ip, "Origin": origin}
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert response.headers["access-control-allow-origin"] == origin
    line, = (tmp_path / "submissions.jsonl").read_text().splitlines()
    entry = json.loads(line)
    assert UUID(entry["id"]).version == 4
    assert datetime.fromisoformat(entry["timestamp"]).utcoffset().total_seconds() == 0
    for field in ("name", "company", "email", "part_number", "quantity", "message"):
        assert entry[field] == submission[field]
    assert entry["ip_hash"] == hashlib.sha256((ip + "test-salt").encode()).hexdigest()
    assert ip not in line


@pytest.mark.parametrize("spam_signal", ["honeypot", "too_fast"])
def test_silent_drop(client, submission, tmp_path, spam_signal):
    if spam_signal == "honeypot":
        submission["website"] = "filled"
    else:
        submission["t"] = time.time_ns() // 1_000_000
    response = client.post("/api/contact", json=submission)
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert not (tmp_path / "submissions.jsonl").exists()


@pytest.mark.parametrize(
    "invalid",
    [
        {"email": "not-an-email"},
        {"name": ""},
        {"message": "x" * 4001},
        {"t": "yesterday"},
    ],
)
def test_validation(client, submission, invalid, tmp_path):
    response = client.post("/api/contact", json=submission | invalid)
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid submission"}
    assert not (tmp_path / "submissions.jsonl").exists()


def test_oversize(client, tmp_path):
    def chunks():
        yield b"x" * 8192
        yield b"x" * 8192
        yield b"x"

    response = client.post("/api/contact", content=chunks())
    assert response.status_code == 413
    assert not (tmp_path / "submissions.jsonl").exists()


def test_hourly_rate_limit(client, submission, tmp_path):
    for _ in range(5):
        assert client.post("/api/contact", json=submission).status_code == 200
    assert client.post("/api/contact", json=submission).status_code == 429
    assert len((tmp_path / "submissions.jsonl").read_text().splitlines()) == 5
    assert client.post(
        "/api/contact", json=submission, headers={"CF-Connecting-IP": "203.0.113.9"}
    ).status_code == 200


def test_daily_rate_limit(monkeypatch):
    limiter = contact_api.RateLimiter()
    for hour in range(4):
        monkeypatch.setattr(contact_api.time, "monotonic", lambda: hour * 3600)
        for _ in range(5):
            assert limiter.allow("client")
    monkeypatch.setattr(contact_api.time, "monotonic", lambda: 4 * 3600)
    assert not limiter.allow("client")
    monkeypatch.setattr(contact_api.time, "monotonic", lambda: 24 * 3600)
    assert limiter.allow("client")


def test_origin_rejection(client, submission, tmp_path):
    headers = {"Origin": "https://unlisted.example"}
    assert client.post("/api/contact", json=submission, headers=headers).status_code == 403
    response = client.options(
        "/api/contact", headers=headers | {"Access-Control-Request-Method": "POST"}
    )
    assert response.status_code == 403
    assert "access-control-allow-origin" not in response.headers
    assert not (tmp_path / "submissions.jsonl").exists()


@pytest.mark.parametrize("field", ["name", "email"])
def test_header_injection(client, submission, tmp_path, field):
    submission[field] += "\r\nBcc: attacker@example.com"
    assert client.post("/api/contact", json=submission).status_code == 422
    assert not (tmp_path / "submissions.jsonl").exists()


def test_storage_failure(client, submission, tmp_path, monkeypatch):
    def fail(_fd):
        raise OSError("storage error")

    assert client.post("/api/contact", json=submission).status_code == 200
    path = tmp_path / "submissions.jsonl"
    original = path.read_bytes()
    monkeypatch.setattr(contact_api.os, "fsync", fail)
    response = client.post("/api/contact", json=submission)
    assert response.status_code == 500
    assert response.json() == {"detail": "Could not store submission"}
    assert path.read_bytes() == original


def test_notification_failure(client, submission, tmp_path, monkeypatch, caplog):
    for key in contact_api.SMTP_SETTINGS:
        monkeypatch.setenv(key, "configured")
    monkeypatch.setenv("NTFY_URL", "https://ntfy.example/test")
    calls = []

    def fail_email(_settings, entry):
        calls.append(entry["id"])
        raise OSError(submission["email"])

    def fail_ntfy(_url, submission_id):
        calls.append(submission_id)
        raise OSError(submission["name"])

    monkeypatch.setattr(contact_api, "send_email", fail_email)
    monkeypatch.setattr(contact_api, "send_ntfy", fail_ntfy)
    response = client.post("/api/contact", json=submission)
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    entry = json.loads((tmp_path / "submissions.jsonl").read_text())
    assert calls == [entry["id"], entry["id"]]
    assert entry["id"] in caplog.text
    assert submission["email"] not in caplog.text
    assert submission["name"] not in caplog.text
