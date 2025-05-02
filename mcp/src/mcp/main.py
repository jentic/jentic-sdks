"""Jentic MCP Plugin main entry point."""

import asyncio
import logging
import os
from enum import Enum

import typer
from rich.console import Console

from mcp.adapters.mcp import MCPAdapter
from mcp.transport.http import HTTPTransport
from mcp.transport.stdio import StdioTransport
from mcp.version import get_version_info


# Configure logging
def setup_logging(log_level: str, transport_mode: str, log_file: str | None = None) -> None:
    """Set up logging configuration.

    Args:
        log_level: Logging level as string (DEBUG, INFO, etc.)
        transport_mode: Transport mode (http or stdio)
        log_file: Optional log file path
    """
    level = getattr(logging, log_level.upper())

    # Reset the logging module
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Set root logger level
    logging.root.setLevel(level)

    # Use a default log file if none provided
    if (transport_mode == "stdio" or log_file) and not log_file:
        log_file = os.path.join(os.getcwd(), "jentic_ark2_mcp.log")

    # Format for all logs
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # In stdio mode or if log file explicitly provided, add a file handler
    if transport_mode == "stdio" or log_file:
        # Ensure the file is writable
        try:
            with open(log_file, "w") as f:
                f.write("")  # Just create/truncate it
            logging.info(f"Successfully created log file: {log_file}")
        except Exception as e:
            logging.warning(f"Failed to write to log file {log_file}: {e}")
            return

        # Create file handler
        try:
            file_handler = logging.FileHandler(log_file, mode="a")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logging.root.addHandler(file_handler)
            logging.info(f"Added file handler for {log_file}")
        except Exception as e:
            logging.error(f"Failed to create file handler: {e}")
            return

    # In HTTP mode, add a console handler
    if transport_mode == "http":
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logging.root.addHandler(console_handler)

    # Test if logging is working
    logging.info("Logging configured successfully")

    # Print debug info
    logging.debug(f"Logging configured with level {log_level}")
    logging.debug(f"Root logger has {len(logging.root.handlers)} handlers")
    for i, handler in enumerate(logging.root.handlers):
        logging.debug(f"  Handler {i+1}: {handler}")


logger = logging.getLogger(__name__)

app = typer.Typer(
    name="ark2-mcp",
    help="Jentic ARK² MCP Plugin - Connect agentic environments to Jentic's API Knowledge Hub",
    invoke_without_command=True,  # Ensure callback runs without command
)
console = Console()


class TransportMode(str, Enum):
    """Transport mode options."""

    HTTP = "http"
    STDIO = "stdio"


@app.callback()
def main(ctx: typer.Context):
    """Default to 'serve --transport stdio' if no subcommand is given."""
    if ctx.invoked_subcommand is None:
        # Import serve here if not already available globally in this scope
        # from .commands import serve # Example if serve is in another module
        serve(
            transport=TransportMode.STDIO,
            port=8010,  # Default port, though not used by stdio
            host="127.0.0.1", # Default host, though not used by stdio
            env_file=None,
            mock=False,
            log_level="INFO",
            log_file=None,
            debug_stdio=False,
        )


@app.command()
def serve(
    transport: TransportMode = typer.Option(
        TransportMode.HTTP, "--transport", "-t", help="Transport mode (http or stdio)"
    ),
    port: int = typer.Option(
        8010, "--port", "-p", help="Port to serve the MCP plugin on (HTTP mode only)"
    ),
    host: str = typer.Option(
        "127.0.0.1", "--host", help="Host to bind the server to (HTTP mode only)"
    ),
    env_file: str | None = typer.Option(
        None, "--env-file", "-e", help="Path to .env file for configuration"
    ),
    mock: bool = typer.Option(False, "--mock", help="Enable mock mode for testing"),
    log_level: str = typer.Option(
        "INFO", "--log-level", help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    ),
    log_file: str | None = typer.Option(
        None,
        "--log-file",
        help="Path to log file (if not provided, logs to jentic_ark2_mcp.log in stdio mode)",
    ),
    debug_stdio: bool = typer.Option(
        False,
        "--debug-stdio",
        help="Log stdio communication for debugging (CAUTION: will log all API requests/responses)",
    ),
) -> None:
    """Start the ARK² MCP Plugin server with the specified transport."""
    # Set up logging
    setup_logging(log_level, transport.value, log_file)

    # Load environment
    if env_file and os.path.exists(env_file):
        console.print(f"Loading environment from {env_file}")
        # Load environment variables from file
        from dotenv import load_dotenv

        load_dotenv(env_file)

    # If mock flag is set, override the environment variable
    if mock:
        os.environ["MOCK_ENABLED"] = "true"
        console.print("[bold yellow]Mock mode enabled[/bold yellow]")

    # Set up the adapter
    adapter = MCPAdapter()

    # List available tools for debugging
    from mcp.tools import get_all_tool_definitions

    tools = get_all_tool_definitions()
    logger.info(f"Registered {len(tools)} tools:")
    for tool in tools:
        logger.info(
            f"  - {tool['name']}: {tool['description'][:50]}{'...' if len(tool['description']) > 50 else ''}"
        )

    # Initialize the appropriate transport
    if transport == TransportMode.HTTP:
        transport_instance = HTTPTransport(adapter, host=host, port=port)
    else:  # stdio mode
        logger.info("ARK² MCP Plugin initializing in stdio mode")
        logger.info(f"Log file: {log_file or os.path.join(os.getcwd(), 'jentic_ark2_mcp.log')}")
        if debug_stdio:
            logger.info("Debug stdio mode enabled - all requests and responses will be logged")
        transport_instance = StdioTransport(adapter, debug_stdio=debug_stdio)

    # Run the transport
    try:
        asyncio.run(transport_instance.start())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Error running server: {e}")


@app.command()
def version() -> None:
    """Display version information for the ARK² MCP Plugin."""
    version_info: dict[str, str] = get_version_info()
    console.print("Jentic ARK² MCP Plugin")
    console.print(f"Version: {version_info['version']}")
    console.print(f"Build date: {version_info.get('build_date', 'N/A')}")


if __name__ == "__main__":
    app()
