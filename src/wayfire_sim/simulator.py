"""Обёртка над xcrun simctl."""

from __future__ import annotations

import logging
import subprocess
import time

log = logging.getLogger(__name__)


class SimulatorError(Exception):
    pass


class SimulatorManager:
    def __init__(self, boot_timeout_sec: int = 120) -> None:
        self.boot_timeout_sec = boot_timeout_sec

    def boot(self, udid: str) -> None:
        if self.is_booted(udid):
            log.info("Симулятор %s уже запущен", udid)
            return
        log.info("Запуск симулятора %s", udid)
        _simctl("boot", udid)
        self.wait_booted(udid)

    def wait_booted(self, udid: str) -> None:
        deadline = time.monotonic() + self.boot_timeout_sec
        while time.monotonic() < deadline:
            if self.is_booted(udid):
                try:
                    _simctl("bootstatus", udid, "-b", timeout=30)
                    return
                except SimulatorError:
                    time.sleep(2)
                    continue
            time.sleep(2)
        raise SimulatorError(f"Таймаут ожидания boot симулятора {udid}")

    def is_booted(self, udid: str) -> bool:
        out = _simctl("list", "devices", "booted", capture=True)
        return udid in out

    def shutdown(self, udid: str) -> None:
        if not self.is_booted(udid):
            return
        log.info("Остановка симулятора %s", udid)
        try:
            _simctl("shutdown", udid)
        except SimulatorError as exc:
            log.warning("shutdown %s: %s", udid, exc)

    def launch(self, udid: str, bundle_id: str) -> None:
        log.info("Запуск %s на %s", bundle_id, udid)
        _simctl("launch", udid, bundle_id)

    def terminate(self, udid: str, bundle_id: str) -> None:
        try:
            _simctl("terminate", udid, bundle_id)
        except SimulatorError:
            pass


def _simctl(*args: str, capture: bool = False, timeout: int | None = None) -> str:
    cmd = ["xcrun", "simctl", *args]
    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise SimulatorError("xcrun не найден — нужен Xcode на macOS") from exc
    except subprocess.TimeoutExpired as exc:
        raise SimulatorError(f"Таймаут simctl {' '.join(args)}") from exc

    if result.returncode != 0:
        msg = (result.stderr or result.stdout or "").strip()
        raise SimulatorError(f"simctl {' '.join(args)}: {msg}")

    if capture:
        return (result.stdout or "").strip()
    return ""
