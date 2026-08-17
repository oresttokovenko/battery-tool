import logging
import os

# Must be set before any batterytool import so battery.py binds the
# file-backed fake backend instead of the real IOKit extension
os.environ["BATTERYTOOL_FAKE"] = "1"

import pytest  # noqa: E402
import structlog  # noqa: E402

LEGACY_KEYS = {"CH0B": "00", "CH0C": "00", "CH0I": "00"}
TAHOE_KEYS = {"CHTE": "00000000", "CHIE": "08"}
# Tahoe machine without CHIE, forcing the CH0J fallback path
TAHOE_FALLBACK_KEYS = {"CHTE": "00000000", "CH0J": "00"}


class FakeHardware:
    """Steers the fake SMC/battery backend via files in a tmp dir"""

    def __init__(self, path):
        self.dir = path

    def set_keys(self, keys):
        """Make the given SMC keys 'exist', e.g. {"CHTE": "00000000"}"""
        lines = [f"{key} {len(value) // 2} {value}\n" for key, value in keys.items()]
        (self.dir / "smc_keys").write_text("".join(lines))

    def script(self, *rows):
        """Script battery readings; each row is
        (current_mAh, max_mAh, design_mAh, cycle_count, is_charging, is_plugged_in)
        The loop consumes one row per poll; the last row repeats"""
        (self.dir / "battery_script").write_text(
            "".join(" ".join(str(field) for field in row) + "\n" for row in rows)
        )

    def writes(self):
        """The listener log: every successful SMC write as 'KEY=hexvalue'"""
        log = self.dir / "smc_writes.log"
        return tuple(log.read_text().splitlines()) if log.exists() else ()


@pytest.fixture
def hw(tmp_path, monkeypatch):
    """Point the fake backend at a fresh tmp dir for this test"""
    monkeypatch.setenv("BATTERYTOOL_FAKE_DIR", str(tmp_path))
    return FakeHardware(tmp_path)


@pytest.fixture(autouse=True)
def _reset_logging():
    """Reset logging state between tests to prevent handler accumulation"""
    yield
    root = logging.getLogger()
    root.handlers.clear()
    structlog.reset_defaults()
