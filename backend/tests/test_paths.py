from app.core.paths import backend_root, monorepo_root


def test_backend_root_contains_app_package() -> None:
    root = backend_root()
    assert (root / "app" / "main.py").is_file()
    assert (root / "pyproject.toml").is_file()


def test_monorepo_root_is_parent_of_backend() -> None:
    assert monorepo_root() == backend_root().parent
    assert (
        (monorepo_root() / "backend" / "pyproject.toml").resolve()
        == (backend_root() / "pyproject.toml").resolve()
    )
