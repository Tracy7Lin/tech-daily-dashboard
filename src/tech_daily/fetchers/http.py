from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_HEADERS = {
    "User-Agent": "tech-daily-dashboard/0.1 (+https://example.invalid/tech-daily)"
}


def fetch_text(url: str, timeout: int = 20) -> str:
    request = Request(url, headers=DEFAULT_HEADERS)
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def describe_fetch_error(error: Exception) -> str:
    if isinstance(error, HTTPError):
        return f"http_error:{error.code}"
    if isinstance(error, URLError):
        return f"url_error:{error.reason}"
    return error.__class__.__name__
