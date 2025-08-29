"""Streamable HTTP transport for MCP Inspector compatibility."""

import asyncio
import json
import logging
import uuid

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from mcp.adapters.mcp import MCPAdapter
from mcp.transport.http_base import HTTPBaseTransport

logger = logging.getLogger(__name__)


class StreamableHTTPTransport(HTTPBaseTransport):
    """Streamable HTTP transport for MCP Inspector."""

    def __init__(
        self,
        adapter: MCPAdapter,
        host: str = "127.0.0.1",
        port: int = 8010,
    ):
        """Initialize the Streamable HTTP transport."""
        super().__init__(
            adapter=adapter,
            host=host,
            port=port,
            title="Jentic MCP Server (Streamable HTTP)"
        )

    def get_transport_name(self) -> str:
        """Get the transport name."""
        return "streamable-http"

    def _setup_custom_routes(self) -> None:
        """Set up Streamable HTTP specific routes."""
        
        @self._app.get("/")
        async def streamable_http_sse(request: Request):
            """GET / - Streamable HTTP SSE endpoint."""
            logger.info("Streamable HTTP SSE connection established")
            
            async def event_stream():
                connection_id = str(uuid.uuid4())
                
                try:
                    # Store connection
                    self._active_connections[connection_id] = {
                        "request": request,
                        "message_queue": asyncio.Queue()
                    }
                    
                    # Send initial notification
                    initial_message = {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                        "params": {}
                    }
                    
                    yield f"data: {json.dumps(initial_message)}\n\n"
                    
                    # Process message queue
                    while True:
                        try:
                            if await request.is_disconnected():
                                break
                            
                            try:
                                message = await asyncio.wait_for(
                                    self._active_connections[connection_id]["message_queue"].get(),
                                    timeout=1.0
                                )
                                yield f"data: {json.dumps(message)}\n\n"
                            except asyncio.TimeoutError:
                                # Send keep-alive
                                yield f": keep-alive\n\n"
                                
                        except asyncio.CancelledError:
                            break
                        
                except Exception as e:
                    logger.error(f"SSE connection error: {e}")
                finally:
                    # Clean up connection
                    if connection_id in self._active_connections:
                        del self._active_connections[connection_id]
            
            return StreamingResponse(
                event_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                }
            )

        @self._app.post("/")
        async def streamable_http_post(request: Request):
            """POST / - Handle JSON-RPC messages."""
            try:
                data = await request.json()
                
                # Use the common JSON-RPC handler
                response = await self.handle_jsonrpc_request(data)
                
                # Send response to all active connections via SSE
                for connection_info in self._active_connections.values():
                    if "message_queue" in connection_info:
                        await connection_info["message_queue"].put(response)
                
                return JSONResponse(response)
                
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                error_response = self.create_error_response(
                    data if 'data' in locals() else {}, 
                    f"Internal error: {str(e)}"
                )
                return JSONResponse(error_response, status_code=500)
