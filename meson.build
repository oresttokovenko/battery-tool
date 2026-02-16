project(
  'batterytool',
  'c',
  version: '0.2.1',
  license: 'Apache-2.0',
  meson_version: '>=1.2.0',
  default_options: [
    'warning_level=2',
  ],
)

if host_machine.system() != 'darwin'
  error('BatteryTool only works on macOS. Detected: ' + host_machine.system())
endif

cc = meson.get_compiler('c')
if not cc.get_id().contains('clang')
  error('Apple Clang is required to link against IOKit and CoreFoundation. Got: ' + cc.get_id())
endif

py = import('python').find_installation(pure: false, modules: ['cffi'])

py.install_sources(
  'src/batterytool/__init__.py',
  'src/batterytool/battery.py',
  'src/batterytool/constants.py',
  'src/batterytool/logging.py',
  'src/batterytool/loop.py',
  'src/batterytool/main.py',
  subdir: 'batterytool',
)

subdir('c')
