# Jentic SDK & MCP Plugin

Jentic MCP empowers AI agent builders to discover and integrate external APIs and workflows rapidly—without writing or maintaining API-specific code.

This repository contains the core Jentic SDK and the Jentic MCP Plugin.

- **[Jentic SDK](#jentic-sdk):** A comprehensive Python library for discovering and executing APIs and workflows, particularly for LLM tool use.
- **[Jentic MCP Plugin](#jentic-mcp-plugin):** A plugin enabling agents (like Windsurf) to discover and use Jentic capabilities via the MCP standard.

See the respective README files for more details:
- [Jentic SDK README](./python/README.md)
- [Jentic MCP Plugin README](./mcp/README.md)

The Jentic SDK is backed by the data in the [Open Agentic Knowledge (OAK)](https://github.com/jentic/oak) repository.

---

## Getting Started

### Jentic MCP Server

The quickest way to get started is to integrate the Jentic MCP plugin with your preferred MCP client (like Windsurf, Claude Desktop or Claude Code).

The recommended method is to run the server directly from the GitHub repository using `uvx`. 
You will need to install `uvx` first using `brew install uvx` or `pipx install uvx`.

```json
{
    "mcpServers": {
        "jentic": {
            "command": "uvx",
            "args": [
                "--from",
                "git+https://github.com/jentic/jentic-tools.git@main#subdirectory=mcp",
                "mcp"
            ],
            "env": {
                "SOME_ENV_VAR": "some_value"
            }
        }
    }
}
```

If using **Windsurf**, you can add this configuration to `~/.codeium/windsurf/mcp_config.json`. 
For **Claude Desktop**, you can add it to `~/Library/Application Support/Claude/claude_desktop_config.json`.
For other clients, check your client's documentation for how to add MCP servers.

_Note:_ After saving the configuration file, you may need to restart the client application (Windsurf, Claude Desktop) for the changes to take effect.

### MCP Tool Use

Once the MCP server is running, you can easily use the MCP tools in your LLM agent to discover and execute APIs and workflows.

1. `search_apis`: Search for APIs in the Jentic directory that match specific functionality needs
2. `load_execution_info`: Retrieve detailed specifications for APIs and operations from the Jentic directory. **This will include auth information you may need to provide in your `mcpServers.jentic.env` configuration.**
3. `execute`: Execute a specific API or workflow operation.

### Local Development
If you are developing the MCP plugin locally, you can configure your client to run it from your local path. Replace `/absolute/path/to/sdk/mcp` with the correct absolute path to the `mcp` directory in this repository:

```json
// Example for Windsurf (adjust path and key for Claude Desktop)
{
    "mcpServers": {
        "jentic-local": {
            "command": "uvx",
            "args": [
                "--from",
                "/absolute/path/to/sdk/mcp", 
                "mcp"
            ]
        }
    }
}
```


**Jentic SDK Use**

`pip install jentic`

**Jentic for Building and Executing LLM Tools**

To provide tools to your LLM that you have selected at runtime, ask your coding agent to use the `load_execution_info` tool to retrieve the necessary information and save it to `jentic.json` at the root of your project.

A typical agent loop with tool use looks like this:

```python
from jentic import Jentic

class MyAgent:
    def __init__(self):
        self.jentic = Jentic()
        # Generate tool definitions compatible with your LLM (e.g., "anthropic", "openai")
        self.jentic_tools = self.jentic.generate_llm_tool_definitions("anthropic")

    async def process_message(self, user_message):
        # Assume `messages` is your conversation history
        # Assume `self.client` is your LLM client (e.g., Anthropic client)

        response = self.client.messages.create(
            model='claude-3-5-sonnet-latest',
            messages=messages,
            tools=self.jentic_tools, # Pass the generated tools
        )

        while response.stop_reason == "tool_use":
            tool_use = next(block for block in response.content if block.type == "tool_use")
            tool_name = tool_use.name
            tool_input = tool_use.input

            # Execute the tool using the Jentic SDK
            tool_result = await self.jentic.run_llm_tool(
                tool_name,
                tool_input
            )
            # ... handle tool_result and continue the conversation ...
```
