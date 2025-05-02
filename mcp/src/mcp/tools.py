"""Tool definitions for the Jentic MCP Plugin, oriented towards a user in a chat app.

This module defines the tools available through the Model Configuration Protocol (MCP)
for a chat application user.

The typical flow for a user interaction:

1. SEARCH: Use search_apis to find actions based on the user's request (e.g., 'send a Discord message'). Keep track of 'operation_uuid' and 'workflow_uuid'.
2. CONFIRM: Show the user the best matching action(s) and confirm they want to proceed.
3. (Optional) LOAD: Use load_execution_info to get details about the action (like required inputs) if needed for clarification or complex actions.
4. EXECUTE: Use execute to perform the confirmed action for the user.

Always clearly communicate the steps to the user.
"""

from typing import Any

SEARCH_API_CAPABILITIES_TOOL = {
    "name": "search_apis",
    "description": "Search for available actions or information based on what the user wants to do (e.g., 'find Discord servers', 'send a message'). Use this first to understand what's possible.",
    "parameters": {
        "type": "object",
        "properties": {
            "capability_description": {
                "type": "string",
                "description": "Natural language description of the action needed (e.g., 'send emails', 'weather forecasting', 'natural language processing')",
            },
            "keywords": {
                "type": "array",
                "description": "Optional list of specific keywords to help narrow down the search",
                "items": {"type": "string"},
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of actions to return",
                "default": 5,
            },
        },
        "required": ["capability_description"],
    },
}

LOAD_CONFIG_TOOL = {
    "name": "load_execution_info",
    "description": (
        "Get more details about a specific action (like what information it needs from the user) before confirming you want to run it. "
        "Usually used if the action requires specific inputs. "
        "Coding Agents: To provide tools to an LLM that you have selected at runtime, use this tool to retrieve the necessary information and save it to 'jentic.json' at the root of your project."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "workflow_uuids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The UUIDs of the workflows to include in the configuration files.",
            },
            "operation_uuids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The UUIDs of the operations to include in the configuration files.",
            },
        },
        "required": ["workflow_uuids", "operation_uuids"],
    },
}

EXECUTE_TOOL = {
    "name": "execute",
    "description": "Perform the chosen action for the user using the provided details (if any are needed).",
    "parameters": {
        "type": "object",
        "properties": {
            "execution_type": {
                "type": "string",
                "enum": ["operation", "workflow"],
                "description": "Specify whether to execute an 'operation' or a 'workflow'.",
            },
            "uuid": {
                "type": "string",
                "description": "The UUID of the operation or workflow to execute.",
            },
            "inputs": {
                "type": "object",
                "description": "The input parameters required by the operation or workflow.",
                "additionalProperties": True, # Allow any structure for inputs
            },
        },
        "required": ["execution_type", "uuid", "inputs"],
    },
}

# Tool definitions complete


def get_all_tool_definitions() -> list[dict[str, Any]]:
    """Get all tool definitions for the Jentic MCP Plugin.

    Returns:
        List[Dict[str, Any]]: All tool definitions.
    """
    return [
        SEARCH_API_CAPABILITIES_TOOL,
        LOAD_CONFIG_TOOL,
        EXECUTE_TOOL,
    ]
