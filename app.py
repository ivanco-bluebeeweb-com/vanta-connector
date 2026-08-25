"""Vanta Connector extension declaration.

Vanta is a Compliance Automation / GRC platform: continuous monitoring of
control frameworks (SOC 2, ISO 27001, HIPAA, PCI DSS, GDPR, NIST, custom),
a Risk Register, Vendor risk inventory, Policy documents and Personnel
compliance tracking, exposed through the Vanta Public API
(api.vanta.com) via OAuth2 Client Credentials.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "vanta-connector",
    version="0.1.0",
    display_name="Vanta",
    description=(
        "Connect your own Vanta organization (OAuth2 Client Credentials) to "
        "monitor compliance Tests/Controls/Frameworks, manage the Risk "
        "Register and Vendor risk inventory, review Policy documents and "
        "Personnel compliance status, and get an aggregated audit-readiness "
        "health report."
    ),
    icon="icon.svg",
    capabilities=["vanta:read", "vanta:write"],
    actions_explicit=True,
    system=False,
)

chat = ChatExtension(
    ext,
    tool_name="vanta",
    description=(
        "Vanta Connector — manage compliance Tests, Controls, Frameworks, "
        "Risk Register, Vendors, Documents, Personnel and Integrations for "
        "a Vanta organization."
    ),
)

ext.secret(
    "vanta_connections",
    "JSON list of connected Vanta organizations and encrypted OAuth2 Client Credentials. Managed only through connect_vanta and disconnect_vanta.",
    required=True,
    write_mode="both",
    max_bytes=65536,
    rotation_hint_days=90,
)(lambda: None)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report whether at least one Vanta organization connection is saved."""
    import json

    raw = await ctx.secrets.get("vanta_connections")
    connections = []
    if raw:
        try:
            connections = json.loads(raw)
        except (TypeError, ValueError):
            connections = []
    return {
        "healthy": True,
        "connected": len(connections) > 0,
        "connection_count": len(connections),
    }
