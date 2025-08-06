"""Ensure the Agent API key is propagated as HTTP header."""

from __future__ import annotations

from jentic.lib.agent_runtime.api_hub import JenticAPIClient


def test_header_injection(monkeypatch):
    client = JenticAPIClient(agent_api_key="ak_test_123")
    assert client.headers["X-JENTIC-API-KEY"] == "ak_test_123"
