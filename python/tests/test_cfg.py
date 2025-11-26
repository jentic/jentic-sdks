import pytest

from jentic import AgentConfig
from jentic.lib.exc import JenticEnvironmentError, MissingAgentKeyError


def test_cfg_from_env__bad(monkeypatch):
    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "")
    monkeypatch.setenv("JENTIC_ENVIRONMENT", "")

    with pytest.raises(MissingAgentKeyError, match="JENTIC_AGENT_API_KEY is not set"):
        AgentConfig.from_env()

    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    monkeypatch.setenv("JENTIC_ENVIRONMENT", "invalid")
    with pytest.raises(JenticEnvironmentError, match="Invalid environment: invalid"):
        AgentConfig.from_env()


def test_cfg_from_env__happy_path(monkeypatch):
    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    monkeypatch.setenv("JENTIC_ENVIRONMENT", "prod")
    cfg = AgentConfig.from_env()
    assert cfg.agent_api_key == "ak_19814bi2f98jhwg"
    assert cfg.environment == "prod"

    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    monkeypatch.setenv("JENTIC_ENVIRONMENT", "qa")
    cfg = AgentConfig.from_env()
    assert cfg.environment == "qa"
    assert cfg.core_api_url == "https://api-gw.qa1.eu-west-1.jenticdev.net/api/v1/"


def test_cfg_from_env__timeouts_defaults(monkeypatch):
    # Ensure required env vars are set and timeout vars are *not* set
    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    monkeypatch.setenv("JENTIC_ENVIRONMENT", "prod")
    monkeypatch.delenv("JENTIC_CONNECT_TIMEOUT", raising=False)
    monkeypatch.delenv("JENTIC_READ_TIMEOUT", raising=False)
    monkeypatch.delenv("JENTIC_WRITE_TIMEOUT", raising=False)
    monkeypatch.delenv("JENTIC_POOL_TIMEOUT", raising=False)

    cfg = AgentConfig.from_env()

    assert cfg.connect_timeout == 10.0
    assert cfg.read_timeout == 10.0
    assert cfg.write_timeout == 120.0
    assert cfg.pool_timeout == 120.0


@pytest.mark.parametrize(
    "env_var, value, attr",
    [
        ("JENTIC_CONNECT_TIMEOUT", "1.5", "connect_timeout"),
        ("JENTIC_READ_TIMEOUT", "2.5", "read_timeout"),
        ("JENTIC_WRITE_TIMEOUT", "130.0", "write_timeout"),
        ("JENTIC_POOL_TIMEOUT", "140.0", "pool_timeout"),
    ],
)
def test_cfg_from_env__timeouts_overrides(monkeypatch, env_var, value, attr):
    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    monkeypatch.setenv("JENTIC_ENVIRONMENT", "prod")
    monkeypatch.setenv(env_var, value)

    cfg = AgentConfig.from_env()

    assert getattr(cfg, attr) == float(value)


@pytest.mark.parametrize(
    "env_var, bad_value",
    [
        ("JENTIC_CONNECT_TIMEOUT", ""),
        ("JENTIC_CONNECT_TIMEOUT", " "),
        ("JENTIC_READ_TIMEOUT", ""),
        ("JENTIC_READ_TIMEOUT", " "),
        ("JENTIC_WRITE_TIMEOUT", ""),
        ("JENTIC_WRITE_TIMEOUT", " "),
        ("JENTIC_POOL_TIMEOUT", ""),
        ("JENTIC_POOL_TIMEOUT", " "),
    ],
)
def test_cfg_from_env__timeouts_invalid_values(monkeypatch, env_var, bad_value):
    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    monkeypatch.setenv("JENTIC_ENVIRONMENT", "prod")
    monkeypatch.setenv(env_var, bad_value)

    with pytest.raises(ValueError):
        AgentConfig.from_env()
