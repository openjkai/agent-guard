"""HTTP LLM client supporting OpenAI-compatible and Anthropic APIs."""

from __future__ import annotations

from typing import Any, Literal

import httpx

Provider = Literal["openai", "anthropic", "openrouter", "mock"]


class LLMClient:
    def __init__(
        self,
        *,
        provider: Provider = "mock",
        model: str = "mock-model",
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout

    def complete(self, messages: list[dict[str, Any]], **kwargs: Any) -> dict[str, Any]:
        if self.provider == "mock":
            return self._mock_complete(messages)

        with httpx.Client(timeout=self.timeout) as client:
            if self.provider == "anthropic":
                return self._anthropic_complete(client, messages, **kwargs)
            return self._openai_compatible_complete(client, messages, **kwargs)

    def _mock_complete(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        last_user = next(
            (
                message["content"]
                for message in reversed(messages)
                if message.get("role") == "user"
            ),
            "",
        )
        return {
            "content": f"[mock response to: {last_user[:120]}]",
            "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
            "model": self.model,
        }

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            if self.provider == "anthropic":
                headers["x-api-key"] = self.api_key
                headers["anthropic-version"] = "2023-06-01"
            else:
                headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _resolve_openai_url(self) -> str:
        if self.base_url:
            return self.base_url.rstrip("/") + "/chat/completions"
        if self.provider == "openrouter":
            return "https://openrouter.ai/api/v1/chat/completions"
        return "https://api.openai.com/v1/chat/completions"

    def _openai_compatible_complete(
        self,
        client: httpx.Client,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        payload = {"model": self.model, "messages": messages, **kwargs}
        response = client.post(
            self._resolve_openai_url(), headers=self._headers(), json=payload
        )
        response.raise_for_status()
        data = response.json()
        choice = data["choices"][0]["message"]
        usage = data.get("usage", {})
        return {
            "content": choice.get("content", ""),
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            "model": data.get("model", self.model),
            "raw": data,
        }

    def _anthropic_complete(
        self,
        client: httpx.Client,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        system_parts = [
            message["content"]
            for message in messages
            if message.get("role") == "system"
        ]
        convo = [message for message in messages if message.get("role") != "system"]
        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 1024),
            "messages": convo,
        }
        if system_parts:
            payload["system"] = "\n".join(system_parts)
        url = (self.base_url or "https://api.anthropic.com").rstrip(
            "/"
        ) + "/v1/messages"
        response = client.post(url, headers=self._headers(), json=payload)
        response.raise_for_status()
        data = response.json()
        text = "".join(
            block.get("text", "")
            for block in data.get("content", [])
            if block.get("type") == "text"
        )
        usage = data.get("usage", {})
        return {
            "content": text,
            "usage": {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0)
                + usage.get("output_tokens", 0),
            },
            "model": data.get("model", self.model),
            "raw": data,
        }
