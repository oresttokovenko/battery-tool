"""Type stubs for iokit_wrapper CFFI module"""

from typing import Any, Protocol

class BatteryInfo(Protocol):
    current_capacity: int
    max_capacity: int
    design_capacity: int
    cycle_count: int
    is_charging: bool
    is_plugged_in: bool

class _Lib(Protocol):
    def FetchBatteryInfo(self) -> BatteryInfo: ...
    def SmcWriteKey(self, key: bytes, value: bytes) -> int: ...
    def SmcReadKey(self, key: bytes, value: bytes, value_size: int) -> int: ...

class _FFI(Protocol):
    def new(self, cdecl: str) -> Any: ...

ffi: _FFI
lib: _Lib
