import pytest
from src.config import MODEL_REGISTRY, DEFAULT_MODEL, get_model


def test_registry_has_required_models():
    for mid in ["qwen3-235b-a22b", "qwen3-30b-a3b", "gpt-oss-120b"]:
        assert mid in MODEL_REGISTRY


def test_specs_are_complete():
    for spec in MODEL_REGISTRY.values():
        assert spec.provider == "fireworks"
        assert spec.base_url.startswith("https://")
        assert spec.input_price > 0 and spec.output_price > 0
        assert spec.api_key_env == "FIREWORKS_API_KEY"


def test_default_model_is_fireworks_qwen():
    assert DEFAULT_MODEL == "qwen3-235b-a22b"
    assert MODEL_REGISTRY[DEFAULT_MODEL].provider == "fireworks"


def test_get_model_unknown_raises():
    with pytest.raises(KeyError, match="Unknown model"):
        get_model("nope")
