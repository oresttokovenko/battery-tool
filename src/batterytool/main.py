from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from batterytool.battery import is_apple_silicon, is_tahoe
from batterytool.iokit_wrapper import lib
from batterytool.logging import setup_logging
from batterytool.loop import legacy_loop, tahoe_loop

if TYPE_CHECKING:
    from batterytool.iokit_wrapper import BatteryInfo


app = typer.Typer(help="BatteryTool - Cycle your MacBook battery for warranty replacement")


@app.command()
def main(
    target_health: Annotated[int, typer.Option("--target-health", help="Target battery health %")] = 79,
    max_charge: Annotated[int, typer.Option("--max-charge", help="Max charge threshold %")] = 95,
    min_charge: Annotated[int, typer.Option("--min-charge", help="Min charge threshold %")] = 5,
    interval: Annotated[int, typer.Option("--interval", help="Polling interval in seconds")] = 60,
    log_file: Annotated[Path | None, typer.Option("--log-file", help="Save logs to file")] = None,
    status: Annotated[bool, typer.Option("--status", help="Show battery status and exit")] = False,
) -> None:
    """BatteryTool - Cycle your MacBook battery for warranty replacement"""
    logger = setup_logging(log_file)

    if not is_apple_silicon():
        logger.error("unsupported", message="Only Apple Silicon Macs are supported")
        return

    battery_info: BatteryInfo = lib.FetchBatteryInfo()

    battery_percentage = battery_info.current_capacity / battery_info.max_capacity * 100
    battery_health = battery_info.max_capacity / battery_info.design_capacity * 100

    if status:
        logger.info(
            "battery_status",
            battery_percentage=battery_percentage,
            battery_health=battery_health,
            current_capacity=battery_info.current_capacity,
            max_capacity=battery_info.max_capacity,
            design_capacity=battery_info.design_capacity,
            cycle_count=battery_info.cycle_count,
            is_charging=battery_info.is_charging,
            charger_connected=battery_info.is_plugged_in,
        )
        return

    # Check if adapter is connected before proceeding
    if not battery_info.is_plugged_in:
        logger.error("charger_not_connected", message="Charger not connected. Exiting...")
        return

    if is_tahoe():
        tahoe_loop(target_health, max_charge, min_charge, interval, logger)
    else:
        legacy_loop(target_health, max_charge, min_charge, interval, logger)


if __name__ == "__main__":
    app()
