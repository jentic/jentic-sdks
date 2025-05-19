"""Integration tests for the MCP functionality."""

import os
from typing import Any

import pytest
import pytest_asyncio

from mcp.adapters.mcp import MCPAdapter
from mcp.handlers import handle_request


class MockStdioTransport:
    """Mock stdio transport for testing without any side effects."""

    def __init__(self, adapter):
        """Initialize the mock stdio transport."""
        self.adapter = adapter
        self.received_messages = []
        self.sent_responses = []

    async def send_response(self, response: dict[str, Any]) -> None:
        """Record sent responses."""
        self.sent_responses.append(response)

    async def process_message(self, message: dict[str, Any]) -> None:
        """Process a mock message."""
        self.received_messages.append(message)

        tool_name = message.get("type")
        data = message.get("data", {})

        if not tool_name:
            await self.send_response({"error": "Invalid message format: missing 'type'"})
            return

        try:
            result = await handle_request(tool_name, data)
            await self.send_response(result)
        except Exception as e:
            await self.send_response({"error": str(e)})


@pytest_asyncio.fixture
async def mock_adapter():
    """Create an MCP adapter with mock components."""
    # Force mock mode on - this needs to be set before any other imports
    os.environ["MOCK_ENABLED"] = "true"

    # Create a temporary directory for test storage - explicitly use .test_output for tests
    temp_dir = os.path.join(os.getcwd(), ".test_output", "test_integration")
    os.makedirs(temp_dir, exist_ok=True)

    # Create the adapter
    adapter = MCPAdapter()

    try:
        yield adapter
    finally:
        # Reset the mock mode
        if "MOCK_ENABLED" in os.environ:
            del os.environ["MOCK_ENABLED"]


@pytest_asyncio.fixture
async def mcp_transport(mock_adapter):
    """Create a mock transport for testing."""
    transport = MockStdioTransport(adapter=mock_adapter)
    return transport


@pytest.mark.asyncio
async def test_search_api_capabilities(mcp_transport):
    """Test the search_api_capabilities MCP command."""
    # Send a search request
    await mcp_transport.process_message(
        {"type": "search_apis", "data": {"capability_description": "spotify music"}}
    )

    # Verify we got a response
    assert len(mcp_transport.sent_responses) == 1

    # Verify the response structure
    response = mcp_transport.sent_responses[0]
    assert "result" in response
    assert "matches" in response["result"]
    assert "query" in response["result"]
    assert "total_matches" in response["result"]

    # In mock mode, we should get some results
