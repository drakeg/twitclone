from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_dockerfile_records_oci_release_provenance():
    dockerfile = read("Dockerfile")
    for required in (
        "ARG RIPPLE_BUILD_REVISION",
        "org.opencontainers.image.revision",
        "org.opencontainers.image.source",
        "org.opencontainers.image.created",
    ):
        assert required in dockerfile


def test_release_image_builder_defaults_to_local_arm64_and_no_push():
    script = read("scripts/build-release-image.sh")
    assert 'PLATFORM="${RIPPLE_BUILD_PLATFORM:-linux/arm64}"' in script
    assert 'PUSH="${RIPPLE_PUSH_IMAGE:-false}"' in script
    assert "docker build" in script
    assert 'if [[ "${PUSH}" == "true" ]]' in script
    assert "Image publication skipped (default)" in script


def test_release_builder_rejects_latest_and_dirty_checkout_by_default():
    script = read("scripts/build-release-image.sh")
    assert 'if [[ "${IMAGE_REF}" == *":latest" ]]' in script
    assert "Refusing release image build from a dirty checkout" in script
    assert "ALLOW_DIRTY_RELEASE_BUILD" in script


def test_release_builder_verifies_revision_label():
    script = read("scripts/build-release-image.sh")
    assert "org.opencontainers.image.revision" in script
    assert "Built image revision label mismatch" in script


def test_ci_builds_release_image_without_publishing_registry_artifacts():
    ci = read(".github/workflows/ci.yml")
    assert "Release image validation" in ci
    assert "bash scripts/build-release-image.sh" in ci
    assert "RIPPLE_BUILD_PLATFORM: linux/amd64" in ci
    assert "docker push" not in ci
