from __future__ import annotations

import json
from urllib import request
from urllib.parse import urlparse


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

        request_url, protocol = self._resolve_request_target()
        body = self._build_request_body(protocol, instructions, input_text, schema_name, schema)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = self._transport(request_url, headers, body, self.timeout_seconds)
        text = self._extract_output_text(payload)
        if not text:
            raise LLMClientError("empty_output")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMClientError("invalid_json") from exc

    def _resolve_request_target(self) -> tuple[str, str]:
        parsed = urlparse(self.api_url)
        path = parsed.path.rstrip("/")
        base = self.api_url.rstrip("/")

        if path.endswith("/chat/completions"):
            return self.api_url, "chat_completions"
        if path.endswith("/responses"):
            return self.api_url, "responses"
        if path == "/v1":
            return f"{base}/responses", "responses"
        if not path:
            return f"{base}/chat/completions", "chat_completions"
        return self.api_url, "responses"

    def _build_request_body(
        self,
        protocol: str,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict,
    ) -> dict:
        if protocol == "chat_completions":
            schema_text = json.dumps(schema, ensure_ascii=False)
            return {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": instructions},
                    {
                        "role": "user",
                        "content": (
                            f"{input_text}\n\n"
                            f"请只返回一个合法 JSON 对象，字段必须符合这个 JSON Schema：{schema_text}"
                        ),
                    },
                ],
                "response_format": {"type": "json_object"},
            }

        return {
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

    def _extract_output_text(self, payload: dict) -> str:
        if payload.get("output_text"):
            return payload["output_text"]
        if payload.get("choices"):
            message = payload["choices"][0].get("message", {})
            content = message.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                for item in content:
                    if item.get("type") in {"text", "output_text"} and item.get("text"):
                        return item["text"]
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text", "")
        return ""
