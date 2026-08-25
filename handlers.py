"""Chat functions for Vanta Connector (Vanta Public API)."""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import vanta_client as vc
from app import chat
from schemas import (
    ComplianceAudit, ConnectVantaParams, ConnectionList, ConnectionRefParams,
    ControlIdParams, ControlList, CreateRiskParams, CreateVendorParams,
    DeleteResult, DismissTestParams, DisconnectVantaParams, DocumentIdParams,
    DocumentList, FrameworkList, GroupList, IntegrationList,
    ListControlsParams, ListDocumentsParams, ListFrameworksParams,
    ListGroupsParams, ListIntegrationsParams, ListMonitoredComputersParams,
    ListPeopleParams, ListRiskScenariosParams, ListRisksParams,
    ListTestsParams, ListVendorsParams, MonitoredComputerList, NoParams,
    PeopleList, PersonIdParams, RiskIdParams, RiskList, RiskScenarioList,
    TestIdParams, TestList, UpdateRiskParams, UpdateVendorParams,
    VantaComputer, VantaConnection, VantaControl, VantaDocument,
    VantaFramework, VantaGroup, VantaIntegration, VantaPerson, VantaRisk,
    VantaRiskScenario, VantaTest, VantaVendor, VendorIdParams, VendorList,
)

_SECRET_NAME = "vanta_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


def _connection_entity(c: dict) -> VantaConnection:
    return VantaConnection(
        connection_id=c.get("id", ""),
        label=c.get("label") or c.get("client_id", ""),
        base_url=c.get("base_url", "") or "https://api.vanta.com",
    )


async def _resolve_connection(ctx, connection_id: str) -> dict:
    connections = await _load_connections(ctx)
    if not connections:
        raise vc.VantaError("No Vanta organization connected yet. Call connect_vanta first.")
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        raise vc.VantaError(f"No saved Vanta connection with id '{connection_id}'.")
    return connections[0]


def _client_for(c: dict) -> vc.VantaClient:
    return vc.VantaClient(
        client_id=c.get("client_id", ""),
        client_secret=c.get("client_secret", ""),
        base_url=c.get("base_url", ""),
    )


@chat.function("connect_vanta", "Connect a Vanta organization via OAuth2 Client Credentials (API application), after verifying connectivity.", action_type="write", chain_callable=True, data_model=VantaConnection, event="vanta-connector.connect_vanta", effects=["vanta.provider.connected"])
async def connect_vanta(ctx, params: ConnectVantaParams) -> ActionResult:
    """Connect a Vanta organization via OAuth2 Client Credentials (API application), after verifying connectivity."""
    record = {
        "client_id": params.client_id,
        "client_secret": params.client_secret,
        "base_url": params.base_url,
    }
    client = _client_for(record)
    try:
        await client.verify_connection()
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), code="VANTA_CONNECT_FAILED", retryable=exc.retryable)

    record.update({"id": str(uuid.uuid4()), "label": params.label or params.client_id})
    connections = await _load_connections(ctx)
    connections.append(record)
    await _save_connections(ctx, connections)
    return ActionResult.success(data=_connection_entity(record), summary="Vanta organization connected.")


