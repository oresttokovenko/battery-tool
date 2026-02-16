// Preventing clang-format from auto-sorting headers
// cmocka needs stddef.h (for size_t) and setjmp.h (for
// jmp_buf) included before it

// clang-format off
#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>
// clang-format on
#include <stdio.h>

#include "power_sources.h"

// (void)state just silences the "unused parameter" compiler warning
static void TestFetchBatteryInfo(void** state) {
  (void)state;

  BatteryInfo info = FetchBatteryInfo();

  double health = (double)info.max_capacity / info.design_capacity * 100.0;

  assert_true(info.current_capacity > 0);
  assert_true(info.max_capacity > 0);
  assert_true(info.design_capacity > 0);
  assert_true(info.cycle_count >= 0);
  assert_true(health >= 1 && health <= 100);
}

int main(void) {
  const struct CMUnitTest kTests[] = {
      cmocka_unit_test(TestFetchBatteryInfo),
  };

  return cmocka_run_group_tests(kTests, NULL, NULL);
}
