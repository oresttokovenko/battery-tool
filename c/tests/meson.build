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

test('power_sources tests', test_power_sources)
