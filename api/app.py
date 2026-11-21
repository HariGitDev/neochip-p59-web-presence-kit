"""NeoChip contact-form backend. POST /api/contact, GET /healthz.

Never logs personal data (ids only). See README.md for env vars.
"""
import asyncio
import hashlib
import ipaddress
import json
import logging
import os
import re
import smtplib
import threading
import time
import urllib.request
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from email.message import EmailMessage

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, ValidationError, field_validator

log = logging.getLogger("contact")

MAX_BODY = 16 * 1024
MIN_FILL_MS = 3000
HOUR, DAY = 3600, 86400
LIMIT_HOUR, LIMIT_DAY = 5, 20
DEFAULT_ORIGINS = (
    "https://neochipsolutions.com,https://www.neochipsolutions.com,"
    "https://testweb.neochipsolutions.com"
)
_CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f  ]")  # all control chars except \t and \n
_HDR_BAD = re.compile(r"[\r\n\x00]")

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

_hits: dict = defaultdict(deque)
_hits_lock = threading.Lock()
_write_lock = threading.Lock()


class Contact(BaseModel):
    name: str
    company: str = ""
    email: EmailStr
    part_number: str = ""
    quantity: str = ""
    message: str
    t: float

    model_config = {"extra": "ignore", "str_strip_whitespace": True}

    @field_validator("name", "company", "part_number", "quantity", mode="after")
    @classmethod
    def _single_line(cls, v: str) -> str:
        if _HDR_BAD.search(v) or _CTRL.search(v):
            raise ValueError("bad characters")
        return v

    @field_validator("message", mode="after")
    @classmethod
    def _msg(cls, v: str) -> str:
        if "\x00" in v:
            raise ValueError("bad characters")
        return v

    @field_validator("name")
    @classmethod
    def _name(cls, v):
        if not v or len(v) > 100:
            raise ValueError("name")
        return v

    @field_validator("company")
    @classmethod
    def _company(cls, v):
        if len(v) > 150:
            raise ValueError("company")
        return v

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        if len(v) > 200:
            raise ValueError("email")
        return v

    @field_validator("part_number")
    @classmethod
    def _pn(cls, v):
        if len(v) > 100:
            raise ValueError("part_number")
        return v

    @field_validator("quantity")
    @classmethod
    def _qty(cls, v):
        if len(v) > 40:
            raise ValueError("quantity")
        return v

    @field_validator("message")
    @classmethod
    def _message(cls, v):
        if not v or len(v) > 4000:
            raise ValueError("message")
        return v


def _err(status: int, msg: str) -> JSONResponse:
    return JSONResponse({"ok": False, "error": msg}, status_code=status)


def _ok() -> JSONResponse:
    return JSONResponse({"ok": True})


def _allowed_origins() -> set:
    raw = os.environ.get("ALLOWED_ORIGINS", DEFAULT_ORIGINS)
    return {o.strip().rstrip("/").lower() for o in raw.split(",") if o.strip()}


def _client_ip(request: Request) -> str:
    cf = request.headers.get("cf-connecting-ip", "").strip()
    if cf:
        try:
            return str(ipaddress.ip_address(cf))
        except ValueError:
            pass
    return request.client.host if request.client else "unknown"


def _rate_limited(ip: str) -> bool:
    now = time.time()
    with _hits_lock:
        q = _hits[ip]
        while q and q[0] <= now - DAY:
            q.popleft()
        if len(q) >= LIMIT_DAY or sum(1 for x in q if x > now - HOUR) >= LIMIT_HOUR:
            return True
        q.append(now)
        if len(_hits) > 50000:  # bound memory
            for k in [k for k, v in _hits.items() if not v or v[-1] <= now - DAY]:
                _hits.pop(k, None)
        return False


def _store(record: dict) -> None:
    d = os.environ.get("DATA_DIR", "/data")
    os.makedirs(d, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False) + "\n"
    with _write_lock:
        with open(os.path.join(d, "submissions.jsonl"), "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())


def _send_email(rec: dict) -> None:
    keys = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "MAIL_FROM", "CONTACT_TO")
    cfg = {k: os.environ.get(k, "") for k in keys}
    if not all(cfg.values()):
        return
    for k in ("CONTACT_TO", "MAIL_FROM", "SMTP_HOST"):
        if re.search(r"[,;\s<>\r\n]", cfg[k]):
            log.error("email skipped: invalid %s", k)
            return
    f = rec["fields"]
    msg = EmailMessage()
    msg["Subject"] = f"New website enquiry {rec['id'][:8]}"
    msg["From"] = cfg["MAIL_FROM"]
    msg["To"] = cfg["CONTACT_TO"]
    if not _HDR_BAD.search(f["email"]):
        msg["Reply-To"] = f["email"]
    msg.set_content(
        f"Name: {f['name']}\nCompany: {f['company']}\nEmail: {f['email']}\n"
        f"Part number: {f['part_number']}\nQuantity: {f['quantity']}\n"
        f"Received: {rec['ts']}\nID: {rec['id']}\n\n{f['message']}\n"
    )
    port = int(cfg["SMTP_PORT"])
    if port == 465:
        s = smtplib.SMTP_SSL(cfg["SMTP_HOST"], port, timeout=15)
    else:
        s = smtplib.SMTP(cfg["SMTP_HOST"], port, timeout=15)
    with s:
        if port != 465:
            s.starttls()
        s.login(cfg["SMTP_USER"], cfg["SMTP_PASSWORD"])
        s.send_message(msg, to_addrs=[cfg["CONTACT_TO"]])


def _ntfy(rec: dict) -> None:
    url = os.environ.get("NTFY_URL", "")
    if not url:
        return
    req = urllib.request.Request(
        url, data=f"New website enquiry {rec['id'][:8]}".encode(), method="POST"
    )
    urllib.request.urlopen(req, timeout=10).close()


def _notify(rec: dict) -> None:
    for fn in (_send_email, _ntfy):
        try:
            fn(rec)
        except Exception as e:  # never fail the request; no personal data in logs
            log.error("notify %s failed for %s: %s", fn.__name__, rec["id"][:8], type(e).__name__)


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.post("/api/contact")
async def contact(request: Request, background: BackgroundTasks):
    origin = request.headers.get("origin")
    if origin is not None and origin.rstrip("/").lower() not in _allowed_origins():
        return _err(403, "Forbidden")

    cl = request.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > MAX_BODY:
        return _err(413, "Request too large")
    body = b""
    async for chunk in request.stream():
        body += chunk
        if len(body) > MAX_BODY:
            return _err(413, "Request too large")

    ip = _client_ip(request)
    if _rate_limited(ip):
        return _err(429, "Too many requests")

    try:
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError
    except ValueError:
        return _err(422, "Invalid request")

    hp = data.get("website")
    if hp not in (None, ""):
        return _ok()  # honeypot: silent drop
    try:
        c = Contact(**{k: v for k, v in data.items() if k in Contact.model_fields})
    except (ValidationError, TypeError):
        return _err(422, "Invalid request")
    if time.time() * 1000 - c.t < MIN_FILL_MS:
        return _ok()  # too fast (or future t): silent drop

    salt = os.environ.get("SALT", "")
    rec = {
        "id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "fields": c.model_dump(exclude={"t"}),
        "ip_hash": hashlib.sha256((ip + salt).encode()).hexdigest(),
    }
    try:
        await asyncio.to_thread(_store, rec)
    except Exception as e:
        log.error("store failed for %s: %s", rec["id"][:8], type(e).__name__)
        return _err(500, "Could not save your request")
    log.info("stored %s", rec["id"])
    background.add_task(_notify, rec)
    return _ok()
