"""Pydantic input contracts and SDL result entities for Vanta Connector."""
from __future__ import annotations

from imperal_sdk import sdl
from pydantic import BaseModel, Field


class NoParams(BaseModel):
    pass


class ConnectionRefParams(BaseModel):
    connection_id: str = Field("", description="Optional saved Vanta organization connection ID. Omit to use the first connected organization.")


class ConnectVantaParams(BaseModel):
    label: str = Field("", description="Friendly organization label, e.g. 'Acme Corp — Production'.")
    client_id: str = Field(..., description="Vanta API application Client ID, from Settings > API.")
    client_secret: str = Field(..., description="Vanta API application Client Secret.")
    base_url: str = Field("", description="Optional API base URL override for segregated tenants. Defaults to https://api.vanta.com.")


class DisconnectVantaParams(ConnectionRefParams):
    connection_id: str = Field(..., description="Saved Vanta organization connection ID to remove from Imperal.")


class ListTestsParams(ConnectionRefParams):
    status: str = Field("", description="Optional status filter: OK, FAIL, DISABLED, OUTDATED, NOT_APPLICABLE.")
    limit: int = Field(50, description="Max tests to return (1-200).")
    page_cursor: str = Field("", description="Pagination cursor from a previous call's next_page_cursor.")


class TestIdParams(ConnectionRefParams):
    test_id: str = Field(..., description="Vanta test ID.")


class ListControlsParams(ConnectionRefParams):
    framework_id: str = Field("", description="Optional framework ID to filter controls to one framework.")
    limit: int = Field(50, description="Max controls to return (1-200).")
    page_cursor: str = Field("", description="Pagination cursor from a previous call's next_page_cursor.")


class ControlIdParams(ConnectionRefParams):
    control_id: str = Field(..., description="Vanta control ID.")


class ListFrameworksParams(ConnectionRefParams):
    pass


class ListRisksParams(ConnectionRefParams):
    status: str = Field("", description="Optional risk status filter, e.g. 'open', 'closed', 'accepted'.")
    limit: int = Field(50, description="Max risks to return (1-200).")
    page_cursor: str = Field("", description="Pagination cursor from a previous call's next_page_cursor.")


class RiskIdParams(ConnectionRefParams):
    risk_id: str = Field(..., description="Vanta risk register entry ID.")


class CreateRiskParams(ConnectionRefParams):
    title: str = Field(..., description="Risk title.")
    description: str = Field("", description="Risk description.")
    likelihood: int = Field(3, description="Likelihood score, 1 (rare) to 5 (near-certain).")
    impact: int = Field(3, description="Impact score, 1 (negligible) to 5 (severe).")
    risk_scenario_id: str = Field("", description="Optional risk scenario/category ID to tie this risk to.")


class UpdateRiskParams(RiskIdParams):
    title: str = Field("", description="New title, or leave blank to keep unchanged.")
    description: str = Field("", description="New description, or leave blank to keep unchanged.")
    status: str = Field("", description="New status, e.g. 'open', 'closed', 'accepted', 'monitoring'. Leave blank to keep unchanged.")
    likelihood: int = Field(0, description="New likelihood score 1-5, or 0 to keep unchanged.")
    impact: int = Field(0, description="New impact score 1-5, or 0 to keep unchanged.")


class ListRiskScenariosParams(ConnectionRefParams):
    pass


class ListVendorsParams(ConnectionRefParams):
    limit: int = Field(50, description="Max vendors to return (1-200).")
    page_cursor: str = Field("", description="Pagination cursor from a previous call's next_page_cursor.")


class VendorIdParams(ConnectionRefParams):
    vendor_id: str = Field(..., description="Vanta vendor ID.")


class CreateVendorParams(ConnectionRefParams):
    name: str = Field(..., description="Vendor name.")
    website: str = Field("", description="Vendor website URL.")
    description: str = Field("", description="What this vendor is used for.")


class UpdateVendorParams(VendorIdParams):
    risk_tier: str = Field("", description="New risk tier, e.g. 'critical', 'high', 'medium', 'low'. Leave blank to keep unchanged.")
    status: str = Field("", description="New review status. Leave blank to keep unchanged.")


class ListDocumentsParams(ConnectionRefParams):
    limit: int = Field(50, description="Max documents to return (1-200).")
    page_cursor: str = Field("", description="Pagination cursor from a previous call's next_page_cursor.")


class DocumentIdParams(ConnectionRefParams):
    document_id: str = Field(..., description="Vanta document ID.")


class ListPeopleParams(ConnectionRefParams):
    limit: int = Field(50, description="Max personnel records to return (1-200).")
    page_cursor: str = Field("", description="Pagination cursor from a previous call's next_page_cursor.")


