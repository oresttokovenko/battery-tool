import time

import structlog

from batterytool.battery import (
    legacy_disable_charging,
    legacy_enable_charging,
    tahoe_disable_charging,
    tahoe_enable_charging,
)
from batterytool.iokit_wrapper import lib


def legacy_loop(
    target_health: int,
    max_charge: int,
    min_charge: int,
    interval: int,
    logger: structlog.stdlib.BoundLogger,
) -> None:
    """Battery cycling loop using legacy SMC keys (pre-macOS 15.7)"""
    charging_enabled = True

    try:
        while True:
            battery_info = lib.FetchBatteryInfo()
            battery_percentage = battery_info.current_capacity / battery_info.max_capacity * 100
            battery_health = battery_info.max_capacity / battery_info.design_capacity * 100

            logger.info(
                "battery_reading",
                battery_percentage=battery_percentage,
                battery_health=battery_health,
                current_capacity=battery_info.current_capacity,
                max_capacity=battery_info.max_capacity,
                design_capacity=battery_info.design_capacity,
                cycle_count=battery_info.cycle_count,
                is_charging=battery_info.is_charging,
                is_plugged_in=battery_info.is_plugged_in,
                charging_enabled=charging_enabled,
            )

            if battery_health <= target_health:
                logger.info(
                    "target_reached",
                    target_health=target_health,
                    current_health=battery_health,
                )
                break

            if battery_percentage > max_charge and charging_enabled:
                logger.info("charging_disabled", battery_percentage=battery_percentage)
                legacy_disable_charging()
                charging_enabled = False
            elif battery_percentage < min_charge and not charging_enabled:
                logger.info("charging_enabled", battery_percentage=battery_percentage)
                legacy_enable_charging()
                charging_enabled = True

            logger.debug("sleeping", interval=interval)
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt")
    except Exception as e:
        logger.exception("unexpected_error", error=str(e))
    finally:
        logger.info("cleanup", action="re-enabling charging")
        legacy_enable_charging()


def tahoe_loop(
    target_health: int,
    max_charge: int,
    min_charge: int,
    interval: int,
    logger: structlog.stdlib.BoundLogger,
) -> None:
    """Battery cycling loop using Tahoe SMC keys (macOS 15.7+)"""
    charging_enabled = True

    try:
        while True:
            battery_info = lib.FetchBatteryInfo()
            battery_percentage = battery_info.current_capacity / battery_info.max_capacity * 100
            battery_health = battery_info.max_capacity / battery_info.design_capacity * 100

            logger.info(
                "battery_reading",
                battery_percentage=battery_percentage,
                battery_health=battery_health,
                current_capacity=battery_info.current_capacity,
                max_capacity=battery_info.max_capacity,
                design_capacity=battery_info.design_capacity,
                cycle_count=battery_info.cycle_count,
                is_charging=battery_info.is_charging,
                is_plugged_in=battery_info.is_plugged_in,
                charging_enabled=charging_enabled,
            )

            if battery_health <= target_health:
                logger.info(
                    "target_reached",
                    target_health=target_health,
                    current_health=battery_health,
                )
                break

            if battery_percentage > max_charge and charging_enabled:
                logger.info("charging_disabled", battery_percentage=battery_percentage)
                tahoe_disable_charging()
                charging_enabled = False
            elif battery_percentage < min_charge and not charging_enabled:
                logger.info("charging_enabled", battery_percentage=battery_percentage)
                tahoe_enable_charging()
                charging_enabled = True

            logger.debug("sleeping", interval=interval)
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("keyboard_interrupt")
    except Exception as e:
        logger.exception("unexpected_error", error=str(e))
    finally:
        logger.info("cleanup", action="re-enabling charging")
        tahoe_enable_charging()
