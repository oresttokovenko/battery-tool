import pytest
import logging
import time

from src import (
    main,
    get_battery_percentage,
    is_charger_connected,
    disable_charging,
    enable_charging,
)


# Test when charger is not connected
def test_charger_not_connected(mocker):
    mocker.patch("batterytool.is_charger_connected", return_value=False)
    mocker.patch("batterytool.get_battery_percentage", return_value=50)
    mocker.patch("batterytool.disable_charging")
    mocker.patch("batterytool.enable_charging")
    mocker.patch("time.sleep", return_value=None)

    with mocker.patch("logging.error") as mock_logging_error:
        main()
        mock_logging_error.assert_called_with("Charger not connected. Exiting...")
        # Ensure no charging action happens
        disable_charging.assert_not_called()
        enable_charging.assert_not_called()


# Test when battery percentage is higher than threshold
def test_battery_above_threshold(mocker):
    mocker.patch("batterytool.is_charger_connected", return_value=True)
    mocker.patch("batterytool.get_battery_percentage", return_value=100)
    mocker.patch("batterytool.disable_charging")
    mocker.patch("batterytool.enable_charging")
    mocker.patch("time.sleep", return_value=None)

    with mocker.patch("logging.info") as mock_logging_info:
        main()
        mock_logging_info.assert_any_call("Battery percentage: 100")
        # Should attempt to disable charging
        disable_charging.assert_called_once()
        # Should not attempt to enable charging
        enable_charging.assert_not_called()


# Test when battery percentage is below threshold
def test_battery_below_threshold(mocker):
    mocker.patch("batterytool.is_charger_connected", return_value=True)
    mocker.patch("batterytool.get_battery_percentage", return_value=10)
    mocker.patch("batterytool.disable_charging")
    mocker.patch("batterytool.enable_charging")
    mocker.patch("time.sleep", return_value=None)

    with mocker.patch("logging.info") as mock_logging_info:
        main()
        mock_logging_info.assert_any_call("Battery percentage: 10")
        # Should attempt to enable charging
        enable_charging.assert_called_once()
        # Should not attempt to disable charging
        disable_charging.assert_not_called()


# Test if KeyboardInterrupt is handled properly
def test_keyboard_interrupt(mocker):
    mocker.patch("batterytool.is_charger_connected", return_value=True)
    mocker.patch("batterytool.get_battery_percentage", return_value=50)
    mocker.patch("batterytool.disable_charging")
    mocker.patch("batterytool.enable_charging")
    mocker.patch("time.sleep", return_value=None)

    with mocker.patch("logging.info") as mock_logging_info:
        with mocker.patch("logging.error") as mock_logging_error:
            # Simulate KeyboardInterrupt
            with pytest.raises(KeyboardInterrupt):
                main()
            mock_logging_info.assert_any_call("Exiting program...")
            mock_logging_info.assert_any_call("Exiting: Re-enabling charging")
            enable_charging.assert_called_once()