class PersonIdParams(ConnectionRefParams):
    person_id: str = Field(..., description="Vanta personnel record ID.")


class ListIntegrationsParams(ConnectionRefParams):
    pass


class ListGroupsParams(ConnectionRefParams):
    limit: int = Field(50, description="Max groups to return (1-200).")


class ListMonitoredComputersParams(ConnectionRefParams):
    limit: int = Field(50, description="Max monitored computers to return (1-200).")
    page_cursor: str = Field("", description="Pagination cursor from a previous call's next_page_cursor.")


class DismissTestParams(TestIdParams):
    reason: str = Field(..., description="Reason for dismissing this test (recorded in Vanta as justification).")


# ---- SDL entities ----

class VantaConnection(sdl.Entity):
    id: str = ""
    title: str = ""
    connection_id: str
    label: str
    base_url: str


class ConnectionList(sdl.Entity):
    id: str = ""
    title: str = ""
    connections: list[VantaConnection]


class VantaTest(sdl.Entity):
    id: str = ""
    title: str = ""
    test_id: str
    name: str
    status: str
    frameworks: str
    last_checked: str


class TestList(sdl.Entity):
    id: str = ""
    title: str = ""
    tests: list[VantaTest]
    next_page_cursor: str


class VantaControl(sdl.Entity):
    id: str = ""
    title: str = ""
    control_id: str
    name: str
    frameworks: str
    test_count: int
    status: str


class ControlList(sdl.Entity):
    id: str = ""
    title: str = ""
    controls: list[VantaControl]
    next_page_cursor: str


class VantaFramework(sdl.Entity):
    id: str = ""
    title: str = ""
    framework_id: str
    name: str
    status: str
    tests_passing: int
    tests_total: int


class FrameworkList(sdl.Entity):
    id: str = ""
    title: str = ""
    frameworks: list[VantaFramework]


class VantaRisk(sdl.Entity):
    id: str = ""
    risk_id: str
    title: str
    likelihood: int
    impact: int
    status: str
    owner: str


class RiskList(sdl.Entity):
    id: str = ""
    title: str = ""
    risks: list[VantaRisk]
    next_page_cursor: str


class VantaRiskScenario(sdl.Entity):
    id: str = ""
    title: str = ""
    scenario_id: str
    name: str


class RiskScenarioList(sdl.Entity):
    id: str = ""
    title: str = ""
    scenarios: list[VantaRiskScenario]


class VantaVendor(sdl.Entity):
    id: str = ""
    title: str = ""
    vendor_id: str
    name: str
    risk_tier: str
    review_status: str
    last_reviewed: str


class VendorList(sdl.Entity):
    id: str = ""
    title: str = ""
    vendors: list[VantaVendor]
    next_page_cursor: str


class VantaDocument(sdl.Entity):
    id: str = ""
    title: str = ""
    document_id: str
    name: str
    document_type: str
    status: str
    last_updated: str


class DocumentList(sdl.Entity):
    id: str = ""
    title: str = ""
    documents: list[VantaDocument]
    next_page_cursor: str


class VantaPerson(sdl.Entity):
    id: str = ""
    title: str = ""
    person_id: str
    name: str
    email: str
    offboarded: bool
    training_status: str


class PeopleList(sdl.Entity):
    id: str = ""
    title: str = ""
    people: list[VantaPerson]
    next_page_cursor: str


class VantaIntegration(sdl.Entity):
    id: str = ""
    title: str = ""
    integration_id: str
    name: str
    category: str
    status: str


class IntegrationList(sdl.Entity):
    id: str = ""
    title: str = ""
    integrations: list[VantaIntegration]


class VantaGroup(sdl.Entity):
    id: str = ""
    title: str = ""
    group_id: str
    name: str
    member_count: int


class GroupList(sdl.Entity):
    id: str = ""
    title: str = ""
    groups: list[VantaGroup]


class VantaComputer(sdl.Entity):
    id: str = ""
    title: str = ""
    computer_id: str
    owner_email: str
    hostname: str
    is_compliant: bool


class MonitoredComputerList(sdl.Entity):
    id: str = ""
    title: str = ""
    computers: list[VantaComputer]
    next_page_cursor: str


class ComplianceAudit(sdl.Entity):
    id: str = ""
    title: str = ""
    organization: str
    failing_tests: int
    total_tests: int
    overdue_risks: int
    total_risks: int
    overdue_vendor_reviews: int
    total_vendors: int
    disabled_integrations: int
    notes: str


class DeleteResult(sdl.Entity):
    id: str = ""
    title: str = ""
    ok: bool
    detail: str