@chat.function("disconnect_vanta", "Disconnect a Vanta organization: deletes only the saved credentials. Nothing in Vanta itself is changed.", action_type="write", chain_callable=True, data_model=DeleteResult, event="vanta-connector.disconnect_vanta", effects=["vanta.provider.disconnected"])
async def disconnect_vanta(ctx, params: DisconnectVantaParams) -> ActionResult:
    """Disconnect a Vanta organization: deletes only the saved credentials. Nothing in Vanta itself is changed."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error(f"No saved Vanta connection with id '{params.connection_id}'.")
    await _save_connections(ctx, remaining)
    return ActionResult.success(data=DeleteResult(ok=True, detail="Vanta organization disconnected."))


@chat.function("list_connections", "List the connected Vanta organizations.", action_type="read", chain_callable=True, data_model=ConnectionList, event="vanta-connector.list_connections")
async def list_connections(ctx, params: NoParams) -> ActionResult:
    """List the connected Vanta organizations."""
    connections = await _load_connections(ctx)
    return ActionResult.success(data=ConnectionList(connections=[_connection_entity(c) for c in connections]))


# ---- Tests ----

def _test_entity(t: dict) -> VantaTest:
    frameworks = ", ".join(f.get("name", "") for f in (t.get("frameworks") or []) if isinstance(f, dict))
    return VantaTest(
        test_id=t.get("id", ""),
        name=t.get("name", ""),
        status=t.get("status", t.get("outcome", "")),
        frameworks=frameworks,
        last_checked=t.get("lastCheckedAt", t.get("updatedAt", "")),
    )


@chat.function("list_tests", "List automated compliance Tests (control checks) with their status (OK/FAIL/DISABLED/OUTDATED/NOT_APPLICABLE).", action_type="read", chain_callable=True, data_model=TestList, event="vanta-connector.list_tests")
async def list_tests(ctx, params: ListTestsParams) -> ActionResult:
    """List automated compliance Tests (control checks) with their status (OK/FAIL/DISABLED/OUTDATED/NOT_APPLICABLE)."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    query: dict = {"pageSize": params.limit}
    if params.status:
        query["status"] = params.status
    if params.page_cursor:
        query["pageCursor"] = params.page_cursor
    try:
        data, _ = await client.request("GET", "/v1/tests", params=query)
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    cursor = (data or {}).get("results", {}).get("pageInfo", {}).get("endCursor", "")
    return ActionResult.success(data=TestList(tests=[_test_entity(t) for t in items], next_page_cursor=cursor or ""))


@chat.function("get_test", "Read one compliance Test in full by id.", action_type="read", chain_callable=True, data_model=VantaTest, event="vanta-connector.get_test")
async def get_test(ctx, params: TestIdParams) -> ActionResult:
    """Read one compliance Test in full by id."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/v1/tests/{params.test_id}")
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_test_entity(data or {}))


@chat.function("dismiss_test", "Dismiss a failing Test with a documented reason -- records an explicit exception/justification in Vanta rather than silently ignoring the failure.", action_type="write", chain_callable=True, data_model=VantaTest, event="vanta-connector.dismiss_test", effects=["vanta.test.dismissed"])
async def dismiss_test(ctx, params: DismissTestParams) -> ActionResult:
    """Dismiss a failing Test with a documented reason -- records an explicit exception/justification in Vanta rather than silently ignoring the failure."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("POST", f"/v1/tests/{params.test_id}/dismiss", json_body={"reason": params.reason})
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_test_entity(data or {}), summary="Test dismissed with recorded justification.")


# ---- Controls ----

def _control_entity(ctl: dict) -> VantaControl:
    frameworks = ", ".join(f.get("name", "") for f in (ctl.get("frameworks") or []) if isinstance(f, dict))
    return VantaControl(
        control_id=ctl.get("id", ""),
        name=ctl.get("name", ""),
        frameworks=frameworks,
        test_count=len(ctl.get("tests") or []),
        status=ctl.get("status", ""),
    )


@chat.function("list_controls", "List Controls (named requirements mapped to one or more frameworks, each backed by 1+ Tests).", action_type="read", chain_callable=True, data_model=ControlList, event="vanta-connector.list_controls")
async def list_controls(ctx, params: ListControlsParams) -> ActionResult:
    """List Controls (named requirements mapped to one or more frameworks, each backed by 1+ Tests)."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    query: dict = {"pageSize": params.limit}
    if params.framework_id:
        query["frameworkId"] = params.framework_id
    if params.page_cursor:
        query["pageCursor"] = params.page_cursor
    try:
        data, _ = await client.request("GET", "/v1/controls", params=query)
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    cursor = (data or {}).get("results", {}).get("pageInfo", {}).get("endCursor", "")
    return ActionResult.success(data=ControlList(controls=[_control_entity(x) for x in items], next_page_cursor=cursor or ""))


@chat.function("get_control", "Read one Control in full by id.", action_type="read", chain_callable=True, data_model=VantaControl, event="vanta-connector.get_control")
async def get_control(ctx, params: ControlIdParams) -> ActionResult:
    """Read one Control in full by id."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/v1/controls/{params.control_id}")
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_control_entity(data or {}))


