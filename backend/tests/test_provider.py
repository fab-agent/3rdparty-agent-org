"""Provider service unit tests + provider API endpoints."""
from unittest.mock import MagicMock, patch

from tests.conftest import make_provider_key

# ── PROVIDER_CONFIGS completeness ─────────────────────────────────────────────

def test_all_five_providers_present():
    from services.provider_service import PROVIDER_CONFIGS
    for p in ("anthropic", "openai", "google", "mistral", "qwen"):
        assert p in PROVIDER_CONFIGS, f"Missing provider: {p}"


def test_each_provider_has_required_keys():
    from services.provider_service import PROVIDER_CONFIGS
    required = {"display_name", "url", "method", "headers", "models"}
    for name, cfg in PROVIDER_CONFIGS.items():
        missing = required - cfg.keys()
        assert not missing, f"{name} missing keys: {missing}"


def test_each_provider_has_models():
    from services.provider_service import PROVIDER_CONFIGS
    for name, cfg in PROVIDER_CONFIGS.items():
        assert len(cfg["models"]) >= 1, f"{name} has no models"
        for m in cfg["models"]:
            assert "id" in m and "name" in m


def test_qwen_uses_dashscope_url():
    from services.provider_service import PROVIDER_CONFIGS
    assert "dashscope" in PROVIDER_CONFIGS["qwen"]["url"]


def test_qwen_models():
    from services.provider_service import get_provider_models
    models = get_provider_models("qwen")
    ids = [m["id"] for m in models]
    assert "qwen-turbo" in ids
    assert "qwen-max" in ids


# ── detect_provider ───────────────────────────────────────────────────────────

def test_detect_google():
    from services.agent_runtime import detect_provider
    assert detect_provider("gemini-2.0-flash") == "google"
    assert detect_provider("gemini-2.5-pro") == "google"


def test_detect_anthropic():
    from services.agent_runtime import detect_provider
    assert detect_provider("claude-sonnet-4-6") == "anthropic"
    assert detect_provider("claude-opus-4-7") == "anthropic"


def test_detect_openai():
    from services.agent_runtime import detect_provider
    assert detect_provider("gpt-4o") == "openai"
    assert detect_provider("gpt-4o-mini") == "openai"
    assert detect_provider("o1-mini") == "openai"
    assert detect_provider("o3-mini") == "openai"


def test_detect_qwen():
    from services.agent_runtime import detect_provider
    assert detect_provider("qwen-max") == "qwen"
    assert detect_provider("qwen-turbo") == "qwen"
    assert detect_provider("qwen-plus") == "qwen"
    assert detect_provider("qwen-long") == "qwen"


def test_detect_unknown_defaults_to_google():
    from services.agent_runtime import detect_provider
    assert detect_provider("unknown-model-xyz") == "google"
    assert detect_provider("") == "google"
    assert detect_provider(None) == "google"


# ── test_provider_key (mocked HTTP) ──────────────────────────────────────────

def test_valid_key_returns_true():
    from services.provider_service import test_provider_key
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("services.provider_service.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_resp
        mock_client.get.return_value = mock_resp
        assert test_provider_key("openai", "sk-fake") is True


def test_invalid_key_returns_false():
    from services.provider_service import test_provider_key
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    with patch("services.provider_service.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_resp
        mock_client.get.return_value = mock_resp
        assert test_provider_key("openai", "bad-key") is False


def test_network_error_returns_false():
    from services.provider_service import test_provider_key
    with patch("services.provider_service.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Network error")
        mock_client.get.side_effect = Exception("Network error")
        assert test_provider_key("openai", "sk-x") is False


def test_unknown_provider_returns_false():
    from services.provider_service import test_provider_key
    assert test_provider_key("nonexistent", "key") is False


# ── Provider API endpoints ─────────────────────────────────────────────────────

def test_get_provider_status(auth_client, db_session):
    r = auth_client.get("/providers/status")
    assert r.status_code == 200
    data = r.json()
    providers = {p["provider"] for p in data}
    assert {"anthropic", "openai", "google", "mistral", "qwen"} == providers


def test_add_provider_key(auth_client, db_session):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with patch("services.provider_service.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_resp
        r = auth_client.post("/providers/openai/key", json={"key": "sk-fake-test-key"})
    assert r.status_code in (200, 201)
    data = r.json()
    assert data["provider"] == "openai"
    assert data["has_key"] is True


def test_add_provider_key_invalid(auth_client):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    with patch("services.provider_service.httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_resp
        r = auth_client.post("/providers/openai/key", json={"key": "bad-key"})
    # Endpoint stores the key as "invalid" status rather than rejecting (201)
    assert r.status_code in (200, 201)
    assert r.json()["status"] == "invalid"


def test_delete_provider_key(auth_client, db_session):
    make_provider_key(db_session, provider="mistral")
    db_session.commit()
    r = auth_client.delete("/providers/mistral/key")
    assert r.status_code in (200, 204)
    r2 = auth_client.get("/providers/status")
    mistral = next(p for p in r2.json() if p["provider"] == "mistral")
    assert mistral["has_key"] is False


def test_get_models_only_active(auth_client, db_session):
    make_provider_key(db_session, provider="openai")
    db_session.commit()
    r = auth_client.get("/providers/models")
    assert r.status_code == 200
    data = r.json()
    providers_in_response = {m["provider"] for m in data}
    assert "openai" in providers_in_response
