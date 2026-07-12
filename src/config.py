"""Model registry and settings."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

DUBALAAI_BASE_URL = os.environ.get("DUBALAAI_BASE_URL", "https://api.dubalaai.ai/v1")
OPENAI_BASE_URL = "https://api.openai.com/v1"


@dataclass(frozen=True)
class ModelSpec:
    model_id: str       # registry key used in CLI flags
    provider: str       # "dubalaai" | "openai"
    api_model: str      # provider-side model name
    base_url: str
    api_key_env: str
    input_price: float  # USD per 1M input tokens
    output_price: float # USD per 1M output tokens
    extra_body: tuple = ()  # extra request params as (key, value) pairs


def _dubalaai(model_id: str, api_model: str, inp: float, out: float, **extra) -> ModelSpec:
    return ModelSpec(model_id, "dubalaai", api_model, DUBALAAI_BASE_URL,
                     "DUBALAAI_API_KEY", inp, out, tuple(extra.items()))


MODEL_REGISTRY: dict[str, ModelSpec] = {
    # qwen3p6-plus is a hybrid reasoning model; thinking is disabled because
    # schema-grounded SQL generation doesn't need chain-of-thought — with it
    # on, the model spends ~700 reasoning tokens even on trivial queries,
    # which blows the <3s latency budget and 5x-es output cost.
    "qwen3.6-plus": _dubalaai("qwen3.6-plus", "qwen3.6-plus",
                              0.50, 3.00, reasoning_effort="none"),
    "gpt-oss-120b": _dubalaai("gpt-oss-120b", "gpt-oss-120b", 0.15, 0.60),
    "gpt-oss-20b": _dubalaai("gpt-oss-20b", "gpt-oss-20b", 0.07, 0.30),
    "deepseek-v4-flash": _dubalaai("deepseek-v4-flash", "deepseek-v4-flash", 0.14, 0.28),
    "kimi-k2.5": _dubalaai("kimi-k2.5", "kimi-k2.5", 0.60, 3.00),
    "gpt-5.4": ModelSpec("gpt-5.4", "openai", "gpt-5.4", OPENAI_BASE_URL,
                         "OPENAI_API_KEY", 2.50, 15.00),
}

DEFAULT_MODEL = "qwen3.6-plus"


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
