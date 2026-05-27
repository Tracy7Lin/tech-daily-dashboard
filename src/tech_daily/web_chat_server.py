from __future__ import annotations

import json
import re
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .llm_client import LLMClient
from .paths import DATA_DIR, SITE_DIR
from .research_agent_pipeline import run_research_agent
from .settings import DEFAULT_SETTINGS


def runtime_health_payload(site_dir: Path, *, llm_available: bool, mode: str) -> dict:
    runtime_hint = (
        "实时增强问答已连接，可直接使用 LLM 研究助理模式。"
        if llm_available and mode != "rule"
        else "本地问答服务已连接，但当前将优先回退到规则回答。"
    )
    return {
        "ok": True,
        "site_dir": str(site_dir),
        "llm_available": llm_available,
        "mode": mode,
        "runtime_hint": runtime_hint,
    }


def _llm_available() -> bool:
    client = LLMClient(
        api_url=DEFAULT_SETTINGS.llm_api_url,
        api_key=DEFAULT_SETTINGS.llm_api_key,
        model=DEFAULT_SETTINGS.llm_model,
        timeout_seconds=DEFAULT_SETTINGS.llm_timeout_seconds,
    )
    return client.is_available()


def handle_chat_request(site_dir: Path, payload: dict, data_dir: Path | None = None) -> tuple[int, dict]:
    report_date = (payload.get("date") or "").strip()
    question = (payload.get("question") or "").strip()
    history = payload.get("messages") or []
    if not report_date or not question:
        return HTTPStatus.BAD_REQUEST, {
            "error": "Both 'date' and 'question' are required.",
        }

    result = run_research_agent(site_dir, data_dir or DATA_DIR, report_date, question, history=history)
    return HTTPStatus.OK, result


def _split_answer_sentences(answer: str) -> list[str]:
    chunks = [chunk.strip() for chunk in re.findall(r".+?(?:[。！？!?]+|$)", answer or "", flags=re.S)]
    return [chunk for chunk in chunks if chunk]


def _build_stream_events(result: dict) -> list[dict]:
    events: list[dict] = [
        {"type": "status", "state": "loading", "text": "正在读取日报知识层…"},
        {"type": "status", "state": "loading", "text": "正在组织研究回答…"},
    ]
    for chunk in _split_answer_sentences(result.get("answer", "")):
        events.append({"type": "answer_delta", "text": chunk})
    events.append({"type": "final", "payload": result})
    return events


def handle_chat_stream_request(site_dir: Path, payload: dict, data_dir: Path | None = None) -> tuple[int, list[dict] | dict]:
    status_code, response_payload = handle_chat_request(site_dir, payload, data_dir=data_dir)
    if status_code != HTTPStatus.OK:
        return status_code, response_payload
    return status_code, _build_stream_events(response_payload)


def serve_dashboard(
    site_dir: Path | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8080,
    data_dir: Path | None = None,
) -> None:
    target_site_dir = (site_dir or SITE_DIR).resolve()
    target_data_dir = (data_dir or DATA_DIR).resolve()
    handler = partial(
        _WebChatRequestHandler,
        directory=str(target_site_dir),
        site_dir=target_site_dir,
        data_dir=target_data_dir,
    )
    server = ThreadingHTTPServer((host, port), handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


class _WebChatRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str, site_dir: Path, data_dir: Path, **kwargs) -> None:
        self._site_dir = site_dir
        self._data_dir = data_dir
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/api/health":
            self._write_json(
                HTTPStatus.OK,
                runtime_health_payload(
                    self._site_dir,
                    llm_available=_llm_available(),
                    mode=DEFAULT_SETTINGS.research_mode,
                ),
            )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        normalized_path = self.path.rstrip("/")
        if normalized_path not in {"/api/chat", "/api/chat-stream"}:
            self._write_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        try:
            payload = json.loads(raw_body or "{}")
        except json.JSONDecodeError:
            self._write_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON body."})
            return

        if normalized_path == "/api/chat-stream":
            status_code, event_payload = handle_chat_stream_request(
                self._site_dir,
                payload,
                data_dir=self._data_dir,
            )
            if status_code != HTTPStatus.OK:
                self._write_json(status_code, event_payload)
                return
            self._write_event_stream(status_code, event_payload)
            return

        status_code, response_payload = handle_chat_request(self._site_dir, payload, data_dir=self._data_dir)
        self._write_json(status_code, response_payload)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _write_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _write_event_stream(self, status_code: int, events: list[dict]) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        for event in events:
            line = json.dumps(event, ensure_ascii=False) + "\n"
            self.wfile.write(line.encode("utf-8"))
            self.wfile.flush()
