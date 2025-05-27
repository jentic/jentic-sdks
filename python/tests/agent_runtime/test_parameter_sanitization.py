"""Tests for parameter name sanitization in the LLM tool specification manager."""

import pytest

from jentic.agent_runtime.tool_specs import (
    LLMToolSpecManager,
    create_llm_tool_manager,
)


def test_anthropic_parameter_sanitization():
    """Test that parameter names are properly sanitized for Anthropic schema."""
    # Operation with problematic keys (dots, spaces, etc.)
    sample_operation = {
        "method": "GET",
        "path": "/users",
        "inputs": {
            "properties": {
                "user.id": {"type": "string"},
                "name.first": {"type": "string"},
                "complex-key.with space": {"type": "string"},
            },
            "required": ["user.id"],
        },
    }

    manager = create_llm_tool_manager()
    manager.load_operations({"test-op-uuid": sample_operation})
    
    # Get anthropic tool specs
    specs = manager.get_tool_specs("anthropic")
    tool = specs["tools"][0]
    properties = tool["input_schema"]["properties"]
    required = tool["input_schema"]["required"]
    
    # Verify keys were sanitized correctly
    assert "user_id" in properties
    assert "name_first" in properties
    assert "complex-key_with_space" in properties
    assert "user.id" not in properties
    
    # Verify required list was also sanitized
    assert "user_id" in required
    
    # Verify mapping is created for restoration
    mapping = manager._parameter_mappings[tool["name"]]
    assert mapping["user_id"] == "user.id"
    
    # Test parameter restoration
    test_inputs = {"user_id": "123", "name_first": "John"}
    restored = manager.restore_input_parameter_names(tool["name"], test_inputs)
    assert "user.id" in restored
    assert restored["user.id"] == "123"


def test_edge_case_parameter_sanitization():
    """Test edge cases for parameter name sanitization."""
    sample_operation = {
        "method": "GET",
        "path": "/edge-cases",
        "inputs": {
            "properties": {
                "": {"type": "string"},  # Empty string
                "a" * 100: {"type": "string"},  # Very long key
                "!@#$%^&*()": {"type": "string"},  # Only special chars
                " leading-trailing ": {"type": "string"},  # Leading/trailing spaces
                "..multiple...dots..": {"type": "string"},  # Multiple dots
            },
            "required": ["!@#$%^&*()"],
        },
    }

    manager = create_llm_tool_manager()
    manager.load_operations({"edge-case-uuid": sample_operation})
    
    # Get anthropic tool specs
    specs = manager.get_tool_specs("anthropic")
    tool = specs["tools"][0]
    properties = tool["input_schema"]["properties"]
    required = tool["input_schema"]["required"]
    
    # Verify edge cases were handled correctly
    assert "param" not in properties  # Empty string or special chars should be excluded
    assert "" not in properties  # Empty string should be excluded
    assert "!@#$%^&*()" not in properties  # Special chars should be excluded
    assert len(list(filter(lambda k: k.startswith("a" * 60), properties.keys()))) == 1  # Truncated
    assert "leading-trailing" in properties  # Spaces removed
    assert "multiple_dots" in properties  # Multiple dots/underscores consolidated
    
    # Check that empty and special char keys were excluded, not added to mappings
    mapping = manager._parameter_mappings[tool["name"]]
    assert "" not in mapping.values()  # Empty string should be excluded
    assert "!@#$%^&*()" not in mapping.values()  # Special chars should be excluded
    
    # Verify required list excludes invalid parameters
    assert len(required) == 0  # Special chars in required list should be excluded
    
    # Test restoration with valid sanitized parameter names only
    edge_inputs = {
        list(filter(lambda k: k.startswith("a" * 60), properties.keys()))[0]: "truncated",
        "leading-trailing": "spaces_removed",
        "multiple_dots": "dots_consolidated"
    }
    
    restored = manager.restore_input_parameter_names(tool["name"], edge_inputs)
    # Verify proper restoration of valid sanitized names
    assert any(key.startswith("a" * 60) for key in restored)
    assert " leading-trailing " in restored
    assert "..multiple...dots.." in restored  
    long_key = list(filter(lambda k: len(k) >= 100, mapping.values()))
    assert len(long_key) == 1  # Should have one long key in mappings
    assert long_key[0] in restored  # Long key restored


def test_valid_parameter_names_unchanged():
    """Test that valid parameter names are not modified."""
    sample_operation = {
        "method": "GET",
        "path": "/users",
        "inputs": {
            "properties": {
                "user_id": {"type": "string"},
                "name": {"type": "string"},
                "page-number": {"type": "integer"},
            },
            "required": ["user_id"],
        },
    }

    manager = create_llm_tool_manager()
    manager.load_operations({"op-uuid": sample_operation})
    
    # Get anthropic tool specs
    specs = manager.get_tool_specs("anthropic")
    tool = specs["tools"][0]
    properties = tool["input_schema"]["properties"]
    
    # Verify valid keys remain unchanged
    assert "user_id" in properties
    assert "name" in properties
    assert "page-number" in properties
    
    # Verify mapping doesn't contain entries for valid keys
    mapping = manager._parameter_mappings.get(tool["name"], {})
    assert "user_id" not in mapping
    assert "name" not in mapping
    assert "page-number" not in mapping
