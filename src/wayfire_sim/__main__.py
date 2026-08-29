"""CLI: python -m wayfire_sim."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from wayfire_sim import __version__
from wayfire_sim.config_loader import ConfigError, load_profiles, load_settings
from wayfire_sim.orchestrator import run_from_config
from wayfire_sim.paths import project_root
from wayfire_sim.storage import SecretStore


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    if args.command == "run":
        return _cmd_run(once=False)
    if args.command == "once":
        return _cmd_run(once=True)
    if args.command == "import-curl":
        return _cmd_import_curl(args)
    if args.command == "check-config":
        return _cmd_check_config()

    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wayfire-sim",
        description="Автосъём curl GetAvailableJobs с iOS Simulator (Wayfair Service Pro)",
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Подробные логи")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Бесконечный цикл по профилям")
    sub.add_parser("once", help="Один профиль из очереди и выход")
    sub.add_parser("check-config", help="Проверить settings и profiles")

    imp = sub.add_parser("import-curl", help="Вручную сохранить curl в профиль")
    imp.add_argument("profile_id", help="Например pro-01")
    imp.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Файл с curl (иначе stdin)",
    )

    return parser


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _cmd_run(*, once: bool) -> int:
    try:
        run_from_config(once=once)
        return 0
    except ConfigError as exc:
        logging.error("%s", exc)
        return 2
    except KeyboardInterrupt:
        return 130


def _cmd_check_config() -> int:
    try:
        settings = load_settings()
        profiles = load_profiles(settings.orchestrator.profiles_config)
    except ConfigError as exc:
        logging.error("%s", exc)
        return 2

    root = project_root()
    logging.info("Корень проекта: %s", root)
    logging.info("Профилей (enabled): %d", len(profiles))
    for profile in profiles:
        logging.info(
            "  • %s — %s, UDID …%s, UI %s",
            profile.id,
            profile.label,
            profile.simulator_udid[-8:],
            profile.ui_scenario,
        )
    return 0


def _cmd_import_curl(args: argparse.Namespace) -> int:
    try:
        settings = load_settings()
        profiles = load_profiles(settings.orchestrator.profiles_config)
    except ConfigError as exc:
        logging.error("%s", exc)
        return 2

    profile = next((p for p in profiles if p.id == args.profile_id), None)
    if profile is None:
        logging.error("Профиль %s не найден в конфиге", args.profile_id)
        return 2

    if args.file:
        curl_text = args.file.read_text(encoding="utf-8")
    else:
        curl_text = sys.stdin.read()

    if not curl_text.strip():
        logging.error("Пустой curl")
        return 2

    store = SecretStore(settings.storage.secrets_dir)
    path = store.save_curl(
        profile.id,
        curl_text,
        label=profile.label,
        device_model=profile.device_model,
    )
    logging.info("Сохранено: %s", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
