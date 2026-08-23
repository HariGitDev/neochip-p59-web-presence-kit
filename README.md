# P59 — Web Presence Kit

Reusable marketing-site kit. **Tenant 1 = `neochipsolutions.com`.** Later tenants: YEP
participant/group sites, with no code fork — a content file plus a token override.

Docs and decisions live in OneDrive, not here:
`NeoChip-Solutions/Projects/59-Web-Presence-Kit/` · brief: `NeoChip-Solutions/briefs/59-brief.md`

## Run

```bash
npm install
npm run dev        # http://127.0.0.1:8059
npm run build
npm run test       # smoke test against dist/
```

`PROD_READY=1 npm run test` makes surviving `{{TBD}}` tokens a hard failure — the pre-launch gate.

## Layout

| Path | What |
|---|---|
| `src/content/neochip.js` | **Tenant content.** Copy, nav, services, products, contact. Edit here first. |
| `src/styles/theme.css` | Design tokens. A tenant re-declares these to re-theme. |
| `src/styles/components.css` | Component styles. Tenant-agnostic. |
| `src/App.jsx` | Page composition and components. |
| `public/mockups/` | Rejected design directions, kept for reference. |
| `scripts/smoke-test.mjs` | Build contract + content guardrail checks. |

## Rules

- **Nothing NeoChip-specific in a component.** If a change needs a `.jsx` edit to say something
  tenant-specific, the abstraction is wrong — fix the abstraction.
- **Content guardrails are enforced by the smoke test.** No claims of authorized lines,
  certifications, physical location, phone, customer counts, supplier relationships, guaranteed
  inventory, or in-house test capability. Unverified content uses a `{{TBD: …}}` token.
- Design direction is **Design B — Technical/Warm** (chosen 2026-08-23). Structure blends
  RH Electronics, A2 Global, SMT Corp and Smith; it deliberately does **not** follow AMPEL's shape.
