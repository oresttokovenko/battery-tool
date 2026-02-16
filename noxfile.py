import nox

nox.options.default_venv_backend = "uv"

PYTHON_VERSIONS = ["3.12"]
PYPROJECT = nox.project.load_toml("pyproject.toml")
CORE_DEPS = PYPROJECT["project"]["dependencies"]
DEV_DEPS = nox.project.dependency_groups(PYPROJECT, "dev")


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    session.install(*CORE_DEPS)
    session.install(*DEV_DEPS)
    session.run("python", "-m", "pytest", *session.posargs)


@nox.session
def lint(session):
    session.install(*DEV_DEPS)
    session.run("ruff", "check", "src/batterytool")


@nox.session
def format_check(session):
    session.install(*DEV_DEPS)
    session.run("ruff", "format", "--check", "src/batterytool")


@nox.session
def type_check(session):
    session.install(*CORE_DEPS)
    session.install(*DEV_DEPS)
    session.run("basedpyright")


@nox.session
def c_test(session):
    session.install("meson")
    session.run("meson", "setup", "builddir", "--native-file", "native-macos.ini", success_codes=[0, 1])
    session.run("meson", "compile", "-C", "builddir")
    session.run("meson", "test", "-C", "builddir")
