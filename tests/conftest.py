import pytest
import logging
import time

from src.main import (
    main,
    get_battery_percentage,
    is_charger_connected,
    disable_charging,
    enable_charging,
)


@pytest.fixture
def mock_battery_functions(mocker):
    """Mock all battery-related functions"""
    return {
        "is_charger_connected": mocker.patch("src.main.is_charger_connected"),
        "get_battery_percentage": mocker.patch("src.main.get_battery_percentage"),
        "disable_charging": mocker.patch("src.main.disable_charging"),
        "enable_charging": mocker.patch("src.main.enable_charging"),
    }


@pytest.fixture
def mock_time_sleep(mocker):
    """Mock time.sleep to avoid actual delays in tests"""
    return mocker.patch("time.sleep", return_value=None)


@pytest.fixture
def mock_logging(mocker):
    """Mock logging functions"""
    return {
        "info": mocker.patch("src.main.logging.info"),
        "error": mocker.patch("src.main.logging.error"),
        "exception": mocker.patch("src.main.logging.exception"),
    }
