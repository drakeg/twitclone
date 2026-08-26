from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_ci_cancels_superseded_runs_and_uses_dependency_cache():
    ci = read(".github/workflows/ci.yml")

    assert "cancel-in-progress: true" in ci
    assert "cache: pip" in ci
    assert "cache-dependency-path:" in ci
    assert "python -m pip install --upgrade pip" not in ci


def test_release_image_ci_uses_persistent_buildx_cache():
    ci = read(".github/workflows/ci.yml")
    builder = read("scripts/build-release-image.sh")

    assert "docker/setup-buildx-action" in ci
    assert 'RIPPLE_USE_BUILDX: "true"' in ci
    assert "--cache-from type=gha" in builder
    assert "--cache-to type=gha,mode=max" in builder
    assert "--target runtime" in builder


def test_release_runtime_does_not_install_development_dependencies():
    dockerfile = read("Dockerfile")

    assert "FROM base AS runtime" in dockerfile
    assert "FROM runtime AS development" in dockerfile
    runtime = dockerfile.split("FROM base AS runtime", 1)[1].split("FROM runtime AS development", 1)[0]
    assert "requirements-dev.txt" not in runtime
    assert "requirements-dev.txt" in dockerfile.split("FROM runtime AS development", 1)[1]


def test_volatile_release_labels_follow_dependency_layer():
    dockerfile = read("Dockerfile")

    install_index = dockerfile.index("RUN pip install --no-cache-dir -r requirements.txt")
    created_label_index = dockerfile.index("org.opencontainers.image.created")
    assert created_label_index > install_index


def test_docker_build_context_excludes_non_runtime_trees():
    ignored = read(".dockerignore").splitlines()

    for path in (".github", "docs", "infra", "tests"):
        assert path in ignored


def test_terraform_provider_downloads_are_cached():
    ci = read(".github/workflows/ci.yml")

    assert "TF_PLUGIN_CACHE_DIR" in ci
    assert "Restore Terraform provider cache" in ci
    assert "actions/cache@v5" in ci
