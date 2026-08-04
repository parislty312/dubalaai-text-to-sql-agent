"""Model registry and settings."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

FIREWORKS_BASE_URL = os.environ.get(
    "FIREWORKS_BASE_URL",
    "https://api.fireworks.ai/inference/v1",
)


@dataclass(frozen=True)
class ModelSpec:
    model_id: str       # registry key used in CLI flags
    provider: str       # "fireworks"
    api_model: str      # provider-side model name
    base_url: str
    api_key_env: str
    input_price: float  # USD per 1M input tokens
    output_price: float # USD per 1M output tokens
    extra_body: tuple = ()  # extra request params as (key, value) pairs


def _fireworks(model_id: str, api_model: str, inp: float, out: float, **extra) -> ModelSpec:
    return ModelSpec(model_id, "fireworks", api_model, FIREWORKS_BASE_URL,
                     "FIREWORKS_API_KEY", inp, out, tuple(extra.items()))


MODEL_REGISTRY: dict[str, ModelSpec] = {
    "qwen3-235b-a22b": _fireworks(
        "qwen3-235b-a22b",
        "accounts/fireworks/models/qwen3-235b-a22b",
        0.22,
        0.88,
    ),
    "qwen3-30b-a3b": _fireworks(
        "qwen3-30b-a3b",
        "accounts/fireworks/models/qwen3-30b-a3b",
        0.15,
        0.60,
    ),
    "qwen3-8b": _fireworks(
        "qwen3-8b",
        "accounts/fireworks/models/qwen3-8b",
        0.05,
        0.20,
    ),
    "gpt-oss-120b": _fireworks(
        "gpt-oss-120b",
        "accounts/fireworks/models/gpt-oss-120b",
        0.15,
        0.60,
    ),
    "gpt-oss-20b": _fireworks(
        "gpt-oss-20b",
        "accounts/fireworks/models/gpt-oss-20b",
        0.07,
        0.30,
    ),
}

DEFAULT_MODEL = "qwen3-235b-a22b"


def get_model(model_id: str) -> ModelSpec:
    if model_id not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model '{model_id}'. Available: {', '.join(MODEL_REGISTRY)}")
    return MODEL_REGISTRY[model_id]


def api_key_for(spec: ModelSpec) -> str:
    key = os.environ.get(spec.api_key_env)
    if not key:
        raise RuntimeError(
            f"{spec.api_key_env} is not set (required for model '{spec.model_id}'). "
            f"Export it or put it in .env"
        )
    return key
