"""Тесты capture channel."""

from pathlib import Path

from wayfire_sim.capture_channel import CaptureChannel


def test_capture_channel_wait_and_flag(tmp_path: Path) -> None:
    channel = CaptureChannel(tmp_path)
    channel.set_active_profile("pro-01")
    assert channel.read_active_profile() == "pro-01"

    channel.clear_flag("pro-01")
    assert channel.wait_captured("pro-01", timeout_sec=0.3) is False

    channel.mark_captured("pro-01")
    assert channel.wait_captured("pro-01", timeout_sec=1.0) is True
