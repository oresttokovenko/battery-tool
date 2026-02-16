/*
 * Thin wrapper around the low-level SMC functions (smc.c) that presents a
 * simple, stateless API suitable for CFFI consumption.  Each call opens and
 * closes its own SMC connection so the Python side never has to manage
 * IOKit handles or SMC-specific types
 */

#include "smc_wrapper.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "smc.h"

int SmcReadKey(const char *key, char *value, int value_size) {
  io_connect_t conn;
  kern_return_t result;
  SMCVal_t val;

  result = SMCOpen(&conn);
  if (result != kIOReturnSuccess) {
    return -1;
  }

  UInt32Char_t smc_key;
  strncpy(smc_key, key, sizeof(smc_key));
  smc_key[sizeof(smc_key) - 1] = '\0';

  result = SMCReadKey2(smc_key, &val, conn);
  SMCClose(conn);

  if (result != kIOReturnSuccess) {
    return -1;
  }

  int copy_size = (int)val.dataSize;
  if (copy_size > value_size) {
    copy_size = value_size;
  }
  memcpy(value, val.bytes, copy_size);

  return 0;
}

int SmcWriteKey(const char *key, const char *value) {
  io_connect_t conn;
  kern_return_t result;
  SMCVal_t read_val;
  SMCKeyData_t input_structure;
  SMCKeyData_t output_structure;

  result = SMCOpen(&conn);
  if (result != kIOReturnSuccess) {
    return -1;
  }

  UInt32Char_t smc_key;
  strncpy(smc_key, key, sizeof(smc_key));
  smc_key[sizeof(smc_key) - 1] = '\0';

  result = SMCReadKey2(smc_key, &read_val, conn);
  if (result != kIOReturnSuccess) {
    SMCClose(conn);
    return -1;
  }

  SMCVal_t write_val;
  memset(&write_val, 0, sizeof(SMCVal_t));
  strncpy(write_val.key, smc_key, sizeof(write_val.key));
  write_val.key[sizeof(write_val.key) - 1] = '\0';

  size_t hex_len = strlen(value);
  write_val.dataSize = (UInt32)(hex_len / 2);
  if (write_val.dataSize != read_val.dataSize) {
    SMCClose(conn);
    return -1;
  }

  for (UInt32 i = 0; i < write_val.dataSize; i++) {
    char c[3] = {value[(size_t)i * 2], value[(size_t)(i * 2) + 1], '\0'};
    write_val.bytes[i] = (unsigned char)strtol(c, NULL, 16);
  }

  memset(&input_structure, 0, sizeof(SMCKeyData_t));
  memset(&output_structure, 0, sizeof(SMCKeyData_t));

  input_structure.key = _strtoul(write_val.key, 4, 16);
  input_structure.data8 = SMC_CMD_WRITE_BYTES;
  input_structure.keyInfo.dataSize = write_val.dataSize;
  memcpy(input_structure.bytes, write_val.bytes, sizeof(write_val.bytes));

  result =
      SMCCall2(KERNEL_INDEX_SMC, &input_structure, &output_structure, conn);
  SMCClose(conn);

  if (result != kIOReturnSuccess) {
    return -1;
  }

  return 0;
}
