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
    """High-level async client for the Jentic API Hub.

    This class is opinionated but intentionally thin: it validates inputs,
    delegates all network traffic to :class:`jentic.lib.core_api.BackendAPI`,
    and returns Pydantic models so you get autocompletion and type checking
    out-of-the-box.

    Environment
    -----------
    Unless you explicitly supply an :class:`~jentic.lib.cfg.AgentConfig` the
    client loads configuration from *environment variables* via
    :meth:`jentic.lib.cfg.AgentConfig.from_env`.

    The only **required** variable is ``JENTIC_AGENT_API_KEY`` – the Agent API
    key you copy from the Jentic dashboard. Example::

        export JENTIC_AGENT_API_KEY=ak_live_*******

    All other values (``JENTIC_ENVIRONMENT`` etc.) default sensibly for production.

    Examples
    --------
    Minimal search → load → execute loop ::

        import asyncio
        from jentic import Jentic, SearchRequest, LoadRequest, ExecutionRequest

        async def main() -> None:
            client = Jentic()
            search = await client.search(SearchRequest(query="send an message via discord"))
            op_id  = search.results[0].id

            # Load the operation, view inputs and outputs
            response = await client.load(LoadRequest(ids=[op_id]))
            tool_info = response.tool_info[op_id]

            # Execute the operation
            result = await client.execute(ExecutionRequest(id=op_id, inputs={"to":"bob@example.com","body":"Hi"}))

            # Print the result
            print (result.status_code)
            print (result.output)

        asyncio.run(main())

    Notes for advanced users
    ------------------------
    • If you need fully-specified LLM tools, see
      :class:`jentic.lib.agent_runtime.AgentToolManager` instead.

    Parameters
    ----------
    config : AgentConfig | None, optional
        Pre-validated agent configuration. If ``None`` the instance resolves
        config from the current environment.
    """

    def __init__(self, config: AgentConfig | None = None):
        self._backend = BackendAPI(config or AgentConfig.from_env())

    async def list_apis(self) -> list[APIIdentifier]:
        """Return every API the current agent is authorised to see.

        Returns
        -------
        list[APIIdentifier]
            Each identifier contains the *vendor*, *name* and *version*.
        """
        return await self._backend.list_apis()

    async def search(self, request: SearchRequest) -> SearchResponse:
        """Full-text search across APIs, operations and workflows.

        The `query` string supports natural-language phrases – the backend uses
        semantic search to find best matches. Results are automatically scoped
        to the APIs your *agent key* grants access to.

        Parameters
        ----------
        request : SearchRequest
            Pass an instance for maximum control (limit, keywords, filter list
            of APIs). For convenience you can also call
            ``await client.search(SearchRequest(query="..."))``.

        Returns
        -------
        SearchResponse
            • ``results`` – ranked list of operations & workflows
            • ``total_count`` – total hits before pagination
            • ``query`` – the original query string

        Examples
        --------
        >>> sr = SearchRequest(query="create a Trello card", limit=10)
        >>> hits = await client.search(sr)
        >>> hits.results[0].summary
        'Create a new card in a Trello list'
        """
        return await self._backend.search(request)

    async def execute(self, request: ExecutionRequest) -> ExecuteResponse:
        """Execute a previously-loaded operation or workflow.

        ``ExecutionRequest.id`` must be the *exact* UUID you obtained from the
        search results – the SDK figures out whether it is an operation or a
        workflow.

        Parameters
        ----------
        request : ExecutionRequest
            • ``id`` – UUID prefixed with ``op_`` or ``wf_``
            • ``inputs`` – dict that satisfies the JSON schema returned by
              :meth:`load`

        Returns
        -------
        ExecuteResponse
            • ``success`` is *True* the ``output`` field contains the tool’s
              returned data (often JSON). On failure the ``error`` field is
              populated and ``success`` is *False*.
            • ``status_code`` – HTTP status code of the response

        Example
        -------
        >>> req = ExecutionRequest(id="op_123", inputs={"text":"hello"})
        >>> resp = await client.execute(req)
        >>> resp.success
        True
        """
        return await self._backend.execute(request)

    async def load(self, request: LoadRequest) -> LoadResponse:
        """Fetch JSON schemas & auth metadata for given IDs.

        Call this *after* a successful search and *before* execute so you can
        validate user input and inform the LLM of required environment
        variables (OAuth tokens, API keys, etc.).

        Parameters
        ----------
        request : LoadRequest
            ``ids`` should contain one or many UUIDs returned by search.

        Returns
        -------
        LoadResponse
            • ``tool_info`` - mapping id -> tool info

        Tip
        ---
        The returned object is compatible with
        :class:`jentic.lib.agent_runtime.AgentToolManager` so you can write the
        JSON to *jentic.json* and immediately generate tool definitions.
        """
        get_files_response = await self._backend.load(request)
        return LoadResponse.from_get_files_response(get_files_response)
