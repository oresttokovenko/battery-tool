from src.main import main
import pytest


def test_charger_not_connected(mock_battery_functions, mock_logging):
    """Test when charger is not connected"""
    mock_battery_functions["is_charger_connected"].return_value = False
    mock_battery_functions["get_battery_percentage"].return_value = 50

    main()

    mock_logging["error"].assert_called_with("Charger not connected. Exiting...")


def test_battery_above_threshold(mock_battery_functions, mock_time_sleep, mock_logging):
    """Test when battery percentage is higher than threshold"""
    mock_battery_functions["is_charger_connected"].return_value = True
    mock_battery_functions["get_battery_percentage"].return_value = 100

    mock_time_sleep.side_effect = KeyboardInterrupt

    main()

    mock_logging["info"].assert_any_call("Battery percentage: 100")
    # Should attempt to disable charging
    mock_battery_functions["disable_charging"].assert_called_once()


def test_battery_below_threshold(mock_battery_functions, mock_time_sleep, mock_logging):
    """Test when battery percentage is below threshold"""
    mock_battery_functions["is_charger_connected"].return_value = True
    mock_battery_functions["get_battery_percentage"].return_value = 4

    mock_time_sleep.side_effect = KeyboardInterrupt

    main()

    mock_logging["info"].assert_any_call("Battery percentage: 4")
    # Should attempt to enable charging
    # Will trigger twice so we're looking for any number of calls
    mock_battery_functions["enable_charging"].assert_called()


def test_keyboard_interrupt(mock_battery_functions, mock_time_sleep, mock_logging):
    """Test if KeyboardInterrupt is handled properly"""
    mock_battery_functions["is_charger_connected"].return_value = True
    mock_battery_functions["get_battery_percentage"].return_value = 50

    mock_time_sleep.side_effect = KeyboardInterrupt

    main()

    mock_logging["error"].assert_any_call("Exiting program...")
    mock_logging["exception"].assert_any_call("Exiting: Re-enabling charging")
    mock_battery_functions["enable_charging"].assert_called_once()
