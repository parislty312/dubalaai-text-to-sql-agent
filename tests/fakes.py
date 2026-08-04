from types import SimpleNamespace

from src.providers import LLMResponse, Usage


FAKE_SPEC = SimpleNamespace(
    model_id="fake",
    provider="fireworks",
    input_price=0.15,
    output_price=0.60,
)


def tool_call(name: str, arguments: str, call_id: str = "c1"):
    return SimpleNamespace(
        id=call_id,
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


class FakeLLMClient:
    """Returns scripted responses in order and records every call."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.spec = FAKE_SPEC

    def chat(self, messages, json_schema=None, tools=None, temperature=0.0):
        self.calls.append(
            {
                "messages": list(messages),
                "json_schema": json_schema,
                "tools": tools,
                "temperature": temperature,
            }
        )
        response = self.responses.pop(0)
        if isinstance(response, LLMResponse):
            return response
        return LLMResponse(
            content=response,
            tool_calls=[],
            usage=Usage(100, 20),
            latency_s=0.01,
        )
