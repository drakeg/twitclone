# Architecture

## Current state

Ripple is a modular Flask application backed by SQLite for local development and
managed PostgreSQL 18 for production. HTML templates and static assets provide
the browser interface. Production media uses a private S3-compatible adapter;
local development retains filesystem uploads.

## Current components

- **Web framework:** Flask application factory with modular blueprints
- **Persistence:** Flask-SQLAlchemy with local SQLite and production PostgreSQL 18
- **Migrations:** Flask-Migrate/Alembic, run as an explicit release task
- **Authentication:** Flask-Login and Flask-Bcrypt
- **Forms and CSRF:** Flask-WTF
- **Background scheduling:** one separately controlled scheduled-worker process
- **Media:** validated image processing with local filesystem and private S3-compatible adapters
- **Presentation:** server-rendered Jinja templates and static assets
- **Billing:** provider-neutral plan/subscription/entitlement model with Stripe integration
- **Operations:** health checks, structured logging, deployment preflight, backup/restore and release-evidence contracts

## Existing domain capabilities

- Users, authentication, and account recovery
- Following relationships and followed hashtags
- Posts, reposts, quotes, bookmarks, and scheduled publishing
- Direct messages and actionable notifications
- Image uploads and private durable production media
- Polls and votes
- Community standards, reporting, and moderation workflows
- Identity verification and paid verified badges
- Ripple+ and Creator Pro subscriptions
- Measured creator analytics and performance insights

## Current architectural risks

### Single application-host launch boundary

Sprint 8's selected low-traffic AWS topology intentionally begins with one EC2
application host. Web and scheduled-worker processes remain logically separate,
but the VM is a shared interruption boundary until measured load or availability
requirements justify a second host and load balancer.

### Single-AZ launch database

The initial managed PostgreSQL database is Single-AZ to control recurring cost.
Backups, restore rehearsals, independent logical dumps, and a documented
Multi-AZ upgrade path are therefore important parts of launch readiness.

### Secret delivery

Production secrets must remain outside source, container images, logs, and
Terraform outputs. The Sprint 8 implementation must define a repeatable bootstrap
and rotation path before apply.

### Release and recovery evidence

Production safety depends on actually exercising the existing migration,
deployment-preflight, backup/restore, rollback, and release-record procedures.
Documentation alone is not evidence that those procedures work in the selected
environment.

### Accessibility evidence

Automated accessibility regression coverage is established, but public launch
still requires the documented manual NVDA/VoiceOver and zoom evidence disposition.
No WCAG conformance claim is currently authorized.

## Target direction

The application remains a modular Flask monolith. Sprint 8 does not introduce a
distributed application architecture.

The selected initial AWS deployment direction is recorded in
[`ADR-0044-production-aws-topology.md`](architecture/ADR-0044-production-aws-topology.md):

- one ARM64 EC2 application host;
- one private managed PostgreSQL 18 database;
- one private encrypted/versioned S3 media bucket;
- exactly one scheduled worker;
- explicit migration and deployment-preflight jobs;
- no NAT Gateway, load balancer, CDN, or second host until justified;
- Terraform-managed infrastructure with a dated cost gate before apply.

This preserves a low-cost path without weakening the durable-state and security
boundaries established in Sprint 6.

## Architecture decision policy

Significant decisions are recorded under `docs/architecture/` when they affect
security, data storage, deployment, operating cost, external services, or major
application structure.