# ---- Frameworks ----

def _framework_entity(f: dict) -> VantaFramework:
    return VantaFramework(
        framework_id=f.get("id", ""),
        name=f.get("name", ""),
        control_count=len(f.get("controls") or []),
        percent_complete=f.get("percentComplete", 0.0),
    )


@chat.function("list_frameworks", "List compliance Frameworks enabled on the connected organization (SOC 2, ISO 27001, HIPAA, etc.).", action_type="read", chain_callable=True, data_model=FrameworkList, event="vanta-connector.list_frameworks")
async def list_frameworks(ctx, params: ListFrameworksParams) -> ActionResult:
    """List compliance Frameworks enabled on the connected organization (SOC 2, ISO 27001, HIPAA, etc.)."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", "/v1/frameworks")
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    return ActionResult.success(data=FrameworkList(frameworks=[_framework_entity(f) for f in items]))


# ---- Risk Register ----

def _risk_entity(r: dict) -> VantaRisk:
    return VantaRisk(
        risk_id=r.get("id", ""),
        name=r.get("name", r.get("title", "")),
        description=r.get("description", ""),
        likelihood=r.get("likelihood", ""),
        impact=r.get("impact", ""),
        status=r.get("status", r.get("treatmentStatus", "")),
        treatment=r.get("treatment", r.get("treatmentPlan", "")),
    )


@chat.function("list_risks", "List Risk Register entries.", action_type="read", chain_callable=True, data_model=RiskList, event="vanta-connector.list_risks")
async def list_risks(ctx, params: ListRisksParams) -> ActionResult:
    """List Risk Register entries."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    query: dict = {"pageSize": params.limit}
    if params.status:
        query["status"] = params.status
    if params.page_cursor:
        query["pageCursor"] = params.page_cursor
    try:
        data, _ = await client.request("GET", "/v1/risks", params=query)
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    cursor = (data or {}).get("results", {}).get("pageInfo", {}).get("endCursor", "")
    return ActionResult.success(data=RiskList(risks=[_risk_entity(r) for r in items], next_page_cursor=cursor or ""))


@chat.function("get_risk", "Read one Risk Register entry in full by id.", action_type="read", chain_callable=True, data_model=VantaRisk, event="vanta-connector.get_risk")
async def get_risk(ctx, params: RiskIdParams) -> ActionResult:
    """Read one Risk Register entry in full by id."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/v1/risks/{params.risk_id}")
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_risk_entity(data or {}))


@chat.function("create_risk", "Create a new Risk Register entry.", action_type="write", chain_callable=True, data_model=VantaRisk, event="vanta-connector.create_risk", effects=["vanta.risk.created"])
async def create_risk(ctx, params: CreateRiskParams) -> ActionResult:
    """Create a new Risk Register entry."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    body = {
        "name": params.name,
        "description": params.description,
        "likelihood": params.likelihood,
        "impact": params.impact,
    }
    if params.risk_scenario_id:
        body["riskScenarioId"] = params.risk_scenario_id
    try:
        data, _ = await client.request("POST", "/v1/risks", json_body=body)
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_risk_entity(data or {}), summary="Risk created in the Risk Register.")


