import os
from unittest.mock import AsyncMock, PropertyMock, patch

import httpx
import pytest

from jentic.lib.core_api import (
    RETRYABLE_EXCEPTIONS,
    RETRYABLE_HTTP_CODES,
    BackendAPI,
    is_retryable_exception,
)

# pytestmark = pytest.mark.skip(reason="They are slow, so only run when you want to")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status_code, should_retry",
    [
        (503, True),  # Retryable (Service Unavailable)
        (408, True),  # Retryable (Request Timeout)
        (429, True),  # Retryable (Too Many Requests)
        # (500, True),  # Retryable  (For now this is off)
        (400, False),  # Not retryable (Bad Request)
        (401, False),  # Not retryable (Unauthorized)
        (402, False),  # Not retryable (Payment Required)
        (403, False),  # Not retryable (Forbidden)
        (404, False),  # Not retryable (Not Found)
        (405, False),  # Not retryable (Method Not Allowed)
        (406, False),  # Not retryable (Not Acceptable)
        (407, False),  # Not retryable (Proxy Authentication Required)
        (409, False),  # Not retryable (Conflict)
    ],
)
async def test_retry_handling_for_status_codes(
    backend_api: BackendAPI, monkeypatch, status_code, should_retry
):
    """
    Test that the retry handling logic is working as expected for different status codes.
    - Retryable status codes should be retried.
    - Non-retryable status codes should fail immediately.
    """
    max_retries = 3
    mock_get = AsyncMock()
    request = httpx.Request("GET", "https://fake-jentic.com/apis")
    monkeypatch.setattr(os, "environ", {"JENTIC_AGENT_API_KEY": "ak_obviouslybadkey"})

    if should_retry:
        # Simulate failure for all retry attempts, then a final error
        side_effects = [
            httpx.HTTPStatusError(
                f"Error {status_code}",
                request=request,
                response=httpx.Response(
                    status_code=status_code, request=request, json={"message": "failed"}
                ),
            )
            for _ in range(max_retries)
        ]

        mock_get.side_effect = side_effects
        mock_httpx_client = AsyncMock()
        mock_httpx_client.get = mock_get
        with patch.object(BackendAPI, "client", new=PropertyMock(return_value=mock_httpx_client)):
            with pytest.raises(httpx.HTTPStatusError) as excinfo:
                await backend_api._get("/apis")

        assert excinfo.value.response.status_code == status_code
        assert mock_httpx_client.get.call_count == max_retries
        assert mock_httpx_client.aclose.call_count == max_retries

    else:
        # Simulate a single failure for non-retryable codes
        mock_get.side_effect = [
            httpx.HTTPStatusError(
                f"Error {status_code}",
                request=request,
                response=httpx.Response(
                    status_code=status_code, request=request, json={"message": "failed"}
                ),
            )
        ]
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = mock_get
        with patch.object(BackendAPI, "client", new=PropertyMock(return_value=mock_client)):
            with pytest.raises(httpx.HTTPStatusError) as excinfo:
                await backend_api._get("/apis")

        assert excinfo.value.response.status_code == status_code
        assert mock_client.get.call_count == 1
        assert mock_client.aclose.call_count == 0


def test_is_retryable_exception():
    """
    Test the is_retryable_exception function with various exceptions and status codes.
    """
    # Test retryable status codes
    for code in RETRYABLE_HTTP_CODES:
        request = httpx.Request("GET", "/")
        response = httpx.Response(status_code=code, request=request)
        err = httpx.HTTPStatusError("error", request=request, response=response)
        assert is_retryable_exception(err) is True

    # Test non-retryable status codes
    for code in [400, 401, 403, 404]:
        request = httpx.Request("GET", "/")
        response = httpx.Response(status_code=code, request=request)
        err = httpx.HTTPStatusError("error", request=request, response=response)
        assert is_retryable_exception(err) is False

    # Test retryable exceptions
    for exc in RETRYABLE_EXCEPTIONS:
        assert is_retryable_exception(exc("error")) is True

    # Test non-retryable exceptions
    assert is_retryable_exception(Exception("Some other error")) is False
