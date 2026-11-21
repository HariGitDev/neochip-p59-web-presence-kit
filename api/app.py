import hashlib
import json
import logging
import os
import smtplib
import ssl
import time
from collections import OrderedDict, deque
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from threading import Lock
from urllib.request import Request as OutboundRequest, urlopen
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field, StrictInt
from starlette.concurrency import run_in_threadpool

BODY_LIMIT = 16 * 1024
HOUR = 3600
DAY = 24 * HOUR
DEFAULT_ORIGINS = (
    "https://neochipsolutions.com,https://www.neochipsolutions.com,"
    "https://testweb.neochipsolutions.com"
)
SMTP_SETTINGS = (
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "MAIL_FROM", "CONTACT_TO"
)
logger = logging.getLogger("uvicorn.error")


class Contact(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    company: str = Field(default="", max_length=150)
    email: EmailStr = Field(max_length=200)
    part_number: str = Field(default="", max_length=100)
    quantity: str = Field(default="", max_length=40)
    message: str = Field(min_length=1, max_length=4000)
    website: str = ""
    t: StrictInt


class RateLimiter:
    def __init__(self):
        self.clients: OrderedDict[str, deque[float]] = OrderedDict()

    def allow(self, client: str) -> bool:
        # Called on the event loop, without yielding while updating the counters.
        now = time.monotonic()
        while self.clients:
            oldest = next(iter(self.clients.values()))
            if oldest[-1] > now - DAY:
                break
            self.clients.popitem(last=False)

        attempts = self.clients.setdefault(client, deque())
        while attempts and attempts[0] <= now - DAY:
            attempts.popleft()
        if len(attempts) >= 20 or sum(at > now - HOUR for at in attempts) >= 5:
            return False
        attempts.append(now)
        self.clients.move_to_end(client)
        return True


def append_submission(path: Path, entry: dict) -> None:
    line = (json.dumps(entry) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab", buffering=0) as output:
        start = output.seek(0, os.SEEK_END)
        try:
            if output.write(line) != len(line):
                raise OSError("Incomplete submission write")
            output.flush()
            os.fsync(output.fileno())
        except OSError:
            output.truncate(start)
            os.fsync(output.fileno())
            raise


def send_email(settings: list[str], entry: dict) -> None:
    host, port, user, password, sender, recipient = settings
    reply_to = entry["email"]
    if any(char in value for value in (sender, recipient, reply_to) for char in ",;\r\n"):
        raise ValueError("Invalid mail header")

    mail = EmailMessage()
    mail["From"] = sender
    mail["To"] = recipient
    mail["Reply-To"] = reply_to
    for header in ("From", "To", "Reply-To"):
        addresses = mail[header].addresses
        if len(addresses) != 1 or mail[header].defects or not addresses[0].domain:
            raise ValueError("Invalid mail address")
    mail["Subject"] = "New NeoChip website enquiry"
    mail.set_content(
        "\n".join(
            f"{label}: {entry[field]}"
            for label, field in (
                ("Name", "name"), ("Company", "company"), ("Email", "email"),
                ("Part number", "part_number"), ("Quantity", "quantity"),
                ("Message", "message"),
            )
        )
    )
    context = ssl.create_default_context()
    smtp_port = int(port)
    if smtp_port == 465:
        client = smtplib.SMTP_SSL(host, smtp_port, timeout=5, context=context)
    else:
        client = smtplib.SMTP(host, smtp_port, timeout=5)
    with client:
        if smtp_port != 465:
            client.starttls(context=context)
        client.login(user, password)
        client.send_message(
            mail, from_addr=mail["From"].addresses[0].addr_spec,
            to_addrs=[mail["To"].addresses[0].addr_spec],
        )


def send_ntfy(url: str, submission_id: str) -> None:
    request = OutboundRequest(
        url,
        data=f"New website enquiry {submission_id[:8]}".encode("utf-8"),
        headers={"Content-Type": "text/plain; charset=utf-8"},
        method="POST",
    )
    with urlopen(request, timeout=5):
        pass


def notify(entry: dict) -> None:
    settings = [os.getenv(key, "") for key in SMTP_SETTINGS]
    if all(settings):
        try:
            send_email(settings, entry)
        except Exception:
            logger.warning("Email notification failed for submission %s", entry["id"])
    url = os.getenv("NTFY_URL")
    if url:
        try:
            send_ntfy(url, entry["id"])
        except Exception:
            logger.warning("ntfy notification failed for submission %s", entry["id"])


def create_app() -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    origins = [
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",")
        if origin.strip() and origin.strip() != "*"
    ]
    app.add_middleware(
        CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    limiter = RateLimiter()
    store_lock = Lock()
    path = Path(os.getenv("DATA_DIR") or "/data") / "submissions.jsonl"
    salt = os.getenv("SALT", "")

    @app.middleware("http")
    async def reject_disallowed_origins(request: Request, call_next):
        if any(origin not in origins for origin in request.headers.getlist("origin")):
            return JSONResponse({"detail": "Origin not allowed"}, status_code=403)
        return await call_next(request)

    @app.get("/healthz")
    async def health():
        return {"ok": True}

    @app.post("/api/contact")
    async def contact(request: Request):
        body = bytearray()
        async for chunk in request.stream():
            if len(body) + len(chunk) > BODY_LIMIT:
                raise HTTPException(413, "Request too large")
            body.extend(chunk)

        ip = request.headers.get("CF-Connecting-IP")
        if ip is None:
            ip = request.client.host if request.client else ""
        ip_hash = hashlib.sha256((ip + salt).encode("utf-8")).hexdigest()
        if not limiter.allow(ip_hash):
            raise HTTPException(429, "Too many submissions")

        try:
            payload = json.loads(body)
            if not isinstance(payload, dict):
                raise ValueError("Expected JSON object")
            if isinstance(payload.get("website"), str) and payload["website"]:
                return {"ok": True}
            timestamp = payload.get("t")
            if type(timestamp) is int and time.time_ns() // 1_000_000 - timestamp < 3000:
                return {"ok": True}
            if any(
                isinstance(payload.get(field), str)
                and ("\r" in payload[field] or "\n" in payload[field])
                for field in ("name", "email")
            ):
                raise ValueError("Invalid header characters")
            form = Contact.model_validate(payload)
            if not form.name.strip() or not form.message.strip() or len(payload["email"]) > 200:
                raise ValueError("Invalid contact fields")
        except (ValueError, RecursionError):
            raise HTTPException(422, "Invalid submission") from None

        entry = {
            "id": str(uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **form.model_dump(exclude={"website", "t"}),
            "ip_hash": ip_hash,
        }

        def store():
            with store_lock:
                append_submission(path, entry)

        try:
            await run_in_threadpool(store)
        except OSError:
            logger.error("Storage failed for submission %s", entry["id"])
            raise HTTPException(500, "Could not store submission") from None

        await run_in_threadpool(notify, entry)
        return {"ok": True}

    return app


app = create_app()
