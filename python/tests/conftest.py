from collections.abc import AsyncGenerator

import pytest_asyncio

from jentic import Jentic
from jentic.lib.cfg import AgentConfig
from jentic.lib.core_api import BackendAPI


def agent_config() -> AgentConfig:
    return AgentConfig(
        agent_api_key="ak_Rw723dw7oy4EjQB5x8lh7d",
        environment="qa",
    )


@pytest_asyncio.fixture(autouse=True)
async def backend_api() -> AsyncGenerator[BackendAPI, None]:
    api = BackendAPI(agent_config())
    yield api


@pytest_asyncio.fixture(autouse=True)
async def client(backend_api: BackendAPI) -> AsyncGenerator[Jentic, None]:
    client = Jentic(agent_config())
    yield client
