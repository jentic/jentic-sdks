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
    assert cfg.base_url == "https://api.jentic.com/api/v1/"

    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    monkeypatch.setenv("JENTIC_ENVIRONMENT", "test")
    cfg = AgentConfig.from_env()
    assert cfg.environment == "test"
    assert cfg.base_url == "https://api.test.jentic.com/api/v1/"

    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    monkeypatch.setenv("JENTIC_ENVIRONMENT", "qa")
    cfg = AgentConfig.from_env()
    assert cfg.environment == "qa"
    assert cfg.base_url == "https://yq6wol1jye.execute-api.eu-west-1.amazonaws.com/api/v1/"
