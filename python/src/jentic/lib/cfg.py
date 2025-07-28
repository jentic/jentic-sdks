import os
from dataclasses import dataclass

from jentic.lib.exc import JenticEnvironmentError, MissingAgentKeyError

# TODO - Ensure we have one fqdn for each env, and  all endpoints are consistent
_ENDPOINTS = {
    "prod": "https://api.jentic.com/api/v1/",
    "qa": "https://yq6wol1jye.execute-api.eu-west-1.amazonaws.com/api/v1/",
    "test": "https://api.test.jentic.com/api/v1/",
    "local": "https://yq6wol1jye.execute-api.eu-west-1.amazonaws.com/api/v1/"  # TODO - maybe remove this, local->qa
}


@dataclass
class AgentConfig:
    # Jentic API key, required for all requests
    agent_api_key: str

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
    def base_url(self) -> str:
        return _ENDPOINTS.get(self.environment, _ENDPOINTS["prod"])

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
