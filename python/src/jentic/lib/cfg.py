import os
from dataclasses import dataclass

from jentic.lib.exc import JenticEnvironmentError, MissingAgentKeyError

# TODO - Ensure we have one fqdn for each env, and  all endpoints are consistent
# TODO - WE DONT WANT THIS!  API GATEWAY CHANGES need to be reflected here

_ENDPOINTS = {
    "prod": {
        "core_api_url": "https://NOT-YET",
        "directory_url": "https://api.jentic.com/api/v1/"
    },
    "qa": {
        "core_api_url": "https://api-gw.qa1.eu-west-1.jenticdev.net/api/v1/",
        "directory_url": "https://directory-api.qa1.eu-west-1.jenticdev.net/api/v1/",
    },
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
    def endpoints_cfg(self) -> dict[str, str]:
        return _ENDPOINTS.get(self.environment, _ENDPOINTS["prod"])

    @property
    def core_api_url(self) -> str:
        return self.endpoints_cfg["core_api_url"]

    @property
    def directory_url(self) -> str:
        return self.endpoints_cfg["directory_url"]

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

        return AgentConfig(
            agent_api_key=agent_api_key,
            environment=environment,
        )
