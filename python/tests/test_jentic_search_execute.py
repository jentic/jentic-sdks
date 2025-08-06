"""End-to-end happy / failure paths for the high-level Jentic client."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from jentic import Jentic, ExecutionRequest, LoadRequest, SearchRequest
from helpers import FakeBackend


@pytest.mark.asyncio
async def test_search_load_execute_success(monkeypatch):
    """search → load → execute returns a successful ExecuteResponse."""

    fake = FakeBackend()
    # Inject fake backend into the Jentic instance
    client = Jentic.__new__(Jentic)  # bypass __init__
    client._backend = fake  # type: ignore[attr-defined]

    # --- act -------------------------------------------------------------
    sr = await client.search(SearchRequest(query="ping"))
    assert sr.total_count == 1

    entity_id = sr.results[0].id
    await client.load(LoadRequest(ids=[entity_id]))  # noqa: F821   # imported later

    resp = await client.execute(ExecutionRequest(id=entity_id, inputs={"foo": "bar"}))

    # --- assert ----------------------------------------------------------
    assert resp.success is True
    assert resp.output == {"echo": {"foo": "bar"}}


@pytest.mark.asyncio
async def test_search_failure(monkeypatch):
    fake = FakeBackend()
    fake.should_fail_search = True
    client = Jentic.__new__(Jentic)
    client._backend = fake  # type: ignore[attr-defined]

    with pytest.raises(RuntimeError):
        await client.search(SearchRequest(query="fails"))


@pytest.mark.asyncio
async def test_execute_failure(monkeypatch):
    fake = FakeBackend()
    fake.should_fail_execute = True
    client = Jentic.__new__(Jentic)
    client._backend = fake  # type: ignore[attr-defined]

    # search must succeed so we have an ID
    sr = await client.search(SearchRequest(query="ping"))
    entity_id = sr.results[0].id
    await client.load(LoadRequest(ids=[entity_id]))  # noqa: F821

    resp = await client.execute(ExecutionRequest(id=entity_id, inputs={}))
    assert resp.success is False
    assert resp.error == "forced failure"
