"""Запуск mitmdump и управление системным прокси macOS."""

from __future__ import annotations

import logging
import os
import re
import shutil
import signal
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from wayfire_sim.models import MacProxySettings, MitmSettings
from wayfire_sim.paths import project_root

log = logging.getLogger(__name__)


@dataclass
class ProxySnapshot:
    web_enabled: str
    web_host: str
    web_port: str
    secure_enabled: str
    secure_host: str
    secure_port: str


class MitmProcess:
    def __init__(self, mitm: MitmSettings, secrets_dir: str) -> None:
        self._mitm = mitm
        self._secrets_dir = secrets_dir
        self._proc: subprocess.Popen[bytes] | None = None
        self._root = project_root()
        self._addon_path = self._root / "src" / "wayfire_sim" / "capture_addon.py"

    def start(self) -> None:
        if self._proc is not None:
            return
        if not self._addon_path.is_file():
            raise FileNotFoundError(f"Не найден addon: {self._addon_path}")

        mitmdump = _mitmdump_bin()
        allow_pattern = "|".join(re.escape(h) for h in self._mitm.allow_hosts)
        cmd = [
            mitmdump,
            "-s",
            str(self._addon_path),
            "--listen-host",
            self._mitm.host,
            "-p",
            str(self._mitm.port),
            "--allow-hosts",
            f"^({allow_pattern})$",
            "--set",
            "stream_large_bodies=1",
        ]

        env = os.environ.copy()
        env["WAYFIRE_ROOT"] = str(self._root)
        env["WAYFIRE_ALLOW_HOSTS"] = ",".join(self._mitm.allow_hosts)
        env["WAYFIRE_SECRETS_DIR"] = self._secrets_dir
        env["PYTHONPATH"] = os.pathsep.join(
            filter(None, [str(self._root / "src"), env.get("PYTHONPATH", "")])
        )

        log.info("Запуск mitmdump: %s", " ".join(cmd))
        self._proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def stop(self) -> None:
        if self._proc is None:
            return
        proc = self._proc
        self._proc = None
        if proc.poll() is None:
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

    def __enter__(self) -> MitmProcess:
        self.start()
        return self

    def __exit__(self, *args) -> None:
        self.stop()


class MacSystemProxy:
    def __init__(self, settings: MacProxySettings, mitm: MitmSettings) -> None:
        self._settings = settings
        self._mitm = mitm
        self._snapshot: ProxySnapshot | None = None

    @staticmethod
    def is_supported() -> bool:
        return os.uname().sysname == "Darwin"

    def enable(self) -> None:
        if not self._settings.manage_system_proxy:
            return
        if not self.is_supported():
            log.warning("Системный прокси поддерживается только на macOS — пропуск")
            return

        service = self._settings.network_service
        self._snapshot = ProxySnapshot(
            web_enabled=_run_networksetup(["-getwebproxystate", service]),
            web_host=_run_networksetup(["-getwebproxy", service]),
            secure_enabled=_run_networksetup(["-getsecurewebproxystate", service]),
            secure_host=_run_networksetup(["-getsecurewebproxy", service]),
        )

        host = self._mitm.host
        port = str(self._mitm.port)
        _run_networksetup(["-setwebproxy", service, host, port])
        _run_networksetup(["-setsecurewebproxy", service, host, port])
        _run_networksetup(["-setwebproxystate", service, "on"])
        _run_networksetup(["-setsecurewebproxystate", service, "on"])
        log.info("Системный прокси включён: %s → %s:%s", service, host, port)

    def disable(self) -> None:
        if not self._settings.manage_system_proxy or not self.is_supported():
            return

        service = self._settings.network_service
        if self._snapshot is None:
            _run_networksetup(["-setwebproxystate", service, "off"])
            _run_networksetup(["-setsecurewebproxystate", service, "off"])
            return

        snap = self._snapshot
        if snap.web_enabled.strip().lower() == "enabled":
            web = _parse_proxy_line(snap.web_host)
            if web:
                _run_networksetup(["-setwebproxy", service, web[0], web[1]])
            _run_networksetup(["-setwebproxystate", service, "on"])
        else:
            _run_networksetup(["-setwebproxystate", service, "off"])

        if snap.secure_enabled.strip().lower() == "enabled":
            sec = _parse_proxy_line(snap.secure_host)
            if sec:
                _run_networksetup(["-setsecurewebproxy", service, sec[0], sec[1]])
            _run_networksetup(["-setsecurewebproxystate", service, "on"])
        else:
            _run_networksetup(["-setsecurewebproxystate", service, "off"])

        log.info("Системный прокси восстановлен для %s", service)
        self._snapshot = None

    def __enter__(self) -> MacSystemProxy:
        self.enable()
        return self

    def __exit__(self, *args) -> None:
        self.disable()


def _run_networksetup(args: list[str]) -> str:
    result = subprocess.run(
        ["networksetup", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.warning("networksetup %s: %s", args, result.stderr.strip())
    return (result.stdout or result.stderr or "").strip()


def _parse_proxy_line(output: str) -> tuple[str, str] | None:
    host = port = None
    for line in output.splitlines():
        if line.startswith("Server:"):
            host = line.split(":", 1)[1].strip()
        if line.startswith("Port:"):
            port = line.split(":", 1)[1].strip()
    if host and port:
        return host, port
    return None


def _mitmdump_bin() -> str:
    found = shutil.which("mitmdump")
    if found:
        return found
    candidate = Path(sys.executable).parent / "mitmdump"
    if candidate.is_file():
        return str(candidate)
    raise FileNotFoundError("mitmdump не найден — выполните pip install mitmproxy в venv")
