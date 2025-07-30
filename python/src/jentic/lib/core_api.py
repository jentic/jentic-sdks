import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, cast

import httpx
from httpx import Response
import tenacity

from jentic.lib.cfg import AgentConfig
from jentic.lib.exc import JenticAPIError
from jentic.lib.models import (
    APIIdentifier,
    ExecuteResponse,
    ExecutionRequest,
    LoadRequest,
    LoadResponse,
    SearchRequest,
    SearchResponse,
)

logger = logging.getLogger(__name__)


RETRYABLE_HTTP_CODES = {
    408,  # Request Timeout
    429,  # Too Many Requests  (TODO - do we want to retry on rate limit?)
    # 500,  # Internal Server Error (TODO - dont think we should retry 500)
    502,  # Bad Gateway
    503,  # Service Unavailable
    504,  # Gateway Timeout
}

RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.RemoteProtocolError,
    httpx.PoolTimeout,
    httpx.TimeoutException,
    httpx.NetworkError,
)

# Types for Request/Response data (Generic on purpose)
T_JSONResponse = dict[str, Any] | list[dict[str, Any]]
T_GETParams = dict[str, str]
T_POSTData = dict[str, Any]


def is_retryable_exception(e: BaseException) -> bool:
    if isinstance(e, httpx.HTTPStatusError):
        return e.response.status_code in RETRYABLE_HTTP_CODES
    if isinstance(e, RETRYABLE_EXCEPTIONS):
        return True
    return False


def retry_request(
    func: Callable,
    max_retries: int = 3,
) -> Callable:
    """
    Retry decorator for httpx requests.

    Args:
        func: The function to decorate.
        max_retries: The maximum number of retries (default=3)

    """

    @tenacity.retry(
        retry=tenacity.retry_if_exception(is_retryable_exception),
        stop=tenacity.stop_after_attempt(max_retries),
        wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            if is_retryable_exception(e):
                logger.info(f"Retrying request due to {e}")
                # Force a close on the httpx client, it will reconnect on retry
                await self.client.aclose()

            # Raise and let tenacity handle the error
            raise

    return wrapper


class BackendAPI:
    """
    BackendAPI REST Client.  This is the client that is used to interact with
    Jentic Backend Services.
    """

    def __init__(self, cfg: AgentConfig):
        self._cfg: AgentConfig = cfg
        self._client: httpx.AsyncClient | None = None
        self._loop = asyncio.get_event_loop()

    # Repo-like access to the backend
    async def search(self, request: SearchRequest) -> SearchResponse:
        resp: T_JSONResponse = await self._post("/agent/search", data=request.model_dump())
        return SearchResponse.model_validate(resp)

    async def execute(self, request: ExecutionRequest) -> ExecuteResponse:
        resp: T_JSONResponse = await self._post("/agent/execute", data=request.model_dump())
        return ExecuteResponse.model_validate(resp)

    async def load(self, request: LoadRequest) -> LoadResponse:
        params = {
            "workflow_uuids": request.workflow_uuids,
            "operation_uuids": request.operation_uuids,
        }
        resp: T_JSONResponse = await self._get(self._cfg.directory_url + "/files", params=params)
        return LoadResponse.model_validate(resp)

    async def list_apis(self) -> list[APIIdentifier]:
        resp: T_JSONResponse = await self._get("/agent/apis")
        return [APIIdentifier.model_validate(api) for api in resp]

    # Client management
    @property
    def client(self) -> httpx.AsyncClient:
        """
        Get the configured httpx.AsyncClient, creating it if it doesn't exist.
        """
        # Need to check against current loop, if loop is different AsyncClient will
        # need to be recreated, else get loop error
        current_loop = asyncio.get_event_loop()
        if (
            self._client is None
            or cast(httpx.AsyncClient, self._client).is_closed
            or current_loop != self._loop
        ):
            self._client = self._create_client()
            self._loop = current_loop

        return cast(httpx.AsyncClient, self._client)

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # HTTP methods, retry and validate - returns T_JSONResponse
    @retry_request
    async def _get(self, url: str, params: T_GETParams | None = None) -> T_JSONResponse:
        logger.debug(f"GET {self._cfg.core_api_url} {url} with params {params}")
        result: Response = await self.client.get(url, params=params)
        return self._validate_response(result)

    @retry_request
    async def _post(self, url: str, data: T_POSTData | None = None) -> T_JSONResponse:
        logger.debug(f"POST {url} with data {data}")
        result: Response = await self.client.post(url, json=data)
        return self._validate_response(result)

    # Validate the response(httpx.Response) and return the data (T_JSONResponse)
    def _validate_response(self, response: Response) -> T_JSONResponse:
        data = response.json()

        # Decode, and if we have 'body' then return this.
        if isinstance(data, dict):
            # This shouldnt happened, but just in case
            if data.get("detail") == "Not Found":
                print(data)
                raise JenticAPIError("Error: API Not Supported")

            # If we have a body, return this
            if data.get("body"):
                return data["body"]

        return data

    def _create_client(self) -> httpx.AsyncClient:
        # Headers set, auth and content-type
        headers = {
            "Content-Type": "application/json",
            "X-JENTIC-API-KEY": self._cfg.agent_api_key,
            "X-JENTIC-USER-AGENT": "Jentic/1.0 Agent (Python)",  # TODO - TILMAN: what should this be?
        }

        # Timeouts (connect, read, write, pool)
        timeouts = httpx.Timeout(
            connect=self._cfg.connect_timeout,
            read=self._cfg.read_timeout,
            write=self._cfg.write_timeout,
            pool=self._cfg.pool_timeout,
        )

        # Connection Limits (max_connections, max_keepalive_connections, max_retries)
        limits = httpx.Limits(
            max_connections=self._cfg.max_connections,
            max_keepalive_connections=self._cfg.max_keepalive_connections,
        )

        # Create the client
        return httpx.AsyncClient(
            headers=headers,
            base_url=self._cfg.core_api_url,
            timeout=timeouts,
            limits=limits,
        )
