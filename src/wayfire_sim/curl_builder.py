"""Сборка строки curl из HTTP-запроса."""

from __future__ import annotations

import shlex
from typing import Mapping

# Заголовки, которые curl выставит сам.
_SKIP_HEADERS = frozenset(
    {
        "host",
        "content-length",
        "connection",
        "accept-encoding",
        "proxy-connection",
    }
)

GET_AVAILABLE_JOBS_MARKERS = (
    "queryName=GetAvailableJobs",
    "7632b54fcfa7cd10bec94e6cda6236bf",
)


def is_get_available_jobs_url(url: str) -> bool:
    return any(marker in url for marker in GET_AVAILABLE_JOBS_MARKERS)


def build_curl(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes | None,
    *,
    multiline: bool = False,
) -> str:
    """Собрать команду curl в формате, пригодном для import_curl_secret."""
    parts: list[str] = ["curl", shlex.quote(url), "-X", method.upper()]

    for name, value in headers.items():
        key = name.lower()
        if key in _SKIP_HEADERS:
            continue
        parts.extend(["-H", shlex.quote(f"{name}: {value}")])

    if body:
        try:
            payload = body.decode("utf-8")
        except UnicodeDecodeError:
            payload = body.decode("utf-8", errors="replace")
        parts.extend(["--data-raw", shlex.quote(payload)])

    if multiline:
        return " \\\n  ".join(parts)
    return " ".join(parts)
