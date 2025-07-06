[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/jentic-jentic-tools-badge.png)](https://mseep.ai/app/jentic-jentic-tools)

# Jentic SDK & MCP Plugin [Beta]

Jentic MCP empowers AI agent builders to discover and integrate external APIs and workflows rapidly—without writing or maintaining API-specific code.

This repository contains the core Jentic SDK and the Jentic MCP Plugin.

- **[Jentic SDK](#jentic-sdk):** A comprehensive Python library for discovering and executing APIs and workflows, particularly for LLM tool use.
- **[Jentic MCP Plugin](#jentic-mcp-plugin):** A plugin enabling agents (like Windsurf, Claude Desktop & Cursor) to discover and use Jentic capabilities via MCP.

See the respective README files for more details:
- [Jentic SDK README](./python/README.md)
- [Jentic MCP Plugin README](./mcp/README.md)

The Jentic SDK is backed by the data in the [Open Agentic Knowledge (OAK)](https://github.com/jentic/oak) repository.


## Getting Started

### Get Your Jentic UUID

To use the Jentic SDK or MCP Plugin, you must first obtain a Jentic UUID. The easiest way is using the Jentic CLI. You can _optionally_ include an email address for higher rate limits and for early access to new features.

```sh
pip install jentic
jentic register --email '<your_email>'
```

This will print your UUID and an export command to set it in your environment:

```sh
export JENTIC_UUID=<your-jentic-uuid>
```

Alternatively, you can use curl to register and obtain your UUID:

```sh
curl -X POST https://api.jentic.com/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "<your_email>"}'
```

### Jentic MCP Server

The quickest way to get started is to integrate the Jentic MCP plugin with your preferred MCP client (like Windsurf, Claude Desktop or Cursor).

The recommended method is to run the server directly from the GitHub repository using `uvx`. 
You will need to install `uv` first using:

`brew install uv` or `pip install uv`

Next, add the following configuration to your MCP client.

The location of the configuration file depends on the client you are using and your OS. Some common examples:

- **Windsurf**: `~/.codeium/windsurf/mcp_config.json`
- **Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Claude Code**: `~/.claude.json`
- **Cursor**: `~/cursor/.mcp.json`

For other clients, check your client's documentation for how to add MCP servers.

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
                "JENTIC_UUID": "<your-jentic-uuid>"
            }
        }
    }
}
```

__Note:__ After saving the configuration file, you may need to restart the client application (Windsurf, Claude Desktop) for the changes to take effect.

### MCP Tool Use

Once the MCP server is running, you can easily use the MCP tools in your LLM agent to discover and execute APIs and workflows.

1. `search_apis`: Search for APIs in the Jentic directory that match specific functionality needs
2. `load_execution_info`: Retrieve detailed specifications for APIs and operations from the Jentic directory. **This will include auth information you may need to provide in your `mcpServers.jentic.env` configuration.**
3. `execute`: Execute a specific API or workflow operation.

### Environment Variables

When you are using an API that requires authentication, the `load_execution_info` tool will describe the required environment variables. You environment variables via the command line in Windsurf, although in some clients like Claude Desktop, you'll need to add them to your MCP config:

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
                "JENTIC_UUID": "<your-jentic-uuid>",
                "DISCORD_BOTTOKEN": "YOUR BOT TOKEN"
            }
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
