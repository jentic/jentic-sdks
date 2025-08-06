from typing import cast

from jentic.jentic import Jentic
from jentic.lib.cfg import AgentConfig
from jentic.lib.models import (
    APIIdentifier,
    ExecuteResponse,
    ExecutionRequest,
    LoadRequest,
    LoadResponse,
    SearchRequest,
    SearchResponse,
)

_JENTIC_CLIENT = None


__all__ = [
    "Jentic",
    "execute",
    "init",
    "list_apis",
    "load",
    "search",
    "ExecutionRequest",
    "SearchRequest",
    "LoadRequest",
    "AgentConfig",
]


def init(config: AgentConfig | None = None) -> None:
    global _JENTIC_CLIENT
    _JENTIC_CLIENT = Jentic(config)


def _get_client() -> Jentic:
    if not _JENTIC_CLIENT:
        init()

    return cast(Jentic, _JENTIC_CLIENT)


async def list_apis() -> list[APIIdentifier]:
    return await _get_client().list_apis()


async def search(
    request: SearchRequest | str,
    *,
    apis: list[str] | None = None,
    keywords: list[str] | None = None,
    limit: int = 5,
) -> SearchResponse:
    if isinstance(request, str):
        request = SearchRequest(query=request, apis=apis, keywords=keywords, limit=limit)
    return await _get_client().search(request)


async def execute(request: ExecutionRequest) -> ExecuteResponse:
    return await _get_client().execute(request)


async def load(request: LoadRequest) -> LoadResponse:
    return await _get_client().load(request)
