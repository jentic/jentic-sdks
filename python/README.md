# Jentic SDK [Beta]

Jentic SDK is a comprehensive library for discovery and execution of APIs and workflows.

The Jentic SDK is backed by the data in the [Jentic Public APIs](https://github.com/jentic/jentic-public-apis) repository.

## Core API & Use Cases

The main entry point is the `Jentic` class.

### Quick Start – search → load → execute

```python
import asyncio
from jentic import Jentic, SearchRequest, LoadRequest, ExecutionRequest

async def main():
    client = Jentic()

    # 1️⃣ find a capability
    results = await client.search(SearchRequest(query="send a Discord DM"))
    entity_id = search.results[0].id  # op_... or wf_...

    # 2️⃣ load details (inspect schemas / auth, see inputs for operations)
    resp = await client.load(LoadRequest(ids=[entity_id]))
    inputs = resp.tool_info[entity_id].inputs

    # 3️⃣ run it
    result = await client.execute(
        ExecutionRequest(id=entity_id, inputs={"recipient_id": "123", "content": "Hello!"})
    )
    print(result)

asyncio.run(main())
```

### LLM Tool Definition & Execution

A typical agent loop with tool use looks like this:

```python
from jentic.lib.agent_runtime import AgentToolManager

manager = AgentToolManager(format="anthropic")
llm_tools = manager.generate_tool_definitions()  # pass to your LLM

# --- within your agent loop ---
while response.stop_reason == "tool_use":
    tool_call = next(b for b in response.content if b.type == "tool_use")
    name      = tool_call.name
    inputs    = tool_call.input

    result = await manager.execute_tool(name, inputs)
    # ... handle result ...
```

## Components

### agent_runtime

A library for generating, managing, and executing LLM-compatible tools from Arazzo workflows and OpenAPI operations.

Features:
- Generate dynamic tool definitions for OpenAI and Anthropic LLMs from project workflows and API operations
- Execute workflows and operations as tools via a unified interface
- Provide runtime classes for tool management (`AgentToolManager`), tool specification (`LLMToolSpecManager`), and execution (`TaskExecutor`)
- Return standardized results for workflow and operation execution

### api

A client for the Jentic API Knowledge Hub.

Set `JENTIC_API_URL` to set the base URL for the API hub client for local testing or testing against the development environment. 

## Installation

### For Development

To install the package in development mode:

```bash
# From the current directory
pip install -e .
```

Then you can import it in your projects:

```python
import jentic
```

You can also import it to other projects by referencing the package directory by specifying the following in your `pyproject.toml`:

```toml
dependencies = [
    "jentic @ file:///path/to/jentic/sdk"
]
```

### For Production

```bash
pip install jentic
```

### API Key

See the [root README](https://github.com/jentic/jentic-sdks?tab=readme-ov-file#2-obtain-your-agent-api-key) for instructions on creating an agent and exporting your `JENTIC_AGENT_API_KEY`. Remember to set it in the environment before running any examples.

### Testing

```bash
# Run unit tests for jentic
pdm run test

# Run integration tests for dev environment
pdm run integration-dev

# Run integration tests for production environment
pdm run integration
```

#### Integration Test Configuration

Integration tests require environment variables to be set in environment-specific files. An example file is provided that you need to copy and configure:

```bash
# For development testing
cp tests/integration/.env.example tests/integration/.env.dev

# For production testing
cp tests/integration/.env.example tests/integration/.env.prod
```

After copying, edit these files to include your API credentials and configuration:

1. For development testing: `tests/integration/.env.dev`
2. For production testing: `tests/integration/.env.prod`

Example configuration:

```
# Required UUIDs for Discord API testing
DISCORD_GET_MY_USER_OPERATION_UUID="your_operation_uuid_here"
DISCORD_GET_USER_DETAILS_WORKFLOW_UUID="your_workflow_uuid_here"

# Base URL for Jentic API (Uncomment for Dev)
JENTIC_API_URL=https://directory-api.qa1.eu-west-1.jenticdev.net

# Your Discord bot token
DISCORD_BOTTOKEN="your_bot_token_here"
```

The integration tests validate:
1. Loading operation and workflow execution information
2. Executing Discord operations and workflows
3. Searching API capabilities
4. Generating LLM tool definitions
5. Running LLM tools including both operations and workflows

### Linting & Formatting

```bash
# Run all linting for jentic
pdm run lint
```