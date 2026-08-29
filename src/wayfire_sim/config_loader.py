"""Загрузка YAML-конфигов."""

from __future__ import annotations

from pathlib import Path

import yaml

from wayfire_sim.models import (
    MacProxySettings,
    MitmSettings,
    OrchestratorSettings,
    Profile,
    Settings,
    StorageSettings,
)
from wayfire_sim.paths import project_root, resolve_path


class ConfigError(Exception):
    """Ошибка чтения или валидации конфигурации."""


def load_settings(path: str | Path | None = None) -> Settings:
    root = project_root()
    cfg_path = resolve_path(path or "config/settings.yaml", base=root)
    if not cfg_path.is_file():
        raise ConfigError(
            f"Не найден {cfg_path}. Скопируйте config/settings.example.yaml → config/settings.yaml"
        )

    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    mitm_raw = raw.get("mitm") or {}
    proxy_raw = raw.get("proxy_mac") or {}
    orch_raw = raw.get("orchestrator") or {}
    storage_raw = raw.get("storage") or {}

    allow_hosts = mitm_raw.get("allow_hosts") or ["www.wayfair.com", "secure.wayfair.com"]

    return Settings(
        mitm=MitmSettings(
            host=str(mitm_raw.get("host", "127.0.0.1")),
            port=int(mitm_raw.get("port", 8080)),
            allow_hosts=tuple(allow_hosts),
        ),
        proxy_mac=MacProxySettings(
            network_service=str(proxy_raw.get("network_service", "Wi-Fi")),
            manage_system_proxy=bool(proxy_raw.get("manage_system_proxy", True)),
        ),
        orchestrator=OrchestratorSettings(
            pause_between_profiles_sec=int(orch_raw.get("pause_between_profiles_sec", 60)),
            capture_timeout_sec=int(orch_raw.get("capture_timeout_sec", 90)),
            boot_timeout_sec=int(orch_raw.get("boot_timeout_sec", 120)),
            profiles_config=str(orch_raw.get("profiles_config", "config/profiles.local.yaml")),
        ),
        storage=StorageSettings(secrets_dir=str(storage_raw.get("secrets_dir", "secrets"))),
    )


def load_profiles(path: str | Path) -> list[Profile]:
    root = project_root()
    cfg_path = resolve_path(path, base=root)
    if not cfg_path.is_file():
        raise ConfigError(
            f"Не найден {cfg_path}. Скопируйте config/profiles.example.yaml → config/profiles.local.yaml"
        )

    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    items = raw.get("profiles") or []
    profiles: list[Profile] = []

    for item in items:
        if not item:
            continue
        profile = Profile(
            id=str(item["id"]),
            label=str(item.get("label", item["id"])),
            device_model=str(item.get("device_model", "")),
            simulator_udid=str(item["simulator_udid"]),
            bundle_id=str(item["bundle_id"]),
            ui_scenario=str(item["ui_scenario"]),
            enabled=bool(item.get("enabled", True)),
        )
        if profile.enabled:
            _validate_profile(profile, root)
        profiles.append(profile)

    enabled = [p for p in profiles if p.enabled]
    if not enabled:
        raise ConfigError("Нет включённых профилей (enabled: true) в конфиге.")

    return enabled


def _validate_profile(profile: Profile, root: Path) -> None:
    if profile.simulator_udid.startswith("00000000"):
        raise ConfigError(
            f"Профиль {profile.id}: замените simulator_udid на реальный UDID симулятора."
        )
    ui_path = resolve_path(profile.ui_scenario, base=root)
    if not ui_path.is_file():
        raise ConfigError(
            f"Профиль {profile.id}: не найден UI-сценарий {ui_path}. "
            f"Скопируйте config/ui/{profile.id}.example.yaml → {profile.ui_scenario}"
        )
