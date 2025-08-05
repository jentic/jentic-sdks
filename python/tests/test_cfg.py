import pytest

from jentic import AgentConfig
from jentic.lib.exc import JenticEnvironmentError, MissingAgentKeyError


def test_cfg_from_env__bad(monkeypatch):
    with pytest.raises(MissingAgentKeyError, match="JENTIC_AGENT_API_KEY is not set"):
        AgentConfig.from_env()

    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    monkeypatch.setenv("JENTIC_ENVIRONMENT", "invalid")
    with pytest.raises(JenticEnvironmentError, match="Invalid environment: invalid"):
        AgentConfig.from_env()


def test_cfg_from_env__happy_path(monkeypatch):
    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    cfg = AgentConfig.from_env()
    assert cfg.agent_api_key == "ak_19814bi2f98jhwg"
    assert cfg.environment == "prod"

    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    monkeypatch.setenv("JENTIC_ENVIRONMENT", "qa")
    cfg = AgentConfig.from_env()
    assert cfg.environment == "qa"
    assert cfg.core_api_url == "https://api-gw.qa1.eu-west-1.jenticdev.net/api/v1/"
