// Preventing clang-format from auto-sorting headers
// cmocka needs stddef.h (for size_t) and setjmp.h (for
// jmp_buf) included before it

// clang-format off
#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>
// clang-format on
#include <string.h>

#include "smc_wrapper.h"

// Read a well-known SMC key that every Mac exposes.
// "#KEY" returns a 4-byte big-endian uint32 with the total number of keys.
static void TestSmcReadKey(void** state) {
  (void)state;

  char buf[32];
  memset(buf, 0, sizeof(buf));

  int rc = SmcReadKey("#KEY", buf, sizeof(buf));
  assert_int_equal(rc, 0);

  // The value is a 4-byte big-endian integer representing total key count.
  // Any real Mac will have at least one key, so at least one byte is nonzero.
  int all_zero = 1;
  for (int i = 0; i < 4; i++) {
    if (buf[i] != 0) {
      all_zero = 0;
      break;
    }
  }
  assert_int_equal(all_zero, 0);
}

int main(void) {
  const struct CMUnitTest kTests[] = {
      cmocka_unit_test(TestSmcReadKey),
  };

  return cmocka_run_group_tests(kTests, NULL, NULL);
}
