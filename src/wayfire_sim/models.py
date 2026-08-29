"""Модели конфигурации."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Profile:
    id: str
    label: str
    device_model: str
    simulator_udid: str
    bundle_id: str
    ui_scenario: str
    enabled: bool = True


@dataclass(frozen=True)
class MitmSettings:
    host: str = "127.0.0.1"
    port: int = 8080
    allow_hosts: tuple[str, ...] = ("www.wayfair.com", "secure.wayfair.com")


@dataclass(frozen=True)
class MacProxySettings:
    network_service: str = "Wi-Fi"
    manage_system_proxy: bool = True


@dataclass(frozen=True)
class OrchestratorSettings:
    pause_between_profiles_sec: int = 60
    capture_timeout_sec: int = 90
    boot_timeout_sec: int = 120
    profiles_config: str = "config/profiles.local.yaml"


@dataclass(frozen=True)
class StorageSettings:
    secrets_dir: str = "secrets"


@dataclass(frozen=True)
class Settings:
    mitm: MitmSettings = field(default_factory=MitmSettings)
    proxy_mac: MacProxySettings = field(default_factory=MacProxySettings)
    orchestrator: OrchestratorSettings = field(default_factory=OrchestratorSettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
