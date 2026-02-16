from enum import StrEnum

DEFAULT_TARGET_HEALTH = 79
DEFAULT_MAX_CHARGE = 95
DEFAULT_MIN_CHARGE = 5
DEFAULT_POLLING_INTERVAL = 60


class SMCKeys(StrEnum):
    """SMC key names for battery charging control"""

    # Legacy keys (pre-macOS 15.7)
    CHARGING_CONTROL_B = "CH0B"
    CHARGING_CONTROL_C = "CH0C"
    DISCHARGE_CONTROL_I = "CH0I"

    # Tahoe keys (macOS 15.7+)
    CHARGING_CONTROL_TE = "CHTE"
    DISCHARGE_CONTROL_IE = "CHIE"
    DISCHARGE_CONTROL_J = "CH0J"


class SMCValues(StrEnum):
    """Hex values written to SMC keys"""

    # Legacy charging (CH0B/CH0C)
    ENABLE_CHARGING = "00"
    DISABLE_CHARGING = "02"

    # Legacy discharge (CH0I)
    ENABLE_DISCHARGE = "01"
    DISABLE_DISCHARGE = "00"

    # Tahoe charging (CHTE)
    TAHOE_ENABLE_CHARGING = "00000000"
    TAHOE_DISABLE_CHARGING = "01000000"

    # Tahoe discharge (CHIE)
    TAHOE_ENABLE_DISCHARGE = "08"
    TAHOE_DISABLE_DISCHARGE = "00"

    # Tahoe discharge fallback (CH0J) — same as legacy CH0I values
    TAHOE_FALLBACK_ENABLE_DISCHARGE = "01"
    TAHOE_FALLBACK_DISABLE_DISCHARGE = "00"
