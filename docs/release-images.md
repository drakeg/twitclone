# Immutable release images

Ripple's production deployment contract consumes an immutable container image through `RIPPLE_IMAGE`. Story 8.4 makes that image reproducible and verifiable without requiring AWS, ECR, or any paid registry.

## Zero-spend local workflow

From a clean checkout:

```bash
bash scripts/build-release-image.sh
```

By default the script:

- derives the release revision from the current Git commit;
- builds `linux/arm64`, matching the planned AWS `t4g.small` host;
- tags the image as `ripple:<first-12-characters-of-SHA>`;
- records OCI source, revision, and creation labels in the image;
- verifies the built revision label against the Git revision;
- does **not** push to a registry.

The local image can then be supplied to the production Compose model for non-cloud validation:

```bash
export RIPPLE_IMAGE="ripple:$(git rev-parse --short=12 HEAD)"
```

The normal development stack remains unchanged and does not need a release image:

```bash
docker compose up --build
```

## Dirty checkout guard

Release builds refuse a dirty Git checkout by default. This prevents an image from claiming a commit SHA while silently containing uncommitted source changes.

`ALLOW_DIRTY_RELEASE_BUILD=true` exists only for local experimentation and should never be used for a release candidate.

## Registry publication

Publication is opt-in and registry-neutral. The repository does not create ECR, GitHub Container Registry packages, or any other registry automatically.

After authenticating Docker to a registry you have deliberately selected:

```bash
RIPPLE_IMAGE_REF='registry.example.com/ripple:<immutable-tag>' \
RIPPLE_PUSH_IMAGE=true \
bash scripts/build-release-image.sh
```

The build script will reject `:latest`. For production, prefer the registry-provided digest after publication and record that digest in release evidence. A digest reference is stronger than a mutable tag because the exact image content cannot move underneath the release record.

## CI validation

GitHub CI builds the same release-image contract on the runner's native `linux/amd64` platform and imports the application from the resulting container. CI never runs `docker push`, so pull requests do not publish package artifacts or incur an AWS registry cost.

The production default remains ARM64 because ADR-0044 selects a Graviton `t4g.small` host. If that architecture changes, update the release-image default and architecture decision together.

## AWS handoff later

When AWS deployment is explicitly authorized, a later story may choose ECR and add authentication/publication automation. That work must remain separate from infrastructure creation and must include a current ECR cost review before enabling retention or automated publication.

Nothing in this workflow runs Terraform or creates AWS resources.
