import pytest
from src.config import MODEL_REGISTRY, DEFAULT_MODEL, get_model


def test_registry_has_required_models():
    for mid in ["gpt-oss-120b", "gpt-oss-20b", "gpt-5.4"]:
        assert mid in MODEL_REGISTRY


def test_specs_are_complete():
    for spec in MODEL_REGISTRY.values():
        assert spec.provider in ("dubalaai", "openai")
        assert spec.base_url.startswith("https://")
        assert spec.input_price > 0 and spec.output_price > 0
        assert spec.api_key_env in ("DUBALAAI_API_KEY", "OPENAI_API_KEY")


def test_default_model_is_dubalaai():
    assert MODEL_REGISTRY[DEFAULT_MODEL].provider == "dubalaai"


def test_get_model_unknown_raises():
    with pytest.raises(KeyError, match="Unknown model"):
        get_model("nope")
