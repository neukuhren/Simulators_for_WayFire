"""Главный цикл: симулятор → UI → ожидание curl."""

from __future__ import annotations

import logging
import signal
import time

from wayfire_sim.capture_channel import CaptureChannel
from wayfire_sim.config_loader import load_profiles, load_settings
from wayfire_sim.models import Profile, Settings
from wayfire_sim.proxy import MacSystemProxy, MitmProcess
from wayfire_sim.simulator import SimulatorError, SimulatorManager
from wayfire_sim.storage import SecretStore, StateStore
from wayfire_sim.ui_runner import UiRunner, UiRunnerError

log = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, settings: Settings, profiles: list[Profile]) -> None:
        self.settings = settings
        self.profiles = profiles
        self.state_store = StateStore()
        self.secret_store = SecretStore(settings.storage.secrets_dir)
        self.capture = CaptureChannel()
        self.simulator = SimulatorManager(settings.orchestrator.boot_timeout_sec)
        self._stop = False

    def request_stop(self) -> None:
        self._stop = True

    def run(self, *, once: bool = False) -> None:
        state = self.state_store.load()
        if state.index >= len(self.profiles):
            state.index = 0

        mitm = MitmProcess(self.settings.mitm, self.settings.storage.secrets_dir)
        mac_proxy = MacSystemProxy(self.settings.proxy_mac, self.settings.mitm)

        mitm.start()
        mac_proxy.enable()

        try:
            while not self._stop:
                profile = self.profiles[state.index]
                log.info(
                    "=== Профиль %s (%s) [%d/%d] ===",
                    profile.id,
                    profile.label,
                    state.index + 1,
                    len(self.profiles),
                )

                success = self._process_profile(profile)
                if not success:
                    self.secret_store.save_failure(
                        profile.id,
                        "Не перехвачен GetAvailableJobs за отведённое время",
                        label=profile.label,
                        device_model=profile.device_model,
                    )

                state.index = (state.index + 1) % len(self.profiles)
                self.state_store.save(state)

                if once:
                    break

                pause = self.settings.orchestrator.pause_between_profiles_sec
                log.info("Пауза %d с до следующего профиля", pause)
                self._interruptible_sleep(pause)
        finally:
            mac_proxy.disable()
            mitm.stop()
            self.capture.clear_active_profile()

    def _process_profile(self, profile: Profile) -> bool:
        self.capture.set_active_profile(profile.id)
        self.capture.clear_flag(profile.id)

        try:
            self.simulator.boot(profile.simulator_udid)
            self.simulator.launch(profile.simulator_udid, profile.bundle_id)

            ui = UiRunner(profile.simulator_udid)
            ui.run_scenario(profile.ui_scenario)

            timeout = self.settings.orchestrator.capture_timeout_sec
            if self.capture.wait_captured(profile.id, timeout):
                log.info("Профиль %s: curl сохранён", profile.id)
                return True

            log.error("Профиль %s: таймаут перехвата (%d с)", profile.id, timeout)
            return False

        except (SimulatorError, UiRunnerError) as exc:
            log.exception("Профиль %s: %s", profile.id, exc)
            self.secret_store.save_failure(
                profile.id,
                str(exc),
                label=profile.label,
                device_model=profile.device_model,
            )
            return False
        finally:
            self.capture.clear_active_profile()
            self.simulator.shutdown(profile.simulator_udid)

    def _interruptible_sleep(self, seconds: int) -> None:
        end = time.monotonic() + seconds
        while time.monotonic() < end and not self._stop:
            time.sleep(min(1.0, end - time.monotonic()))


def run_from_config(*, once: bool = False) -> None:
    settings = load_settings()
    profiles = load_profiles(settings.orchestrator.profiles_config)
    orch = Orchestrator(settings, profiles)

    def _handle_sigint(_signum, _frame) -> None:
        log.warning("Остановка по сигналу…")
        orch.request_stop()

    signal.signal(signal.SIGINT, _handle_sigint)
    signal.signal(signal.SIGTERM, _handle_sigint)
    orch.run(once=once)
