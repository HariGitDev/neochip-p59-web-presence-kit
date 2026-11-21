# NeoChip contact API

FastAPI service behind the public site's contact form: `POST /api/contact`, `GET /healthz`.
Accepted submissions are appended (fsynced) to `${DATA_DIR}/submissions.jsonl`; the client IP is stored only as `sha256(ip + SALT)`.
Honeypot (`website`) or submit-within-3s-of-`t` requests get a normal 200 and are dropped. Limits: 16 KB body (413), 5/hour and 20/day per IP (429, in memory, reset on restart). Personal data is never logged.

## Environment

| Var | Default | Purpose |
|---|---|---|
| `DATA_DIR` | `/data` | Directory for `submissions.jsonl` (mount a volume) |
| `SALT` | empty | Salt for the IP hash; set a random secret |
| `ALLOWED_ORIGINS` | prod, www, testweb `https://…neochipsolutions.com` | Comma list; a present `Origin` not in it gets 403 |
| `SMTP_HOST` `SMTP_PORT` `SMTP_USER` `SMTP_PASSWORD` `MAIL_FROM` `CONTACT_TO` | unset | All six required to send mail; `CONTACT_TO` must be exactly one address. Port 465 = SSL, otherwise STARTTLS |
| `NTFY_URL` | unset | If set, POSTs "New website enquiry <id8>" (no personal data) |

Client IP is `CF-Connecting-IP` when it is a valid IP, else the peer address.

## Tests

```bash
cd api
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests -v
```

## Deployment

Run as a container listening on `0.0.0.0:8060`, published only on the host loopback; cloudflared routes `/api/*` to it.

```bash
docker build -t neochip-contact-api api/
docker run -d --name contact-api --restart unless-stopped \
  -p 127.0.0.1:8060:8060 -v contact-data:/data \
  -e SALT=... -e SMTP_HOST=... -e SMTP_PORT=587 -e SMTP_USER=... -e SMTP_PASSWORD=... \
  -e MAIL_FROM=... -e CONTACT_TO=... neochip-contact-api
```

The `/data` volume is owned by uid 10001 (the container user). Run a single worker (rate limits are per process).
