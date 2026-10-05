"""Documentation contract checks for supported runtime and roadmap guidance."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_readme_runtime_matches_python_version_contract():
    readme = _read("README.md")
    python_minor = _read(".python-version").strip()

    assert f"Python {python_minor}.x" in readme
    assert "Python 3.11 or newer" not in readme


def test_configuration_docs_match_secret_key_runtime_contract():
    docs = _read("docs/configuration.md")

    assert "| `SECRET_KEY` | Yes | None |" in docs
    assert "Startup fails in every environment when absent." in docs
    assert "development fallback" not in docs.lower()


def test_readme_points_to_authoritative_roadmap_instead_of_duplication():
    readme = _read("README.md")

    assert "[`docs/ROADMAP.md`](docs/ROADMAP.md)" in readme
    assert "Do not use this" in readme
    assert "README as a second backlog" in readme
    assert "## Near-term roadmap" not in readme


def test_startup_paths_do_not_embed_predictable_secret_placeholders():
    app_py = _read("app.py")
    application_py = _read("application.py")
    secrets_docs = _read("docs/secrets.md")

    for placeholder in ("your_secret_key", "development-only-change-me"):
        assert placeholder not in app_py
        assert placeholder not in application_py

    assert "historical placeholder assignment" not in secrets_docs
    assert "tracked as an urgent removal item" not in secrets_docs
    assert "neither startup path contains a built-in application secret" in secrets_docs.lower()
