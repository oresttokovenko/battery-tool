"""CFFI build script for generating iokit_wrapper C sources"""

import logging
import sys

from cffi import FFI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)

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
""")

ffibuilder.set_source(
    "iokit_wrapper",
    """
    #include "power_sources.h"
    """,
    sources=[],
    include_dirs=["c"],
)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
        ffibuilder.emit_c_code(output_file)
    else:
        logging.error("error")
        sys.exit(1)
