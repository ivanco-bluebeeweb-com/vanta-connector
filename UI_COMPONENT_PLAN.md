# Vanta Connector — UI Component Plan

Source: `UI_COMPONENT_VOCABULARY.md` + `~/UI_INTERFACE_STANDARD.md`. Only primitives
from the verified vocabulary are used below.

## Standing rules applied (binding for every screen in this plan)
- Every input carries its own visible label (via a `Text(variant="caption")` +
  input pair, never a bare placeholder).
- Placeholders are contextually specific to the exact field (e.g. a real-looking
  Client ID shape), never generic ("enter value").
- The connect form container is stretched to the full width of the left sidebar;
  its own contents (inputs, selects, buttons) stretch to fill it (`align="stretch"`).
- The sidebar carries NO instructions duplicated from the "How do I get this?"
  modal — the modal is the only place with the credential-setup walkthrough.
- No `Card` (decorated box) anywhere in the left sidebar — plain `Stack` +
  `Divider` only.

## 1. Left sidebar (`slot="left"`)

**Not connected:**
- `Button` "How do I get this?" (ghost, opens `vanta_connect_help` modal panel)
- `Form(action="connect_vanta")`:
  - Label `Input` (placeholder: "Acme Corp — Production")
  - Client ID `Input` (placeholder: a realistic Vanta OAuth client id shape)
  - Client Secret `Input` (password-type)
  - Base URL `Input` (placeholder: "https://api.vanta.com", optional/advanced)
  - Submit button "Connect"

**Connected (one or more organizations):**
- `Text` organization label, `Divider`
- `Button` list (ghost, full width, left-aligned) opening each center panel:
  Compliance Overview, Tests, Controls, Frameworks, Risk Register, Vendors,
  Documents, Personnel, Integrations
- `Divider`
- `Button` "App settings" (secondary, always last)

## 2. Center panels (`slot="center"`, `center_overlay=True`)

- `vanta_overview` — aggregated audit-readiness health report (failing tests,
  overdue risks, overdue vendor reviews, expiring documents) as `Stack` of
  `Text`/`Badge` summary rows, or `Empty` if nothing connected
- `vanta_tests` — `DataTable` (name, framework, status, last checked)
- `vanta_controls` — `DataTable` (name, frameworks, test count, status)
- `vanta_frameworks` — `DataTable` (name, status, tests passing/total)
- `vanta_risks` — `DataTable` (title, likelihood, impact, status, owner)
- `vanta_vendors` — `DataTable` (name, risk tier, review status, last reviewed)
- `vanta_documents` — `DataTable` (name, type, status, last updated)
- `vanta_people` — `DataTable` (name, email, offboarded, training status)
- `vanta_integrations` — `DataTable` (name, category, status)
- `vanta_connect_help` — `Markdown` walkthrough (API application creation + scopes)
- Every panel above: `Empty(message="Nothing to show here", icon=...)` base state
  when not connected, registered with `center_overlay=True`.

## 3. App settings (`slot="center"`, separate screen)

- `vanta_settings` — one row per connected organization: `Text` label + `Button`
  "Disconnect" (destructive). This is the ONLY place disconnect lives.

## 4. Actions map (`ui.Call` targets, no duplication with chat tools)

Every sidebar/center button maps 1:1 to a `@chat.function` name already declared
in `handlers.py` — no UI-only actions invented here that don't exist as callable
tools.
