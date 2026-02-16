"""Type stubs for iokit_wrapper CFFI module"""

from typing import Protocol

class BatteryInfo(Protocol):
    current_capacity: int
    max_capacity: int
    design_capacity: int
    cycle_count: int
    is_charging: bool
    is_plugged_in: bool

class _Lib(Protocol):
    def FetchBatteryInfo(self) -> BatteryInfo: ...

lib: _Lib
