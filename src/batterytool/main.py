"""
SMC Learnings

The System Management Controller (SMC) controls most power functions on modern Macs.
Battery charging is one of the functions controlled by the SMC. By manipulating the SMC keys,
you can control battery charging on your Mac.

There is a good discussion on the SMC keys that control battery charging
on this GitHub issue: https://github.com/zackelia/bclm/issues/20

Legacy keys (pre-macOS 15.7):

  CH0I/CH0C are "hard" controls that will allow the battery to run down to 0
  CH0K/CH0B are "soft" controls that are reset to 0 when SOC drops below 50%

  CH0B and CH0C are used to control whether the SMC permits charging
      - Writing "00" to CH0B & CH0C tells the SMC to allow or resume charging
      - Writing "02" to CH0B & CH0C tells the SMC to disable or block charging

  CH0I controls whether the Mac will force battery discharge even when it's plugged in
      - Writing "00" to CH0I disables discharge
      - Writing "01" to CH0I enables discharge

Tahoe keys (macOS 15.7+):

  Apple's firmware update replaced the legacy keys with a new set.
  See: https://github.com/actuallymentor/battery/pull/388

  CHTE replaces CH0B/CH0C for charging control
      - Writing "00000000" to CHTE enables charging
      - Writing "01000000" to CHTE disables charging

  For forced discharge, there are now two keys with a fallback chain:
      CHIE is preferred (replaces CH0I)
          - Writing "00" to CHIE disables discharge
          - Writing "08" to CHIE enables discharge
      CH0J is the fallback if CHIE is unavailable
          - Writing "00" to CH0J disables discharge
          - Writing "01" to CH0J enables discharge

  Not all Tahoe machines expose the same keys. The tool detects which keys
  are available at runtime by attempting to read each one.
"""

import subprocess
import time
from pathlib import Path
from typing import Annotated

import structlog
import typer
from structlog.typing import FilteringBoundLogger

from batterytool.constants import (
    MANIPULATE_SMC_KEY,
    SMCKeys,
    SMCValues,
)

# Configure structlog for JSON output
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

logger: FilteringBoundLogger = structlog.get_logger()  # type: ignore[reportAny]

app = typer.Typer(help="BatteryTool - Cycle your MacBook battery for warranty replacement")


def get_battery_percentage() -> int:
    """Get current battery percentage"""
    battery_perc_command = "pmset -g batt | grep -Eo '[0-9]+%' | head -n1 | sed 's/%//'"
    result = subprocess.run(
        battery_perc_command,
        shell=True,
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout.strip()

    if not output.isdigit():
        raise ValueError(f"Unexpected battery percentage output: '{output}'")

    return int(output)


def get_battery_health() -> int:
    """Get battery health as maximum capacity percentage"""
    battery_health_command = "ioreg -r -c AppleSmartBattery | grep -i 'MaximumCapacityPercent' | awk '{print $3}'"
    result = subprocess.run(
        battery_health_command,
        shell=True,
        capture_output=True,
        text=True,
        check=True,
    )
    output = result.stdout.strip()

    if not output.isdigit():
        raise ValueError(f"Unexpected battery health output: '{output}'")

    return int(output)


def is_charger_connected() -> bool:
    """Check if the power adapter is connected"""
    charger_state_command = "pmset -g batt | head -n1 | awk '{ x=match($0, /AC Power/) > 0; print x }'"
    result = subprocess.run(
        charger_state_command,
        shell=True,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip() == "1"


def disable_charging() -> None:
    """Disable charging and enable forced discharge via SMC"""
    _ = subprocess.run(
        f"{MANIPULATE_SMC_KEY} {SMCKeys.CHARGING_CONTROL_B} -w {SMCValues.DISABLE_CHARGING}",
        shell=True,
        check=True,
    )
    _ = subprocess.run(
        f"{MANIPULATE_SMC_KEY} {SMCKeys.CHARGING_CONTROL_C} -w {SMCValues.DISABLE_CHARGING}",
        shell=True,
        check=True,
    )
    _ = subprocess.run(
        f"{MANIPULATE_SMC_KEY} {SMCKeys.DISCHARGE_CONTROL_I} -w {SMCValues.ENABLE_DISCHARGE}",
        shell=True,
        check=True,
    )


def enable_charging() -> None:
    """Re-enable charging and disable forced discharge via SMC"""
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


@app.command()
def main(
    target_health: Annotated[int, typer.Option("--target-health", help="Target battery health %")] = 79,
    max_charge: Annotated[int, typer.Option("--max-charge", help="Max charge threshold %")] = 95,
    min_charge: Annotated[int, typer.Option("--min-charge", help="Min charge threshold %")] = 5,
    interval: Annotated[int, typer.Option("--interval", help="Polling interval in seconds")] = 60,
    log_file: Annotated[Path | None, typer.Option("--log-file", help="Save logs to file")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show actions without executing")] = False,
    status: Annotated[bool, typer.Option("--status", help="Show battery status and exit")] = False,
    monitor_only: Annotated[bool, typer.Option("--monitor-only", help="Monitor without controlling charging")] = False,
    force: Annotated[bool, typer.Option("--force", help="Skip safety checks")] = False,
) -> None:
    """BatteryTool - Cycle your MacBook battery for warranty replacement"""
    # Handle --status flag
    if status:
        battery_percentage = get_battery_percentage()
        battery_health = get_battery_health()
        charger_connected = is_charger_connected()

        logger.info(
            "battery_status",
            battery_percentage=battery_percentage,
            battery_health=battery_health,
            charger_connected=charger_connected,
        )
        return

    # Check if adapter is connected before proceeding
    if not force and not is_charger_connected():
        logger.error("charger_not_connected", message="Charger not connected. Exiting...")
        return

    if dry_run:
        logger.info(
            "dry_run",
            target_health=target_health,
            max_charge=max_charge,
            min_charge=min_charge,
            interval=interval,
        )
        return

    # Track charging state to avoid unnecessary SMC writes
    charging_enabled = True

    try:
        while True:
            battery_percentage = get_battery_percentage()
            battery_health = get_battery_health()

            logger.info(
                "battery_reading",
                battery_percentage=battery_percentage,
                battery_health=battery_health,
                charging_enabled=charging_enabled,
            )

            # Check if target battery health has been reached
            if battery_health <= target_health:
                logger.info(
                    "target_reached",
                    target_health=target_health,
                    current_health=battery_health,
                )
                break

            # Only change state when crossing thresholds (skip if monitor-only)
            if not monitor_only:
                if battery_percentage > max_charge and charging_enabled:
                    logger.info("charging_disabled", battery_percentage=battery_percentage)
                    disable_charging()
                    charging_enabled = False
                elif battery_percentage < min_charge and not charging_enabled:
                    logger.info("charging_enabled", battery_percentage=battery_percentage)
                    enable_charging()
                    charging_enabled = True

            logger.debug("sleeping", interval=interval)
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt")
    except Exception as e:
        logger.exception("unexpected_error", error=str(e))
    # This always triggers to reset the SMC chip state
    finally:
        if not monitor_only:
            logger.info("cleanup", action="re-enabling charging")
            enable_charging()


if __name__ == "__main__":
    app()