@chat.function("update_risk", "Update selected fields of an existing Risk Register entry (status, treatment plan). Only given fields change.", action_type="write", chain_callable=True, data_model=VantaRisk, event="vanta-connector.update_risk", effects=["vanta.risk.updated"])
async def update_risk(ctx, params: UpdateRiskParams) -> ActionResult:
    """Update selected fields of an existing Risk Register entry (status, treatment plan). Only given fields change."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    body = {}
    if params.status:
        body["status"] = params.status
    if params.treatment:
        body["treatment"] = params.treatment
    if params.likelihood:
        body["likelihood"] = params.likelihood
    if params.impact:
        body["impact"] = params.impact
    try:
        data, _ = await client.request("PATCH", f"/v1/risks/{params.risk_id}", json_body=body)
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_risk_entity(data or {}), summary="Risk updated.")


@chat.function("list_risk_scenarios", "List Risk Scenarios (the named risk categories Risk Register entries can be tied to).", action_type="read", chain_callable=True, data_model=RiskScenarioList, event="vanta-connector.list_risk_scenarios")
async def list_risk_scenarios(ctx, params: ListRiskScenariosParams) -> ActionResult:
    """List Risk Scenarios (the named risk categories Risk Register entries can be tied to)."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", "/v1/risk-scenarios")
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    scenarios = [VantaRiskScenario(scenario_id=s.get("id", ""), name=s.get("name", ""), description=s.get("description", "")) for s in items]
    return ActionResult.success(data=RiskScenarioList(scenarios=scenarios))


# ---- Vendors ----

def _vendor_entity(v: dict) -> VantaVendor:
    return VantaVendor(
        vendor_id=v.get("id", ""),
        name=v.get("name", ""),
        risk_tier=v.get("riskTier", v.get("riskLevel", "")),
        status=v.get("status", v.get("securityReviewStatus", "")),
        last_review_date=v.get("lastReviewDate", v.get("lastAssessedAt", "")),
        next_review_date=v.get("nextReviewDate", ""),
    )


@chat.function("list_vendors", "List Vendor risk inventory (third-party risk management) entries.", action_type="read", chain_callable=True, data_model=VendorList, event="vanta-connector.list_vendors")
async def list_vendors(ctx, params: ListVendorsParams) -> ActionResult:
    """List Vendor risk inventory (third-party risk management) entries."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    query: dict = {"pageSize": params.limit}
    if params.page_cursor:
        query["pageCursor"] = params.page_cursor
    try:
        data, _ = await client.request("GET", "/v1/vendors", params=query)
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    cursor = (data or {}).get("results", {}).get("pageInfo", {}).get("endCursor", "")
    return ActionResult.success(data=VendorList(vendors=[_vendor_entity(v) for v in items], next_page_cursor=cursor or ""))


@chat.function("get_vendor", "Read one Vendor risk record in full by id.", action_type="read", chain_callable=True, data_model=VantaVendor, event="vanta-connector.get_vendor")
async def get_vendor(ctx, params: VendorIdParams) -> ActionResult:
    """Read one Vendor risk record in full by id."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/v1/vendors/{params.vendor_id}")
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_vendor_entity(data or {}))


@chat.function("create_vendor", "Register a new Vendor for risk tracking.", action_type="write", chain_callable=True, data_model=VantaVendor, event="vanta-connector.create_vendor", effects=["vanta.vendor.created"])
async def create_vendor(ctx, params: CreateVendorParams) -> ActionResult:
    """Register a new Vendor for risk tracking."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    body = {"name": params.name}
    if params.risk_tier:
        body["riskTier"] = params.risk_tier
    if params.description:
        body["description"] = params.description
    try:
        data, _ = await client.request("POST", "/v1/vendors", json_body=body)
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_vendor_entity(data or {}), summary="Vendor registered.")


@chat.function("update_vendor", "Update selected fields of an existing Vendor (risk tier, review status). Only given fields change.", action_type="write", chain_callable=True, data_model=VantaVendor, event="vanta-connector.update_vendor", effects=["vanta.vendor.updated"])
async def update_vendor(ctx, params: UpdateVendorParams) -> ActionResult:
    """Update selected fields of an existing Vendor (risk tier, review status). Only given fields change."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    body = {}
    if params.risk_tier:
        body["riskTier"] = params.risk_tier
    if params.status:
        body["status"] = params.status
    try:
        data, _ = await client.request("PATCH", f"/v1/vendors/{params.vendor_id}", json_body=body)
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_vendor_entity(data or {}), summary="Vendor updated.")


