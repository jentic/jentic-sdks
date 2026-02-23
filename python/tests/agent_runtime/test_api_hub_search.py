"""Tests for api_hub.py search_api_capabilities with the new WorkflowSearchResult format.

Covers:
- search_api_capabilities parsing of new-format workflow results (api_references)
- search_api_capabilities parsing of legacy-format workflow results (api_name)
- ensure_api_names_in_response with new and legacy formats
"""

from unittest.mock import AsyncMock, patch

import pytest

from jentic.lib.agent_runtime.api_hub import JenticAPIClient


@pytest.fixture
def api_client() -> JenticAPIClient:
    return JenticAPIClient(base_url="https://test.example.com", agent_api_key="test-key")


# ---------------------------------------------------------------------------
# ensure_api_names_in_response
# ---------------------------------------------------------------------------

class TestEnsureApiNamesInResponse:
    """Test the ensure_api_names_in_response method."""

    def test_workflow_with_api_references_list_format(self, api_client):
        """Workflow search results in list format with api_references should derive api_name."""
        response_data = {
            "workflows": [
                {
                    "id": "wf_1",
                    "workflow_id": "sendMessage",
                    "name": "Send Message",
                    "api_references": [
                        {"api_id": "a1", "api_name": "discord.com", "api_version": "10"},
                    ],
                },
            ],
        }
        result = api_client.ensure_api_names_in_response(response_data)
        assert result["workflows"][0]["api_name"] == "discord.com"

    def test_workflow_with_existing_api_name_not_overwritten(self, api_client):
        """If api_name is already present, it should not be overwritten."""
        response_data = {
            "workflows": [
                {
                    "id": "wf_1",
                    "api_name": "existing.com",
                    "api_references": [
                        {"api_id": "a1", "api_name": "different.com", "api_version": "1"},
                    ],
                },
            ],
        }
        result = api_client.ensure_api_names_in_response(response_data)
        assert result["workflows"][0]["api_name"] == "existing.com"

    def test_workflow_without_api_references_or_api_name(self, api_client):
        """Workflow with neither api_name nor api_references should remain without api_name."""
        response_data = {
            "workflows": [
                {"id": "wf_1", "workflow_id": "wf", "name": "WF"},
            ],
        }
        result = api_client.ensure_api_names_in_response(response_data)
        assert "api_name" not in result["workflows"][0]

    def test_operation_dict_format(self, api_client):
        """Operations in dict format should still be enriched via api_references."""
        response_data = {
            "operations": {
                "op_1": {
                    "id": "op_1",
                    "api_references": [
                        {"api_id": "a1", "api_name": "github.com", "api_version": "3"},
                    ],
                },
            },
        }
        result = api_client.ensure_api_names_in_response(response_data)
        assert result["operations"]["op_1"]["api_name"] == "github.com"

    def test_empty_api_references_no_api_name(self, api_client):
        """Empty api_references should not set api_name."""
        response_data = {
            "workflows": [
                {"id": "wf_1", "api_references": []},
            ],
        }
        result = api_client.ensure_api_names_in_response(response_data)
        assert "api_name" not in result["workflows"][0]

    def test_workflow_dict_format_with_api_references(self, api_client):
        """Workflows in dict format (execution info) with api_references."""
        response_data = {
            "workflows": {
                "wf_1": {
                    "id": "wf_1",
                    "api_references": [
                        {"api_id": "a1", "api_name": "hubspot.com", "api_version": "3"},
                    ],
                },
            },
        }
        result = api_client.ensure_api_names_in_response(response_data)
        assert result["workflows"]["wf_1"]["api_name"] == "hubspot.com"

    def test_multi_api_references_uses_first(self, api_client):
        """When multiple api_references, derive api_name from the first."""
        response_data = {
            "workflows": [
                {
                    "id": "wf_1",
                    "api_references": [
                        {"api_id": "a1", "api_name": "first.com", "api_version": "1"},
                        {"api_id": "a2", "api_name": "second.com", "api_version": "2"},
                    ],
                },
            ],
        }
        result = api_client.ensure_api_names_in_response(response_data)
        assert result["workflows"][0]["api_name"] == "first.com"


# ---------------------------------------------------------------------------
# search_api_capabilities — new workflow format
# ---------------------------------------------------------------------------

