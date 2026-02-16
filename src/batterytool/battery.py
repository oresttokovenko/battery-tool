"""
SMC Learnings

The System Management Controller (SMC) controls most power functions on modern Macs.
Battery charging is one of the functions controlled by the SMC. By manipulating the SMC keys,
I can control battery charging on the Mac.

I found a good discussion on the SMC keys that control battery charging
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

  Not all Tahoe machines expose the same keys. I detect which keys
  are available at runtime by attempting to read each one.
"""

import platform

from batterytool.constants import SMCKeys, SMCValues
from batterytool.iokit_wrapper import ffi, lib


def is_apple_silicon() -> bool:
    """Check if I'm running on an Apple Silicon Mac"""
    return platform.machine() == "arm64"


def is_tahoe() -> bool:
    """Check if I'm on a Tahoe mac (macOS 15.7+) by trying to read the CHTE key"""
    buf = ffi.new("char[32]")
    return lib.SmcReadKey(SMCKeys.CHARGING_CONTROL_TE, buf, 32) == 0


# Legacy (pre-macOS 15.7)


def legacy_disable_charging() -> None:
    """Disable charging and force discharge via CH0B/CH0C/CH0I"""
    lib.SmcWriteKey(SMCKeys.CHARGING_CONTROL_B, SMCValues.DISABLE_CHARGING)
    lib.SmcWriteKey(SMCKeys.CHARGING_CONTROL_C, SMCValues.DISABLE_CHARGING)
    lib.SmcWriteKey(SMCKeys.DISCHARGE_CONTROL_I, SMCValues.ENABLE_DISCHARGE)


def legacy_enable_charging() -> None:
    """Re-enable charging and stop forced discharge via CH0B/CH0C/CH0I"""
    lib.SmcWriteKey(SMCKeys.CHARGING_CONTROL_B, SMCValues.ENABLE_CHARGING)
    lib.SmcWriteKey(SMCKeys.CHARGING_CONTROL_C, SMCValues.ENABLE_CHARGING)
    lib.SmcWriteKey(SMCKeys.DISCHARGE_CONTROL_I, SMCValues.DISABLE_DISCHARGE)


# Tahoe (macOS 15.7+)


def tahoe_disable_charging() -> None:
    """Disable charging and force discharge via CHTE/CHIE, falls back to CH0J"""
    lib.SmcWriteKey(SMCKeys.CHARGING_CONTROL_TE, SMCValues.TAHOE_DISABLE_CHARGING)
    if lib.SmcWriteKey(SMCKeys.DISCHARGE_CONTROL_IE, SMCValues.TAHOE_ENABLE_DISCHARGE) != 0:
        lib.SmcWriteKey(SMCKeys.DISCHARGE_CONTROL_J, SMCValues.TAHOE_FALLBACK_ENABLE_DISCHARGE)


def tahoe_enable_charging() -> None:
    """Re-enable charging and stop forced discharge via CHTE/CHIE, falls back to CH0J"""
    lib.SmcWriteKey(SMCKeys.CHARGING_CONTROL_TE, SMCValues.TAHOE_ENABLE_CHARGING)
    if lib.SmcWriteKey(SMCKeys.DISCHARGE_CONTROL_IE, SMCValues.TAHOE_DISABLE_DISCHARGE) != 0:
        lib.SmcWriteKey(SMCKeys.DISCHARGE_CONTROL_J, SMCValues.TAHOE_FALLBACK_DISABLE_DISCHARGE)
