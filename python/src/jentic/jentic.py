from jentic.lib.cfg import AgentConfig
from jentic.lib.core_api import BackendAPI
from jentic.lib.models import (
    APIIdentifier,
    ExecuteResponse,
    ExecutionRequest,
    LoadRequest,
    LoadResponse,
    SearchRequest,
    SearchResponse,
)


class Jentic:
    """
    Jentic client for interacting with the Jentic API.

    Args:
        config: AgentConfig instance, defaults to AgentConfig.from_env()
    """

    def __init__(self, config: AgentConfig | None = None):
        self._backend = BackendAPI(config or AgentConfig.from_env())

    async def list_apis(self) -> list[APIIdentifier]:
        """
        List all APIs available to the agent.

        Returns:
            list[APIIdentifier]: List of API identifiers.
        """
        return await self._backend.list_apis()

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Search for apis, operations and workflows via a SearchRequest.

        Results are filtered by the APIs the current Agent has access to.

        Args:
            request: SearchRequest instance.

        Returns:
            SearchResponse: Search response.
        """
        return await self._backend.search(request)

    async def execute(self, request: ExecutionRequest) -> ExecuteResponse:
        """
        Execute an ExecutionRequest.

        Args:
            request: ExecutionRequest instance.

        Returns:
            ExecuteResponse: Execute response.
        """
        return await self._backend.execute(request)

    async def load(self, request: LoadRequest) -> LoadResponse:
        """
        Load a LoadRequest.

        Args:
            request: LoadRequest instance.

        Returns:
            LoadResponse: Load response.
        """
        return await self._backend.load(request)
