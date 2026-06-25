# QueueStorm Warmup — Ticket Classifier

A stateless backend service that classifies a single CRM ticket. It exposes two
HTTPS endpoints and answers four questions per ticket: case type, severity,
department, and a one-sentence agent summary. It also flags phishing/critical
cases for human review.

- **Approach:** Rules-based (keyword matching). No LLM, no GPU, no database.
- **Runtime:** Python standard library only — **zero dependencies**, no `requirements.txt`.
- **Host:** Vercel serverless functions (free tier, automatic HTTPS). Runs locally too.

## Layout

```
backend/
├── api/
│   ├── health.py        # GET  -> /health
│   └── sort_ticket.py   # POST -> /sort-ticket  (contains the classifier)
├── server.py            # local dev server (stdlib only) — for local replication
├── vercel.json          # path rewrites for deployment
└── README.md            # this runbook
```

The bash smoke-test script `test_api.sh` lives **one level up**, in the repo root.

## API

### `GET /health`
`200 → {"status": "ok"}`

### `POST /sort-ticket`
Request:
```json
{
  "ticket_id": "T-001",
  "channel": "app",
  "locale": "en",
  "message": "I sent 5000 taka to a wrong number this morning, please help me get it back"
}
```
- Required: `ticket_id`, `message`. Optional: `channel`, `locale`.
- Missing a required field → `400 {"error": "ticket_id and message are required"}`.
- Malformed JSON → `400 {"error": "invalid JSON body"}`.

Response `200`:
```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports sending money to an unintended recipient and requests recovery.",
  "human_review_required": true,
  "confidence": 0.85
}
```

## Classification logic

`message` is lowercased and matched against keyword sets. Rules are evaluated in
a fixed order; the **first match wins** (`other` is the fallback). Single-token
keywords (`otp`, `pin`, `cvv`, `refund`, ...) are matched on word boundaries to
avoid false positives (e.g. `shopping` does not match `pin`).

| Order | case_type | severity | department | confidence |
|---|---|---|---|---|
| 1 | `phishing_or_social_engineering` | critical | fraud_risk | 0.85 |
| 2 | `wrong_transfer` | high | dispute_resolution | 0.85 |
| 3 | `payment_failed` | high | payments_ops | 0.85 |
| 4 | `refund_request` | low | customer_support | 0.85 |
| 5 | `other` (fallback) | low | customer_support | 0.50 |

`human_review_required` is `true` when `severity == "critical"` **or**
`case_type == "phishing_or_social_engineering"`.

**Safety:** `agent_summary` is always one of five fixed neutral templates — none
ask the customer for PIN/OTP/password/card number, so the grader's safety check
passes by construction.

## Run locally (deployment replication)

No third-party packages required. Python 3.8+ is enough.

```bash
cd backend
python server.py            # serves on http://localhost:3000  (set PORT to change)
```

Then, from the repo root in another terminal:

```bash
./test_api.sh                          # tests http://localhost:3000 by default
./test_api.sh http://localhost:3000    # explicit base URL
```

Or hit it manually:

```bash
curl http://localhost:3000/health
curl -X POST http://localhost:3000/sort-ticket \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"T-001","message":"I sent 3000 to wrong number"}'
```

## Deploy to Vercel

Vercel's Python runtime loads the class named `handler` (a
`http.server.BaseHTTPRequestHandler` subclass) from each file in `api/` and
serves it as a serverless function. `vercel.json` rewrites the public paths
`/health` and `/sort-ticket` onto those functions. No build step, no secrets.

1. Push this repo to a **public** GitHub repository.
2. **Dashboard route:** vercel.com → *New Project* → import the repo. If the repo
   root is the project root, set **Root Directory = `backend`** so `api/` and
   `vercel.json` are detected. Click *Deploy*.
   - **CLI route:** `npm i -g vercel`, then from `backend/`: `vercel` (preview)
     and `vercel --prod` (production).
3. Vercel assigns `https://<project>.vercel.app`.
4. Verify: `GET /health` returns `{"status":"ok"}`; `POST /sort-ticket` with a
   sample body returns the classification JSON. You can point the test script at
   the live URL: `./test_api.sh https://<project>.vercel.app`.
5. Submit the base URL + GitHub repo URL in the Google Form.

Environment variables (none needed here) would be set under
**Project → Settings → Environment Variables** and never committed.

## Validated against the public samples

| # | Message | case_type | severity |
|---|---|---|---|
| 1 | I sent 3000 to wrong number | `wrong_transfer` | high |
| 2 | Payment failed but balance deducted | `payment_failed` | high |
| 3 | Someone called asking my OTP, is that bKash? | `phishing_or_social_engineering` | critical |
| 4 | Please refund my last transaction, I changed my mind | `refund_request` | low |
| 5 | App crashed when I opened it | `other` | low |

LLM used: **No** (rules-based).
