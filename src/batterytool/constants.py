from enum import Enum

DEFAULT_TARGET_HEALTH = 79
DEFAULT_MAX_CHARGE = 95
DEFAULT_MIN_CHARGE = 5
DEFAULT_POLLING_INTERVAL = 60


class SMCKeys(bytes, Enum):
    """SMC key names for battery charging control"""

    # Legacy keys (pre-macOS 15.7)
    CHARGING_CONTROL_B = b"CH0B"
    CHARGING_CONTROL_C = b"CH0C"
    DISCHARGE_CONTROL_I = b"CH0I"

    # Tahoe keys (macOS 15.7+)
    CHARGING_CONTROL_TE = b"CHTE"
    DISCHARGE_CONTROL_IE = b"CHIE"
    DISCHARGE_CONTROL_J = b"CH0J"


class SMCValues(bytes, Enum):
    """Hex values written to SMC keys"""

    # Legacy charging (CH0B/CH0C)
    ENABLE_CHARGING = b"00"
    DISABLE_CHARGING = b"02"

    # Legacy discharge (CH0I)
    ENABLE_DISCHARGE = b"01"
    DISABLE_DISCHARGE = b"00"

    # Tahoe charging (CHTE)
    TAHOE_ENABLE_CHARGING = b"00000000"
    TAHOE_DISABLE_CHARGING = b"01000000"

    # Tahoe discharge (CHIE)
    TAHOE_ENABLE_DISCHARGE = b"08"
    TAHOE_DISABLE_DISCHARGE = b"00"

    # Tahoe discharge fallback (CH0J) — same as legacy CH0I values
    TAHOE_FALLBACK_ENABLE_DISCHARGE = b"01"
    TAHOE_FALLBACK_DISABLE_DISCHARGE = b"00"
