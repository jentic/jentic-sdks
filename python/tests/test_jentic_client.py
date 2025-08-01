import pytest

from jentic import Jentic, SearchRequest, LoadRequest, APIIdentifier, LoadResponse


@pytest.mark.asyncio
async def test_client_list_apis(client: Jentic):
    apis = await client.list_apis()
    assert len(apis) == 1
    assert apis == [
        APIIdentifier(api_vendor="discord.com", api_name="main", api_version="10"),
    ]


@pytest.mark.asyncio
async def test_client_search(client: Jentic):
    response = await client.search(SearchRequest(query="discord search message"))
    assert len(response.results) == 5
    assert response.total_count == 5
    assert response.query == "discord search message"


@pytest.mark.skip("skip for now, load not implemented")
@pytest.mark.asyncio
async def test_client_load(client: Jentic):
    operation_id = "6d1cac84da642f4ebc31e2688484a0c5"
    response: LoadResponse = await client.load(LoadRequest(operation_uuids=[operation_id]))
    assert response.operations is not None
    assert response.operations[operation_id].id == operation_id
