"""Tests for the LLM tool specification manager."""

from pathlib import Path

import pytest

from jentic.agent_runtime.tool_specs import (
    LLMToolSpecManager,
    create_llm_tool_manager,
)


class TestLLMToolSpecManager:
    """Test suite for the LLM tool specification manager."""

    @pytest.fixture
    def sample_workflow(self):
        """Return a sample workflow for testing."""
        return {
            "workflowId": "testWorkflow",
            "description": "A test workflow",
            "api_name": "Discord",  # Vendor name for the workflow
            "inputs": {
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
            "steps": [
                {
                    "id": "step1",
                    "operation": {
                        "path": "/search",
                        "method": "GET",
                    },
                    "parameters": {
                        "q": "$inputs.query",
                        "limit": "$inputs.limit",
                    },
                },
            ],
            "output": "$steps.step1",
        }

    def test_create_llm_tool_manager(self):
        """Test that create_llm_tool_manager returns the correct manager."""
        manager = create_llm_tool_manager()
        assert isinstance(manager, LLMToolSpecManager)

    def test_load_workflows(self, sample_workflow):
        """Test loading workflows into the manager."""
        manager = create_llm_tool_manager()
        manager.load_workflows({"testWorkflow": sample_workflow})
        # Verify workflows are loaded (implementation-specific, testing through get_tool_specs)
        specs = manager.get_tool_specs("openai")
        assert len(specs["tools"]) == 1
        assert specs["tools"][0]["function"]["name"] == "Discord-testWorkflow"

    def test_extract_parameters(self, sample_workflow):
        """Test parameter extraction from workflows."""
        manager = create_llm_tool_manager()
        manager.load_workflows({"testWorkflow": sample_workflow})
        # Test through get_tool_specs
        specs = manager.get_tool_specs("openai")

        tool_params = specs["tools"][0]["function"]["parameters"]["properties"]
        assert "query" in tool_params
        assert tool_params["query"]["type"] == "string"
        assert tool_params["query"]["description"] == "Search query"

        assert "limit" in tool_params
        assert tool_params["limit"]["type"] == "integer"
        assert tool_params["limit"]["description"] == "Maximum number of results"
        assert tool_params["limit"]["default"] == 10

    def test_required_parameters(self, sample_workflow):
        """Test required parameter extraction from workflows."""
        manager = create_llm_tool_manager()
        manager.load_workflows({"testWorkflow": sample_workflow})
        # Test through get_tool_specs
        specs = manager.get_tool_specs("openai")

        required = specs["tools"][0]["function"]["parameters"]["required"]
        assert "query" in required
        assert "limit" not in required

    def test_openai_tool_specs(self, sample_workflow):
        """Test OpenAI tool spec generation."""
        manager = create_llm_tool_manager()
        manager.load_workflows({"testWorkflow": sample_workflow})

        specs = manager.get_tool_specs("openai")
        assert specs["format"] == "openai"
        assert len(specs["tools"]) == 1

        tool = specs["tools"][0]
        assert tool["type"] == "function"
        assert tool["function"]["name"] == "Discord-testWorkflow"
        assert tool["function"]["description"] == "A test workflow"
        assert tool["function"]["parameters"]["type"] == "object"
        assert "query" in tool["function"]["parameters"]["properties"]
        assert "limit" in tool["function"]["parameters"]["properties"]
        assert tool["function"]["parameters"]["required"] == ["query"]

    def test_anthropic_tool_specs(self, sample_workflow):
        """Test Anthropic tool spec generation."""
        manager = create_llm_tool_manager()
        manager.load_workflows({"testWorkflow": sample_workflow})

        specs = manager.get_tool_specs("anthropic")
        assert specs["format"] == "anthropic"
        assert len(specs["tools"]) == 1

        tool = specs["tools"][0]
        assert tool["name"] == "Discord-testWorkflow"
        assert tool["description"] == "A test workflow"
        assert tool["input_schema"]["type"] == "object"
        assert "query" in tool["input_schema"]["properties"]
        assert "limit" in tool["input_schema"]["properties"]
        assert tool["input_schema"]["required"] == ["query"]
        assert tool["input_schema"]["additionalProperties"] is False
        assert tool["input_schema"]["$schema"] == "http://json-schema.org/draft-07/schema#"

    def test_format_switching(self, sample_workflow):
        """Test that we can get tools in different formats."""
        manager = create_llm_tool_manager()
        manager.load_workflows({"testWorkflow": sample_workflow})

        # Get specs in OpenAI format
        openai_specs = manager.get_tool_specs("openai")
        assert openai_specs["format"] == "openai"
        assert len(openai_specs["tools"]) == 1
        assert openai_specs["tools"][0]["type"] == "function"

        # Get specs in Anthropic format
        claude_specs = manager.get_tool_specs("anthropic")
        assert claude_specs["format"] == "anthropic"
        assert len(claude_specs["tools"]) == 1
        assert "name" in claude_specs["tools"][0]

        # Both formats should represent the same tool
        assert openai_specs["tools"][0]["function"]["name"] == claude_specs["tools"][0]["name"]
        assert (
            openai_specs["tools"][0]["function"]["description"]
            == claude_specs["tools"][0]["description"]
        )

    def test_vendor_prefix_feature(self, sample_workflow):
        """Test that vendor prefixes are correctly added to tool names when enabled."""
        manager = create_llm_tool_manager()
        # Ensure vendor prefixes are enabled (default is True)
        manager.load_workflows({"testWorkflow": sample_workflow})
        
        # Test OpenAI format
        openai_specs = manager.get_tool_specs("openai")
        assert openai_specs["tools"][0]["function"]["name"] == "Discord-testWorkflow"
        
        # Test Anthropic format
        anthropic_specs = manager.get_tool_specs("anthropic")
        assert anthropic_specs["tools"][0]["name"] == "Discord-testWorkflow"
