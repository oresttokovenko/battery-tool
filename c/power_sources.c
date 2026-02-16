#include "power_sources.h"

#include <CoreFoundation/CoreFoundation.h>
#include <IOKit/IOKitLib.h>
#include <stdio.h>

static const char kAppleSmartBattery[] = "AppleSmartBattery";

// AppleSmartBattery dictionary keys
static const char kCurrentCapacityKey[] = "AppleRawCurrentCapacity";
static const char kMaxCapacityKey[] = "AppleRawMaxCapacity";
static const char kDesignCapacityKey[] = "DesignCapacity";
static const char kCycleCountKey[] = "CycleCount";
static const char kIsChargingKey[] = "IsCharging";
static const char kExternalConnectedKey[] = "ExternalConnected";

static bool GetDictInt(CFDictionaryRef dict, const char *key, void *out,
                       CFNumberType type) {
  CFStringRef cf_key =
      CFStringCreateWithCString(NULL, key, kCFStringEncodingUTF8);
  CFNumberRef ref = CFDictionaryGetValue(dict, cf_key);
  CFRelease(cf_key);
  if (ref == NULL) {
    return false;
  }
  return CFNumberGetValue(ref, type, out);
}

static bool GetDictBool(CFDictionaryRef dict, const char *key, bool *out) {
  CFStringRef cf_key =
      CFStringCreateWithCString(NULL, key, kCFStringEncodingUTF8);
  CFBooleanRef ref = CFDictionaryGetValue(dict, cf_key);
  CFRelease(cf_key);
  if (ref == NULL) {
    return false;
  }
  *out = CFBooleanGetValue(ref);
  return true;
}

BatteryInfo FetchBatteryInfo(void) {
  BatteryInfo info = {0};

  io_service_t entry = IOServiceGetMatchingService(
      kIOMainPortDefault, IOServiceMatching(kAppleSmartBattery));
  if (entry == IO_OBJECT_NULL) {
    return info;
  }

  CFMutableDictionaryRef properties;
  kern_return_t result = IORegistryEntryCreateCFProperties(
      entry, &properties, kCFAllocatorDefault, 0);
  IOObjectRelease(entry);
  if (result != kIOReturnSuccess) {
    return info;
  }

  GetDictInt(properties, kCurrentCapacityKey, &info.current_capacity,
             kCFNumberIntType);
  GetDictInt(properties, kMaxCapacityKey, &info.max_capacity, kCFNumberIntType);
  GetDictInt(properties, kDesignCapacityKey, &info.design_capacity,
             kCFNumberIntType);
  GetDictInt(properties, kCycleCountKey, &info.cycle_count, kCFNumberIntType);
  GetDictBool(properties, kIsChargingKey, &info.is_charging);
  GetDictBool(properties, kExternalConnectedKey, &info.is_plugged_in);

  CFRelease(properties);
  return info;
}
