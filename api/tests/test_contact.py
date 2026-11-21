import json
import os
import sys
import time

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import app as appmod  # noqa: E402

OK_ORIGIN = "https://neochipsolutions.com"
_ip = [0]


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SALT", "s")
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "MAIL_FROM", "CONTACT_TO", "NTFY_URL"):
        monkeypatch.delenv(k, raising=False)
    appmod._hits.clear()
    return tmp_path


@pytest.fixture
def client(env):
    return TestClient(appmod.app)


def fresh_ip():
    _ip[0] += 1
    return {"CF-Connecting-IP": f"203.0.113.{_ip[0] % 250 + 1}"}


def payload(**kw):
    d = {
        "name": "Jane Doe", "email": "jane@example.com", "part_number": "STM32F407VGT6",
        "quantity": "2,500", "message": "Need a quote.", "website": "",
        "t": int(time.time() * 1000) - 10_000,
    }
    d.update(kw)
    return d


def post(client, data=None, headers=None, **kw):
    h = {"Origin": OK_ORIGIN, **fresh_ip(), **(headers or {})}
    return client.post("/api/contact", json=data if data is not None else payload(), headers=h, **kw)


def lines(env):
    p = env / "submissions.jsonl"
    return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []


def test_healthz(client):
    assert client.get("/healthz").json() == {"ok": True}


def test_success_stores_line(client, env):
    r = post(client)
    assert r.status_code == 200 and r.json() == {"ok": True}
    rows = lines(env)
    assert len(rows) == 1
    row = rows[0]
    assert row["fields"]["email"] == "jane@example.com" and row["fields"]["part_number"] == "STM32F407VGT6"
    assert "id" in row and "ts" in row and len(row["ip_hash"]) == 64
    assert "203.0.113" not in json.dumps(row)  # raw IP never stored


def test_honeypot_drops_silently(client, env):
    r = post(client, payload(website="http://spam"))
    assert r.status_code == 200 and r.json() == {"ok": True}
    assert lines(env) == []


def test_too_fast_drops_silently(client, env):
    r = post(client, payload(t=int(time.time() * 1000) - 500))
    assert r.status_code == 200 and r.json() == {"ok": True}
    assert lines(env) == []


@pytest.mark.parametrize("bad", [
    {"name": ""}, {"email": "not-an-email"}, {"message": ""}, {"name": "x" * 101},
    {"message": "x" * 4001}, {"quantity": "9" * 41}, {"part_number": "p" * 101},
    {"email": "a" * 195 + "@example.com"}, {"t": "abc"},
])
def test_validation_422(client, env, bad):
    r = post(client, payload(**bad))
    assert r.status_code == 422 and lines(env) == []


def test_missing_field_422(client):
    d = payload()
    del d["message"]
    assert post(client, d).status_code == 422


def test_413_large_body(client, env):
    r = post(client, payload(message="x" * 20000))
    assert r.status_code == 413 and lines(env) == []


def test_rate_limit_429(client):
    h = {"CF-Connecting-IP": "198.51.100.7"}
    codes = [client.post("/api/contact", json=payload(), headers={"Origin": OK_ORIGIN, **h}).status_code
             for _ in range(7)]
    assert codes[:5] == [200] * 5 and codes[5:] == [429, 429]


def test_rate_limit_falls_back_to_peer_and_ignores_bad_header(client):
    codes = [client.post("/api/contact", json=payload(),
                         headers={"Origin": OK_ORIGIN, "CF-Connecting-IP": "garbage"}).status_code
             for _ in range(6)]
    assert codes[-1] == 429


def test_origin_rejected(client, env):
    r = post(client, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403 and lines(env) == []


def test_no_origin_header_allowed(client):
    r = client.post("/api/contact", json=payload(), headers=fresh_ip())
    assert r.status_code == 200


def test_no_cors_wildcard(client):
    r = post(client)
    assert r.headers.get("access-control-allow-origin") != "*"


@pytest.mark.parametrize("field", ["name", "email", "part_number", "quantity", "company"])
def test_header_injection_rejected(client, env, field):
    r = post(client, payload(**{field: "a@example.com\r\nBcc: evil@example.com"}))
    assert r.status_code == 422 and lines(env) == []


def test_storage_failure_500(client, monkeypatch):
    def boom(rec):
        raise OSError("disk full")
    monkeypatch.setattr(appmod, "_store", boom)
    r = post(client)
    assert r.status_code == 500 and r.json()["ok"] is False


def test_notification_failure_does_not_fail(client, env, monkeypatch):
    monkeypatch.setenv("NTFY_URL", "http://127.0.0.1:9/x")
    for k, v in dict(SMTP_HOST="127.0.0.1", SMTP_PORT="9", SMTP_USER="u", SMTP_PASSWORD="p",
                     MAIL_FROM="from@example.com", CONTACT_TO="to@example.com").items():
        monkeypatch.setenv(k, v)

    def boom(*a, **k):
        raise RuntimeError("down")
    monkeypatch.setattr(appmod.smtplib, "SMTP", boom)
    monkeypatch.setattr(appmod.urllib.request, "urlopen", boom)
    r = post(client)
    assert r.status_code == 200 and len(lines(env)) == 1


def test_email_single_recipient_and_ntfy_no_pii(client, monkeypatch):
    sent, posted = [], []

    class FakeSMTP:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def starttls(self): pass
        def login(self, u, p): pass
        def send_message(self, msg, to_addrs=None):
            sent.append((msg, to_addrs))

    class Resp:
        def close(self): pass

    monkeypatch.setattr(appmod.smtplib, "SMTP", FakeSMTP)
    monkeypatch.setattr(appmod.urllib.request, "urlopen", lambda req, timeout=0: posted.append(req) or Resp())
    for k, v in dict(SMTP_HOST="smtp.example.com", SMTP_PORT="587", SMTP_USER="u", SMTP_PASSWORD="p",
                     MAIL_FROM="from@example.com", CONTACT_TO="to@example.com",
                     NTFY_URL="https://ntfy.example/topic").items():
        monkeypatch.setenv(k, v)
    assert post(client).status_code == 200
    msg, to = sent[0]
    assert to == ["to@example.com"] and msg["To"] == "to@example.com" and msg["Reply-To"] == "jane@example.com"
    body = posted[0].data.decode()
    assert body.startswith("New website enquiry ") and "jane" not in body.lower()


def test_multi_recipient_contact_to_skips_email(client, monkeypatch):
    sent = []
    monkeypatch.setattr(appmod.smtplib, "SMTP", lambda *a, **k: sent.append(1))
    for k, v in dict(SMTP_HOST="h", SMTP_PORT="587", SMTP_USER="u", SMTP_PASSWORD="p",
                     MAIL_FROM="from@example.com", CONTACT_TO="a@example.com,b@example.com").items():
        monkeypatch.setenv(k, v)
    assert post(client).status_code == 200 and sent == []


def test_logs_contain_no_personal_data(client, caplog):
    caplog.set_level("DEBUG")
    post(client, payload(name="Zed Unique", message="secret-message-xyz"))
    text = caplog.text
    assert "Zed" not in text and "jane@example.com" not in text and "secret-message" not in text
