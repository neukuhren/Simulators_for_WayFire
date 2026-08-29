"""Сохранение curl, meta и состояния очереди."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from wayfire_sim.paths import project_root, resolve_path


@dataclass
class QueueState:
    index: int = 0


@dataclass
class CaptureMeta:
    profile_id: str
    updated_at: str
    success: bool
    label: str = ""
    device_model: str = ""
    error: str | None = None


class SecretStore:
    def __init__(self, secrets_dir: str | Path) -> None:
        self._root = project_root()
        self.secrets_dir = resolve_path(secrets_dir, base=self._root)

    def curl_path(self, profile_id: str) -> Path:
        return self.secrets_dir / profile_id / "get_available_jobs.curl"

    def meta_path(self, profile_id: str) -> Path:
        return self.secrets_dir / profile_id / "meta.json"

    def save_curl(
        self,
        profile_id: str,
        curl_text: str,
        *,
        label: str = "",
        device_model: str = "",
    ) -> Path:
        target = self.curl_path(profile_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(target, curl_text.rstrip() + "\n")
        self.save_meta(
            CaptureMeta(
                profile_id=profile_id,
                updated_at=_utc_now(),
                success=True,
                label=label,
                device_model=device_model,
            )
        )
        return target

    def save_meta(self, meta: CaptureMeta) -> Path:
        path = self.meta_path(meta.profile_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(path, json.dumps(asdict(meta), ensure_ascii=False, indent=2) + "\n")
        return path

    def save_failure(
        self,
        profile_id: str,
        error: str,
        *,
        label: str = "",
        device_model: str = "",
    ) -> None:
        self.save_meta(
            CaptureMeta(
                profile_id=profile_id,
                updated_at=_utc_now(),
                success=False,
                label=label,
                device_model=device_model,
                error=error,
            )
        )


class StateStore:
    def __init__(self, path: str | Path = "data/state.json") -> None:
        self.path = resolve_path(path, base=project_root())

    def load(self) -> QueueState:
        if not self.path.is_file():
            return QueueState()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return QueueState(index=int(data.get("index", 0)))

    def save(self, state: QueueState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write_text(
            self.path,
            json.dumps({"index": state.index}, ensure_ascii=False, indent=2) + "\n",
        )


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
