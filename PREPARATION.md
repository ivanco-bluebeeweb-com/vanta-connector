# Vanta Connector — Preparation

**Prepared:** 2026-08-25
**Scope:** Tier 1 (Tests/Controls/Frameworks/Risks/Vendors read+key writes) + Tier 2
(Documents/Monitors/People/Integrations/Evidence read, comments) — maximum practical
functionality against Vanta's public API, per the user's standing "maximum functionality"
instruction for every new app.

## 1. Product outcome

Vanta Connector lets an authorized Imperal user connect one or more Vanta organizations
(BYOK OAuth2 Client Credentials), inspect real-time compliance posture (tests, controls,
frameworks), manage the Risk Register and Vendor risk inventory, review policy documents
and personnel compliance status, and get an aggregated audit-readiness health report —
all without leaving the chat. Vanta remains the system of record; the connector never
fabricates or overrides a computed test result.

## 2. Connection architecture

- **Model:** BYOK, per Imperal account, multi-connection JSON secret
  (`vanta_connections`).
- **Secret shape:** each record = `{connection_id, label, client_id, client_secret,
  base_url}` (base_url defaults to `https://api.vanta.com`, but is kept configurable in
  case of EU/segregated tenants).
- **Auth:** OAuth2 Client Credentials — the client exchanges client_id/client_secret for
  a bearer token at the Vanta token endpoint; token is cached in-process per call chain
  and refreshed on expiry/401. The long-lived client_secret is the only thing persisted,
  encrypted at rest like every other connector's secret.
- **No secret echo:** client_secret and any live access token are never returned in
  entities, labels, errors, panels, or logs.
- **Verification:** `connect_vanta` performs the token exchange, then a bounded
  single-page call to Tests (or the lightest available "identity"/organization info
  endpoint) before persisting the connection.

## 3. Provider client

`vanta_client.py` is the single HTTP boundary. It:

1. holds no long-lived token across process restarts — always re-authenticates via
   client credentials at the top of a call chain (simplicity over premature caching
   correctness, since Vanta tokens are short-lived anyway);
2. builds `Authorization: Bearer <token>` for the resource call;
3. maps status codes to clear, user-facing errors: 401 → "token invalid or app
   deauthorized in Vanta", 403 → "the Vanta API application lacks a scope needed for
   this action — grant it in Vanta Settings > API", 404 → "not found", 429 → "rate
   limited, retry shortly" (echoing Retry-After if present);
4. supports cursor pagination for every list_* function, returning a `next_cursor`
   consistently.

## 4. Function surface (final)

**Connection**
- `connect_vanta`, `disconnect_vanta`, `list_connections`

**Tests / Controls / Frameworks**
- `list_tests`, `get_test`, `list_controls`, `get_control`, `list_frameworks`

**Risk Register**
- `list_risks`, `get_risk`, `create_risk`, `update_risk`

**Vendors**
- `list_vendors`, `get_vendor`, `create_vendor`, `update_vendor`

**Documents / Policies**
- `list_documents`, `get_document`

**Monitors / Integrations**
- `list_monitors`, `list_integrations`

**People**
- `list_people`, `get_person`

**Evidence**
- `list_evidence`

**Comments (audit trail)**
- `list_comments`, `add_comment`

**Value-add reports**
- `audit_compliance_posture` — one aggregated report: failing test count by framework,
  overdue risk reviews, vendor reviews past due, personnel not yet compliant (missing
  training/background check), integration sync failures. This is the flagship "one
  glance, is the org audit-ready" tool, matching the audit_* pattern established across
  the portfolio (audit_org, audit_tenant, audit_estate, etc).

## 5. Error mapping table

| HTTP | Meaning | User-facing message |
|---|---|---|
| 401 | invalid/expired credentials | "Vanta rejected the API application credentials — reconnect or check they weren't revoked." |
| 403 | scope missing | "This Vanta API application isn't scoped for that action — grant the scope in Vanta Settings > API." |
| 404 | not found | "That Vanta record wasn't found (wrong id or already deleted)." |
| 429 | rate limited | "Vanta is rate-limiting this connection — try again in a moment." |
| 5xx | provider outage | "Vanta's API is currently having issues on their end." |

## 6. Security & domain-sensitivity notes

- Never surface a smoothed/inferred compliance status — always the literal Vanta value.
- Personnel data (People resource) can include sensitive HR-adjacent fields (training
  completion, background-check status) — list/get functions expose only compliance-
  relevant fields, not full HR PII beyond what's needed to act.
- Risk/Vendor writes are explicit human actions (create_risk, update_vendor, etc.) —
  never auto-triggered from a report/audit function.
