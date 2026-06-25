# How to Use the API

The service is live on Vercel. You call it by appending an endpoint path to the
base URL — the base URL alone does nothing useful; you must add `/health` or
`/sort-ticket`.

## Base URL

```
https://sust-preli-backend.vercel.app
```

| Method | Full URL | Purpose |
|---|---|---|
| `GET`  | `https://sust-preli-backend.vercel.app/health` | Service health check |
| `POST` | `https://sust-preli-backend.vercel.app/sort-ticket` | Classify one CRM ticket |

> Note: the bare base URL (`https://sust-preli-backend.vercel.app/`) is **not** a
> usable endpoint — always add `/health` or `/sort-ticket`.

---

## 1. Health check — `GET /health`

Use this to confirm the service is up. Just open it in a browser or run:

```bash
curl https://sust-preli-backend.vercel.app/health
```

Response (`200 OK`):

```json
{ "status": "ok" }
```

---

## 2. Classify a ticket — `POST /sort-ticket`

Send a JSON body describing one customer message. The service returns the case
type, severity, department, a one-sentence agent summary, a human-review flag,
and a confidence score.

### Request body

```json
{
  "ticket_id": "T-001",
  "channel": "app",
  "locale": "en",
  "message": "I sent 5000 taka to a wrong number this morning, please help me get it back"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `ticket_id` | string | **Yes** | Echoed back in the response |
| `message` | string | **Yes** | Free-text customer complaint |
| `channel` | string | No | `app`, `sms`, `call_center`, `merchant_portal` |
| `locale` | string | No | `bn`, `en`, `mixed` |

### Example call

```bash
curl -X POST https://sust-preli-backend.vercel.app/sort-ticket \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"T-001","message":"I sent 3000 to wrong number"}'
```

### Response (`200 OK`)

```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports sending money to an unintended recipient and requests recovery.",
  "human_review_required": false,
  "confidence": 0.85
}
```

### Response fields

| Field | Type | Notes |
|---|---|---|
| `ticket_id` | string | Same value you sent |
| `case_type` | enum | `wrong_transfer`, `payment_failed`, `refund_request`, `phishing_or_social_engineering`, `other` |
| `severity` | enum | `low`, `medium`, `high`, `critical` |
| `department` | enum | `customer_support`, `dispute_resolution`, `payments_ops`, `fraud_risk` |
| `agent_summary` | string | One neutral sentence; never asks for PIN/OTP/password |
| `human_review_required` | boolean | `true` for critical / phishing cases |
| `confidence` | number | Float in `[0, 1]` (`0.85` on a keyword match, `0.5` on fallback) |

---

## Error responses

| Situation | Status | Body |
|---|---|---|
| Missing `ticket_id` or `message` | `400` | `{"error": "ticket_id and message are required"}` |
| Body is not valid JSON | `400` | `{"error": "invalid JSON body"}` |

```bash
curl -X POST https://sust-preli-backend.vercel.app/sort-ticket \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"T-009"}'
# -> {"error": "ticket_id and message are required"}
```

---

## Calling from code

### JavaScript (fetch)

```js
const res = await fetch("https://sust-preli-backend.vercel.app/sort-ticket", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    ticket_id: "T-001",
    message: "Someone called asking my OTP, is that bKash?",
  }),
});
const data = await res.json();
console.log(data.case_type, data.severity); // phishing_or_social_engineering critical
```

### Python (standard library)

```python
import json, urllib.request

req = urllib.request.Request(
    "https://sust-preli-backend.vercel.app/sort-ticket",
    data=json.dumps({"ticket_id": "T-001", "message": "Payment failed but balance deducted"}).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
print(json.load(urllib.request.urlopen(req)))
```

---

## Quick sample reference

| Message | case_type | severity |
|---|---|---|
| I sent 3000 to wrong number | `wrong_transfer` | high |
| Payment failed but balance deducted | `payment_failed` | high |
| Someone called asking my OTP, is that bKash? | `phishing_or_social_engineering` | critical |
| Please refund my last transaction, I changed my mind | `refund_request` | low |
| App crashed when I opened it | `other` | low |

## Run the full smoke test against the live URL

From the repo root:

```bash
./test_api.sh https://sust-preli-backend.vercel.app
```