# ---- Documents (policies) ----

def _document_entity(d: dict) -> VantaDocument:
    return VantaDocument(
        document_id=d.get("id", ""),
        name=d.get("name", d.get("title", "")),
        status=d.get("status", ""),
        last_reviewed_date=d.get("lastReviewedDate", d.get("lastReviewedAt", "")),
        next_review_date=d.get("nextReviewDate", ""),
    )


@chat.function("list_documents", "List Policy Documents tracked in Vanta (with review status/dates).", action_type="read", chain_callable=True, data_model=DocumentList, event="vanta-connector.list_documents")
async def list_documents(ctx, params: ListDocumentsParams) -> ActionResult:
    """List Policy Documents tracked in Vanta (with review status/dates)."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    query: dict = {"pageSize": params.limit}
    if params.page_cursor:
        query["pageCursor"] = params.page_cursor
    try:
        data, _ = await client.request("GET", "/v1/documents", params=query)
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    cursor = (data or {}).get("results", {}).get("pageInfo", {}).get("endCursor", "")
    return ActionResult.success(data=DocumentList(documents=[_document_entity(d) for d in items], next_page_cursor=cursor or ""))


@chat.function("get_document", "Read one Policy Document in full by id.", action_type="read", chain_callable=True, data_model=VantaDocument, event="vanta-connector.get_document")
async def get_document(ctx, params: DocumentIdParams) -> ActionResult:
    """Read one Policy Document in full by id."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/v1/documents/{params.document_id}")
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_document_entity(data or {}))


# ---- People (personnel compliance) ----

def _person_entity(p: dict) -> VantaPerson:
    return VantaPerson(
        person_id=p.get("id", ""),
        full_name=p.get("fullName", p.get("name", "")),
        email=p.get("email", ""),
        employment_status=p.get("employmentStatus", ""),
        security_training_complete=bool(p.get("securityTrainingComplete", p.get("hasCompletedTraining", False))),
        offboarding_status=p.get("offboardingStatus", ""),
    )


@chat.function("list_people", "List Personnel records with security-training and offboarding compliance status.", action_type="read", chain_callable=True, data_model=PeopleList, event="vanta-connector.list_people")
async def list_people(ctx, params: ListPeopleParams) -> ActionResult:
    """List Personnel records with security-training and offboarding compliance status."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    query: dict = {"pageSize": params.limit}
    if params.page_cursor:
        query["pageCursor"] = params.page_cursor
    try:
        data, _ = await client.request("GET", "/v1/people", params=query)
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    cursor = (data or {}).get("results", {}).get("pageInfo", {}).get("endCursor", "")
    return ActionResult.success(data=PeopleList(people=[_person_entity(p) for p in items], next_page_cursor=cursor or ""))


@chat.function("get_person", "Read one Personnel record in full by id.", action_type="read", chain_callable=True, data_model=VantaPerson, event="vanta-connector.get_person")
async def get_person(ctx, params: PersonIdParams) -> ActionResult:
    """Read one Personnel record in full by id."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", f"/v1/people/{params.person_id}")
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    return ActionResult.success(data=_person_entity(data or {}))


# ---- Integrations, Groups, Monitored Computers ----

