import asyncio
import json
from typing import Any, Dict

import jentic

try:
    import click  # type: ignore
except Exception:  # pragma: no cover - graceful fallback if click missing
    click = None  # type: ignore


def _infer_inputs(schema: Dict[str, Any] | None, *, topic: str) -> Dict[str, Any]:
    """Build a minimal inputs object from a JSON schema.

    Heuristics:
    - Prefer explicit defaults and enums
    - Fill common fields like query/q/search/topic with the provided topic
    - Provide simple placeholders for other primitives
    """

    if not isinstance(schema, dict):
        return {}

    properties = schema.get("properties", {}) or {}
    required = schema.get("required", []) or []

    def default_for(name: str, prop_schema: Dict[str, Any]) -> Any:
        # Explicit default or enum takes precedence
        if "default" in prop_schema:
            return prop_schema["default"]
        if isinstance(prop_schema.get("enum"), list) and prop_schema["enum"]:
            return prop_schema["enum"][0]

        typ = prop_schema.get("type")
        name_lower = name.lower()

        if typ == "string":
            if any(k in name_lower for k in ["query", "q", "search", "topic", "keywords"]):
                return topic
            if any(k in name_lower for k in ["message", "content", "text", "body"]):
                return topic
            if any(k in name_lower for k in ["channel_id", "channel", "room", "chat_id"]):
                return "1234567890"
            return "example"
        if typ == "integer":
            if any(k in name_lower for k in ["limit", "count", "page_size", "max_results"]):
                return 5
            if any(k in name_lower for k in ["channel_id", "chat_id"]):
                return 1234567890
            return 1
        if typ == "number":
            return 1.0
        if typ == "boolean":
            return True
        if typ == "array":
            items = prop_schema.get("items", {}) or {}
            # Try to create a single-item array with an inferred primitive
            if isinstance(items, dict) and items.get("type") == "string":
                return [topic]
            if isinstance(items, dict) and items.get("type") == "integer":
                return [1]
            return []
        if typ == "object":
            # Recurse shallowly if sub-properties exist
            return {}

        # Fallback
        return None

    inputs: Dict[str, Any] = {}

    # Fill required fields first
    for name in required:
        if name in properties and isinstance(properties[name], dict):
            inputs[name] = default_for(name, properties[name])

    # Opportunistically fill common optional fields
    for name, prop_schema in properties.items():
        if name in inputs:
            continue
        if any(
            k in name.lower()
            for k in ["query", "q", "search", "topic", "keywords", "limit", "count"]
        ):
            inputs[name] = default_for(name, prop_schema)

    return inputs


async def concept_find_articles_about_ai(client: jentic.Jentic) -> int:
    """Concept: Search → Load → Execute for finding articles about AI."""

    query = "find articles about AI"
    print(f"Searching: {query}")
    search_response = await client.search(
        jentic.SearchRequest(query=query, limit=5, filter_by_credentials=False)
    )

    if not search_response.results:
        print("No results found.")
        return 2

    print("Top results:")
    for idx, hit in enumerate(search_response.results, start=1):
        print(f"  {idx}. {hit.entity_type:<9} {hit.id} — {hit.summary}")

    # Choose the first result for this concept demo
    selected_id = search_response.results[0].id
    print(f"\nLoading schema for: {selected_id}")
    load_response = await client.load(jentic.LoadRequest(ids=[selected_id]))
    tool_detail = load_response.tool_info.get(selected_id)

    # Determine inputs from the schema if available
    inputs_schema = None
    if tool_detail is not None:
        # Both OperationDetail and WorkflowDetail expose an 'inputs' field
        inputs_schema = getattr(tool_detail, "inputs", None)

    inputs = _infer_inputs(inputs_schema, topic="artificial intelligence")

    print("Planned inputs:")
    print(json.dumps(inputs, indent=2))

    print("\nExecuting…")
    exec_resp = await client.execute(jentic.ExecutionRequest(id=selected_id, inputs=inputs))

    print(f"Success: {exec_resp.success}  Status: {exec_resp.status_code}")
    if exec_resp.error:
        print(f"Error: {exec_resp.error}")
    if exec_resp.output is not None:
        # Avoid overwhelming logs
        out_preview = json.dumps(exec_resp.output)[:2000]
        print(f"Output: {out_preview}")

    return 0 if exec_resp.success else 1


