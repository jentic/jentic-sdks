import os
from dataclasses import dataclass
from typing import cast
import logging

logger = logging.getLogger(__name__)

from jentic.lib.exc import JenticEnvironmentError, MissingAgentKeyError

_ENDPOINTS = {
    "prod": "https://api-gw.main.us-east-1.jenticprod.net/api/v1/",
    "qa": "https://api-gw.qa1.eu-west-1.jenticdev.net/api/v1/",
}


@dataclass
class AgentConfig:
    # Jentic API key, required for all requests
    agent_api_key: str
    user_agent: str = "Jentic/1.0 Agent (Python)"

    # Jentic environment, defaults to production
    environment: str = "prod"

    # httpx.Timeout parameters
    connect_timeout: float = 10.0
    read_timeout: float = 10.0
    write_timeout: float = 120.0
    pool_timeout: float = 120.0

    # httpx.Limits parameters
    max_connections: int = 5
    max_keepalive_connections: int = 5

    @property
    def core_api_url(self) -> str:
        return _ENDPOINTS[self.environment]

    @classmethod
    def from_env(cls) -> "AgentConfig":
        """
        Create an AgentConfig from environment variables.

        Raises:
            MissingAgentKeyError: If the JENTIC_AGENT_API_KEY environment variable is not set.
            JenticEnvironmentError: If the JENTIC_ENVIRONMENT environment variable is not set or is invalid.
        """
        agent_api_key = os.getenv("JENTIC_AGENT_API_KEY")
        if not agent_api_key:
            raise MissingAgentKeyError("JENTIC_AGENT_API_KEY is not set")

        environment = os.getenv("JENTIC_ENVIRONMENT", "prod")
        if environment not in _ENDPOINTS:
            raise JenticEnvironmentError(f"Invalid environment: {environment}")

        # Expose timeouts as environment variables
        connect_timeout = float(os.getenv("JENTIC_CONNECT_TIMEOUT", "10.0"))
        read_timeout = float(os.getenv("JENTIC_READ_TIMEOUT", "10.0"))
        write_timeout = float(os.getenv("JENTIC_WRITE_TIMEOUT", "120.0"))
        pool_timeout = float(os.getenv("JENTIC_POOL_TIMEOUT", "120.0"))

        logger.debug(
            f"Built config for {environment} with connect_timeout: {connect_timeout}, read_timeout: {read_timeout}, write_timeout: {write_timeout}, pool_timeout: {pool_timeout}"
        )
        return AgentConfig(
            agent_api_key=agent_api_key,
            environment=environment,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            write_timeout=write_timeout,
            pool_timeout=pool_timeout,
        )
