import logging
from types import SimpleNamespace

import pytest
import structlog

FAKE_BATTERY_INFO = SimpleNamespace(
    current_capacity=79,
    max_capacity=79,
    design_capacity=100,
    cycle_count=42,
    is_charging=True,
    is_plugged_in=True,
)


@pytest.fixture(autouse=True)
def _reset_logging():
    """Reset logging state between tests to prevent handler accumulation."""
    yield
    root = logging.getLogger()
    root.handlers.clear()
    structlog.reset_defaults()


@pytest.fixture
def mock_smc(mocker):
    """Mock all charging functions to prevent any real SMC writes."""
    return {
        "legacy_disable": mocker.patch("batterytool.loop.legacy_disable_charging"),
        "legacy_enable": mocker.patch("batterytool.loop.legacy_enable_charging"),
        "tahoe_disable": mocker.patch("batterytool.loop.tahoe_disable_charging"),
        "tahoe_enable": mocker.patch("batterytool.loop.tahoe_enable_charging"),
    }


@pytest.fixture(autouse=True)
def mock_sleep(mocker):
    """Mock time.sleep to avoid actual delays. Request by name to configure side_effect."""
    return mocker.patch("batterytool.loop.time.sleep")


@pytest.fixture
def mock_fetch(mocker):
    """Mock FetchBatteryInfo with static fake data. Override return_value/side_effect per test."""
    mock = mocker.patch("batterytool.loop.fetch_battery_info")
    mock.return_value = FAKE_BATTERY_INFO
    return mock
