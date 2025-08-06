import asyncio
from jentic import Jentic, AgentConfig, ExecutionRequest


def main():
    async def run():
        # Initialize the client (API key from env or pass explicitly)
        client = Jentic()

        # List available APIs
        apis = await client.list_apis()
        print("Available APIs:", apis)

        # Search for a workflow or operation
        search_result = await client.search("send message to discord channel")
        print("Search result:", search_result)

        # Example: Execute an operation
        request = jentic.ExecutionRequest(id="op_1234567890", inputs={"message": "Hello, world!"})

        result = await client.execute(request)
        print("Execution result:", result)

    asyncio.run(run())


if __name__ == "__main__":
    main()
