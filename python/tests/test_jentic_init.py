import pytest


@pytest.fixture
def fresh_client(monkeypatch):
    import jentic

    monkeypatch.delenv("JENTIC_ENVIRONMENT", raising=False)
    monkeypatch.delenv("JENTIC_AGENT_API_KEY", raising=False)
    jentic._JENTIC_CLIENT = None
    yield
    jentic._JENTIC_CLIENT = None


@pytest.fixture
def as_agent(fresh_client, monkeypatch):
    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    yield
    monkeypatch.delenv("JENTIC_AGENT_API_KEY")


def test_imports(monkeypatch, fresh_client):
    import jentic

    # _JENTIC_CLIENT should be None before init
    assert jentic._JENTIC_CLIENT is None

    with pytest.raises(Exception, match="JENTIC_AGENT_API_KEY is not set"):
        jentic.init()

    monkeypatch.setenv("JENTIC_AGENT_API_KEY", "ak_19814bi2f98jhwg")
    jentic.init()
    assert jentic._JENTIC_CLIENT is not None
    assert jentic._JENTIC_CLIENT._backend._cfg.agent_api_key == "ak_19814bi2f98jhwg"

    # reset client
    jentic._JENTIC_CLIENT = None
    assert jentic._JENTIC_CLIENT is None

    jentic.init(config=jentic.AgentConfig(agent_api_key="ak_anewkey"))
    assert jentic._JENTIC_CLIENT is not None
    assert jentic._JENTIC_CLIENT._backend._cfg.agent_api_key == "ak_anewkey"

    assert jentic.execute is not None
    assert jentic.search is not None
    assert jentic.load is not None
    assert jentic.list_apis is not None
    assert jentic.ExecutionRequest is not None
    assert jentic.SearchRequest is not None
    assert jentic.LoadRequest is not None
    assert jentic.AgentConfig is not None


def test_global_and_local_client(as_agent, monkeypatch):
    import jentic

    assert jentic._JENTIC_CLIENT is None

    jentic.init()
    assert jentic._JENTIC_CLIENT is not None
    assert jentic._JENTIC_CLIENT._backend._cfg.agent_api_key == "ak_19814bi2f98jhwg"
    assert jentic._JENTIC_CLIENT._backend._cfg.environment == "prod"

    client = jentic.Jentic(
        config=jentic.AgentConfig(agent_api_key="ak_anewkey", environment="local")
    )
    assert client._backend._cfg.agent_api_key == "ak_anewkey"
    assert client._backend._cfg.environment == "local"

    # global client should not be affected
    assert jentic._JENTIC_CLIENT._backend._cfg.agent_api_key == "ak_19814bi2f98jhwg"
    assert jentic._JENTIC_CLIENT._backend._cfg.environment == "prod"
