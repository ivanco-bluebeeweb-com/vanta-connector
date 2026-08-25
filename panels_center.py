"""Vanta Connector -- center panels for Overview/Tests/Controls/Frameworks/Risks/Vendors/Documents/People/Integrations."""
from __future__ import annotations

from imperal_sdk import ui

import handlers as h
from app import ext


def _table_or_empty(rows, columns, empty_message, empty_icon):
    if not rows:
        return ui.Empty(message=empty_message, icon=empty_icon)
    return ui.DataTable(rows=rows, columns=columns)


@ext.panel("vanta_overview", slot="center", title="Compliance overview", center_overlay=True)
async def vanta_overview(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="ShieldCheck")
    from schemas import ConnectionRefParams
    result = await h.audit_compliance_posture(ctx, ConnectionRefParams(connection_id=connections[0].get("id", "")))
    if not result.success:
        return ui.Alert(type="error", message=f"Could not load compliance overview: {result.error}")
    d = result.data
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Compliance overview", level=2),
        ui.Stack(direction="h", gap=4, align="stretch", children=[
            ui.Stat(label="Failing tests", value=f"{d.failing_tests}/{d.total_tests}"),
            ui.Stat(label="Overdue risks", value=f"{d.overdue_risks}/{d.total_risks}"),
            ui.Stat(label="Overdue vendor reviews", value=f"{d.overdue_vendor_reviews}/{d.total_vendors}"),
            ui.Stat(label="Disabled integrations", value=str(d.disabled_integrations)),
        ]),
        ui.Text(d.notes, variant="caption"),
    ])


@ext.panel("vanta_tests", slot="center", title="Tests", center_overlay=True)
async def vanta_tests(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="CheckCircle2")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/v1/tests", params={"pageSize": 50})
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load tests: {exc}")
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    rows = [{
        "name": t.get("name", ""),
        "status": t.get("status", t.get("outcome", "")),
        "frameworks": ", ".join(f.get("name", "") for f in (t.get("frameworks") or []) if isinstance(f, dict)),
    } for t in items]
    columns = [
        ui.DataColumn(key="name", label="Test"),
        ui.DataColumn(key="status", label="Status"),
        ui.DataColumn(key="frameworks", label="Frameworks"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Tests", level=2),
        _table_or_empty(rows, columns, "No tests found", "CheckCircle2"),
    ])


@ext.panel("vanta_controls", slot="center", title="Controls", center_overlay=True)
async def vanta_controls(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="ListChecks")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/v1/controls", params={"pageSize": 50})
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load controls: {exc}")
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    rows = [{
        "name": c.get("name", ""),
        "status": c.get("status", ""),
        "tests": str(len(c.get("tests") or [])),
    } for c in items]
    columns = [
        ui.DataColumn(key="name", label="Control"),
        ui.DataColumn(key="status", label="Status"),
        ui.DataColumn(key="tests", label="Tests"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Controls", level=2),
        _table_or_empty(rows, columns, "No controls found", "ListChecks"),
    ])


@ext.panel("vanta_frameworks", slot="center", title="Frameworks", center_overlay=True)
async def vanta_frameworks(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="Layers")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/v1/frameworks")
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load frameworks: {exc}")
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    rows = [{
        "name": f.get("name", ""),
        "controls": str(len(f.get("controls") or [])),
        "percentComplete": f"{f.get('percentComplete', 0)}%",
    } for f in items]
    columns = [
        ui.DataColumn(key="name", label="Framework"),
        ui.DataColumn(key="controls", label="Controls"),
        ui.DataColumn(key="percentComplete", label="Complete"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Frameworks", level=2),
        _table_or_empty(rows, columns, "No frameworks enabled", "Layers"),
    ])


@ext.panel("vanta_risks", slot="center", title="Risk register", center_overlay=True)
async def vanta_risks(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="AlertTriangle")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/v1/risks", params={"pageSize": 50})
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load risks: {exc}")
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    rows = [{
        "name": r.get("name", r.get("title", "")),
        "likelihood": r.get("likelihood", ""),
        "impact": r.get("impact", ""),
        "status": r.get("status", r.get("treatmentStatus", "")),
    } for r in items]
    columns = [
        ui.DataColumn(key="name", label="Risk"),
        ui.DataColumn(key="likelihood", label="Likelihood"),
        ui.DataColumn(key="impact", label="Impact"),
        ui.DataColumn(key="status", label="Status"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Risk register", level=2),
        _table_or_empty(rows, columns, "No risks recorded", "AlertTriangle"),
    ])


@ext.panel("vanta_vendors", slot="center", title="Vendors", center_overlay=True)
async def vanta_vendors(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="Building2")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/v1/vendors", params={"pageSize": 50})
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load vendors: {exc}")
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    rows = [{
        "name": v.get("name", ""),
        "riskTier": v.get("riskTier", v.get("riskLevel", "")),
        "status": v.get("status", v.get("securityReviewStatus", "")),
        "nextReview": v.get("nextReviewDate", ""),
    } for v in items]
    columns = [
        ui.DataColumn(key="name", label="Vendor"),
        ui.DataColumn(key="riskTier", label="Risk tier"),
        ui.DataColumn(key="status", label="Status"),
        ui.DataColumn(key="nextReview", label="Next review"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Vendors", level=2),
        _table_or_empty(rows, columns, "No vendors tracked", "Building2"),
    ])


@ext.panel("vanta_documents", slot="center", title="Documents", center_overlay=True)
async def vanta_documents(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="FileText")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/v1/documents", params={"pageSize": 50})
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load documents: {exc}")
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    rows = [{
        "name": d.get("name", d.get("title", "")),
        "status": d.get("status", ""),
        "expiration": d.get("expirationDate", ""),
    } for d in items]
    columns = [
        ui.DataColumn(key="name", label="Document"),
        ui.DataColumn(key="status", label="Status"),
        ui.DataColumn(key="expiration", label="Expiration"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Documents", level=2),
        _table_or_empty(rows, columns, "No documents found", "FileText"),
    ])


@ext.panel("vanta_people", slot="center", title="Personnel", center_overlay=True)
async def vanta_people(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="Users")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/v1/people", params={"pageSize": 50})
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load personnel: {exc}")
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    rows = [{
        "name": p.get("fullName", p.get("name", "")),
        "email": p.get("email", ""),
        "offboarded": "Yes" if p.get("offboarded") else "No",
    } for p in items]
    columns = [
        ui.DataColumn(key="name", label="Name"),
        ui.DataColumn(key="email", label="Email"),
        ui.DataColumn(key="offboarded", label="Offboarded"),
    ]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Personnel", level=2),
        _table_or_empty(rows, columns, "No personnel records found", "Users"),
    ])


@ext.panel("vanta_integrations", slot="center", title="Integrations", center_overlay=True)
async def vanta_integrations(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(message="Nothing to show here", icon="Plug")
    client = h._client_for(connections[0])
    try:
        data, _ = await client.request("GET", "/v1/integrations")
    except Exception as exc:  # noqa: BLE001
        return ui.Alert(type="error", message=f"Could not load integrations: {exc}")
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    rows = [{
        "name": i.get("name", ""),
        "status": i.get("status", "")
    } for i in items]
    columns = [ui.DataColumn(key="name", label="Integration"), ui.DataColumn(key="status", label="Status")]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Integrations", level=2),
        _table_or_empty(rows, columns, "No integrations connected", "Plug"),
    ])
