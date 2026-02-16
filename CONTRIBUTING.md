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
