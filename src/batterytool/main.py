"""
SMC Learnings

The System Management Controller (SMC) controls most power functions on modern Macs.
Battery charging is one of the functions controlled by the SMC. By manipulating the SMC keys,
you can control battery charging on your Mac. THe SMC keys that control battery charging are:

There is a good discussion on the SMC keys that control battery charging
on this GitHub issue: https://github.com/zackelia/bclm/issues/20

CH0I/CH0C are "hard" controls that will allow the battery to run down to 0
CH0K/CH0B are "soft" controls that are reset to 0 when SOC drops below 50%

CH0B and CH0C are used to control whether the SMC permits charging
    - Writing "00" to CH0B & CH0C tells the SMC to allow or resume charging
    - Writing "02" to CH0B & CH0C tells the SMC to disable or block charging

CH0I controls whether the Mac will force battery discharge even when it’s plugged in
"""

import logging
import subprocess
import time
from enum import StrEnum
from pathlib import Path

logging.basicConfig(level=logging.INFO)

BIN_PATH = Path("smc-command") / "smc"
MANIPULATE_SMC_KEY = f"{BIN_PATH} -k"
LOW_BATTERY_THRESHOLD = 5
HIGH_BATTERY_THRESHOLD = 95


class SMCKeys(StrEnum):
    CHARGING_CONTROL_B = "CH0B"  # Used to enable (00) or disable (02) charging
    CHARGING_CONTROL_C = "CH0C"  # Works alongside CH0B to control charging
    DISCHARGE_CONTROL_I = "CH0I"  # Controls discharging when adapter is connected


def get_battery_percentage() -> int:
    battery_perc_command = "pmset -g batt | tail -n1 | awk '{print $3}' | sed 's:%;::'"
    result = subprocess.run(
        battery_perc_command,
        shell=True,
        capture_output=True,
        text=True,
        check=True,
    )
    return int(result.stdout)


def is_charger_connected() -> bool:
    charger_state_command = (
        "pmset -g batt | head -n1 | awk '{ x=match($0, /AC Power/) > 0; print x }'"
    )
    result = subprocess.run(
        charger_state_command,
        shell=True,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip() == "1"


def disable_charging() -> None:
    # Disable charging by writing 02 to CH0B and CH0C
    # and force discharge by writing 01 to CH0I
    _ = subprocess.run(
        f"{MANIPULATE_SMC_KEY} {SMCKeys.CHARGING_CONTROL_B} -w 02",
        shell=True,
        check=True,
    )
    _ = subprocess.run(
        f"{MANIPULATE_SMC_KEY} {SMCKeys.CHARGING_CONTROL_C} -w 02",
        shell=True,
        check=True,
    )
    _ = subprocess.run(
        f"{MANIPULATE_SMC_KEY} {SMCKeys.DISCHARGE_CONTROL_I} -w 01",
        shell=True,
        check=True,
    )


def enable_charging() -> None:
    # Re-enable charging by writing 00 to CH0B and CH0C
    # and allow the adapter to charge by writing 00 to CH0I
    _ = subprocess.run(
        f"{MANIPULATE_SMC_KEY} {SMCKeys.CHARGING_CONTROL_B} -w 00",
        shell=True,
        check=True,
    )
    _ = subprocess.run(
        f"{MANIPULATE_SMC_KEY} {SMCKeys.CHARGING_CONTROL_C} -w 00",
        shell=True,
        check=True,
    )
    _ = subprocess.run(
        f"{MANIPULATE_SMC_KEY} {SMCKeys.DISCHARGE_CONTROL_I} -w 00",
        shell=True,
        check=True,
    )


def main() -> None:
    # Check if adapter is connected before proceeding
    if not is_charger_connected():
        logging.error("Charger not connected. Exiting...")
        # Early return
        return

    # Track charging state to avoid unnecessary SMC writes
    charging_enabled = True  # Assume charging is enabled at start

    try:
        while True:
            battery_percentage = get_battery_percentage()
            logging.info(f"Battery percentage: {battery_percentage}")

            # Only change state when crossing thresholds
            if battery_percentage > HIGH_BATTERY_THRESHOLD and charging_enabled:
                logging.info("Disabling charging")
                disable_charging()
                charging_enabled = False
            elif battery_percentage < LOW_BATTERY_THRESHOLD and not charging_enabled:
                logging.info("Enabling charging")
                enable_charging()
                charging_enabled = True

            logging.info("Sleeping for 60 seconds")
            time.sleep(60)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, exiting...")
    except Exception:
        logging.exception("Unexpected error occurred")
    finally:
        logging.info("Exiting: Re-enabling charging")
        enable_charging()


if __name__ == "__main__":
    main()
