from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_project_file(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_gunicorn_is_an_exact_runtime_dependency():
    requirements = read_project_file("requirements.txt").splitlines()

    assert "gunicorn==26.0.0" in requirements
    assert "psycopg[binary]==3.3.4" in requirements


def test_image_defaults_to_the_supported_wsgi_entry_point():
    dockerfile = read_project_file("Dockerfile")
    command = dockerfile.split("CMD ", maxsplit=1)[1]

    assert '"gunicorn"' in command
    assert '"application:application"' in command
    assert '"--workers", "1"' in command
    assert "flask" not in command
    assert "db upgrade" not in command


def test_compose_keeps_migration_web_and_worker_processes_separate():
    compose = read_project_file("compose.yaml")

    assert "command: flask --app application db upgrade" in compose
    assert (
        "command: gunicorn --bind 0.0.0.0:8000 --workers 1 --threads 4 "
        "--timeout 30 application:application"
    ) in compose
    assert "command: python -m twitclone.scheduled_worker" in compose
    assert "http://127.0.0.1:8000/health/ready" in compose
    assert "flask --app application run" not in compose
    assert compose.count("condition: service_completed_successfully") == 2


def test_compose_test_service_is_isolated_from_local_application_data():
    compose = read_project_file("compose.yaml")

    assert 'profiles: ["tools"]' in compose
    assert "command: python -m pytest --strict-markers --maxfail=1" in compose
    assert "TWITCLONE_ENV: testing" in compose
    assert 'DATABASE_URL: "sqlite:///:memory:"' in compose
    test_service = compose.split("  test:\n", maxsplit=1)[1].split("\nvolumes:", maxsplit=1)[0]
    assert "twitclone_data" not in test_service
