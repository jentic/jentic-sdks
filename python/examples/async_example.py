import asyncio
import jentic


async def main():
    # List available APIs
    apis = await jentic.list_apis()
    print("Available APIs:", apis)

    # Search for a workflow or operation
    search_result = await jentic.search("send message to discord channel")
    print("Search result:", search_result)

    # Example: Execute an operation (replace with real UUID and inputs)
    request = jentic.ExecutionRequest(
        execution_type="operation",
        uuid="your-operation-uuid",
        inputs={"arg1": "value1"}
    )
    try:
        result = await jentic.execute(request)
        print("Execution result:", result)
    except Exception as e:
        print("Execution failed:", e)


if __name__ == "__main__":
    asyncio.run(main()) 
