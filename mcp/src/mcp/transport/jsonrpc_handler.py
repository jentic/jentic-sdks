"""Common JSON-RPC handler for MCP protocol."""

import json
import logging
from typing import Any, Dict

from mcp.adapters.mcp import MCPAdapter
from mcp import version

logger = logging.getLogger(__name__)


class JSONRPCHandler:
    """Common JSON-RPC handler for MCP protocol."""

    def __init__(self, adapter: MCPAdapter):
        """Initialize the JSON-RPC handler."""
        self.adapter = adapter

    async def handle_request(self, data: dict) -> dict:
        """Handle a JSON-RPC request and return the response."""
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")

        logger.info(f"Handling JSON-RPC method: {method} (id: {request_id})")

        try:
            if method == "initialize":
                return await self._handle_initialize(params, request_id)
            elif method == "notifications/initialized":
                # Handle initialized notification (no response needed)
                logger.info("Client initialization complete")
                return None
            elif method == "tools/list":
                return await self._handle_tools_list(params, request_id)
            elif method == "tools/call":
                return await self._handle_tools_call(params, request_id)
            elif method == "ping":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"pong": True}
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                }
        except Exception as e:
            logger.error(f"Error handling JSON-RPC method {method}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}",
                },
            }

    async def _handle_initialize(self, params: dict, request_id: Any) -> dict:
        """Handle initialize request."""
        logger.info(f"Handling initialize request (id: {request_id})")
        
        # Extract client info
        client_info = params.get("clientInfo", {})
        protocol_version = params.get("protocolVersion", "2024-11-05")
        
        logger.info(f"Client: {client_info.get('name', 'unknown')} v{client_info.get('version', 'unknown')}")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": protocol_version,
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "jentic",
                    "version": version.__version__
                },
            },
        }

    async def _handle_tools_list(self, params: dict, request_id: Any) -> dict:
        """Handle tools/list request."""
        logger.info(f"Handling tools/list request (id: {request_id})")
        
        from mcp.tools import get_all_tool_definitions
        tool_definitions = get_all_tool_definitions()
        
        tools = []
        for tool in tool_definitions:
            tools.append({
                "name": tool["name"],
                "description": tool["description"],
                "inputSchema": {
                    "type": "object",
                    "properties": tool["parameters"]["properties"],
                    "required": tool["parameters"].get("required", []),
                },
            })
        
        logger.info(f"Returning {len(tools)} tools")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools
            },
        }

    async def _handle_tools_call(self, params: dict, request_id: Any) -> dict:
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        logger.info(f"Handling tools/call for {tool_name} (id: {request_id})")
        
        # Map tool names to adapter methods
        tool_handlers = {
            "search_apis": self.adapter.search_api_capabilities,
            "load_execution_info": self.adapter.generate_runtime_config,
            "execute": self.adapter.execute,
            "submit_feedback": self.adapter.submit_feedback,
        }
        
        if tool_name not in tool_handlers:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}",
                },
            }
        
        try:
            result = await tool_handlers[tool_name](arguments)
            logger.info(f"Tool {tool_name} executed successfully")
            
            # Format result - extract actual result if wrapped
            if isinstance(result, dict) and "result" in result:
                actual_result = result["result"]
            else:
                actual_result = result
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(actual_result, indent=2)
                        }
                    ]
                },
            }
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": f"Tool execution error: {str(e)}",
                },
            }
