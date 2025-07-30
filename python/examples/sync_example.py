import asyncio
from jentic import Jentic, AgentConfig, ExecutionRequest


def main():
    async def run():
        # Initialize the client (API key from env or pass explicitly)
        client = Jentic(AgentConfig.from_env())

        # List available APIs
        apis = await client.list_apis()
        print("Available APIs:", apis)

        # Search for a workflow or operation
        search_result = await client.search("send message to discord channel")
        print("Search result:", search_result)

        # Example: Execute an operation (replace with real UUID and inputs)
        request = ExecutionRequest(
            execution_type="operation", uuid="your-operation-uuid", inputs={"arg1": "value1"}
        )
        try:
            result = await client.execute(request)
            print("Execution result:", result)
        except Exception as e:
            print("Execution failed:", e)

    asyncio.run(run())


if __name__ == "__main__":
    main()
