"""Vanta Connector -- App settings panel."""
from __future__ import annotations

from imperal_sdk import ui

import handlers as h
from app import ext


@ext.panel("vanta_settings", slot="center", title="Vanta settings", icon="Settings", center_overlay=True)
async def vanta_settings(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Text("No Vanta organization connected yet.", variant="body")
    rows = []
    for c in connections:
        rows.append(ui.Stack(direction="h", gap=2, align="center", children=[
            ui.Text(c.get("label") or c.get("client_id", ""), variant="body"),
            ui.Button("Disconnect", variant="destructive", on_click=ui.Call("disconnect_vanta", {"connection_id": c.get("id", "")})),
        ]))
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Connected organizations", level=2),
        *rows,
    ])
