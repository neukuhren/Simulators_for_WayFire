"""
Addon для mitmdump: перехват GetAvailableJobs и сохранение curl.

Запускается отдельным процессом mitmdump. Пути — из переменных окружения WAYFIRE_*.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from mitmproxy import ctx, http

from wayfire_sim.capture_channel import CaptureChannel
from wayfire_sim.curl_builder import build_curl, is_get_available_jobs_url
from wayfire_sim.storage import SecretStore

log = logging.getLogger("wayfire_capture")


class GetAvailableJobsCapture:
    def __init__(self) -> None:
        self._root = Path(os.environ.get("WAYFIRE_ROOT", ".")).resolve()
        hosts = os.environ.get("WAYFIRE_ALLOW_HOSTS", "www.wayfair.com,secure.wayfair.com")
        self._allow_hosts = {h.strip() for h in hosts.split(",") if h.strip()}
        self._secrets_dir = os.environ.get("WAYFIRE_SECRETS_DIR", "secrets")
        self._channel = CaptureChannel(self._root)
        self._store = SecretStore(self._secrets_dir)

    def load(self, loader) -> None:
        log.info(
            "wayfire addon загружен: root=%s hosts=%s secrets=%s",
            self._root,
            self._allow_hosts,
            self._secrets_dir,
        )

    def request(self, flow: http.HTTPFlow) -> None:
        if flow.request.method.upper() != "POST":
            return

        host = flow.request.host or ""
        if self._allow_hosts and host not in self._allow_hosts:
            return

        url = flow.request.pretty_url
        if not is_get_available_jobs_url(url):
            return

        profile_id = self._channel.read_active_profile()
        if not profile_id:
            ctx.log.warn("GetAvailableJobs без active_profile — пропуск")
            return

        headers = dict(flow.request.headers)
        body = flow.request.get_content()
        curl_text = build_curl(flow.request.method, url, headers, body)
        path = self._store.save_curl(profile_id, curl_text)
        self._channel.mark_captured(profile_id)
        ctx.log.info(f"Сохранён curl для {profile_id} → {path}")


addons = [GetAvailableJobsCapture()]
