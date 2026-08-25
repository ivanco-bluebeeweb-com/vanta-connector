# Vanta Connector — Discovery

**Prepared:** 2026-08-25
**Source:** Vanta Public API (developer.vanta.com), OAuth2 Client Credentials flow.

## 1. What Vanta is

Vanta is a Compliance Automation / GRC platform: it continuously monitors a company's
cloud/IdP/HR/ticketing integrations against control frameworks (SOC 2, ISO 27001, HIPAA,
PCI DSS, GDPR, NIST, custom frameworks) and surfaces pass/fail "Tests" for each control,
tracks a Risk Register, a Vendor (third-party) risk inventory, and Policy documents that
need periodic review/acknowledgement by personnel.

## 2. Authentication

- OAuth2 **Client Credentials** grant. A user creates a Vanta API application under
  Settings > API, receiving a `client_id` + `client_secret` (client-scoped, not
  per-user).
- Token endpoint issues a short-lived bearer access token (~1 hour); the connector must
  transparently refresh it on 401/expiry, caching it in memory only for the lifetime of
  a call chain — never persisting the raw access token, only client_id/client_secret in
  the encrypted secret store.
- Scopes are assigned when the API application is created in the Vanta UI (e.g.
  read access to tests, vendors, risks, documents, private-computed-data). The
  connector cannot request broader scopes than what the user configured in Vanta itself.

## 3. Core resources (Tier 1)

| Resource | Description | Ops |
|---|---|---|
| Tests | Automated control checks; each has a status (OK / FAIL / DISABLED / OUTDATED / NOT_APPLICABLE) | list, get |
| Controls | Named controls mapped to one or more frameworks, each backed by 1+ tests | list, get |
| Frameworks | SOC 2, ISO 27001, HIPAA, etc. enabled on the account | list |
| Risks | Risk Register entries (title, description, likelihood/impact, treatment, status) | list, get, create, update |
| Risk Scenarios | Named risk categories the register entries can be tied to | list |
| Vendors | Third-party vendor risk records (name, risk tier, review status, security review docs) | list, get, create, update |
| Documents (Policies) | Policy documents, versions, and their approval/renewal status | list, get |
| Monitors | Underlying resource-level monitors (e.g. one AWS S3 bucket, one GitHub repo setting) feeding a Test | list |
| People | Personnel roster: onboarding/offboarding status, security training completion, background check status | list, get |
| Integrations | Connected source integrations (AWS, GCP, Okta, GitHub, etc.) and their sync health | list |
| Evidence Library | Uploaded/generated evidence artifacts tied to controls | list, get |
| Comments | Comments/notes threads on a Test or Risk (audit trail) | list, create |

## 4. Write operations available (explicit, human-in-the-loop)

- Update a Risk's status/treatment/owner.
- Create a new Risk Register entry.
- Update a Vendor's risk tier / review status.
- Create a new Vendor entry.
- Add a comment to a Test or Risk (for audit trail / remediation notes).
- Dismiss/mark a Test as not-applicable is NOT exposed for arbitrary override in the
  public API (Tests are computed by Vanta's own integrations) — only supported where
  the API documents an explicit "test not applicable" endpoint per test id. Discovery
  must confirm exact endpoint names before implementation; do not fabricate an endpoint.

## 5. Pagination & errors

- Cursor-based pagination (`pageCursor` / `pageSize`) on all list endpoints.
- Standard REST status codes; 401 = expired/invalid token (auto-refresh once, then
  surface clearly), 403 = scope not granted on the Vanta API application, 429 = rate
  limited (surface retry-after if provided).

## 6. Domain sensitivity

Same class of care as Alloy/Middesk: this is a compliance/audit-evidence domain. Status
values (test pass/fail, risk severity, vendor tier) must be surfaced exactly as Vanta
reports them — no smoothing, no inferred "probably fine". A wrong compliance status
shown to a user preparing for an audit is a trust-breaking bug, not a cosmetic one.
