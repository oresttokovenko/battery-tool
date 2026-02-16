import json
from types import SimpleNamespace

from batterytool.logging import setup_logging
from batterytool.loop import legacy_loop, tahoe_loop


def make_battery_info(**overrides):
    defaults = dict(
        current_capacity=80,
        max_capacity=100,
        design_capacity=100,
        cycle_count=10,
        is_charging=True,
        is_plugged_in=True,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


# -- Legacy loop --


def test_legacy_breaks_at_target_health(mock_smc, mock_fetch):
    """Loop exits when battery health drops to target."""
    logger = setup_logging()

    legacy_loop(target_health=79, max_charge=95, min_charge=5, interval=60, logger=logger)

    mock_smc["legacy_disable"].assert_not_called()
    mock_smc["legacy_enable"].assert_called_once()  # finally block


def test_legacy_disables_charging_above_max(mock_smc, mock_fetch):
    """Charging disabled when battery percentage exceeds max_charge."""
    mock_fetch.side_effect = [
        make_battery_info(current_capacity=96),
        make_battery_info(current_capacity=79, max_capacity=79),
    ]
    logger = setup_logging()

    legacy_loop(target_health=79, max_charge=95, min_charge=5, interval=60, logger=logger)

    mock_smc["legacy_disable"].assert_called_once()


def test_legacy_enables_charging_below_min(mock_smc, mock_fetch):
    """Charging re-enabled when battery drops below min_charge."""
    mock_fetch.side_effect = [
        make_battery_info(current_capacity=96),
        make_battery_info(current_capacity=4),
        make_battery_info(current_capacity=79, max_capacity=79),
    ]
    logger = setup_logging()

    legacy_loop(target_health=79, max_charge=95, min_charge=5, interval=60, logger=logger)

    mock_smc["legacy_disable"].assert_called_once()
    # enable called once in the loop + once in finally
    assert mock_smc["legacy_enable"].call_count == 2


def test_legacy_keyboard_interrupt_reenables_charging(mock_smc, mock_fetch, mock_sleep):
    """KeyboardInterrupt is handled and charging is re-enabled."""
    mock_fetch.return_value = make_battery_info(current_capacity=50)
    mock_sleep.side_effect = KeyboardInterrupt
    logger = setup_logging()

    legacy_loop(target_health=79, max_charge=95, min_charge=5, interval=60, logger=logger)

    mock_smc["legacy_enable"].assert_called_once()


def test_legacy_unexpected_exception_reenables_charging(mock_smc, mock_fetch):
    """Unexpected exceptions are caught and charging is re-enabled."""
    mock_fetch.side_effect = RuntimeError("boom")
    logger = setup_logging()

    legacy_loop(target_health=79, max_charge=95, min_charge=5, interval=60, logger=logger)

    mock_smc["legacy_enable"].assert_called_once()


# -- Tahoe loop --


def test_tahoe_breaks_at_target_health(mock_smc, mock_fetch):
    """Loop exits when battery health drops to target."""
    logger = setup_logging()

    tahoe_loop(target_health=79, max_charge=95, min_charge=5, interval=60, logger=logger)

    mock_smc["tahoe_disable"].assert_not_called()
    mock_smc["tahoe_enable"].assert_called_once()


def test_tahoe_disables_charging_above_max(mock_smc, mock_fetch):
    """Charging disabled when battery percentage exceeds max_charge."""
    mock_fetch.side_effect = [
        make_battery_info(current_capacity=96),
        make_battery_info(current_capacity=79, max_capacity=79),
    ]
    logger = setup_logging()

    tahoe_loop(target_health=79, max_charge=95, min_charge=5, interval=60, logger=logger)

    mock_smc["tahoe_disable"].assert_called_once()


def test_tahoe_enables_charging_below_min(mock_smc, mock_fetch):
    """Charging re-enabled when battery drops below min_charge."""
    mock_fetch.side_effect = [
        make_battery_info(current_capacity=96),
        make_battery_info(current_capacity=4),
        make_battery_info(current_capacity=79, max_capacity=79),
    ]
    logger = setup_logging()

    tahoe_loop(target_health=79, max_charge=95, min_charge=5, interval=60, logger=logger)

    mock_smc["tahoe_disable"].assert_called_once()
    assert mock_smc["tahoe_enable"].call_count == 2


def test_tahoe_keyboard_interrupt_reenables_charging(mock_smc, mock_fetch, mock_sleep):
    """KeyboardInterrupt is handled and charging is re-enabled."""
    mock_fetch.return_value = make_battery_info(current_capacity=50)
    mock_sleep.side_effect = KeyboardInterrupt
    logger = setup_logging()

    tahoe_loop(target_health=79, max_charge=95, min_charge=5, interval=60, logger=logger)

    mock_smc["tahoe_enable"].assert_called_once()


# -- Logging --


def test_logs_json_to_stderr(mock_smc, mock_fetch, capfd):
    """JSON log lines appear on stderr."""
    logger = setup_logging()

    legacy_loop(target_health=79, max_charge=95, min_charge=5, interval=60, logger=logger)

    stderr = capfd.readouterr().err
    lines = [line for line in stderr.strip().splitlines() if line.strip()]
    assert len(lines) > 0
    for line in lines:
        data = json.loads(line)
        assert "event" in data


def test_battery_reading_contains_all_metrics(mock_smc, mock_fetch, capfd):
    """battery_reading event includes all BatteryInfo metrics."""
    logger = setup_logging()

    legacy_loop(target_health=79, max_charge=95, min_charge=5, interval=60, logger=logger)

    stderr = capfd.readouterr().err
    readings = [json.loads(line) for line in stderr.strip().splitlines() if "battery_reading" in line]
    assert len(readings) >= 1
    reading = readings[0]
    assert reading["battery_percentage"] == 100.0
    assert reading["battery_health"] == 79.0
    assert reading["current_capacity"] == 79
    assert reading["max_capacity"] == 79
    assert reading["design_capacity"] == 100
    assert reading["cycle_count"] == 42
    assert reading["is_charging"] is True
    assert reading["is_plugged_in"] is True
    assert "charging_enabled" in reading


def test_logs_to_file(mock_smc, mock_fetch, tmp_path):
    """When log_file is provided, JSON lines are written to the file."""
    log_file = tmp_path / "battery.log"
    logger = setup_logging(log_file=log_file)

    legacy_loop(target_health=79, max_charge=95, min_charge=5, interval=60, logger=logger)

    assert log_file.exists()
    lines = [line for line in log_file.read_text().strip().splitlines() if line.strip()]
    assert len(lines) > 0
    for line in lines:
        data = json.loads(line)
        assert "event" in data
