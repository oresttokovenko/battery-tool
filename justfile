# List all available commands
default:
    @just --list

# ==================== C Recipes ====================

[doc("Format C code with clang-format")]
c-format:
    clang-format -i c/*.c c/*.h

[doc("Check C code formatting without modifying files")]
c-format-check:
    clang-format --dry-run --Werror c/*.c c/*.h

[doc("Lint C code with clang-tidy")]
c-lint:
    clang-tidy c/power_sources.c

[doc("Lint and fix C code with clang-tidy")]
c-lint-fix:
    clang-tidy --fix c/power_sources.c

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

# ==================== Setup & Dependencies ====================

[doc("Check for required dependencies")]
check-deps:
    @echo "Checking dependencies..."
    @command -v clang-format >/dev/null 2>&1 || (echo "❌ clang-format not found" && exit 1)
    @command -v clang-tidy >/dev/null 2>&1 || (echo "❌ clang-tidy not found" && exit 1)
    @command -v meson >/dev/null 2>&1 || (echo "❌ meson not found" && exit 1)
    @pkg-config --exists cmocka || (echo "❌ cmocka not found" && exit 1)
    @echo "✅ All dependencies found!"

[doc("Install all dependencies via Homebrew")]
setup:
    brew bundle

# ==================== Build & Install ====================

[doc("Build the project with meson")]
build:
    uv run meson setup builddir --native-file native-macos.ini || true
    uv run meson compile -C builddir

[doc("Wipe build directory and rebuild from scratch")]
rebuild:
    uv run meson setup builddir --native-file native-macos.ini --wipe
    uv run meson compile -C builddir

[doc("Clean build artifacts")]
clean:
    rm -rf builddir build dist *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type d -name .pytest_cache -exec rm -rf {} +

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
