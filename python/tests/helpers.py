"""Test helpers and lightweight fakes used across the Jentic SDK test-suite."""

from __future__ import annotations

from typing import Any, List

from jentic.lib.models import (
    APIIdentifier,
    ExecuteResponse,
    ExecutionRequest,
    SearchResult,
    LoadRequest,
    LoadResponse,
    GetFilesResponse,
    SearchRequest,
    SearchResponse,
)


class FakeBackend:
    """A minimal stub for :class:`jentic.lib.core_api.BackendAPI`."""

    def __init__(self) -> None:
        # Internal toggles to simulate error scenarios
        self.should_fail_search: bool = False
        self.should_fail_execute: bool = False

    # ---------------------------------------------------------------------
    # Public API expected by ``jentic.Jentic``
    # ---------------------------------------------------------------------
    async def list_apis(self) -> List[APIIdentifier]:  # noqa: D401 – simple
        return [APIIdentifier(api_vendor="github", api_name="repos", api_version="v1")]

    async def search(self, request: SearchRequest) -> SearchResponse:  # noqa: D401
        if self.should_fail_search:
            raise RuntimeError("forced search failure")
        dummy_result = SearchResult(
            id="op_dummy",
            path="/ping",
            method="GET",
            api_name="health",
            entity_type="operation",
            summary="Ping operation",
            description="A simple ping operation",
            match_score=0.99,
        )
        return SearchResponse(results=[dummy_result], total_count=1, query=request.query)

    async def load(self, request: LoadRequest) -> GetFilesResponse:  # noqa: D401
        # The real BackendAPI returns a GetFilesResponse; we shortcut by
        # returning the model-compatible dict so that LoadResponse.from_get_*
        # works without extra scaffolding.
        return GetFilesResponse(files={}, workflows={}, operations={})

    async def execute(self, request: ExecutionRequest) -> ExecuteResponse:  # noqa: D401
        if self.should_fail_execute:
            return ExecuteResponse(success=False, error="forced failure")
        return ExecuteResponse(success=True, output={"echo": request.inputs})
