from __future__ import annotations

import json
from urllib import request


class LLMClientError(RuntimeError):
    pass


def _default_transport(url: str, headers: dict[str, str], body: dict, timeout: int) -> dict:
    payload = json.dumps(body).encode("utf-8")
    req = request.Request(url, data=payload, headers=headers, method="POST")
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class LLMClient:
    def __init__(
        self,
        api_url: str,
        api_key: str,
        model: str,
        timeout_seconds: int,
        transport=None,
    ) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self._transport = transport or _default_transport

    def is_available(self) -> bool:
        return bool(self.api_url and self.api_key and self.model)

    def generate_json(self, instructions: str, input_text: str, schema_name: str, schema: dict) -> dict:
        if not self.is_available():
            raise LLMClientError("llm_unavailable")

        body = {
            "model": self.model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": instructions}]},
                {"role": "user", "content": [{"type": "input_text", "text": input_text}]},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = self._transport(self.api_url, headers, body, self.timeout_seconds)
        text = self._extract_output_text(payload)
        if not text:
            raise LLMClientError("empty_output")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMClientError("invalid_json") from exc

    def _extract_output_text(self, payload: dict) -> str:
        if payload.get("output_text"):
            return payload["output_text"]
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "")
        return ""
