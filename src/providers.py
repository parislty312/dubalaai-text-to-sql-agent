"""Provider client utilities for OpenAI-compatible chat APIs."""
import time
from dataclasses import dataclass, field

import openai

from .config import ModelSpec, api_key_for


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    latency_s: float = 0.0


def build_response_format(provider: str, schema: dict) -> dict:
    """Return provider-specific structured-output parameters."""
    if provider == "openai":
        return {
            "type": "json_schema",
            "json_schema": {"name": "response", "schema": schema, "strict": False},
        }
    return {"type": "json_object", "schema": schema}


def cost_usd(spec: ModelSpec, usage: Usage) -> float:
    return (
        usage.input_tokens * spec.input_price
        + usage.output_tokens * spec.output_price
    ) / 1e6


class LLMClient:
    """Small wrapper around the OpenAI SDK for DubalaAI and OpenAI models."""

    def __init__(self, spec: ModelSpec):
        self.spec = spec
        self._client = openai.OpenAI(
            base_url=spec.base_url,
            api_key=api_key_for(spec),
            max_retries=2,
        )

    def chat(
        self,
        messages: list,
        json_schema: dict | None = None,
        tools: list | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        kwargs: dict = {
            "model": self.spec.api_model,
            "messages": messages,
            "temperature": temperature,
        }
        if self.spec.extra_body:
            kwargs["extra_body"] = dict(self.spec.extra_body)
        if json_schema:
            kwargs["response_format"] = build_response_format(
                self.spec.provider, json_schema
            )
        if tools:
            kwargs["tools"] = tools

        t0 = time.perf_counter()
        try:
            resp = self._client.chat.completions.create(**kwargs)
        except openai.BadRequestError as exc:
            if "temperature" in str(exc) and "temperature" in kwargs:
                kwargs.pop("temperature")
                resp = self._client.chat.completions.create(**kwargs)
            else:
                raise
        latency = time.perf_counter() - t0

        msg = resp.choices[0].message
        raw_usage = resp.usage
        usage = Usage(
            input_tokens=getattr(raw_usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(raw_usage, "completion_tokens", 0) or 0,
        )
        return LLMResponse(
            content=msg.content,
            tool_calls=list(msg.tool_calls or []),
            usage=usage,
            latency_s=latency,
        )
