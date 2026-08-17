# Always use cmocka from subproject wrap (ensures consistent version)
cmocka_proj = subproject('cmocka')
cmocka_dep = cmocka_proj.get_variable('cmocka_dep')

test_power_sources = executable(
  'test_power_sources',
  'test_power_sources.c',
  '../power_sources.c',
  dependencies: [
    cmocka_dep,
    dependency('appleframeworks', modules: ['IOKit', 'CoreFoundation']),
  ],
  include_directories: include_directories('..'),
)

test('power_sources tests', test_power_sources, suite: 'hardware')

test_smc_wrapper = executable(
  'test_smc_wrapper',
  'test_smc_wrapper.c',
  '../smc.c',
  '../smc_wrapper.c',
  dependencies: [
    cmocka_dep,
    dependency('appleframeworks', modules: ['IOKit', 'CoreFoundation']),
  ],
  include_directories: include_directories('..'),
)

test('smc_wrapper tests', test_smc_wrapper, suite: 'hardware')

test_smc_fake = executable(
  'test_smc_fake',
  'test_smc_fake.c',
  '../smc_fake.c',
  '../smc_wrapper.c',
  '../power_sources_fake.c',
  dependencies: [
    cmocka_dep,
    dependency('appleframeworks', modules: ['IOKit', 'CoreFoundation']),
  ],
  include_directories: include_directories('..'),
)

# No 'hardware' suite: safe to run anywhere, including CI and VMs.
test('smc_fake tests', test_smc_fake)
