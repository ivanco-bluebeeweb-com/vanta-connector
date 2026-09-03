"""Vanta Connector panels.

SIDEBAR CONTENT -- NO CARDS ANYWHERE, per ~/UI_INTERFACE_STANDARD.md's
"left sidebar, no decorated cards" rule (same convention as Ping Identity's /
Okta Connector's panels.py). Every section is a plain ui.Stack, stacked
vertically and left-aligned, no Card border/background/shadow. Disconnect
lives only in "App settings" (panels_settings.py). The one secondary
"App settings" button is always the LAST element at the bottom of the
sidebar.

Per Vlad's standing rule: every input carries its own label (not just a
placeholder), placeholders are contextually specific, the form container is
stretched to the full width of the left sidebar with its contents stretched
to fill it, and the sidebar carries NO instructions that duplicate the
"How do I set this up?" modal.
"""
from __future__ import annotations

from imperal_sdk import ui

import handlers as h
from app import ext


def _field(label: str, node: ui.UINode) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, align="stretch", children=[
        ui.Text(label, variant="caption"),
        node,
    ])


def _settings_button() -> ui.UINode:
    return ui.Button(
        "App settings", variant="secondary", size="sm", icon="Settings", on_click=ui.Call("__panel__vanta_settings"),
    )


@ext.panel("vanta_sidebar", slot="left", title="Vanta")
async def vanta_sidebar(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Button("How do I get this?", variant="ghost", size="sm", icon="HelpCircle",
                      on_click=ui.Call("__panel__vanta_connect_help")),
            ui.Button("Sign in with Vanta (OAuth 2.0 / SSO)", variant="primary", size="sm", icon="login"),
            ui.Divider(),
            ui.Text("Or connect via OAuth2 Client Credentials", variant="caption"),
            ui.Form(action="connect_vanta", submit_label="Connect", children=[
                _field("Organization label", ui.Input(param_name="label", placeholder="Acme Corp — Production")),
                _field("Client ID", ui.Input(param_name="client_id", placeholder="vnt_client_8f2a1c...")),
                _field("Client Secret", ui.Password(param_name="client_secret", placeholder="vnt_secret_...")),
                _field("Base URL (optional)", ui.Input(param_name="base_url", placeholder="https://api.vanta.com")),
            ]),
        ])
    c = connections[0]
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text(c.get("label") or c.get("client_id", ""), variant="body"),
        ui.Divider(),
        ui.Button("Compliance overview", variant="ghost", size="sm", icon="ShieldCheck",
                  on_click=ui.Call("__panel__vanta_overview")),
        ui.Button("Tests", variant="ghost", size="sm", icon="CheckCircle2",
                  on_click=ui.Call("__panel__vanta_tests")),
        ui.Button("Controls", variant="ghost", size="sm", icon="ListChecks",
                  on_click=ui.Call("__panel__vanta_controls")),
        ui.Button("Frameworks", variant="ghost", size="sm", icon="Layers",
                  on_click=ui.Call("__panel__vanta_frameworks")),
        ui.Button("Risk register", variant="ghost", size="sm", icon="AlertTriangle",
                  on_click=ui.Call("__panel__vanta_risks")),
        ui.Button("Vendors", variant="ghost", size="sm", icon="Building2",
                  on_click=ui.Call("__panel__vanta_vendors")),
        ui.Button("Documents", variant="ghost", size="sm", icon="FileText",
                  on_click=ui.Call("__panel__vanta_documents")),
        ui.Button("Personnel", variant="ghost", size="sm", icon="Users",
                  on_click=ui.Call("__panel__vanta_people")),
        ui.Button("Integrations", variant="ghost", size="sm", icon="Plug",
                  on_click=ui.Call("__panel__vanta_integrations")),
        ui.Divider(),
        _settings_button(),
    ])


@ext.panel("vanta_connect_help", slot="center", title="How do I get this?", center_overlay=True)
async def vanta_connect_help(ctx, **kwargs) -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Text("1. In Vanta, go to Settings > API.", variant="body"),
        ui.Text("2. Create a new API application and choose the scopes it needs (read-only, or read+write for the sections you plan to manage from here).", variant="body"),
        ui.Text("3. Copy its Client ID and Client Secret and paste them into the form. This is a separate API application — not your personal Vanta login.", variant="body"),
        ui.Text("4. Access here will be exactly what you granted that application in Vanta itself.", variant="caption"),
    ])