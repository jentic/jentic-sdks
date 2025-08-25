"""Base HTTP transport with common functionality."""

import asyncio
import logging
import signal
import uuid
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from mcp.adapters.mcp import MCPAdapter
from mcp.config import load_config
from mcp.transport.base import BaseTransport
from mcp.transport.jsonrpc_handler import JSONRPCHandler

logger = logging.getLogger(__name__)


class HTTPBaseTransport(BaseTransport):
    """Base class for HTTP-based transports."""

    def __init__(
        self,
        adapter: MCPAdapter,
        host: str = "127.0.0.1",
        port: int = 8010,
        title: str = "Jentic MCP Server",
    ):
        """Initialize the HTTP base transport."""
        self.adapter = adapter
        self.host = host
        self.port = port
        self.config = load_config()
        self._app = FastAPI(title=title)
        self._server = None
        self._running = False
        self._active_connections: Dict[str, Dict[str, Any]] = {}
        
        # Common JSON-RPC handler
        self.jsonrpc_handler = JSONRPCHandler(adapter)
        
        # Set up common middleware and routes
        self._setup_common_middleware()
        self._setup_common_routes()
        self._setup_custom_routes()

    def _setup_common_middleware(self) -> None:
        """Set up common middleware (CORS, etc.)."""
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_common_routes(self) -> None:
        """Set up common routes that all HTTP transports need."""
        
        @self._app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return JSONResponse({
                "status": "ok", 
                "transport": self.get_transport_name()
            })

    def _setup_custom_routes(self) -> None:
        """Set up transport-specific routes. Override in subclasses."""
        pass

    def get_transport_name(self) -> str:
        """Get the transport name. Override in subclasses."""
        return "http-base"

    async def handle_jsonrpc_request(self, data: dict) -> dict:
        """Handle JSON-RPC request using the common handler."""
        # Validate JSON-RPC format
        if not isinstance(data, dict) or "jsonrpc" not in data or data["jsonrpc"] != "2.0":
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC request")
        
        method = data.get("method")
        if not method:
            raise HTTPException(status_code=400, detail="Missing method in JSON-RPC request")
        
        return await self.jsonrpc_handler.handle_request(data)

    def create_error_response(self, data: dict, error_message: str, error_code: int = -32603) -> dict:
        """Create a JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "id": data.get("id") if isinstance(data, dict) else None,
            "error": {
                "code": error_code,
                "message": error_message
            }
        }

    async def start(self) -> None:
        """Start the HTTP server."""
        config = uvicorn.Config(
            app=self._app, 
            host=self.host, 
            port=self.port, 
            log_level="info"
        )
        self._server = uvicorn.Server(config)
        self._running = True

        # Handle termination gracefully
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_exit)

        logger.info(f"Starting {self.get_transport_name()} server on {self.host}:{self.port}")
        await self._server.serve()

    async def stop(self) -> None:
        """Stop the HTTP server."""
        if self._server and self._running:
            self._running = False
            if hasattr(self._server, "should_exit"):
                self._server.should_exit = True
            logger.info(f"{self.get_transport_name()} server stopped")

    @property
    def is_running(self) -> bool:
        """Check if the HTTP server is running."""
        return self._running

    def _handle_exit(self, signum, frame):
        """Handle exit signals."""
        logger.info(f"Received signal {signum}, shutting down {self.get_transport_name()} server...")
        if self._server:
            self._server.should_exit = True
