# NeoChip contact API

`POST /api/contact` accepts JSON and returns `{"ok": true}` for a stored enquiry or a silently dropped spam submission. Send `t` as the integer result of `Date.now()` captured at page load and leave `website` empty. `GET /healthz` checks that the service is running.

| Variable | Purpose |
| --- | --- |
| `DATA_DIR` | Directory for `submissions.jsonl`. Defaults to `/data`. |
| `SALT` | Secret suffix used to hash client IPs. Set a random value in production. Defaults to empty. |
| `ALLOWED_ORIGINS` | Comma-separated origins. Defaults to `https://neochipsolutions.com,https://www.neochipsolutions.com,https://testweb.neochipsolutions.com`. |
| `SMTP_HOST`, `SMTP_PORT` | SMTP endpoint. Port 465 uses implicit TLS. Other ports use STARTTLS. |
| `SMTP_USER`, `SMTP_PASSWORD` | SMTP credentials. |
| `MAIL_FROM`, `CONTACT_TO` | SMTP sender and single recipient. Email is enabled when all six SMTP and mail variables are set. |
| `NTFY_URL` | Optional ntfy topic URL. The notification contains only a short submission ID. |

Run from `api/`:

```sh
python -m pip install -r requirements-test.txt
python -m pytest -q
```

Build from `api/`. Keep one container and one Uvicorn worker because rate limits are in memory. Use the named volume for durable submissions.

```sh
docker build -t neochip-contact .
docker run -d --name neochip-contact --env-file /path/to/contact.env \
  -p 127.0.0.1:8060:8060 -v neochip-contact-data:/data neochip-contact
```

On the host, configure cloudflared to route `/api/*` to `http://127.0.0.1:8060` before the website catch-all. The API uses the Cloudflare-provided `CF-Connecting-IP` header when present and falls back to the peer IP.
