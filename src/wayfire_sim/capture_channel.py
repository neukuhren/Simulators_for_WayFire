"""Файловый IPC между оркестратором и mitmproxy addon."""

from __future__ import annotations

import time
from pathlib import Path

from wayfire_sim.paths import project_root


class CaptureChannel:
    """Сигнализация перехвата через файлы в data/capture/."""

    def __init__(self, base: Path | None = None) -> None:
        root = base or project_root()
        self.dir = root / "data" / "capture"
        self.active_profile_file = self.dir / "active_profile.txt"
        self.flags_dir = self.dir / "flags"

    def ensure_dirs(self) -> None:
        self.flags_dir.mkdir(parents=True, exist_ok=True)

    def set_active_profile(self, profile_id: str) -> None:
        self.ensure_dirs()
        self.active_profile_file.write_text(profile_id, encoding="utf-8")

    def clear_active_profile(self) -> None:
        if self.active_profile_file.exists():
            self.active_profile_file.unlink()

    def clear_flag(self, profile_id: str) -> None:
        flag = self._flag_path(profile_id)
        if flag.exists():
            flag.unlink()

    def wait_captured(self, profile_id: str, timeout_sec: float) -> bool:
        deadline = time.monotonic() + timeout_sec
        flag = self._flag_path(profile_id)
        while time.monotonic() < deadline:
            if flag.is_file():
                return True
            time.sleep(0.25)
        return False

    def mark_captured(self, profile_id: str) -> None:
        self.ensure_dirs()
        self._flag_path(profile_id).write_text(str(time.time()), encoding="utf-8")

    def read_active_profile(self) -> str | None:
        if not self.active_profile_file.is_file():
            return None
        value = self.active_profile_file.read_text(encoding="utf-8").strip()
        return value or None

    def _flag_path(self, profile_id: str) -> Path:
        return self.flags_dir / f"{profile_id}.captured"
