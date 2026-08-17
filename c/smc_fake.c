/*
 * File-backed fake of the SMC layer (smc.h) for sandboxed testing
 *
 * State lives in $BATTERYTOOL_FAKE_DIR so tests can steer hardware behavior
 * from outside the process:
 *
 *   smc_keys        one "KEY <byte-size> <hex-value>" line per key; the set
 *                   of SMC keys that "exist" and their current values
 *   smc_writes.log  append-only listener log, "KEY=<hex-value>" per
 *                   successful write. Tests assert on this file
 *
 * With BATTERYTOOL_FAKE_DIR unset the fake is inert: SMCOpen fails and every
 * wrapper call returns -1 without touching the filesystem or hardware
 *
 * The directory is re-read from the environment on every call, so tests in
 * the same process can each point the fake at their own tmp dir
 */

#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "smc.h"

#define MAX_VALUE_HEX 64

static void fake_path(char *buf, size_t size, const char *file) {
  snprintf(buf, size, "%s/%s", getenv("BATTERYTOOL_FAKE_DIR"), file);
}

static void bytes_to_hex(const unsigned char *bytes, UInt32 len, char *out) {
  for (UInt32 i = 0; i < len; i++) {
    sprintf(out + i * 2, "%02x", bytes[i]);
  }
  out[len * 2] = '\0';
}

static void hex_to_bytes(const char *hex, unsigned char *bytes, UInt32 len) {
  for (UInt32 i = 0; i < len; i++) {
    char pair[3] = {hex[i * 2], hex[i * 2 + 1], '\0'};
    bytes[i] = (unsigned char)strtol(pair, NULL, 16);
  }
}

/* Look up a key in smc_keys. Returns 1 and fills hex value + size if found. */
static int lookup_key(const char *key, char *hex_out, UInt32 *size_out) {
  if (getenv("BATTERYTOOL_FAKE_DIR") == NULL) {
    return 0;
  }

  char path[PATH_MAX];
  fake_path(path, sizeof(path), "smc_keys");

  FILE *f = fopen(path, "r");
  if (f == NULL) {
    return 0;
  }

  char line[128], file_key[8], file_value[MAX_VALUE_HEX + 1];
  unsigned int file_size;
  int found = 0;
  while (fgets(line, sizeof(line), f) != NULL) {
    if (sscanf(line, "%7s %u %64s", file_key, &file_size, file_value) == 3 &&
        strncmp(file_key, key, 4) == 0) {
      strncpy(hex_out, file_value, MAX_VALUE_HEX);
      hex_out[MAX_VALUE_HEX] = '\0';
      *size_out = (UInt32)file_size;
      found = 1;
      break;
    }
  }
  fclose(f);
  return found;
}

/* Rewrite smc_keys with a new value for key. Key must exist (the wrapper
 * reads before writing, so SMCCall2 never sees unknown keys). */
static void update_key(const char *key, const char *hex) {
  char path[PATH_MAX];
  fake_path(path, sizeof(path), "smc_keys");

  FILE *f = fopen(path, "r");
  if (f == NULL) {
    return;
  }

  char contents[4096] = {0};
  char line[128], file_key[8], file_value[MAX_VALUE_HEX + 1];
  unsigned int file_size;
  size_t used = 0;
  while (fgets(line, sizeof(line), f) != NULL) {
    if (sscanf(line, "%7s %u %64s", file_key, &file_size, file_value) == 3 &&
        strncmp(file_key, key, 4) == 0) {
      used += snprintf(contents + used, sizeof(contents) - used, "%s %u %s\n",
                       file_key, file_size, hex);
    } else {
      used += snprintf(contents + used, sizeof(contents) - used, "%s", line);
    }
  }
  fclose(f);

  f = fopen(path, "w");
  if (f != NULL) {
    fputs(contents, f);
    fclose(f);
  }
}

/* The listener: append one "KEY=<hex>" line to smc_writes.log. */
static void log_write(const char *key, const char *hex) {
  char path[PATH_MAX];
  fake_path(path, sizeof(path), "smc_writes.log");

  FILE *f = fopen(path, "a");
  if (f != NULL) {
    fprintf(f, "%s=%s\n", key, hex);
    fclose(f);
  }
}

kern_return_t SMCOpen(io_connect_t *conn) {
  if (getenv("BATTERYTOOL_FAKE_DIR") == NULL) {
    return kIOReturnError;
  }
  *conn = 0;
  return kIOReturnSuccess;
}

kern_return_t SMCClose(io_connect_t conn) {
  (void)conn;
  return kIOReturnSuccess;
}

kern_return_t SMCReadKey2(UInt32Char_t key, SMCVal_t *val, io_connect_t conn) {
  (void)conn;

  char hex[MAX_VALUE_HEX + 1];
  UInt32 size;
  if (!lookup_key(key, hex, &size)) {
    return kIOReturnNotFound;
  }

  memset(val, 0, sizeof(SMCVal_t));
  strncpy(val->key, key, sizeof(val->key));
  val->dataSize = size;
  hex_to_bytes(hex, val->bytes, size);
  return kIOReturnSuccess;
}

kern_return_t SMCCall2(int index, SMCKeyData_t *input_structure,
                       SMCKeyData_t *output_structure, io_connect_t conn) {
  (void)output_structure;
  (void)conn;

  if (index != KERNEL_INDEX_SMC ||
      input_structure->data8 != SMC_CMD_WRITE_BYTES) {
    return kIOReturnError;
  }

  /* The wrapper packs the 4 ASCII key chars big-endian into input.key. */
  char key[5];
  for (int i = 0; i < 4; i++) {
    key[i] = (char)(input_structure->key >> (24 - 8 * i));
  }
  key[4] = '\0';

  char hex[MAX_VALUE_HEX + 1];
  bytes_to_hex(input_structure->bytes, input_structure->keyInfo.dataSize, hex);

  update_key(key, hex);
  log_write(key, hex);
  return kIOReturnSuccess;
}

/* Same big-endian ASCII packing as the real smc.c (smcFanControl). */
UInt32 _strtoul(char *str, int size, int base) {
  (void)base;

  UInt32 total = 0;
  for (int i = 0; i < size; i++) {
    total += (UInt32)(unsigned char)str[i] << ((size - 1 - i) * 8);
  }
  return total;
}
