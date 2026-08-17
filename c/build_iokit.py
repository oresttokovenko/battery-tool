"""CFFI build script for generating iokit_wrapper C sources"""

import sys

from cffi import FFI

ffibuilder = FFI()

ffibuilder.cdef("""
    typedef int MilliampHours;

    typedef struct {
        MilliampHours current_capacity;
        MilliampHours max_capacity;
        MilliampHours design_capacity;
        int cycle_count;
        bool is_charging;
        bool is_plugged_in;
    } BatteryInfo;

    BatteryInfo FetchBatteryInfo(void);

    int SmcWriteKey(const char *key, const char *value);
    int SmcReadKey(const char *key, char *value, int value_size);
""")

# Module name must match the final extension filename (it becomes PyInit_<name>).
# The fake backend build passes 'iokit_wrapper_fake' as argv[2].
module_name = sys.argv[2] if len(sys.argv) > 2 else "iokit_wrapper"

ffibuilder.set_source(
    module_name,
    """
    #include "power_sources.h"
    #include "smc_wrapper.h"
    """,
    sources=[],
    include_dirs=["c"],
)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        ffibuilder.emit_c_code(output_file)
    else:
        sys.exit("Usage: build_iokit.py <output_file> [module_name]")
