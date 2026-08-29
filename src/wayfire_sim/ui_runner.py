"""Выполнение UI-сценария через idb."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import yaml

from wayfire_sim.paths import resolve_path

log = logging.getLogger(__name__)


class UiRunnerError(Exception):
    pass


class UiRunner:
    def __init__(self, udid: str, idb_path: str | None = None) -> None:
        self.udid = udid
        self.idb_path = idb_path or os.environ.get("IDB_PATH") or shutil.which("idb") or "idb"

    def run_scenario(self, scenario_path: str | Path) -> None:
        path = resolve_path(scenario_path)
        if not path.is_file():
            raise UiRunnerError(f"UI-сценарий не найден: {path}")

        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        steps = raw.get("steps") or raw
        if not isinstance(steps, list):
            raise UiRunnerError(f"Некорректный формат сценария: {path}")

        log.info("UI-сценарий %s (%d шагов)", path.name, len(steps))
        for index, step in enumerate(steps, start=1):
            self._run_step(index, step)

    def _run_step(self, index: int, step: dict[str, Any]) -> None:
        action = step.get("action")
        if action == "sleep":
            seconds = float(step.get("seconds", 1))
            log.debug("Шаг %d: sleep %.1fs", index, seconds)
            time.sleep(seconds)
            return

        if action == "tap":
            x = int(step["x"])
            y = int(step["y"])
            duration = step.get("duration_ms")
            log.info("Шаг %d: tap (%s, %s)", index, x, y)
            args = [self.idb_path, "-u", self.udid, "ui", "tap", str(x), str(y)]
            if duration is not None:
                args.extend(["--duration", str(float(duration) / 1000.0)])
            _run_idb(args)
            return

        if action == "swipe":
            x1, y1 = int(step["x1"]), int(step["y1"])
            x2, y2 = int(step["x2"]), int(step["y2"])
            duration_ms = int(step.get("duration_ms", 400))
            log.info("Шаг %d: swipe (%s,%s)→(%s,%s)", index, x1, y1, x2, y2)
            _run_idb(
                [
                    self.idb_path,
                    "-u",
                    self.udid,
                    "ui",
                    "swipe",
                    str(x1),
                    str(y1),
                    str(x2),
                    str(y2),
                    "--duration",
                    str(duration_ms / 1000.0),
                ]
            )
            return

        raise UiRunnerError(f"Шаг {index}: неизвестное действие {action!r}")


def _run_idb(args: list[str]) -> None:
    try:
        result = subprocess.run(args, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise UiRunnerError(
            "idb не найден. Установите idb-companion (brew) и добавьте idb в PATH."
        ) from exc

    if result.returncode != 0:
        msg = (result.stderr or result.stdout or "").strip()
        raise UiRunnerError(f"{' '.join(args)}: {msg}")
