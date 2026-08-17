// Preventing clang-format from auto-sorting headers
// cmocka needs stddef.h (for size_t) and setjmp.h (for
// jmp_buf) included before it

// clang-format off
#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>
// clang-format on
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "power_sources.h"
#include "smc_wrapper.h"

// Each test gets a fresh fake-hardware dir via the group fixtures.
static char test_dir[PATH_MAX];

static int SetupFakeDir(void** state) {
  (void)state;

  strcpy(test_dir, "/tmp/batterytool_fake_test_XXXXXX");
  assert_non_null(mkdtemp(test_dir));
  assert_int_equal(setenv("BATTERYTOOL_FAKE_DIR", test_dir, 1), 0);
  return 0;
}

static int TeardownFakeDir(void** state) {
  (void)state;

  char path[PATH_MAX];
  const char* files[] = {"smc_keys", "smc_writes.log", "battery_script",
                         "battery_cursor"};
  for (size_t i = 0; i < sizeof(files) / sizeof(files[0]); i++) {
    snprintf(path, sizeof(path), "%s/%s", test_dir, files[i]);
    unlink(path);
  }
  rmdir(test_dir);
  unsetenv("BATTERYTOOL_FAKE_DIR");
  return 0;
}

static void WriteFile(const char* name, const char* contents) {
  char path[PATH_MAX];
  snprintf(path, sizeof(path), "%s/%s", test_dir, name);

  FILE* f = fopen(path, "w");
  assert_non_null(f);
  fputs(contents, f);
  fclose(f);
}

static void ReadFile(const char* name, char* buf, size_t size) {
  char path[PATH_MAX];
  snprintf(path, sizeof(path), "%s/%s", test_dir, name);

  FILE* f = fopen(path, "r");
  assert_non_null(f);
  size_t n = fread(buf, 1, size - 1, f);
  buf[n] = '\0';
  fclose(f);
}

static void TestInertWithoutDir(void** state) {
  (void)state;

  unsetenv("BATTERYTOOL_FAKE_DIR");

  char buf[32];
  assert_int_equal(SmcReadKey("CH0B", buf, sizeof(buf)), -1);
  assert_int_equal(SmcWriteKey("CH0B", "00"), -1);

  BatteryInfo info = FetchBatteryInfo();
  assert_int_equal(info.max_capacity, 0);
}

static void TestReadUnknownKeyFails(void** state) {
  (void)state;

  char buf[32];
  assert_int_equal(SmcReadKey("CH0B", buf, sizeof(buf)), -1);
}

static void TestWriteReadRoundTrip(void** state) {
  (void)state;

  WriteFile("smc_keys", "CH0B 1 00\n");

  assert_int_equal(SmcWriteKey("CH0B", "02"), 0);

  char buf[32] = {0};
  assert_int_equal(SmcReadKey("CH0B", buf, sizeof(buf)), 0);
  assert_int_equal((unsigned char)buf[0], 0x02);
}

static void TestWriteIsLoggedForListener(void** state) {
  (void)state;

  WriteFile("smc_keys", "CHTE 4 00000000\nCH0J 1 00\n");

  assert_int_equal(SmcWriteKey("CHTE", "01000000"), 0);
  assert_int_equal(SmcWriteKey("CH0J", "01"), 0);

  char log[256];
  ReadFile("smc_writes.log", log, sizeof(log));
  assert_string_equal(log, "CHTE=01000000\nCH0J=01\n");
}

static void TestWriteUnknownKeyFailsAndIsNotLogged(void** state) {
  (void)state;

  WriteFile("smc_keys", "CHTE 4 00000000\n");

  // CHIE is not in the key store, mirroring a Tahoe Mac without it.
  assert_int_equal(SmcWriteKey("CHIE", "08"), -1);

  char path[PATH_MAX];
  snprintf(path, sizeof(path), "%s/smc_writes.log", test_dir);
  assert_null(fopen(path, "r"));
}

static void TestWriteWrongSizeFails(void** state) {
  (void)state;

  WriteFile("smc_keys", "CH0B 1 00\n");

  // CH0B holds 1 byte; a 2-byte value must be rejected like the real wrapper.
  assert_int_equal(SmcWriteKey("CH0B", "0002"), -1);
}

static void TestBatteryScriptYieldsRowsInOrderThenRepeatsLast(void** state) {
  (void)state;

  WriteFile("battery_script", "96 100 100 10 1 1\n4 100 100 10 0 1\n");

  BatteryInfo first = FetchBatteryInfo();
  assert_int_equal(first.current_capacity, 96);
  assert_true(first.is_charging);
  assert_true(first.is_plugged_in);

  BatteryInfo second = FetchBatteryInfo();
  assert_int_equal(second.current_capacity, 4);
  assert_false(second.is_charging);

  BatteryInfo third = FetchBatteryInfo();
  assert_int_equal(third.current_capacity, 4);
}

static void TestMissingBatteryScriptReturnsZeros(void** state) {
  (void)state;

  BatteryInfo info = FetchBatteryInfo();
  assert_int_equal(info.max_capacity, 0);
  assert_int_equal(info.design_capacity, 0);
}

// Every test below runs with a fresh fake-hardware dir via per-test fixtures.
#define FAKE_TEST(fn) \
  cmocka_unit_test_setup_teardown(fn, SetupFakeDir, TeardownFakeDir)

int main(void) {
  const struct CMUnitTest kTests[] = {
      FAKE_TEST(TestInertWithoutDir),
      FAKE_TEST(TestReadUnknownKeyFails),
      FAKE_TEST(TestWriteReadRoundTrip),
      FAKE_TEST(TestWriteIsLoggedForListener),
      FAKE_TEST(TestWriteUnknownKeyFailsAndIsNotLogged),
      FAKE_TEST(TestWriteWrongSizeFails),
      FAKE_TEST(TestBatteryScriptYieldsRowsInOrderThenRepeatsLast),
      FAKE_TEST(TestMissingBatteryScriptReturnsZeros),
  };

  // No 'hardware' suite tag: these run everywhere, including CI.
  return cmocka_run_group_tests(kTests, NULL, NULL);
}
