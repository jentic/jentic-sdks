"""AgentToolManager execution happy and failure scenarios."""

from __future__ import annotations

import pytest

from jentic.lib.agent_runtime.agent_tools import AgentToolManager


class DummyExecutor:
    """Pretend TaskExecutor that succeeds or fails deterministically."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    async def execute_workflow(self, uuid, inputs):  # noqa: D401
        if self.should_fail:
            return {"success": False, "error": "boom"}
        return {"success": True, "output": {"ok": True}}

    async def execute_operation(self, uuid, inputs):  # noqa: D401
        return await self.execute_workflow(uuid, inputs)


@pytest.mark.asyncio
async def test_execute_unknown_tool(monkeypatch):
    mgr = AgentToolManager()
    result = await mgr.execute_tool("nonexistent_tool", {})
    assert result["success"] is False


@pytest.mark.asyncio
async def test_execute_success(monkeypatch):
    # Patch internal TaskExecutor with dummy success executor
    mgr = AgentToolManager()
    monkeypatch.setattr(mgr, "tool_executor", DummyExecutor())
    # also monkeypatch spec manager to return operation id
    monkeypatch.setattr(mgr.tool_spec_manager, "get_tool_type", lambda name: "workflow")
    monkeypatch.setattr(mgr.tool_spec_manager, "get_workflow_uuid", lambda name: "wf_123")

    result = await mgr.execute_tool("hello", {})
    assert result["success"] is True
