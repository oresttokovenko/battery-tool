#ifndef POWER_SOURCES_H
#define POWER_SOURCES_H

#include <stdbool.h>

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

#endif
