from __future__ import annotations

import json
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .chat_agent_pipeline import run_chat_agent
from .paths import DATA_DIR, SITE_DIR


def handle_chat_request(site_dir: Path, payload: dict, data_dir: Path | None = None) -> tuple[int, dict]:
    report_date = (payload.get("date") or "").strip()
    question = (payload.get("question") or "").strip()
    if not report_date or not question:
        return HTTPStatus.BAD_REQUEST, {
            "error": "Both 'date' and 'question' are required.",
        }

    result = run_chat_agent(site_dir, report_date, question, data_dir=data_dir or DATA_DIR)
    return HTTPStatus.OK, result


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
                {
                    "ok": True,
                    "site_dir": str(self._site_dir),
                },
            )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/api/chat":
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

        status_code, response_payload = handle_chat_request(
            self._site_dir,
            payload,
            data_dir=self._data_dir,
        )
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
