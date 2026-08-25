# Pricing History — Vanta Connector

## 2026-08-25 — initial pricing (build → deploy → save_pricing → submit_for_review)

Same pattern as Ping Identity/Okta/MuleSoft this build cycle: pricing set via
`developer.save_pricing` BEFORE `submit_for_review`, per the standing rule
("ты не выставила прайсинги на функции перед заливом на платформу... это
должно быть частью дефолтного поведения всегда для всех приложений и для
всех сессий").

**First call failed with the same silent-mismatch pattern already logged for
Okta/MuleSoft/Ping Identity** (task #2260 — a known systemic platform bug):
response reported `model stored as 'free'` and every `tool_prices` key "not
stored" despite no error being raised by the API. Immediate retry with the
identical payload succeeded (returned the full saved app object with
`manifest_json` populated). Confirms this is a platform-side quirk, not a
client mistake.

**Category note:** `create_app` rejected `category="grc"` outright
("Unknown category 'grc'. It must be one of the catalog ids served by
GET /v1/marketplace/categories/catalog."). No dedicated GRC category exists
yet on the platform catalog — used `productivity`, matching the precedent of
Middesk (KYB/compliance-adjacent) which is also filed under `productivity`.

**Prices — fixed platform scale {0, 8, 16, 20, 40, 60}, no exceptions, no
markup:**

| Цена | Функции |
|---|---|
| 0 | `connect_vanta`, `disconnect_vanta`, `list_connections` (настройка доступа, не операция с Vanta API) |
| 8 | `list_tests`, `get_test`, `list_controls`, `get_control`, `list_frameworks`, `list_risk_scenarios`, `list_groups` (лёгкие read-операции) |
| 16 | `list_risks`, `get_risk`, `list_vendors`, `get_vendor`, `list_documents`, `get_document`, `list_people`, `get_person`, `list_integrations`, `list_monitored_computers` (более тяжёлые/детальные read-операции) |
| 20 | `dismiss_test`, `create_risk`, `update_risk`, `create_vendor`, `update_vendor` (write-операции, реально меняющие состояние в Vanta) |
| 40 | `audit_compliance_posture` (агрегированный отчёт — несколько API-вызовов под капотом) |
