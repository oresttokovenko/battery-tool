# CFFI + meson integration

# CFFI doesn't have native meson support, so we use custom_target()
# to generate C wrapper code, then compile it with our sources.
# Approach borrowed from: https://github.com/grimme-lab/xtb-python

# Run CFFI ffibuilder to generate C wrapper code
# this translates between Python objects and C structs/functions
cffi_generated = custom_target(
  'iokit_cffi_gen',
  output: '_iokit_wrapper.c',
  command: [
    py,
    meson.current_source_dir() / 'build_iokit.py',
    '@OUTPUT@',
  ],
)

# Compile CFFI-generated code + C sources into extension
py.extension_module(
  'iokit_wrapper',
  [cffi_generated, 'smc.c', 'smc_wrapper.c', 'power_sources.c'],
  dependencies: [
    dependency('appleframeworks', modules: ['IOKit', 'CoreFoundation']),
  ],
  install: true,
  subdir: 'batterytool',
)

subdir('tests')
