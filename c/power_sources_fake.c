/*
 * File-backed fake of FetchBatteryInfo for sandboxed testing
 *
 * Reads $BATTERYTOOL_FAKE_DIR/battery_script, one whitespace-separated row
 * per line:
 *
 *   <current_mAh> <max_mAh> <design_mAh> <cycle_count> <is_charging>
 * <is_plugged_in>
 *
 * Each call consumes the row at the position stored in battery_cursor
 * (created on first call), so a test can script a sequence of readings
 * Past the last row, the last row repeats. With BATTERYTOOL_FAKE_DIR unset
 * or no script file, returns all zeros (callers treat that as invalid data,
 * never as a real battery)
 */

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>

#include "power_sources.h"

static long read_cursor(const char* dir) {
  char path[PATH_MAX];
  snprintf(path, sizeof(path), "%s/battery_cursor", dir);

  FILE* f = fopen(path, "r");
  if (f == NULL) {
    return 0;
  }
  long cursor = 0;
  if (fscanf(f, "%ld", &cursor) != 1) {
    cursor = 0;
  }
  fclose(f);
  return cursor;
}

static void write_cursor(const char* dir, long cursor) {
  char path[PATH_MAX];
  snprintf(path, sizeof(path), "%s/battery_cursor", dir);

  FILE* f = fopen(path, "w");
  if (f != NULL) {
    fprintf(f, "%ld", cursor);
    fclose(f);
  }
}

BatteryInfo FetchBatteryInfo(void) {
  BatteryInfo info = {0};
  const char* dir = getenv("BATTERYTOOL_FAKE_DIR");
  if (dir == NULL) {
    return info;
  }

  char path[PATH_MAX];
  snprintf(path, sizeof(path), "%s/battery_script", dir);

  FILE* f = fopen(path, "r");
  if (f == NULL) {
    return info;
  }

  long cursor = read_cursor(dir);
  char line[128], last[128] = {0}, selected[128] = {0};
  long index = 0;
  while (fgets(line, sizeof(line), f) != NULL) {
    if (index == cursor) {
      snprintf(selected, sizeof(selected), "%s", line);
    }
    snprintf(last, sizeof(last), "%s", line);
    index++;
  }
  fclose(f);

  /* Past the end of the script, keep returning the final row. */
  const char* row = selected[0] != '\0' ? selected : last;
  int charging = 0, plugged = 0;
  if (sscanf(row, "%d %d %d %d %d %d", &info.current_capacity,
             &info.max_capacity, &info.design_capacity, &info.cycle_count,
             &charging, &plugged) == 6) {
    info.is_charging = charging != 0;
    info.is_plugged_in = plugged != 0;
  }

  write_cursor(dir, cursor + 1);
  return info;
}
