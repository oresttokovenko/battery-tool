# List all available commands
default:
    @just --list

# ==================== C Recipes ====================

# Third-party SMC files excluded from formatting/linting
c_sources := `find c -maxdepth 1 \( -name '*.c' -o -name '*.h' \) ! -name 'smc.c' ! -name 'smc.h' | tr '\n' ' '`

[doc("Format C code with clang-format")]
c-format:
    clang-format -i {{ c_sources }}

[doc("Check C code formatting without modifying files")]
c-format-check:
    clang-format --dry-run --Werror {{ c_sources }}

[doc("Lint C code with clang-tidy")]
c-lint:
    clang-tidy {{ c_sources }}

[doc("Lint and fix C code with clang-tidy")]
c-lint-fix:
    clang-tidy --fix {{ c_sources }}

[doc("Run C tests with cmocka")]
c-test:
    uv run meson test -C builddir

[doc("Run all C checks (format + lint + test)")]
c-check: c-format-check c-lint c-test

# ==================== Python Recipes ====================

[doc("Format pyproject.toml")]
python-format-toml:
    uv run pyproject-fmt pyproject.toml

[doc("Format Python code with ruff")]
python-format:
    uv run ruff format

[doc("Check Python formatting without modifying files")]
python-format-check:
    uv run ruff format --check

[doc("Lint Python code with ruff")]
python-lint:
    uv run ruff check

[doc("Fix Python linting issues automatically")]
python-lint-fix:
    uv run ruff check --fix

[doc("Type check Python code with basedpyright")]
python-typecheck:
    uv run basedpyright

[doc("Run all Python checks (format + lint + typecheck)")]
python-check: python-format-check python-lint python-typecheck

# ==================== Build & Install ====================

[doc("Build the project with meson")]
build:
    uv run meson compile -C builddir

[doc("Wipe build directory and rebuild from scratch")]
rebuild:
    uv run meson setup builddir --native-file native-macos.ini --wipe
    uv run meson compile -C builddir

[doc("Clean build artifacts")]
clean:
    rm -rf builddir build dist *.egg-info

[doc("Install the package in development mode")]
install:
    uv sync --all-groups

# ==================== Combined Recipes ====================

[doc("Run all checks (Python + C)")]
check: python-check c-check

[doc("Format all code (Python + C)")]
format: python-format c-format

[doc("Run all checks and build")]
all: check build
