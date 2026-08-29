"""Поиск корня репозитория и общие пути."""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    env = os.environ.get("WAYFIRE_ROOT")
    if env:
        return Path(env).resolve()
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "config").is_dir() and (candidate / "src" / "wayfire_sim").is_dir():
            return candidate
    return cwd


def resolve_path(path: str | Path, *, base: Path | None = None) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return (base or project_root()) / p
