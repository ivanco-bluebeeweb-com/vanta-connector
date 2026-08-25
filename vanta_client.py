"""Thin Vanta Public API REST client.

Auth model: OAuth2 client-credentials (client_id + client_secret from a Vanta
API application created in Settings > API). Base URL defaults to
https://api.vanta.com but is kept configurable for segregated tenants.
"""
from __future__ import annotations

import time
from typing import Any

import httpx

_DEFAULT_BASE = "https://api.vanta.com"
_TOKEN_PATH = "/oauth/token"


class VantaError(RuntimeError):
    """A safe provider-facing error; never includes credentials."""

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class VantaClient:
    """REST client for the Vanta Public API, scoped to one organization."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = "",
        *,
        timeout: float = 30.0,
    ):
        if not client_id or not client_secret:
            raise VantaError("Client ID and Client Secret are required.")
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = (base_url or _DEFAULT_BASE).rstrip("/")
        self.timeout = timeout
        self._access_token = ""
        self._token_expiry = 0.0

    async def _ensure_token(self) -> str:
        if self._access_token and time.time() < self._token_expiry - 30:
            return self._access_token
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(
                    f"{self.base_url}{_TOKEN_PATH}",
                    json={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "grant_type": "client_credentials",
                        "scope": "vanta-api.all:read vanta-api.all:read-private vanta-api.all:write",
                    },
                    headers={"Content-Type": "application/json"},
                )
            except httpx.HTTPError as exc:
                raise VantaError(f"Could not reach Vanta auth endpoint: {exc}", retryable=True) from exc
        if resp.status_code == 401:
            raise VantaError("Invalid Client ID or Client Secret.")
        if resp.status_code >= 400:
            raise VantaError(f"Vanta auth failed ({resp.status_code}): {resp.text[:300]}")
        data = resp.json()
        self._access_token = data.get("access_token", "")
        self._token_expiry = time.time() + float(data.get("expires_in", 3600))
        if not self._access_token:
            raise VantaError("Vanta auth response did not include an access token.")
        return self._access_token

    async def request(self, method: str, path: str, params: dict | None = None, json_body: dict | None = None) -> tuple[Any, dict]:
        token = await self._ensure_token()
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.request(method, url, params=params, json=json_body, headers=headers)
            except httpx.HTTPError as exc:
                raise VantaError(f"Could not reach Vanta: {exc}", retryable=True) from exc
        if resp.status_code == 401:
            raise VantaError("Authentication failed -- credentials may be invalid or revoked.")
        if resp.status_code == 403:
            raise VantaError("Forbidden -- this API application may be missing a required scope in Vanta > Settings > API.")
        if resp.status_code == 404:
            raise VantaError("Not found.")
        if resp.status_code == 429:
            raise VantaError("Rate limited by Vanta. Try again shortly.", retryable=True)
        if resp.status_code >= 500:
            raise VantaError(f"Vanta server error ({resp.status_code}).", retryable=True)
        if resp.status_code >= 400:
            raise VantaError(f"Vanta request failed ({resp.status_code}): {resp.text[:300]}")
        if resp.status_code == 204 or not resp.content:
            return None, dict(resp.headers)
        return resp.json(), dict(resp.headers)

    async def verify_connection(self) -> dict:
        """Cheap call used by connect_vanta to prove the credentials actually work."""
        data, _ = await self.request("GET", "/v1/organizations/summary")
        return data or {}