@chat.function("list_integrations", "List connected data-source Integrations (cloud/IdP/HR/ticketing) Vanta pulls evidence from, with their sync status.", action_type="read", chain_callable=True, data_model=IntegrationList, event="vanta-connector.list_integrations")
async def list_integrations(ctx, params: ListIntegrationsParams) -> ActionResult:
    """List connected data-source Integrations (cloud/IdP/HR/ticketing) Vanta pulls evidence from, with their sync status."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", "/v1/integrations")
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    integrations = [VantaIntegration(name=i.get("name", ""), status=i.get("status", ""), last_sync=i.get("lastSyncedAt", "")) for i in items]
    return ActionResult.success(data=IntegrationList(integrations=integrations))


@chat.function("list_groups", "List Groups (Vanta's grouping of resources/people for scoping tests).", action_type="read", chain_callable=True, data_model=GroupList, event="vanta-connector.list_groups")
async def list_groups(ctx, params: ListGroupsParams) -> ActionResult:
    """List Groups (Vanta's grouping of resources/people for scoping tests)."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    try:
        data, _ = await client.request("GET", "/v1/groups", params={"pageSize": params.limit})
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    groups = [VantaGroup(group_id=g.get("id", ""), name=g.get("name", ""), member_count=len(g.get("members") or [])) for g in items]
    return ActionResult.success(data=GroupList(groups=groups))


@chat.function("list_monitored_computers", "List employee computers Vanta monitors for device-compliance (disk encryption, screen lock, AV, OS updates).", action_type="read", chain_callable=True, data_model=MonitoredComputerList, event="vanta-connector.list_monitored_computers")
async def list_monitored_computers(ctx, params: ListMonitoredComputersParams) -> ActionResult:
    """List employee computers Vanta monitors for device-compliance (disk encryption, screen lock, AV, OS updates)."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    query: dict = {"pageSize": params.limit}
    if params.page_cursor:
        query["pageCursor"] = params.page_cursor
    try:
        data, _ = await client.request("GET", "/v1/monitored-computers", params=query)
    except vc.VantaError as exc:
        return ActionResult.error(str(exc), retryable=exc.retryable)
    items = (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])
    cursor = (data or {}).get("results", {}).get("pageInfo", {}).get("endCursor", "")
    computers = [VantaComputer(computer_id=x.get("id", ""), owner_email=x.get("ownerEmail", ""), hostname=x.get("hostname", ""), is_compliant=bool(x.get("isCompliant", False))) for x in items]
    return ActionResult.success(data=MonitoredComputerList(computers=computers, next_page_cursor=cursor or ""))


# ---- Value-add audit report ----

@chat.function("audit_compliance_posture", "Build one aggregated audit-readiness health report: failing tests, overdue risks, overdue vendor reviews, and documents past their review date.", action_type="read", chain_callable=True, data_model=ComplianceAudit, event="vanta-connector.audit_compliance_posture")
async def audit_compliance_posture(ctx, params: ConnectionRefParams) -> ActionResult:
    """Build one aggregated audit-readiness health report: failing tests, overdue risks, overdue vendor reviews, and documents past their review date."""
    c = await _resolve_connection(ctx, params.connection_id)
    client = _client_for(c)
    import datetime
    today = datetime.date.today().isoformat()

    async def _safe_list(path: str, query: dict) -> list[dict]:
        try:
            data, _ = await client.request("GET", path, params=query)
        except vc.VantaError:
            return []
        return (data or {}).get("results", {}).get("data", data.get("data", []) if isinstance(data, dict) else [])

    tests = await _safe_list("/v1/tests", {"pageSize": 200, "status": "FAIL"})
    risks = await _safe_list("/v1/risks", {"pageSize": 200})
    vendors = await _safe_list("/v1/vendors", {"pageSize": 200})
    documents = await _safe_list("/v1/documents", {"pageSize": 200})

    overdue_vendors = [v for v in vendors if (v.get("nextReviewDate") or "9999") < today]
    overdue_docs = [d for d in documents if (d.get("nextReviewDate") or "9999") < today]
    open_risks = [r for r in risks if (r.get("status") or "").lower() not in ("closed", "resolved", "accepted")]

    return ActionResult.success(data=ComplianceAudit(
        failing_test_count=len(tests),
        open_risk_count=len(open_risks),
        overdue_vendor_review_count=len(overdue_vendors),
        overdue_document_review_count=len(overdue_docs),
        failing_tests=[_test_entity(t) for t in tests[:20]],
    ))