async def concept_send_discord_message(
    client: jentic.Jentic, *, message: str | None = None, channel_id: str | None = None
) -> int:
    """Concept: Search → Load → Execute for sending a message to a Discord channel."""

    query = "send message to discord channel"
    print(f"Searching: {query}")
    search_response = await client.search(
        jentic.SearchRequest(query=query, limit=5, filter_by_credentials=False)
    )

    if not search_response.results:
        print("No results found.")
        return 2

    print("Top results:")
    for idx, hit in enumerate(search_response.results, start=1):
        print(f"  {idx}. {hit.entity_type:<9} {hit.id} — {hit.summary}")

    selected_id = search_response.results[1].id
    print(f"\nLoading schema for: {selected_id}")
    load_response = await client.load(jentic.LoadRequest(ids=[selected_id]))
    tool_detail = load_response.tool_info.get(selected_id)

    inputs_schema = getattr(tool_detail, "inputs", None) if tool_detail is not None else None
    inferred = _infer_inputs(inputs_schema, topic=message or "Hello from Jentic")

    # Allow overrides
    if message is not None:
        for key in list(inferred.keys()):
            if any(k in key.lower() for k in ["message", "content", "text", "body"]):
                inferred[key] = message
    if channel_id is not None:
        for key in list(inferred.keys()):
            if any(k in key.lower() for k in ["channel_id", "channel", "chat_id", "room"]):
                inferred[key] = channel_id

    print("Planned inputs:")
    print(json.dumps(inferred, indent=2))

    print("\nExecuting…")
    exec_resp = await client.execute(jentic.ExecutionRequest(id=selected_id, inputs=inferred))

    print(f"Success: {exec_resp.success}  Status: {exec_resp.status_code}")
    if exec_resp.error:
        print(f"Error: {exec_resp.error}")
    if exec_resp.output is not None:
        out_preview = json.dumps(exec_resp.output)[:2000]
        print(f"Output: {out_preview}")

    return 0 if exec_resp.success else 1


def main() -> None:
    if click is None:
        print("This CLI requires 'click'. Install it with: pip install click")
        raise SystemExit(3)

    @click.group(help="Jentic examples: real concept runs")
    @click.option(
        "--agent-key",
        required=True,
        envvar="JENTIC_AGENT_API_KEY",
        help="Agent API key (or set JENTIC_AGENT_API_KEY)",
    )
    @click.option(
        "--environment",
        type=click.Choice(["prod", "qa"], case_sensitive=False),
        default="prod",
        show_default=True,
        help="Target environment",
    )
    @click.pass_context
    def cli(ctx: Any, agent_key: str, environment: str) -> None:  # noqa: ANN401 - click runtime
        ctx.ensure_object(dict)
        ctx.obj["agent_key"] = agent_key
        ctx.obj["environment"] = environment

    @cli.command(
        "articles-ai", help="Run the 'find articles about AI' concept (search → load → execute)"
    )
    @click.pass_context
    def articles_ai(ctx: Any) -> None:  # noqa: ANN401 - click runtime
        config = jentic.AgentConfig(
            agent_api_key=ctx.obj["agent_key"],
            environment=ctx.obj["environment"],
        )
        client = jentic.Jentic(config=config)
        exit_code = asyncio.run(concept_find_articles_about_ai(client))
        raise SystemExit(exit_code)

    @cli.command(
        "discord-send",
        help="Run the 'send message to discord channel' concept (search → load → execute)",
    )
    @click.option("--message", help="Message content to send", default=None)
    @click.option("--channel-id", help="Discord channel ID", default=None)
    @click.pass_context
    def discord_send(ctx: Any, message: str | None, channel_id: str | None) -> None:  # noqa: ANN401
        config = jentic.AgentConfig(
            agent_api_key=ctx.obj["agent_key"],
            environment=ctx.obj["environment"],
        )
        client = jentic.Jentic(config=config)
        exit_code = asyncio.run(
            concept_send_discord_message(client, message=message, channel_id=channel_id)
        )
        raise SystemExit(exit_code)

    cli(obj={})


if __name__ == "__main__":
    main()
