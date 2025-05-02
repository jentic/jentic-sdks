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

## Core API & Use Cases

### Jentic MCP Server

A plugin allowing external systems (like Windsurf) to interact with Jentic Protocol, located in the `./mcp/` directory.

### Why Use Jentic MCP?
Leverage MCP and Jentic's agentic runtime to:

- Search for APIs and workflows by capability.
- Instantly generate integration code samples.
- Avoid boilerplate and reduce maintenance.
- Focus on building features, while Jentic MCP handles API interaction complexity.

### MCP API Tools

The plugin provides tools callable via the MCP protocol:

- `search_apis`: Search the Jentic directory.
- `get_execution_configuration`: Retrieve API/operation specifications.
- `generate_code_sample`: Generate integration code samples for agents.

### MCP Plugin Installation & Setup

**Windsurf Integration**

Configure Windsurf via `~/.codeium/windsurf/mcp_config.json`. **Replace `/absolute/path/to/sdk/mcp` with the correct absolute path to the `mcp` directory in this repository.**

```json
{
    "mcpServers": {
        "jentic-mcp": {
            "command": "pdm",
            "args": [
                "run",
                "--project",
                "/absolute/path/to/sdk/mcp", 
                "mcp",
                "serve",
                "--transport",
                "stdio"
            ]
        }
    }
}
```

**Jentic SDK Use**

`pip install jentic`

INSTRUCTIONS TO FOLLOW

**Jentic for Building and Executing LLM Tools**

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
