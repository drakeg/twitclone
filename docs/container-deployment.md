# Container-first production deployment

Ripple's production deployment unit is the same container image used throughout development and CI. Sprint 8 deliberately avoids a separate AWS-only application runtime. The current local `compose.yaml` remains the everyday development/test path; `compose.production.yaml` defines the future production release contract.

No AWS resources or recurring spend are required to develop, test, review, or merge this deployment contract.

## Current local workflow

Continue using the existing local stack:

```bash
docker compose up --build
```

Use `RIPPLE_PORT` when several local applications are running at once:

```bash
RIPPLE_PORT=8001 docker compose up --build
```

Nothing in Sprint 8 changes the SQLite/filesystem-backed local development contract.

## Production container topology

`compose.production.yaml` defines five roles:

1. `migrate` — one-shot Alembic/Flask-Migrate upgrade.
2. `preflight` — one-shot production database and private-media verification.
3. `web` — Gunicorn only; no migrations and no scheduler side effects.
4. `worker` — exactly one scheduled-post worker.
5. `proxy` — Caddy TLS/reverse-proxy endpoint in front of the web container.

The production Compose file does not build application source on the server. It requires `RIPPLE_IMAGE` to identify an immutable release image. `:latest` is rejected by the deployment script because rollback and release evidence must identify an exact release.

## Production environment file

Start from `deploy/env.production.example`, but place the populated file outside the repository on the deployment host. The default deployment path is:

```text
/etc/ripple/ripple.env
```

The real file must be readable only by the deployment/operator account. It contains secrets and must never be committed.

Production requires at minimum:

- `TWITCLONE_ENV=production`
- a strong `SECRET_KEY`
- a PostgreSQL `DATABASE_URL`
- `MEDIA_STORAGE_BACKEND=s3`
- `MEDIA_S3_BUCKET`
- `MEDIA_S3_REGION`

AWS credentials are intentionally absent. On EC2, Boto3 should obtain temporary S3 credentials from the IAM instance role created by Terraform.

## Release inputs

The deployment wrapper requires:

```bash
export RIPPLE_IMAGE='registry.example/ripple:<immutable-tag-or-digest>'
export RIPPLE_DOMAIN='ripple.example.com'
export RIPPLE_TLS_EMAIL='operator@example.com'
export RIPPLE_ENV_FILE='/etc/ripple/ripple.env'
```

Story 8.3 does not select or create a paid container registry. Image publication is a separate release-pipeline concern. Until that exists, the production contract can be reviewed and validated without deploying it.

## Validate without deploying

Once an image reference and host-only environment file are available, validate the Compose model without starting services:

```bash
bash scripts/deploy-production.sh validate
```

This runs `docker compose config --quiet`. It does not run Terraform and does not create AWS infrastructure.

## Deploy sequence

When a future environment is explicitly authorized and already provisioned, the supported release sequence is:

```bash
bash scripts/deploy-production.sh deploy
```

The wrapper performs these steps in order:

1. validate the production Compose configuration;
2. pull the exact application/proxy images;
3. run migrations as a one-shot container;
4. run `deployment-preflight` as a separate one-shot container;
5. start the web and exactly one worker container;
6. start the TLS proxy only after the web service can become healthy;
7. print container status and the remaining manual release checks.

The script intentionally does **not** run `terraform apply`.

After deployment, release approval still requires the checks in `docs/operations.md`, including HTTPS, `/health/live`, `/health/ready`, login, timeline reads, media retrieval, scheduled-worker behavior, Stripe webhook reachability when enabled, backup evidence, and rollback readiness.

## Rollback

Rollback changes application containers only. It never automatically downgrades the database:

```bash
export PREVIOUS_RIPPLE_IMAGE='registry.example/ripple:<previous-known-good>'
bash scripts/deploy-production.sh rollback
```

This matches the existing rollback contract: when the schema remains compatible, restore the previous application image and verify the service. Incompatible/destructive migration failures require the rehearsed forward-fix or restore path in `docs/operations.md`.

## TLS and reverse proxy

`deploy/Caddyfile` terminates public HTTPS and proxies only to `web:8000`. Caddy manages the public certificate when DNS points at the host and ports 80/443 are reachable. The proxy also supplies HSTS, `X-Content-Type-Options`, and a conservative referrer policy.

The application container itself is not published directly to the Internet in the production Compose model.

## Push-button AWS boundary

The intended end state is a small number of explicit operator actions rather than handcrafted host configuration:

1. review the dated Terraform plan and cost estimate;
2. explicitly authorize spend;
3. apply the approved Terraform;
4. bootstrap Docker/Compose and the host-only environment file;
5. publish/select an immutable Ripple image;
6. run the container deployment wrapper;
7. complete release evidence.

Stories after 8.3 can automate the remaining bootstrap/image-delivery pieces. Until then, Ripple remains fully usable through the existing local Docker Compose workflow and no AWS resources are necessary.
