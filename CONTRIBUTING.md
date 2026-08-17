# Contributing

## Commit messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/) and [Release Please](https://github.com/googleapis/release-please) to automate versioning and changelog generation.

Every commit to `main` must follow this format:

```
type: short description
```

### Types

| Type       | Purpose                                      | Version bump |
|------------|----------------------------------------------|--------------|
| `feat`     | New feature                                  | Minor        |
| `fix`      | Bug fix                                      | Patch        |
| `docs`     | Documentation only                           | None         |
| `ci`       | CI/CD changes                                | None         |
| `refactor` | Code change that neither fixes nor adds      | None         |
| `test`     | Adding or updating tests                     | None         |
| `chore`    | Maintenance (deps, configs)                  | None         |

For breaking changes, add `!` after the type or include `BREAKING CHANGE:` in the commit body:

```
feat!: redesign SMC key API
```

### Examples

```
feat: add tahoe SMC key support for macOS 15.7+
fix: prevent double-close of SMC connection
ci: skip hardware-dependent tests on CI runners
docs: add contributing guidelines
refactor: extract battery info fetch into wrapper function
test: add cmocka test for SmcReadKey
```

## How releases work

1. You merge PRs into `main` with conventional commit messages
2. Release Please automatically opens a "Release PR" that bumps the version in `pyproject.toml` and updates the changelog
3. When you merge the Release PR, a git tag (`v0.3.0`, etc.) is created
4. The tag triggers the publish workflow which builds the wheel and publishes to PyPI

Only `feat` and `fix` commits trigger a release. Types like `docs`, `ci`, `test`, and `chore` are included in the changelog but don't create a new release on their own.

## Development

### Prerequisites

- macOS (Apple Silicon)
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- [just](https://github.com/casey/just)

### Setup

```bash
uv sync --all-groups
```

### Running checks

```bash
just c-test          # Run all C tests (including hardware)
just c-test-ci       # Run C tests excluding hardware-dependent tests
just c-check         # Format check + lint + C tests
just python-check    # Format check + lint + typecheck
just check           # All checks
```

### C code

C sources live in `c/`. The third-party `smc.c`/`smc.h` are excluded from formatting and linting. All other C files are checked by `clang-format` and `clang-tidy`.

Hardware-dependent C tests (those that talk to the SMC or IOKit) are tagged with `suite: 'hardware'` in meson and skipped in CI.

## Testing against the fake backend

Tests never touch real hardware and never use mocks. Instead, the package is built with **two** extension modules exposing the same API:

- `iokit_wrapper`: the real one, talks to IOKit/SMC
- `iokit_wrapper_fake`: file-backed fakes (`c/smc_fake.c`, `c/power_sources_fake.c`)

Setting `BATTERYTOOL_FAKE=1` makes `battery.py` bind the fake at import time, so the entire package, CLI included, runs the real code path end-to-end, including CFFI byte marshaling and the Tahoe fallback from CHIE to CH0J.

### How the fake is steered

The fake reads `$BATTERYTOOL_FAKE_DIR` on every call and keeps all state in files there:

| File | Role |
|------|------|
| `smc_keys` | One `KEY <byte-size> <hex-value>` line per key. Only these keys "exist"; reads/writes of anything else fail, exactly like real hardware |
| `battery_script` | One `current max design cycle is_charging is_plugged_in` row per line. Each `FetchBatteryInfo` poll consumes the next row; the last row repeats |
| `smc_writes.log` | The listener: every **successful** write appended as `KEY=hexvalue`. This is what tests assert on |

With `BATTERYTOOL_FAKE_DIR` unset the fake is inert (every call fails), so no code path in the test suite can accidentally write to a real SMC.

### Writing a Python test

Use the `hw` fixture from `tests/conftest.py`. It points the fake at a fresh tmp dir per test and exposes the three files as methods. Pass `interval=0` to the loops so they don't sleep:

```python
def test_tahoe_disables_above_max(hw):
    hw.set_keys({"CHTE": "00000000", "CHIE": "08"})  # keys that "exist"
    hw.script((96, 100, 100, 10, 1, 1), (79, 79, 100, 10, 1, 1))

    tahoe_loop(target_health=79, max_charge=95, min_charge=5, interval=0, logger=setup_logging())

    assert hw.writes() == ("CHTE=01000000", "CHIE=08", "CHTE=00000000", "CHIE=00")
```

To exercise the Tahoe fallback, omit `CHIE` from `set_keys`. The write then fails like real hardware and the loop falls back to `CH0J`.

Custom pytest marks (e.g. `apple_silicon`) are registered in `pyproject.toml` and applied in `conftest.py`'s `pytest_collection_modifyitems`, so don't add `skipif` logic inline in test files.

### Writing a C test

The fake itself is tested in `c/tests/test_smc_fake.c` with cmocka. Each test gets a fresh fake dir via the `FAKE_TEST(...)` macro (per-test setup/teardown). These tests carry no `hardware` suite tag, so they run everywhere, including CI.
