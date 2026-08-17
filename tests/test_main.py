import json
import platform

import pytest

from tests.conftest import LEGACY_KEYS, TAHOE_FALLBACK_KEYS, TAHOE_KEYS

from batterytool.logging import setup_logging
from batterytool.loop import legacy_loop, tahoe_loop
from batterytool.main import main

# Loop polls until health <= target, so every script ends on this row.
TARGET_ROW = (79, 79, 100, 10, 1, 1)  # health = 79%

LEGACY_ENABLE = ["CH0B=00", "CH0C=00", "CH0I=00"]
LEGACY_DISABLE = ["CH0B=02", "CH0C=02", "CH0I=01"]
TAHOE_ENABLE = ["CHTE=00000000", "CHIE=00"]
TAHOE_DISABLE = ["CHTE=01000000", "CHIE=08"]


def run_legacy():
    legacy_loop(target_health=79, max_charge=95, min_charge=5, interval=0, logger=setup_logging())


def run_tahoe():
    tahoe_loop(target_health=79, max_charge=95, min_charge=5, interval=0, logger=setup_logging())


# -- Legacy loop --


def test_legacy_breaks_at_target_health(hw):
    """Loop exits when battery health drops to target; only the finally-block re-enable is written."""
    hw.set_keys(LEGACY_KEYS)
    hw.script(TARGET_ROW)

    run_legacy()

    assert hw.writes() == LEGACY_ENABLE


def test_legacy_disables_charging_above_max(hw):
    """Charging disabled when battery percentage exceeds max_charge."""
    hw.set_keys(LEGACY_KEYS)
    hw.script((96, 100, 100, 10, 1, 1), TARGET_ROW)

    run_legacy()

    assert hw.writes() == LEGACY_DISABLE + LEGACY_ENABLE


def test_legacy_enables_charging_below_min(hw):
    """Charging re-enabled when battery drops below min_charge."""
    hw.set_keys(LEGACY_KEYS)
    hw.script((96, 100, 100, 10, 1, 1), (4, 100, 100, 10, 0, 1), TARGET_ROW)

    run_legacy()

    assert hw.writes() == LEGACY_DISABLE + LEGACY_ENABLE + LEGACY_ENABLE


def test_legacy_invalid_battery_data_still_reenables(hw):
    """Zero capacities break the loop and the finally block re-enables charging."""
    hw.set_keys(LEGACY_KEYS)
    hw.script((0, 0, 0, 0, 0, 0))

    run_legacy()

    assert hw.writes() == LEGACY_ENABLE


# -- Tahoe loop --


def test_tahoe_breaks_at_target_health(hw):
    hw.set_keys(TAHOE_KEYS)
    hw.script(TARGET_ROW)

    run_tahoe()

    assert hw.writes() == TAHOE_ENABLE


def test_tahoe_disables_charging_above_max(hw):
    hw.set_keys(TAHOE_KEYS)
    hw.script((96, 100, 100, 10, 1, 1), TARGET_ROW)

    run_tahoe()

    assert hw.writes() == TAHOE_DISABLE + TAHOE_ENABLE


def test_tahoe_falls_back_to_ch0j_without_chie(hw):
    """On Tahoe machines without CHIE, discharge control falls back to CH0J.

    The fake rejects the CHIE write like real hardware (unknown key), so the
    wrapper returns -1 and the Python fallback chain runs for real."""
    hw.set_keys(TAHOE_FALLBACK_KEYS)
    hw.script((96, 100, 100, 10, 1, 1), TARGET_ROW)

    run_tahoe()

    assert hw.writes() == [
        "CHTE=01000000",
        "CH0J=01",  # CHIE write failed, fallback fired
        "CHTE=00000000",
        "CH0J=00",
    ]


def test_tahoe_invalid_battery_data_still_reenables(hw):
    hw.set_keys(TAHOE_KEYS)
    hw.script((0, 0, 0, 0, 0, 0))

    run_tahoe()

    assert hw.writes() == TAHOE_ENABLE


# -- Logging --


def read_stderr_json(capfd):
    return [json.loads(line) for line in capfd.readouterr().err.strip().splitlines()]


def test_logs_json_to_stderr(hw, capfd):
    hw.set_keys(LEGACY_KEYS)
    hw.script(TARGET_ROW)

    run_legacy()

    events = read_stderr_json(capfd)
    assert len(events) > 0
    for event in events:
        assert "event" in event


def test_battery_reading_contains_all_metrics(hw, capfd):
    hw.set_keys(LEGACY_KEYS)
    hw.script(TARGET_ROW)

    run_legacy()

    readings = [e for e in read_stderr_json(capfd) if e["event"] == "battery_reading"]
    assert len(readings) >= 1
    reading = readings[0]
    assert reading["battery_percentage"] == 100.0
    assert reading["battery_health"] == 79.0
    assert reading["current_capacity"] == 79
    assert reading["max_capacity"] == 79
    assert reading["design_capacity"] == 100
    assert reading["cycle_count"] == 10
    assert reading["is_charging"] is True
    assert reading["is_plugged_in"] is True
    assert "charging_enabled" in reading


def test_logs_to_file(hw, tmp_path):
    hw.set_keys(LEGACY_KEYS)
    hw.script(TARGET_ROW)
    log_file = tmp_path / "battery.log"

    legacy_loop(target_health=79, max_charge=95, min_charge=5, interval=0, logger=setup_logging(log_file=log_file))

    events = [json.loads(line) for line in log_file.read_text().strip().splitlines()]
    assert len(events) > 0
    for event in events:
        assert "event" in event


# -- CLI (main.py) --

needs_apple_silicon = pytest.mark.skipif(
    platform.machine() != "arm64", reason="main() rejects non-Apple-Silicon machines"
)


@needs_apple_silicon
def test_cli_status_prints_and_writes_nothing(hw, capfd):
    hw.script((80, 100, 100, 10, 1, 1))

    main(status=True)

    events = [e for e in read_stderr_json(capfd) if e["event"] == "battery_status"]
    assert len(events) == 1
    assert events[0]["battery_percentage"] == 80.0
    assert hw.writes() == []


@needs_apple_silicon
def test_cli_picks_tahoe_loop_when_chte_exists(hw):
    hw.set_keys(TAHOE_KEYS)
    hw.script(TARGET_ROW)

    main(interval=0)

    assert hw.writes() == TAHOE_ENABLE


@needs_apple_silicon
def test_cli_picks_legacy_loop_without_chte(hw):
    hw.set_keys(LEGACY_KEYS)
    hw.script(TARGET_ROW)

    main(interval=0)

    assert hw.writes() == LEGACY_ENABLE


@needs_apple_silicon
def test_cli_refuses_to_run_unplugged(hw, capfd):
    hw.script((50, 100, 100, 10, 0, 0))

    main(interval=0)

    events = read_stderr_json(capfd)
    assert any(e["event"] == "charger_not_connected" for e in events)
    assert hw.writes() == []