class TestSearchApiCapabilities:
    """Test search_api_capabilities with new-format workflow results."""

    @pytest.mark.asyncio
    async def test_new_format_workflow_parsed(self, api_client):
        """Workflows with api_references should parse correctly."""
        mock_search_response = {
            "workflows": [
                {
                    "id": "wf_1",
                    "workflow_id": "sendMessage",
                    "name": "Send Message",
                    "description": "Send a Discord message",
                    "distance": 0.15,
                    "entity_type": "workflow",
                    "api_references": [
                        {"api_id": "a1", "api_name": "discord.com", "api_version": "10"},
                    ],
                },
            ],
            "operations": [],
        }

        with patch.object(api_client, "_search_all", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_response

            from jentic.lib.models import SearchRequest
            request = SearchRequest(query="send discord message")
            result = await api_client.search_api_capabilities(request)

        workflows = [r for r in result.results if r.entity_type == "workflow"]
        assert len(workflows) == 1
        wf = workflows[0]
        assert wf.id == "wf_1"
        assert wf.api_name == "discord.com"
        assert wf.summary == "sendMessage"
        assert wf.api_references is not None
        assert wf.api_references[0].api_name == "discord.com"

    @pytest.mark.asyncio
    async def test_legacy_format_workflow_still_works(self, api_client):
        """Old-style results with top-level api_name should still work."""
        mock_search_response = {
            "workflows": [
                {
                    "id": "wf_2",
                    "workflow_id": "legacyWf",
                    "name": "Legacy Workflow",
                    "description": "A legacy workflow",
                    "distance": 0.3,
                    "entity_type": "workflow",
                    "api_name": "legacy.com",
                },
            ],
            "operations": [],
        }

        with patch.object(api_client, "_search_all", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_response

            from jentic.lib.models import SearchRequest
            request = SearchRequest(query="legacy search")
            result = await api_client.search_api_capabilities(request)

        workflows = [r for r in result.results if r.entity_type == "workflow"]
        assert len(workflows) == 1
        assert workflows[0].api_name == "legacy.com"

    @pytest.mark.asyncio
    async def test_multi_api_workflow(self, api_client):
        """Workflows referencing multiple APIs should use first api_name."""
        mock_search_response = {
            "workflows": [
                {
                    "id": "wf_multi",
                    "workflow_id": "multiApiWf",
                    "name": "Multi-API Workflow",
                    "description": "Uses two APIs",
                    "distance": 0.1,
                    "entity_type": "workflow",
                    "api_references": [
                        {"api_id": "a1", "api_name": "discord.com", "api_version": "10"},
                        {"api_id": "a2", "api_name": "slack.com", "api_version": "2"},
                    ],
                },
            ],
            "operations": [],
        }

        with patch.object(api_client, "_search_all", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_response

            from jentic.lib.models import SearchRequest
            request = SearchRequest(query="multi api")
            result = await api_client.search_api_capabilities(request)

        workflows = [r for r in result.results if r.entity_type == "workflow"]
        wf = workflows[0]
        assert wf.api_name == "discord.com"
        assert len(wf.api_references) == 2

    @pytest.mark.asyncio
    async def test_workflow_no_api_info(self, api_client):
        """Workflow with neither api_name nor api_references should get empty string."""
        mock_search_response = {
            "workflows": [
                {
                    "id": "wf_no_api",
                    "workflow_id": "noApiWf",
                    "name": "No API Workflow",
                    "description": "Missing API info",
                    "distance": 0.5,
                    "entity_type": "workflow",
                },
            ],
            "operations": [],
        }

        with patch.object(api_client, "_search_all", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_response

            from jentic.lib.models import SearchRequest
            request = SearchRequest(query="no api")
            result = await api_client.search_api_capabilities(request)

        workflows = [r for r in result.results if r.entity_type == "workflow"]
        assert workflows[0].api_name == ""

    @pytest.mark.asyncio
    async def test_operations_still_parsed(self, api_client):
        """Operations should still parse correctly alongside new-format workflows."""
        mock_search_response = {
            "workflows": [],
            "operations": [
                {
                    "id": "op_1",
                    "summary": "Create channel",
                    "description": "Create a Discord channel",
                    "path": "/guilds/{guild_id}/channels",
                    "method": "POST",
                    "api_name": "discord.com",
                    "distance": 0.2,
                    "entity_type": "operation",
                },
            ],
        }

        with patch.object(api_client, "_search_all", new_callable=AsyncMock) as mock_search:
            mock_search.return_value = mock_search_response

            from jentic.lib.models import SearchRequest
            request = SearchRequest(query="create channel")
            result = await api_client.search_api_capabilities(request)

        operations = [r for r in result.results if r.entity_type == "operation"]
        assert len(operations) == 1
        assert operations[0].api_name == "discord.com"
        assert operations[0].path == "/guilds/{guild_id}/channels"
