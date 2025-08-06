# Jentic SDK & MCP Plugin [Beta] ![PyPI](https://img.shields.io/pypi/v/jentic?logo=pypi&color=blue)

Jentic empowers AI-agent builders to discover and integrate external APIs and workflows rapidly—without writing or maintaining any API-specific code.

This mono-repo contains:

- **Jentic SDK** – a Python library for searching, loading and executing APIs / workflows, plus helpers for turning those actions into LLM tools.
- **Jentic MCP Plugin** – an MCP server that exposes the same capabilities to any MCP-compatible client (Windsurf, Claude Desktop, Cursor, …).

See the dedicated READMEs for full details:

- [`python/README.md`](./python/README.md) – SDK usage & API reference
- [`mcp/README.md`](./mcp/README.md) – MCP server setup & configuration

The SDK is backed by the data in the [Jentic Public API](https://github.com/jentic/jentic-public-api) repository.

## Quick start

### 1. Install Python package

```bash
pip install jentic
```

### 2. Obtain your Agent API Key

Visit https://jentic.com/register  (TODO _ MAKE SURE THIS IS RIGHT), create an agent and copy the key.

```bash
export JENTIC_AGENT_API_KEY=<your-agent-api-key>
```

### 3. Use the SDK

```python
import asyncio
from jentic import Jentic, SearchRequest, LoadRequest, ExecutionRequest

async def main():
    client = Jentic()

    # 1️⃣ Search for an operation or workflow that matches what you need
    search = await client.search(
        SearchRequest(query="send a Discord DM")
    )
    first_result = search.results[0]
    entity_id = first_result.id  # UUID prefixed with op_ or wf_

    # 2️⃣ Load detailed execution info (input schema, auth requirements, etc.)
    await client.load(LoadRequest(ids=[entity_id]))

    # 3️⃣ Execute it!
    result = await client.execute(
        ExecutionRequest(id=entity_id,
                         inputs={"recipientId": "123", "content": "Hello!"})
    )
    print(result)

asyncio.run(main())
```

### 4. Integrate with your LLM agent (optional)

If you need fully-formed tool definitions for Anthropic or OpenAI models, use the runtime helpers:

```python
from jentic.lib.agent_runtime import AgentToolManager

manager = AgentToolManager(format="anthropic")
tools   = manager.generate_tool_definitions()        # pass these to the LLM
result  = await manager.execute_tool("discord_send_message",
                                     {"recipientId": "123", "content": "Hi"})
print(result)
```

## Using the MCP plugin

To expose the same capabilities via MCP, follow the instructions in [`mcp/README.md`](./mcp/README.md).

```bash
uvx --from \
  git+https://github.com/jentic/jentic-sdks.git@main#subdirectory=mcp \
  mcp
```

Then configure your MCP-compatible client to point at the running server (see the sub-README for sample client configs).
